from copy import deepcopy

from backend.configs.effects import FORMATION_EFFECTS, ITEM_ACTIVE_EFFECTS
from backend.configs.items import ITEM_TEMPLATES


ITEMS_BY_CODE = {item["code"]: item for item in ITEM_TEMPLATES}

EFFECT_TYPE_NAMES = {
    "explore_luck_bonus": "探索机缘提升",
    "explore_damage_reduction": "探索受伤降低",
    "explore_mana_discount": "探索法力消耗降低",
    "train_cultivation_bonus": "修炼收益提升",
    "train_next_bonus": "下次修炼收益提升",
    "breakthrough_next_bonus": "下次突破概率提升",
    "explore_reward_bonus": "探索收获提升",
}

EFFECT_TYPE_SUMMARIES = {
    "explore_luck_bonus": "提高探索中触发机缘的机会。",
    "explore_damage_reduction": "降低探索战斗或危险事件造成的伤害。",
    "explore_mana_discount": "减少下一次探索消耗的法力。",
    "train_cultivation_bonus": "提高后续修炼获得的修为。",
    "train_next_bonus": "提高下一次修炼获得的修为，触发后消耗。",
    "breakthrough_next_bonus": "提高下一次突破判定的成功率，判定后消耗。",
    "explore_reward_bonus": "提高探索获得资源的数量。",
}

FORMATION_NAMES = {
    "formation_gather_spirit": "聚灵阵",
    "formation_guard": "护身阵",
    "formation_draw_spirit": "引灵阵",
}

FORMATION_DESCRIPTIONS = {
    "formation_gather_spirit": "布置后获得临时修炼收益提升效果。",
    "formation_guard": "布置后获得临时探索受伤降低效果。",
    "formation_draw_spirit": "布置后获得临时探索收获提升效果。",
}


def item_name(code: str | None) -> str:
    if not code:
        return ""
    return ITEMS_BY_CODE.get(code, {}).get("name") or FORMATION_NAMES.get(code) or "未知物品"


def item_description(code: str | None) -> str:
    if not code:
        return ""
    return ITEMS_BY_CODE.get(code, {}).get("description") or FORMATION_DESCRIPTIONS.get(code) or ""


def effect_type_name(effect_type: str | None) -> str:
    if not effect_type:
        return ""
    return EFFECT_TYPE_NAMES.get(effect_type, "未知效果")


def effect_summary(effect_type: str | None) -> str:
    if not effect_type:
        return ""
    return EFFECT_TYPE_SUMMARIES.get(effect_type, "")


def source_name(source: str | None) -> str:
    if not source:
        return ""
    return item_name(source)


def material_payload(item: dict) -> dict:
    code = item["code"]
    quantity = int(item.get("quantity", 1))
    return {
        **item,
        "item_id": code,
        "name": item_name(code),
        "count": quantity,
        "quantity": quantity,
    }


def recipe_payload(recipe: dict) -> dict:
    payload = deepcopy(recipe)
    materials = [material_payload(item) for item in recipe.get("required_items", [])]
    payload["required_items"] = materials
    payload["materials"] = materials
    payload["realm_requirement"] = recipe.get("required_realm", "无")

    unlock_item = recipe.get("unlock_item")
    if unlock_item:
        payload["unlock_item_name"] = item_name(unlock_item)

    if recipe.get("output_item_id"):
        output_code = recipe["output_item_id"]
        payload["output_item_name"] = item_name(output_code)
        payload["output_item_description"] = item_description(output_code)
        payload["output_name"] = payload["output_item_name"]
        payload["effect_summary"] = payload["output_item_description"]
    elif recipe.get("output_effect_id"):
        effect_id = recipe["output_effect_id"]
        effect_config = FORMATION_EFFECTS.get(effect_id, {})
        effect_type = effect_config.get("effect_type")
        payload["output_effect_name"] = FORMATION_NAMES.get(effect_id, effect_type_name(effect_type))
        payload["output_effect_description"] = FORMATION_DESCRIPTIONS.get(effect_id, effect_summary(effect_type))
        payload["output_name"] = payload["output_effect_name"]
        payload["effect_summary"] = payload["output_effect_description"]

    return payload


def active_effect_display(effect_type: str, source: str) -> dict:
    return {
        "effect_name": effect_type_name(effect_type),
        "effect_summary": effect_summary(effect_type),
        "source_name": source_name(source),
    }


def item_effect_summary(item_code: str) -> str:
    config = ITEM_ACTIVE_EFFECTS.get(item_code)
    if not config:
        return item_description(item_code)
    effect_type = config.get("effect_type")
    uses = int(config.get("remaining_uses", 1))
    return f"{effect_summary(effect_type)}剩余 {uses} 次。"
