from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.configs.realms import REALM_NAMES
from backend.configs.sects import (
    FACTIONS,
    NPC_SECTS,
    POSITION_NAMES,
    POSITION_ORDER,
    PROMOTION_RULES,
    SECT_SHOP,
    SECT_TASKS,
)
from backend.models import Character, Sect, SectMember, SectReputationLog, SectTask, User, utc_now
from backend.services.inventory_service import add_item_to_main_bag, consume_item_by_code, has_item


def derive_sect_position(character: Character) -> str:
    if not character.sect_id or not character.sect:
        return "散修"
    return position_name(character.sect.faction, character.sect_position or "outer_disciple")


def identity_status(character: Character) -> str:
    if not character.sect_id or not character.sect:
        return "散修"
    return f"{character.sect.name} · {derive_sect_position(character)}"


def position_name(faction: str, position_code: str) -> str:
    return POSITION_NAMES.get(faction, POSITION_NAMES["righteous"]).get(position_code, position_code)


def list_sects(db: Session) -> list[dict]:
    sects = db.query(Sect).order_by(Sect.faction, Sect.level.desc(), Sect.id).all()
    return [sect_payload(sect) for sect in sects]


def sect_payload(sect: Sect) -> dict:
    config = _sect_config(sect.code)
    return {
        "id": sect.id,
        "code": sect.code,
        "name": sect.name,
        "faction": sect.faction,
        "faction_name": FACTIONS.get(sect.faction, {}).get("name", sect.faction),
        "level": sect.level,
        "description": sect.description,
        "is_player_created": bool(sect.is_player_created),
        "required_realm": config.get("required_realm"),
        "required_spirit_stones": config.get("required_spirit_stones", 0),
        "preferred_root": config.get("preferred_root", []),
        "specialty": config.get("specialty", []),
    }


def sect_me_payload(db: Session, character: Character) -> dict:
    member = active_member(db, character)
    reputations = reputation_summary(db, character)
    if not member:
        return {"sect": None, "member": None, "reputations": reputations}
    return {
        "sect": sect_payload(member.sect),
        "member": member_payload(member),
        "reputations": reputations,
    }


def active_member(db: Session, character: Character) -> SectMember | None:
    return (
        db.query(SectMember)
        .filter(SectMember.character_id == character.id, SectMember.status == "active")
        .order_by(SectMember.id.desc())
        .first()
    )


def member_payload(member: SectMember) -> dict:
    return {
        "id": member.id,
        "sect_id": member.sect_id,
        "position": member.position,
        "position_name": position_name(member.sect.faction, member.position),
        "contribution": member.contribution,
        "reputation": member.reputation,
        "status": member.status,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
    }


def join_sect(db: Session, user: User, sect_code: str) -> tuple[bool, str, dict]:
    character = user.character
    if active_member(db, character) or character.sect_id:
        return False, "你已经加入宗门，不能同时拜入两个宗门。", {"reason": "already_in_sect"}
    sect = db.query(Sect).filter(Sect.code == sect_code).first()
    if not sect:
        return False, "没有找到这个宗门。", {"reason": "sect_not_found"}
    config = _sect_config(sect.code)
    required_realm = config.get("required_realm", "炼气一层")
    if not _realm_at_least(character.realm, required_realm):
        return False, f"境界不足，拜入{sect.name}至少需要{required_realm}。", {"reason": "required_realm"}
    required_stones = int(config.get("required_spirit_stones", 0))
    if character.spirit_stones < required_stones:
        return False, f"灵石不足，拜入{sect.name}需要 {required_stones} 灵石。", {"reason": "required_spirit_stones"}
    character.spirit_stones -= required_stones
    matched_root = _matches_root(character, config.get("preferred_root", []))
    initial_contribution = 30 if matched_root else 0
    member = SectMember(
        sect_id=sect.id,
        character_id=character.id,
        position="outer_disciple",
        contribution=initial_contribution,
        reputation=0,
        status="active",
    )
    db.add(member)
    character.sect_id = sect.id
    character.sect_position = "outer_disciple"
    character.updated_at = utc_now()
    _add_reputation_logs(db, character, sect, 10, "join_sect")
    db.flush()
    root_bonus = "灵根契合，获初始贡献 30。" if matched_root else ""
    return True, f"你拜入{sect.name}，成为{position_name(sect.faction, 'outer_disciple')}。{root_bonus}", {"sect": sect_payload(sect), "member": member_payload(member)}


def leave_sect(db: Session, user: User) -> tuple[bool, str, dict]:
    character = user.character
    member = active_member(db, character)
    if not member:
        return False, "你尚未加入宗门。", {"reason": "not_in_sect"}
    sect = member.sect
    penalty = min(50, member.contribution // 3)
    member.contribution = max(0, member.contribution - penalty)
    member.status = "left"
    member.last_left_at = utc_now()
    character.sect_id = None
    character.sect_position = "散修"
    character.updated_at = utc_now()
    _add_reputation_logs(db, character, sect, -8, "leave_sect")
    db.flush()
    return True, f"你离开了{sect.name}，扣除 {penalty} 宗门贡献。", {"sect": sect_payload(sect), "member": member_payload(member)}


def available_tasks(db: Session, character: Character) -> list[dict]:
    member = active_member(db, character)
    if not member:
        return []
    return [task_config_payload(task, member.sect) for task in SECT_TASKS if _task_available(task, member.sect.faction, member.position)]


def my_tasks(db: Session, character: Character) -> list[dict]:
    tasks = db.query(SectTask).filter(SectTask.character_id == character.id).order_by(SectTask.id.desc()).limit(20).all()
    return [sect_task_payload(task) for task in tasks]


def accept_sect_task(db: Session, user: User, task_code: str) -> tuple[bool, str, dict]:
    character = user.character
    member = active_member(db, character)
    if not member:
        return False, "你尚未加入宗门。", {"reason": "not_in_sect"}
    if db.query(SectTask).filter(SectTask.character_id == character.id, SectTask.status == "active").first():
        return False, "你已有进行中的宗门任务。", {"reason": "active_task_exists"}
    config = _task_config(task_code)
    if not config or not _task_available(config, member.sect.faction, member.position):
        return False, "当前职位无法接取这个宗门任务。", {"reason": "task_unavailable"}
    task = SectTask(
        sect_id=member.sect_id,
        character_id=character.id,
        task_code=config["code"],
        task_type=config["type"],
        target=int(config.get("target", 1)),
        reward_json=config.get("reward", {}),
    )
    db.add(task)
    db.flush()
    return True, f"你接取了宗门任务「{config['name']}」。", {"task": sect_task_payload(task)}


def complete_sect_task(db: Session, user: User, task_id: int | None = None) -> tuple[bool, str, dict, dict, list[dict]]:
    character = user.character
    member = active_member(db, character)
    if not member:
        return False, "你尚未加入宗门。", {"reason": "not_in_sect"}, {}, []
    query = db.query(SectTask).filter(SectTask.character_id == character.id, SectTask.status == "active")
    task = query.filter(SectTask.id == task_id).first() if task_id else query.order_by(SectTask.id.asc()).first()
    if not task:
        return False, "没有可完成的宗门任务。", {"reason": "no_active_sect_task"}, {}, []
    config = _task_config(task.task_code)
    if not config:
        return False, "宗门任务配置不存在。", {"reason": "task_config_missing"}, {}, []

    ok, message, cost = _pay_task_cost(db, character, config)
    if not ok:
        return False, message, {"reason": "task_cost_failed", "task": sect_task_payload(task)}, cost, []

    reward = config.get("reward", {})
    reward_logs = _grant_sect_reward(db, character, reward)
    contribution = int(reward.get("contribution", 0))
    member.contribution += contribution
    member.reputation += int(config.get("reputation", 0))
    member.last_task_at = utc_now()
    task.progress = task.target
    task.status = "completed"
    task.completed_at = utc_now()
    _add_reputation_logs(db, character, member.sect, int(config.get("reputation", 0)), f"sect_task:{task.task_code}")
    db.flush()
    return True, f"完成宗门任务「{config['name']}」，获得 {contribution} 贡献。", {"task": sect_task_payload(task), "member": member_payload(member), "reward": reward}, cost, reward_logs


def promote_position(db: Session, user: User) -> tuple[bool, str, dict]:
    character = user.character
    member = active_member(db, character)
    if not member:
        return False, "你尚未加入宗门。", {"reason": "not_in_sect"}
    current_index = POSITION_ORDER.index(member.position) if member.position in POSITION_ORDER else 0
    if current_index >= len(POSITION_ORDER) - 1:
        return False, "你已位极本宗，暂不可继续晋升。", {"reason": "max_position"}
    target_position = POSITION_ORDER[current_index + 1]
    rule = PROMOTION_RULES.get(target_position)
    if not rule:
        return False, "该职位暂未开放晋升。", {"reason": "promotion_unavailable"}
    if member.contribution < rule["contribution"]:
        return False, f"贡献不足，晋升需要 {rule['contribution']} 贡献。", {"reason": "contribution"}
    if not _realm_at_least(character.realm, rule["realm"]):
        return False, f"境界不足，晋升需要{rule['realm']}。", {"reason": "realm"}
    member.position = target_position
    character.sect_position = target_position
    character.updated_at = utc_now()
    db.flush()
    return True, f"你晋升为{position_name(member.sect.faction, target_position)}。", {"member": member_payload(member)}


def shop_payload(db: Session, character: Character) -> list[dict]:
    member = active_member(db, character)
    if not member:
        return []
    return [{**item, "faction": member.sect.faction} for item in SECT_SHOP.get(member.sect.faction, [])]


def exchange_reward(db: Session, user: User, reward_code: str) -> tuple[bool, str, dict]:
    character = user.character
    member = active_member(db, character)
    if not member:
        return False, "你尚未加入宗门。", {"reason": "not_in_sect"}
    reward = next((item for item in SECT_SHOP.get(member.sect.faction, []) if item["code"] == reward_code), None)
    if not reward:
        return False, "没有找到这个宗门兑换奖励。", {"reason": "reward_not_found"}
    cost = int(reward["cost"])
    if member.contribution < cost:
        return False, f"宗门贡献不足，兑换需要 {cost} 贡献。", {"reason": "insufficient_contribution"}
    ok, message, payload = add_item_to_main_bag(db, character, reward["item_code"], int(reward.get("quantity", 1)))
    if not ok:
        return False, message, {"reason": "inventory_full"}
    member.contribution -= cost
    if reward.get("inner_demon"):
        character.hidden_inner_demon = max(0, min(100, character.hidden_inner_demon + int(reward["inner_demon"])))
    db.flush()
    return True, f"消耗 {cost} 贡献，兑换{reward['name']}。", {"reward": reward, "item": payload, "member": member_payload(member)}


def reputation_summary(db: Session, character: Character) -> dict:
    rows = (
        db.query(SectReputationLog.faction, func.coalesce(func.sum(SectReputationLog.delta), 0))
        .filter(SectReputationLog.character_id == character.id)
        .group_by(SectReputationLog.faction)
        .all()
    )
    values = {faction: 0 for faction in FACTIONS}
    values.update({faction: int(total) for faction, total in rows})
    return values


def task_config_payload(task: dict, sect: Sect) -> dict:
    return {
        "code": task["code"],
        "name": task["name"],
        "type": task["type"],
        "faction": task["faction"],
        "required_position": task["required_position"],
        "required_position_name": position_name(sect.faction, task["required_position"]),
        "target": task.get("target", 1),
        "cost": task.get("cost", {}),
        "reward": task.get("reward", {}),
        "description": task["description"],
    }


def sect_task_payload(task: SectTask) -> dict:
    config = _task_config(task.task_code) or {}
    return {
        "id": task.id,
        "sect_id": task.sect_id,
        "task_code": task.task_code,
        "name": config.get("name", task.task_code),
        "task_type": task.task_type,
        "status": task.status,
        "progress": task.progress,
        "target": task.target,
        "reward": task.reward_json,
        "description": config.get("description", ""),
    }


def _task_available(task: dict, faction: str, position: str) -> bool:
    if faction not in task.get("faction", []):
        return False
    required = task.get("required_position", "outer_disciple")
    return _position_rank(position) >= _position_rank(required)


def _pay_task_cost(db: Session, character: Character, config: dict) -> tuple[bool, str, dict]:
    cost = dict(config.get("cost", {}))
    mana_cost = int(cost.get("mana", 0))
    if mana_cost:
        if character.mana < mana_cost:
            return False, f"法力不足，完成该宗门任务需要 {mana_cost} 点法力。", cost
        character.mana -= mana_cost
    required_stones = int(config.get("required_spirit_stones", 0))
    if required_stones:
        if character.spirit_stones < required_stones:
            return False, f"灵石不足，该任务需要捐献 {required_stones} 灵石。", {"spirit_stones": required_stones}
        character.spirit_stones -= required_stones
        cost["spirit_stones"] = required_stones
    for item in config.get("required_items", []):
        code = item["code"]
        quantity = int(item.get("quantity", 1))
        if not has_item(db, character, code, quantity):
            return False, f"缺少任务所需物品：{code} x{quantity}", {"items": config.get("required_items", [])}
        consume_item_by_code(db, character, code, quantity)
    return True, "", cost


def _grant_sect_reward(db: Session, character: Character, reward: dict) -> list[dict]:
    logs: list[dict] = []
    stones = int(reward.get("spirit_stones", 0))
    if stones:
        character.spirit_stones += stones
    for item in reward.get("items", []):
        ok, message, payload = add_item_to_main_bag(db, character, item["code"], int(item.get("quantity", 1)))
        logs.append({"type": "sect", "content": message, "data": {"stored": ok, "item": payload}})
    return logs


def _add_reputation_logs(db: Session, character: Character, sect: Sect, amount: int, reason: str) -> None:
    if not amount:
        return
    deltas = _faction_deltas(sect.faction, amount)
    for faction, delta in deltas.items():
        db.add(SectReputationLog(character_id=character.id, sect_id=sect.id, faction=faction, delta=delta, reason=reason))


def _faction_deltas(faction: str, amount: int) -> dict[str, int]:
    if faction == "righteous":
        return {"righteous": amount, "demonic": -amount, "ghost": -amount, "buddhist": max(1, amount // 3)}
    if faction == "demonic":
        return {"demonic": amount, "righteous": -amount, "buddhist": -amount, "ghost": max(1, amount // 4)}
    if faction == "ghost":
        return {"ghost": amount, "righteous": -amount, "buddhist": -amount, "demonic": max(1, amount // 4)}
    if faction == "buddhist":
        return {"buddhist": amount, "demonic": -amount, "ghost": -amount, "righteous": max(1, amount // 3)}
    return {faction: amount}


def _matches_root(character: Character, roots: list[str]) -> bool:
    if not roots:
        return False
    return any(root in character.spiritual_root for root in roots)


def _realm_at_least(current: str, required: str) -> bool:
    if current not in REALM_NAMES or required not in REALM_NAMES:
        return False
    return REALM_NAMES.index(current) >= REALM_NAMES.index(required)


def _position_rank(position: str) -> int:
    return POSITION_ORDER.index(position) if position in POSITION_ORDER else 0


def _sect_config(code: str) -> dict:
    return next((sect for sect in NPC_SECTS if sect["code"] == code), {})


def _task_config(code: str) -> dict | None:
    return next((task for task in SECT_TASKS if task["code"] == code), None)
