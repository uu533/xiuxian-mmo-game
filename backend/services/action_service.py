import random

from sqlalchemy.orm import Session

from backend.configs.actions import ACTION_CONFIGS, MANA_HELP_TEXT
from backend.models import User, utc_now
from backend.services.calc_service import (
    apply_item_effects,
    get_action_mana_cost,
    get_breakthrough_rate,
    sync_base_and_caps,
)
from backend.services.character_service import character_payload
from backend.services.event_service import resolve_explore_event
from backend.services.inventory_service import consume_slot_item, inventory_payload
from backend.services.log_service import write_action_record, write_log
from backend.services.realm_service import is_major_breakthrough, next_realm_config, normalize_realm


def execute_action(db: Session, user: User, action_type: str, params: dict | None = None) -> dict:
    params = params or {}
    character = user.character
    sync_base_and_caps(character)

    handlers = {
        "train": _train,
        "explore": _explore,
        "breakthrough": _breakthrough,
        "recover_mana_meditate": _recover_mana_meditate,
        "recover_mana_stone": _recover_mana_stone,
        "use_item": _use_item,
    }
    handler = handlers.get(action_type)
    if not handler:
        result = _result(db, user, False, f"未知行为：{action_type}", {}, [], [], action_type)
        db.commit()
        return result

    result = handler(db, user, params)
    db.commit()
    db.refresh(character)
    return result


def _spend_mana(character, action_type: str) -> tuple[bool, dict, str | None]:
    cost = get_action_mana_cost(character, action_type)
    if character.mana < cost:
        return False, {"mana": cost}, f"法力不足，本次需要 {cost} 点，当前只有 {character.mana} 点。{MANA_HELP_TEXT}"
    character.mana -= cost
    return True, {"mana": cost}, None


def _train(db: Session, user: User, params: dict) -> dict:
    _ = params
    character = user.character
    ok, cost, error = _spend_mana(character, "train")
    if not ok:
        return _finalize(db, user, False, "train", error or MANA_HELP_TEXT, cost, [], {"reason": "insufficient_mana"})

    gain = int(random.randint(16, 28) * character_payload(character)["cultivation_speed"] + character.max_mana * 0.03)
    character.cultivation = min(character.cultivation_cap, character.cultivation + gain)
    character.hidden_inner_demon = min(100, character.hidden_inner_demon + random.choice([0, 0, 1]))
    character.updated_at = utc_now()
    message = f"打坐修炼消耗 {cost['mana']} 点法力，炼化灵气，修为增加 {gain}。"
    return _finalize(db, user, True, "train", message, cost, [{"type": "cultivation", "quantity": gain}], {"cultivation_gain": gain})


def _explore(db: Session, user: User, params: dict) -> dict:
    _ = params
    character = user.character
    ok, cost, error = _spend_mana(character, "explore")
    if not ok:
        return _finalize(db, user, False, "explore", error or MANA_HELP_TEXT, cost, [], {"reason": "insufficient_mana"})
    event_result = resolve_explore_event(db, character)
    character.cultivation = min(character.cultivation_cap, character.cultivation + random.randint(4, 16))
    character.updated_at = utc_now()
    message = f"外出探索消耗 {cost['mana']} 点法力。{event_result['message']}"
    return _finalize(db, user, True, "explore", message, cost, event_result["rewards"], event_result["data"])


def _breakthrough(db: Session, user: User, params: dict) -> dict:
    _ = params
    character = user.character
    normalize_realm(character)
    if character.cultivation < character.cultivation_cap:
        message = f"修为尚未圆满，至少需要 {character.cultivation_cap} 修为。"
        return _finalize(db, user, False, "breakthrough", message, {}, [], {"reason": "cultivation_not_full"})

    target = next_realm_config(character)
    if not target:
        message = "你已抵达当前版本最高境界，暂无法继续突破。"
        return _finalize(db, user, False, "breakthrough", message, {}, [], {"reason": "max_realm"})

    ok, cost, error = _spend_mana(character, "breakthrough")
    if not ok:
        return _finalize(db, user, False, "breakthrough", error or MANA_HELP_TEXT, cost, [], {"reason": "insufficient_mana"})

    rate = get_breakthrough_rate(character)
    forced_success = character.hidden_luck >= 100
    forced_failure = character.hidden_inner_demon >= 100
    if forced_success or (not forced_failure and random.random() <= rate):
        from_realm = character.realm
        character.realm = target.name
        character.realm_stage = target.stage
        character.cultivation = 0
        character.cultivation_cap = target.cultivation_cap
        character.hidden_inner_demon = max(0, character.hidden_inner_demon - 10)
        sync_base_and_caps(character)
        character.mana = character.max_mana
        message = (
            f"突破消耗 {cost['mana']} 点法力。大境界突破成功！你踏入「{character.realm}」。"
            if is_major_breakthrough(from_realm, character.realm)
            else f"突破消耗 {cost['mana']} 点法力。突破成功！你踏入「{character.realm}」。"
        )
        return _finalize(db, user, True, "breakthrough", message, cost, [{"type": "realm", "name": character.realm}], {"success_rate": rate, "from_realm": from_realm, "to_realm": character.realm})

    character.cultivation = int(character.cultivation_cap * 0.42)
    character.hidden_inner_demon = min(100, character.hidden_inner_demon + random.randint(10, 18))
    character.hp = max(20, character.hp - random.randint(8, 22))
    message = f"突破消耗 {cost['mana']} 点法力。突破失败，心魔反噬。当前突破成功率约 {int(rate * 100)}%。"
    return _finalize(db, user, False, "breakthrough", message, cost, [], {"success_rate": rate})


def _recover_mana_meditate(db: Session, user: User, params: dict) -> dict:
    _ = params
    character = user.character
    amount = int(ACTION_CONFIGS["recover_mana_meditate"]["recover_mana"])
    before = character.mana
    character.mana = min(character.max_mana, character.mana + amount)
    recovered = character.mana - before
    message = f"静坐调息，恢复 {recovered} 点法力。"
    return _finalize(db, user, True, "recover_mana_meditate", message, {}, [{"type": "mana", "quantity": recovered}], {"recovered": recovered})


def _recover_mana_stone(db: Session, user: User, params: dict) -> dict:
    _ = params
    character = user.character
    stone_cost = int(ACTION_CONFIGS["recover_mana_stone"]["spirit_stone_cost"])
    if character.spirit_stones < stone_cost:
        message = f"灵石不足，吸收灵石恢复法力需要 {stone_cost} 枚灵石。"
        return _finalize(db, user, False, "recover_mana_stone", message, {"spirit_stones": stone_cost}, [], {"reason": "insufficient_spirit_stones"})
    character.spirit_stones -= stone_cost
    amount = int(ACTION_CONFIGS["recover_mana_stone"]["recover_mana"])
    before = character.mana
    character.mana = min(character.max_mana, character.mana + amount)
    recovered = character.mana - before
    message = f"手握灵石吸取灵力，消耗 {stone_cost} 灵石，恢复 {recovered} 点法力。"
    return _finalize(db, user, True, "recover_mana_stone", message, {"spirit_stones": stone_cost}, [{"type": "mana", "quantity": recovered}], {"recovered": recovered})


def _use_item(db: Session, user: User, params: dict) -> dict:
    character = user.character
    slot_index = int(params.get("slot_index", 0))
    ok, message, template = consume_slot_item(db, character, slot_index, 1)
    if not ok or not template:
        return _finalize(db, user, False, "use_item", message, {}, [], {"reason": "invalid_item"})
    applied = apply_item_effects(character, template.effects_json or {})
    if not applied:
        message = f"{message}，但暂未产生效果。"
    else:
        message = f"{message}，效果：{applied}。"
    return _finalize(db, user, True, "use_item", message, {"slot_index": slot_index, "quantity": 1}, [{"type": "item_effect", **applied}], {"item_code": template.code, "effects": applied})


def _finalize(db: Session, user: User, success: bool, action_type: str, message: str, cost: dict, rewards: list[dict], data: dict) -> dict:
    character = user.character
    sync_base_and_caps(character)
    data = {"success": success, **(data or {})}
    log_type = ACTION_CONFIGS.get(action_type, {}).get("log_type", action_type)
    write_log(db, user, log_type, message, data)
    write_action_record(db, character.id, action_type, cost, {"success": success, "message": message, "rewards": rewards, "data": data})
    return _result(db, user, success, message, cost, rewards, [message], action_type)


def _result(db: Session, user: User, success: bool, message: str, cost: dict, rewards: list[dict], logs: list[str], action_type: str) -> dict:
    _ = action_type
    return {
        "success": success,
        "message": message,
        "character": character_payload(user.character),
        "rewards": rewards,
        "cost": cost,
        "logs": logs,
        "inventory": inventory_payload(db, user.character),
    }
