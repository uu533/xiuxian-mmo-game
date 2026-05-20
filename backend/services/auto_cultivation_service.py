"""
自动修行服务
核心：洞府挂机 / 离线结算 / 自动循环
"""

import json
import random

from sqlalchemy.orm import Session

from backend.configs.auto_cultivation import (
    ADVENTURE_CULTIVATION_GAIN_MAX,
    ADVENTURE_CULTIVATION_GAIN_MIN,
    ADVENTURE_MANA_COST,
    ADVENTURE_STONES_MAX,
    ADVENTURE_STONES_MIN,
    AUTO_DROP_TABLE,
    AUTO_STATE_NAMES,
    BATTLE_DAMAGE_MAX,
    BATTLE_DAMAGE_MIN,
    MEDITATE_CULTIVATION_GAIN,
    MEDITATE_MANA_RECOVER,
    REST_HEAL_AMOUNT,
    SETTLE_INTERVAL_MINUTES,
    STRATEGIES,
    MAX_OFFLINE_HOURS,
)
from backend.configs.events import EXPLORE_EVENTS
from backend.models import Character, User, utc_now
from backend.services.calc_service import get_guard_talisman_damage_reduction, sync_base_and_caps
from backend.services.inventory_service import add_item_to_main_bag
from backend.services.sect_service import record_sect_task_progress
from backend.utils.random_utils import weighted_choice


def _ensure_naive(dt):
    """把 datetime 转为 naive（去掉 tzinfo），兼容 aware/naive 混用场景。"""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def _generate_pending_matters(db: Session, character: Character, report: dict) -> None:
    """生成更丰富的待处理事项"""
    matters = list(report.get("pending_matters", []))
    auto_state = character.auto_state
    auto_reason = character.auto_paused_reason

    # 已有暂停原因 → 加入待处理
    if auto_reason:
        if auto_reason not in matters:
            matters.append(auto_reason)

    # 背包满
    if any("背包" in m for m in matters):
        pass  # 已有
    elif _check_bag_full(db, character):
        matters.append("背包已满，请整理后继续修行")

    # 可尝试突破（修为 >= 80%）
    cult_progress = character.cultivation / character.cultivation_cap if character.cultivation_cap > 0 else 0
    if cult_progress >= 0.8:
        matters.append("修为接近突破，可尝试突破当前境界")

    # 气血过低（刚结算完且 hp 较低）
    hp_ratio = character.hp / character.max_hp if character.max_hp > 0 else 0
    if hp_ratio < 0.5 and auto_state not in ("injured",):
        matters.append("气血不足，建议先休整再继续历练")

    # 法力较低
    mana_ratio = character.mana / character.max_mana if character.max_mana > 0 else 0
    if mana_ratio < 0.3:
        matters.append("法力偏低，建议打坐恢复")

    # 如果上述都没有，且 auto_state 为 meditating → 加入一句鼓励
    if not matters and auto_state == "meditating":
        matters.append("自动修行中，一切平稳 ✦")

    report["pending_matters"] = matters


def _check_bag_full(db: Session, character: Character) -> bool:
    """检查背包是否已满"""
    from backend.models import InventorySlot
    total_slots = db.query(InventorySlot).filter(
        InventorySlot.character_id == character.id,
        InventorySlot.container_type == "main_bag",
    ).count()
    filled_slots = db.query(InventorySlot).filter(
        InventorySlot.character_id == character.id,
        InventorySlot.container_type == "main_bag",
        InventorySlot.item_template_id.isnot(None),
    ).count()
    return filled_slots >= total_slots and total_slots > 0


def get_auto_cultivation_status(db: Session, character: Character) -> dict:
    """
    只读：返回当前自动修行状态
    不修改任何玩家数据
    """
    strategy_config = STRATEGIES.get(character.auto_strategy, STRATEGIES["balanced"])
    state_name = AUTO_STATE_NAMES.get(character.auto_state, character.auto_state)

    can_settle = False
    settle_minutes_available = 0
    if character.last_auto_settle_at and character.auto_enabled:
        now_naive = _ensure_naive(utc_now())
        last_naive = _ensure_naive(character.last_auto_settle_at)
        elapsed = now_naive - last_naive
        settle_minutes_available = int(elapsed.total_seconds() / 60)
        max_minutes = MAX_OFFLINE_HOURS * 60
        settle_minutes_available = min(settle_minutes_available, max_minutes)
        if settle_minutes_available >= SETTLE_INTERVAL_MINUTES:
            can_settle = True

    last_report = None
    if character.last_auto_report_json:
        try:
            last_report = json.loads(character.last_auto_report_json)
        except Exception:
            last_report = None

    available_strategies = []
    for key, cfg in STRATEGIES.items():
        available_strategies.append({
            "strategy": key,
            "name": cfg["name"],
            "description": cfg["description"],
            "mana_threshold_percent": cfg["mana_threshold_percent"],
            "hp_threshold_percent": cfg["hp_threshold_percent"],
        })

    return {
        "enabled": character.auto_enabled,
        "strategy": character.auto_strategy,
        "strategy_name": strategy_config["name"],
        "strategy_description": strategy_config["description"],
        "state": character.auto_state,
        "state_name": state_name,
        "last_settle_at": character.last_auto_settle_at.isoformat() if character.last_auto_settle_at else None,
        "can_settle": can_settle,
        "settle_minutes_available": settle_minutes_available,
        "max_offline_hours": MAX_OFFLINE_HOURS,
        "paused_reason": character.auto_paused_reason,
        "last_report": last_report,
        "realtime_logs": _get_realtime_logs(character),
        "available_strategies": available_strategies,
    }


def _get_realtime_logs(character: Character) -> list:
    """读取最近实时修仙日志"""
    if not character.last_auto_log_json:
        return []
    try:
        return json.loads(character.last_auto_log_json)
    except Exception:
        return []


def configure_auto_cultivation(db: Session, user: User, strategy: str, enabled: bool) -> dict:
    """
    配置自动修行策略和开关
    """
    character = user.character
    if strategy not in STRATEGIES:
        return {"success": False, "message": f"未知策略：{strategy}"}

    character.auto_strategy = strategy
    character.auto_enabled = enabled
    strategy_config = STRATEGIES[strategy]
    character.updated_at = utc_now()

    if enabled:
        character.auto_state = "meditating"
        character.auto_paused_reason = None
        character.last_auto_settle_at = utc_now()
        message = f"已开启自动修行，策略：{strategy_config['name']}。{strategy_config['description']}"
    else:
        character.auto_state = "paused"
        character.auto_paused_reason = "玩家主动暂停"
        message = "已暂停自动修行。"

    db.flush()
    return {
        "success": True,
        "message": message,
        "auto_cultivation": get_auto_cultivation_status(db, character),
    }


def pause_auto_cultivation(db: Session, user: User, reason: str) -> dict:
    """
    暂停自动修行
    """
    character = user.character
    character.auto_enabled = False
    character.auto_state = "paused"
    character.auto_paused_reason = reason
    character.updated_at = utc_now()
    db.flush()
    return {
        "success": True,
        "message": f"自动修行已暂停：{reason}",
        "auto_cultivation": get_auto_cultivation_status(db, character),
    }


def resume_auto_cultivation(db: Session, user: User) -> dict:
    """
    恢复自动修行
    """
    character = user.character
    if character.auto_state in ("injured",):
        # 重伤状态：如果当前气血低于稳健阈值，先休整再恢复
        strategy_config = STRATEGIES.get(character.auto_strategy, STRATEGIES["balanced"])
        hp_threshold = int(character.max_hp * strategy_config["hp_threshold_percent"] / 100)
        if character.hp < hp_threshold:
            character.auto_state = "resting"
        else:
            character.auto_state = "meditating"
    else:
        character.auto_state = "meditating"

    character.auto_enabled = True
    character.auto_paused_reason = None
    character.updated_at = utc_now()
    db.flush()

    status = get_auto_cultivation_status(db, character)
    return {
        "success": True,
        "message": "已恢复自动修行。",
        "auto_cultivation": status,
    }


def settle_auto_cultivation(db: Session, user: User) -> dict:
    """
    结算离线修行收益
    所有状态修改在这里发生
    """
    character = user.character
    strategy_config = STRATEGIES.get(character.auto_strategy, STRATEGIES["balanced"])

    now = utc_now()
    start = character.last_auto_settle_at or _ensure_naive(now)
    elapsed_seconds = (_ensure_naive(now) - _ensure_naive(start)).total_seconds()
    elapsed_minutes = int(elapsed_seconds / 60)

    max_minutes = MAX_OFFLINE_HOURS * 60
    if elapsed_minutes > max_minutes:
        elapsed_minutes = max_minutes

    if elapsed_minutes < SETTLE_INTERVAL_MINUTES:
        return {
            "success": False,
            "message": "离线时间不足，无需结算。",
            "auto_cultivation": get_auto_cultivation_status(db, character),
        }

    cycles = elapsed_minutes // SETTLE_INTERVAL_MINUTES
    cycles = min(cycles, 48)  # 最多48个周期（8小时）

    mana_threshold = int(character.max_mana * strategy_config["mana_threshold_percent"] / 100)
    hp_threshold = int(character.max_hp * strategy_config["hp_threshold_percent"] / 100)

    MAX_LOG_ENTRIES = 50

    report = {
        "duration_minutes": elapsed_minutes,
        "settled_minutes": cycles * SETTLE_INTERVAL_MINUTES,
        "cycles": cycles,
        "max_offline_hours": MAX_OFFLINE_HOURS,
        "actions": {"meditating": 0, "adventuring": 0, "resting": 0},
        "gains": {"cultivation": 0, "spirit_stones": 0, "items": []},
        "losses": {"mana": 0, "hp": 0, "items": []},
        "sect_task_messages": [],
        "pending_matters": [],
        "auto_logs": [],
        "final_state": {"state": character.auto_state, "state_name": AUTO_STATE_NAMES.get(character.auto_state, character.auto_state)},
    }

    sect_task_messages_accum = []
    all_drops = []
    total_mana_cost = 0
    total_hp_damage = 0

    def add_log(report, text):
        report["auto_logs"].append(text)

    for i in range(cycles):
        cycle_state = character.auto_state

        # 如果已经 paused/injured，停止结算
        if cycle_state in ("paused", "injured"):
            report["pending_matters"].append(character.auto_paused_reason or "自动修行已暂停")
            add_log(report, f"【修行暂停】{character.auto_paused_reason or '自动修行已暂停'}")
            break

        # 气血低于阈值 → 休整
        if character.hp < hp_threshold:
            _do_rest(db, character, report, strategy_config)
            add_log(report, "【洞府休整】你在洞府静养，气血渐渐恢复。")
            continue

        # 法力低于阈值 → 打坐
        if character.mana < mana_threshold:
            _do_meditate(db, character, report)
            mana_recover = MEDITATE_MANA_RECOVER
            add_log(report, f"【洞府打坐】你在洞府盘膝调息，法力恢复 {mana_recover} 点。")
            continue

        # 法力充足 → 历练
        result = _do_adventure(db, character, user, report, strategy_config)
        total_mana_cost += ADVENTURE_MANA_COST
        total_hp_damage += result.get("hp_damage", 0)
        sect_task_messages_accum.extend(result.get("sect_messages", []))
        all_drops.extend(result.get("drops", []))

        # 根据冒险结果生成氛围型日志
        event_type = result.get("event_type", "normal")
        hp_dmg = result.get("hp_damage", 0)
        stones = result.get("stones", 0)
        items = result.get("drops", [])
        battle_count = result.get("battle_count", 0)
        sect_msg = result.get("sect_messages", [])

        if hp_dmg > 0:
            add_log(report, f"【外出历练】你在野外遭遇敌人，损失气血 {hp_dmg} 点。")
        elif stones > 0:
            add_log(report, f"【外出历练】你探寻灵脉，获得灵石 +{stones}。")
        else:
            add_log(report, f"【外出历练】你在天地间感悟，修为有所精进。")

        if items:
            for item in items[:3]:
                add_log(report, f"【偶得】你发现 {item.get('name', item.get('code', '未知物品'))}，收入囊中。")

        # 宗门任务推进消息
        for msg in sect_msg[:2]:
            add_log(report, f"【宗门】{msg}")

        # 检查是否背包满
        if result.get("bag_full"):
            character.auto_state = "paused"
            character.auto_paused_reason = "背包已满，请整理后继续修行"
            character.auto_enabled = False
            report["pending_matters"].append("背包已满，请整理后继续修行")
            report["final_state"] = {"state": "paused", "state_name": "等待处理"}
            add_log(report, "【修行暂停】背包已满，无法收纳更多物品，请整理后继续。")
            break

        # 检查是否重伤（HP 低于 hp_threshold 且当前 HP 足够低）
        if character.hp <= hp_threshold and character.hp < character.max_hp * 0.35:
            character.hp = max(1, character.hp)  # 不死亡
            character.auto_state = "injured"
            character.auto_paused_reason = "你在自行历练中遭遇重创，已重伤返回洞府"
            character.auto_enabled = False
            report["pending_matters"].append("你在自行历练中遭遇重创，已重伤返回洞府")
            report["final_state"] = {"state": "injured", "state_name": "重伤暂停"}
            add_log(report, "【重伤】你在历练中遭遇强敌，身受重创，被迫返回洞府疗养。")
            break
        # 当前周期 HP 低于阈值但未达重伤 → 下一周期先休整
        if character.hp < hp_threshold:
            _do_rest(db, character, report, strategy_config)
            add_log(report, "【气血不足】你感到体力不支，返回洞府休整。")

    # 更新角色数值
    character.last_auto_settle_at = now
    sync_base_and_caps(character)

    # 如果历练了，去重 sect 消息
    if sect_task_messages_accum:
        unique_messages = []
        seen = set()
        for msg in sect_task_messages_accum:
            if msg not in seen:
                seen.add(msg)
                unique_messages.append(msg)
        report["sect_task_messages"] = unique_messages

    report["losses"]["mana"] = total_mana_cost
    report["losses"]["hp"] = total_hp_damage

    # 生成离线报告的增强内容：事件感/成长感/危险感
    actions = report["actions"]
    adv_count = actions.get("adventuring", 0)
    rest_count = actions.get("resting", 0)
    losses_hp = report["losses"]["hp"]
    losses_mana = report["losses"]["mana"]

    # 事件摘要
    event_summary_parts = []
    if adv_count > 0:
        event_summary_parts.append(f"历练 {adv_count} 次")
    if rest_count > 0:
        event_summary_parts.append(f"休整 {rest_count} 次")
    if losses_hp > 30:
        event_summary_parts.append("多次负伤")
    if losses_mana > total_mana_cost * 0.7:
        event_summary_parts.append("法力消耗较大")

    report["event_summary"] = "、".join(event_summary_parts) if event_summary_parts else "平静无事"

    # 成长感描述
    cult_gain_total = report["gains"].get("cultivation", 0)
    stones_gain = report["gains"].get("spirit_stones", 0)
    if cult_gain_total > 200:
        report["growth_feel"] = "你感悟天地，修为精进神速。"
    elif cult_gain_total > 100:
        report["growth_feel"] = "你潜心修行，修为有所长进。"
    elif cult_gain_total > 50:
        report["growth_feel"] = "你静心修炼，小有所得。"
    else:
        report["growth_feel"] = "你稳扎稳打，循序渐进。"

    # 危险感描述
    if losses_hp > 80:
        report["danger_feel"] = "你在历练中多次遭遇强敌，险象环生。"
    elif losses_hp > 40:
        report["danger_feel"] = "历练途中偶有凶险，你受伤不轻。"
    elif losses_hp > 0:
        report["danger_feel"] = "外出历练小有波折，受了些许轻伤。"
    else:
        report["danger_feel"] = "此番历练平安无事，安然无恙。"

    # 生成待处理事项（更丰富）
    _generate_pending_matters(db, character, report)

    # 保存报告
    character.last_auto_report_json = json.dumps(report, ensure_ascii=False)

    # 合并并保存实时日志（保留最近 MAX_LOG_ENTRIES 条）
    # 日志存储顺序：旧 → 新（最新追加到末尾）
    # 合并时：旧日志在前，新日志在后，取最后 50 条即为最新
    new_logs = report.get("auto_logs", [])
    existing_logs = []
    if character.last_auto_log_json:
        try:
            existing_logs = json.loads(character.last_auto_log_json)
        except Exception:
            existing_logs = []
    merged_logs = existing_logs + new_logs
    # 保留最新 MAX_LOG_ENTRIES 条
    trimmed_logs = merged_logs[-MAX_LOG_ENTRIES:]
    character.last_auto_log_json = json.dumps(trimmed_logs, ensure_ascii=False)

    # 重置自动状态（以便下次自动修行）
    if character.auto_state not in ("paused", "injured"):
        character.auto_state = "meditating"

    db.flush()

    # 构建响应
    messages = []
    action_counts = report["actions"]
    if cycles > 0:
        messages.append(f"离线修行 {elapsed_minutes} 分钟，共执行 {cycles} 次行动。")
        if action_counts["meditating"] > 0:
            messages.append(f"洞府打坐 {action_counts['meditating']} 次")
        if action_counts["adventuring"] > 0:
            messages.append(f"自行历练 {action_counts['adventuring']} 次")
        if action_counts["resting"] > 0:
            messages.append(f"洞府休整 {action_counts['resting']} 次")
    else:
        messages.append("离线期间未执行任何行动。")

    gains = report["gains"]
    if gains["cultivation"] > 0:
        messages.append(f"修为 +{gains['cultivation']}")
    if gains["spirit_stones"] > 0:
        messages.append(f"灵石 +{gains['spirit_stones']}")
    if gains["items"]:
        item_names = [f"{item['name']} x{item['quantity']}" for item in gains["items"]]
        messages.append(f"获得物品：{', '.join(item_names)}")
    losses = report["losses"]
    if losses["mana"] > 0:
        messages.append(f"消耗法力 {losses['mana']}")
    if losses["hp"] > 0:
        messages.append(f"损失气血 {losses['hp']}")

    if report["pending_matters"]:
        messages.append("待处理：" + "；".join(report["pending_matters"]))

    full_message = " ".join(messages)

    return {
        "success": True,
        "message": full_message,
        "auto_cultivation": get_auto_cultivation_status(db, character),
        "auto_report": report,
        "gains": gains,
        "losses": losses,
    }


def _do_meditate(db: Session, character: Character, report: dict) -> None:
    """执行洞府打坐"""
    mana_recover = MEDITATE_MANA_RECOVER
    before = character.mana
    character.mana = min(character.max_mana, character.mana + mana_recover)
    recovered = character.mana - before

    cultivation_gain = MEDITATE_CULTIVATION_GAIN
    character.cultivation = min(character.cultivation_cap, character.cultivation + cultivation_gain)

    report["actions"]["meditating"] += 1
    report["gains"]["cultivation"] += cultivation_gain


def _do_rest(db: Session, character: Character, report: dict, strategy_config: dict) -> None:
    """执行洞府休整"""
    heal = REST_HEAL_AMOUNT
    before = character.hp
    character.hp = min(character.max_hp, character.hp + heal)
    healed = character.hp - before

    report["actions"]["resting"] += 1


def _do_adventure(db: Session, character: Character, user: User, report: dict, strategy_config: dict) -> dict:
    """执行自行历练"""
    reward_mult = strategy_config.get("reward_multiplier", 1.0)
    injury_mult = strategy_config.get("injury_multiplier", 1.0)

    # 消耗法力
    if character.mana < ADVENTURE_MANA_COST:
        return {"hp_damage": 0, "drops": [], "sect_messages": []}

    character.mana -= ADVENTURE_MANA_COST

    # 历练修为
    cult_gain = random.randint(ADVENTURE_CULTIVATION_GAIN_MIN, ADVENTURE_CULTIVATION_GAIN_MAX)
    cult_gain = int(cult_gain * reward_mult)
    character.cultivation = min(character.cultivation_cap, character.cultivation + cult_gain)

    # 获得灵石
    stones = random.randint(ADVENTURE_STONES_MIN, ADVENTURE_STONES_MAX)
    stones = int(stones * reward_mult)
    character.spirit_stones += stones

    # 随机事件
    event = _pick_simple_event(character)
    event_type = event.get("type", "empty")
    hp_damage = 0
    drops = []
    sect_messages = []
    bag_full = False

    if event_type == "battle":
        # 战斗，可能受伤
        base_damage = random.randint(BATTLE_DAMAGE_MIN, BATTLE_DAMAGE_MAX)
        reduction = get_guard_talisman_damage_reduction(character)
        damage = max(1, int(base_damage * injury_mult * (1 - reduction)))
        hp_damage = damage
        character.hp = max(0, character.hp - hp_damage)
        # 战斗胜利额外灵石
        extra_stones = int(random.randint(20, 50) * reward_mult)
        character.spirit_stones += extra_stones
        stones += extra_stones

        # 推进宗门任务
        msgs = record_sect_task_progress(db, user, "explore", True, {
            "event_type": "battle",
            "event": event.get("code", ""),
        })
        sect_messages.extend(msgs)

    elif event_type in ("reward_spirit_stones", "reward_item"):
        # 额外灵石/物品
        extra = int(random.randint(10, 40) * reward_mult)
        character.spirit_stones += extra
        stones += extra

        # 推进宗门任务（探索类）
        msgs = record_sect_task_progress(db, user, "explore", True, {
            "event_type": event_type,
            "event": event.get("code", ""),
        })
        sect_messages.extend(msgs)

    elif event_type == "hidden_opportunity":
        # 隐藏机缘
        extra = int(random.randint(30, 80) * reward_mult)
        character.spirit_stones += extra
        stones += extra

        # 推进宗门任务（秘密探查类）
        msgs = record_sect_task_progress(db, user, "explore", True, {
            "event_type": "hidden_opportunity",
            "event": event.get("code", ""),
        })
        sect_messages.extend(msgs)

    elif event_type == "trap":
        # 陷阱
        base_damage = random.randint(5, 16)
        reduction = get_guard_talisman_damage_reduction(character)
        damage = max(1, int(base_damage * injury_mult * (1 - reduction)))
        hp_damage = damage
        character.hp = max(0, character.hp - hp_damage)

    # 尝试掉落物品
    drop_result = _grant_auto_drop(db, character, reward_mult)
    if drop_result.get("bag_full"):
        bag_full = True
    drops = drop_result.get("drops", [])

    # 更新报告
    report["actions"]["adventuring"] += 1
    report["gains"]["cultivation"] += cult_gain
    report["gains"]["spirit_stones"] += stones
    for drop in drops:
        report["gains"]["items"].append(drop)

    return {
        "hp_damage": hp_damage,
        "drops": drops,
        "sect_messages": sect_messages,
        "bag_full": bag_full,
        "event_type": event_type,
        "stones": stones,
        "battle_count": 1 if event_type == "battle" else 0,
    }


def _pick_simple_event(character) -> dict:
    """从现有探索事件中随机选一个（简化版，不复用 event_service 的加权逻辑）"""
    # 简化：直接按权重随机
    weights = [28, 26, 20, 18, 8, 6, 4, 3]  # 对应原 EXPLORE_EVENTS 的权重
    idx = random.choices(range(len(EXPLORE_EVENTS)), weights=weights, k=1)[0]
    return EXPLORE_EVENTS[idx]


def _grant_auto_drop(db: Session, character: Character, reward_mult: float) -> dict:
    """
    尝试给予自动历练掉落
    返回 bag_full 标志
    """
    drops = []
    bag_full = False

    # 掉落 1-2 件物品
    roll_count = random.randint(1, 2)
    selected_items = []
    available = list(AUTO_DROP_TABLE)
    for _ in range(roll_count):
        if not available:
            break
        item = weighted_choice(available, lambda x: x["weight"])
        selected_items.append(item)
        # 不允许同一物品重复（权重降到 0）
        for entry in available:
            if entry["code"] == item["code"]:
                entry["weight"] = 0
                break

    for entry in selected_items:
        quantity_range = entry.get("quantity_range", [1, 1])
        quantity = random.randint(int(quantity_range[0]), int(quantity_range[1]))
        quantity = max(1, int(quantity * reward_mult))

        ok, message, reward = add_item_to_main_bag(db, character, entry["code"], quantity)
        if not ok:
            bag_full = True
        else:
            drops.append({
                "name": reward.get("name", entry["code"]),
                "code": entry["code"],
                "quantity": quantity,
                "rarity": entry["rarity"],
            })

    return {"drops": drops, "bag_full": bag_full}


def auto_cultivation_tick(db: Session, character: Character) -> dict:
    """
    在线挂机轻量 tick：
    - 生成 1 条修仙氛围日志
    - 不发奖励（不能成为刷资源入口）
    - 不完整结算
    - 仅追加日志 + 更新 last_auto_settle_at（避免重复触发 settle）
    """
    if not character.auto_enabled or character.auto_state in ("paused", "injured"):
        return {
            "success": False,
            "message": "自动修行未开启或已暂停，无法产生新的修仙动态。",
            "auto_cultivation": get_auto_cultivation_status(db, character),
        }

    # 存储顺序：旧 → 新，最新追加到末尾
    MAX_LOG_ENTRIES = 50

    # 随机生成一条氛围日志
    log = _generate_atmosphere_log(character)

    # 追加到日志列表
    existing_logs = []
    if character.last_auto_log_json:
        try:
            existing_logs = json.loads(character.last_auto_log_json)
        except Exception:
            existing_logs = []

    updated_logs = existing_logs + [log]
    updated_logs = updated_logs[-MAX_LOG_ENTRIES:]
    character.last_auto_log_json = json.dumps(updated_logs, ensure_ascii=False)

    # 更新 last_auto_settle_at（防重复触发 settle，但不改变数值）
    character.last_auto_settle_at = utc_now()

    db.flush()

    return {
        "success": True,
        "message": log,
        "auto_cultivation": get_auto_cultivation_status(db, character),
        "new_log": log,
    }


# 在线氛围日志素材库
_TICK_ATMOSPHERE_LOGS = [
    "你在洞府吐纳灵气，周身缓缓环绕着淡淡的灵光。",
    "你听见远处山巅传来阵阵钟声，心神微动。",
    "你感应到天地灵气潮汐，默默运转小周天。",
    "你沿着洞府外的山道缓行，感受万物生机。",
    "你闭目凝神，体内真元缓缓流转。",
    "你察觉山外似乎有妖兽嘶吼，但并未靠近洞府。",
    "你检查储物袋，确认收获无误后继续修行。",
    "你收敛气息，继续稳固境界。",
    "你感到修为渐长，天地灵气入体更加顺畅。",
    "你观察洞府外风云变幻，悟得一丝天地至理。",
    "你在洞府附近发现一株低阶灵草，采收入袋。",
    "你听闻远处有修士斗法，余波隐隐传来。",
    "你盘膝而坐，天地灵气如涓涓细流汇入丹田。",
    "你感受到体内真元蠢蠢欲动，隐约有突破之兆。",
    "你望着洞府外的云海，思绪飘远又收回。",
    "你轻抚腰间法器，法器微微发出微弱光芒。",
    "你闭目调息，法力在经脉中缓缓运行。",
    "你检视自身，发现气息比昨日更加沉稳。",
    "你感应到洞府结界微微颤动，片刻后恢复平静。",
    "你望见天边流星划过，默默许下修行之愿。",
]


def _generate_atmosphere_log(character: Character) -> str:
    """根据角色状态生成一条随机氛围日志"""
    state = character.auto_state
    hp_ratio = character.hp / character.max_hp if character.max_hp > 0 else 0
    mana_ratio = character.mana / character.max_mana if character.max_mana > 0 else 0

    # 根据状态选择合适的日志
    if state == "meditating":
        pool = _TICK_ATMOSPHERE_LOGS
    elif state == "resting":
        pool = [
            "你在洞府静养，气血渐渐恢复。",
            "你服下一粒丹药，药力缓缓化解，伤势好转。",
            "你在洞府中小憩，醒来后精神恢复了许多。",
            "你闭目养神，感受体内的生机正在回归。",
        ]
    elif state == "adventuring":
        pool = [
            "你离开洞府，在外探索片刻后返回。",
            "你沿着山道行进，发现山间云雾缭绕。",
            "你隐约感应到远处灵脉的波动。",
            "你在山野间行走，随手采集了几株灵草。",
        ]
    else:
        pool = _TICK_ATMOSPHERE_LOGS

    return random.choice(pool)


def auto_cultivation_summary(character: Character) -> dict:
    """
    生成 character_payload 用的自动修行状态摘要
    """
    strategy_config = STRATEGIES.get(character.auto_strategy, STRATEGIES["balanced"])
    state_name = AUTO_STATE_NAMES.get(character.auto_state, character.auto_state)

    can_settle = False
    settle_minutes = 0
    if character.last_auto_settle_at and character.auto_enabled:
        now_naive = _ensure_naive(utc_now())
        last_naive = _ensure_naive(character.last_auto_settle_at)
        elapsed = now_naive - last_naive
        settle_minutes = int(elapsed.total_seconds() / 60)
        max_minutes = MAX_OFFLINE_HOURS * 60
        settle_minutes = min(settle_minutes, max_minutes)
        if settle_minutes >= SETTLE_INTERVAL_MINUTES:
            can_settle = True

    last_report = None
    if character.last_auto_report_json:
        try:
            last_report = json.loads(character.last_auto_report_json)
        except Exception:
            last_report = None

    return {
        "enabled": character.auto_enabled,
        "strategy": character.auto_strategy,
        "strategy_name": strategy_config["name"],
        "state": character.auto_state,
        "state_name": state_name,
        "last_settle_at": character.last_auto_settle_at.isoformat() if character.last_auto_settle_at else None,
        "can_settle": can_settle,
        "settle_minutes_available": settle_minutes,
        "paused_reason": character.auto_paused_reason,
        "last_report": last_report,
    }