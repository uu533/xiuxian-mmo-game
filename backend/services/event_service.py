import random

from sqlalchemy.orm import Session

from backend.configs.events import EXPLORE_EVENTS
from backend.configs.drop_tables import DROP_ROLLS_BY_EVENT_TYPE
from backend.configs.opportunities import LUCKY_EVENT_CONFIG, LUCKY_EVENTS
from backend.models import Character
from backend.services.calc_service import get_battle_power_bonus, get_explore_reward_bonus, get_final_attack, get_final_defense
from backend.services.drop_service import grant_drop_items
from backend.services.realm_service import next_realm_config
from backend.utils.random_utils import weighted_choice


def pick_explore_event(character: Character) -> dict:
    luck = character.hidden_luck

    def event_weight(event: dict) -> float:
        weight = float(event["weight"])
        if event["type"] == "hidden_opportunity":
            weight *= 1 + luck / 100
        if event["type"] in {"trap", "empty"}:
            weight *= max(0.35, 1 - luck / 180)
        return weight

    return weighted_choice(EXPLORE_EVENTS, event_weight)


def resolve_explore_event(db: Session, character: Character, params: dict | None = None) -> dict:
    params = params or {}
    lucky = resolve_lucky_event(db, character, params.get("force_lucky_code"))
    if lucky:
        return lucky

    event = pick_explore_event(character)
    rewards: list[dict] = []
    messages: list[str] = []
    extra_logs: list[dict] = []
    data: dict = {"event": event["code"], "event_type": event["type"], "rewards": []}

    if event["type"] == "reward_spirit_stones":
        amount = int((_roll_range(event["rewards"]["spirit_stones"]) + character.hidden_luck // 5) * (1 + get_explore_reward_bonus(character)))
        character.spirit_stones += amount
        rewards.append({"type": "spirit_stones", "quantity": amount})
        messages.append(f"你发现一处废弃矿脉，获得 {amount} 灵石。")

    elif event["type"] == "reward_item":
        drop_rewards, drop_messages = grant_drop_items(db, character, _rolls_for_event(event))
        rewards.extend(drop_rewards)
        messages.extend(drop_messages)
        extra_logs.append({"type": "drop", "content": "探索获得掉落：" + "，".join(item["name"] for item in drop_rewards), "data": {"drop_items": [item["code"] for item in drop_rewards]}})

    elif event["type"] == "battle":
        battle_result = resolve_battle(character)
        data["battle"] = battle_result
        messages.append(battle_result["message"])
        if battle_result["won"]:
            amount = int(_roll_range(event["rewards"].get("spirit_stones", [20, 50])) * (1 + get_explore_reward_bonus(character)))
            character.spirit_stones += amount
            rewards.append({"type": "spirit_stones", "quantity": amount})
            messages.append(f"战后搜得 {amount} 灵石。")
            drop_rewards, drop_messages = grant_drop_items(db, character, _rolls_for_event(event))
            rewards.extend(drop_rewards)
            messages.extend(drop_messages)
            if drop_rewards:
                extra_logs.append({"type": "drop", "content": "战斗获得掉落：" + "，".join(item["name"] for item in drop_rewards), "data": {"drop_items": [item["code"] for item in drop_rewards]}})

    elif event["type"] == "hidden_opportunity":
        amount = int(_roll_range(event["rewards"].get("spirit_stones", [0, 0])) * (1 + get_explore_reward_bonus(character)))
        if amount:
            character.spirit_stones += amount
            rewards.append({"type": "spirit_stones", "quantity": amount})
        drop_rewards, drop_messages = grant_drop_items(db, character, _rolls_for_event(event))
        rewards.extend(drop_rewards)
        messages.extend(drop_messages)
        messages.insert(0, f"你遇到机缘「{event['name']}」。")
        extra_logs.append({"type": "lucky", "content": f"你遇到机缘「{event['name']}」。", "data": {"event": event["code"], "drop_items": [item["code"] for item in drop_rewards]}})

    elif event["type"] == "trap":
        damage = _roll_range(event["risks"].get("hp_damage", [1, 1]))
        character.hp = max(0, character.hp - damage)
        messages.append(f"你误入迷阵，损失 {damage} 气血。")

    else:
        messages.append("你在山野间寻觅许久，空手而归。")

    data["rewards"] = rewards
    return {"event": event, "message": " ".join(messages), "rewards": rewards, "data": data, "extra_logs": extra_logs}


def resolve_lucky_event(db: Session, character: Character, force_lucky_code: str | None = None) -> dict | None:
    chance = min(
        LUCKY_EVENT_CONFIG["max_rate"],
        LUCKY_EVENT_CONFIG["base_rate"] + character.hidden_luck * LUCKY_EVENT_CONFIG["luck_factor"],
    )
    if not force_lucky_code and random.random() > chance:
        return None

    event = next((item for item in LUCKY_EVENTS if item["code"] == force_lucky_code), None)
    if not event:
        event = weighted_choice(LUCKY_EVENTS, lambda item: item["weight"])
    rewards: list[dict] = []
    messages = [f"机缘降临：{event['description']}"]
    data = {"event": event["code"], "event_type": event["type"], "lucky_rate": chance, "rewards": rewards}
    extra_logs = [{"type": "lucky", "content": messages[0], "data": data}]

    if event["type"] == "lucky_breakthrough":
        target = next_realm_config(character)
        if target:
            from_realm = character.realm
            character.realm = target.name
            character.realm_stage = target.stage
            character.cultivation = 0
            character.cultivation_cap = target.cultivation_cap
            rewards.append({"type": "realm", "name": character.realm})
            messages.append(f"你直接突破瓶颈，从「{from_realm}」踏入「{character.realm}」。")
            data.update({"from_realm": from_realm, "to_realm": character.realm})
    elif event["type"] in {"rare_item", "hidden_cave"}:
        rolls = 2 if event["type"] == "rare_item" else 4
        drop_rewards, drop_messages = grant_drop_items(db, character, rolls)
        rewards.extend(drop_rewards)
        messages.extend(drop_messages)
        extra_logs.append({"type": "drop", "content": "机缘获得掉落：" + "，".join(item["name"] for item in drop_rewards), "data": {"drop_items": [item["code"] for item in drop_rewards]}})
    elif event["type"] == "master_teach":
        method = next((item for item in character.methods if item.equipped), None)
        if method:
            method.exp += 120
            rewards.append({"type": "method_exp", "quantity": 120})
            messages.append("主修功法经验增加 120。")
        else:
            character.cultivation = min(character.cultivation_cap, character.cultivation + 120)
            rewards.append({"type": "cultivation", "quantity": 120})
            messages.append("你尚未主修功法，只将感悟化作 120 修为。")
    data["rewards"] = rewards
    return {"event": event, "message": " ".join(messages), "rewards": rewards, "data": data, "extra_logs": extra_logs}


def resolve_battle(character: Character) -> dict:
    enemy = random.choice(["青毛妖狼", "黑鳞妖蛇", "散修劫匪", "山魈"])
    enemy_hp = random.randint(42, 82)
    enemy_attack = random.randint(8, 18)
    player_attack = get_final_attack(character) + get_battle_power_bonus(character)
    player_defense = get_final_defense(character) + get_battle_power_bonus(character)
    damage_taken = 0
    rounds: list[str] = []
    won = False
    for index in range(1, 7):
        enemy_hp -= max(1, player_attack + random.randint(0, 8) - random.randint(0, 5))
        if enemy_hp <= 0:
            won = True
            rounds.append(f"第{index}回合击退{enemy}")
            break
        taken = max(1, enemy_attack + random.randint(0, 6) - player_defense)
        damage_taken += taken
        character.hp = max(0, character.hp - taken)
        if character.hp <= 0:
            break
    if won:
        message = f"你遭遇了一只{enemy}，苦战后获胜。"
    else:
        message = f"你遭遇了一只{enemy}，负伤后撤退。"
        character.hidden_inner_demon = min(100, character.hidden_inner_demon + 4)
    return {"enemy": enemy, "won": won, "damage_taken": damage_taken, "rounds": rounds, "message": message}


def _roll_range(value: list[int] | tuple[int, int]) -> int:
    return random.randint(int(value[0]), int(value[1]))


def _rolls_for_event(event: dict) -> int:
    roll_range = DROP_ROLLS_BY_EVENT_TYPE.get(event["type"], [1, 1])
    return _roll_range(roll_range)
