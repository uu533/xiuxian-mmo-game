import random

from sqlalchemy.orm import Session

from backend.configs.recipes_alchemy import ALCHEMY_RECIPES
from backend.configs.recipes_crafting import CRAFTING_RECIPES
from backend.configs.recipes_formation import FORMATION_RECIPES
from backend.configs.recipes_talisman import TALISMAN_RECIPES
from backend.configs.realms import REALM_NAMES
from backend.models import Character, LifeSkillRecord
from backend.services.active_effect_service import activate_formation_effect
from backend.services.calc_service import get_life_skill_mana_cost, get_life_skill_success_rate
from backend.services.display_service import item_name, recipe_payload
from backend.services.inventory_service import add_item_to_main_bag, consume_item_by_code, has_item

RECIPES_BY_SKILL = {
    "alchemy": ALCHEMY_RECIPES,
    "talisman": TALISMAN_RECIPES,
    "crafting": CRAFTING_RECIPES,
    "formation": FORMATION_RECIPES,
}


def get_recipe(skill_type: str, recipe_id: str) -> dict | None:
    return next((recipe for recipe in RECIPES_BY_SKILL.get(skill_type, []) if recipe["id"] == recipe_id), None)


def get_all_recipes() -> dict[str, list[dict]]:
    """Return all recipes grouped by skill type, for API exposure."""
    return {
        "alchemy": [recipe_payload(recipe) for recipe in ALCHEMY_RECIPES],
        "talisman": [recipe_payload(recipe) for recipe in TALISMAN_RECIPES],
        "crafting": [recipe_payload(recipe) for recipe in CRAFTING_RECIPES],
        "formation": [recipe_payload(recipe) for recipe in FORMATION_RECIPES],
    }


def run_life_skill(db: Session, character: Character, skill_type: str, recipe_id: str) -> tuple[bool, str, dict, dict, list[dict]]:
    recipe = get_recipe(skill_type, recipe_id)
    if not recipe:
        data = {"reason": "recipe_not_found", "skill_type": skill_type, "recipe_id": recipe_id}
        _record(db, character, skill_type, recipe_id, False, {}, data)
        return False, "没有找到这个配方。", data, {}, []
    if recipe.get("skill_type") != skill_type:
        data = {"reason": "skill_type_mismatch", "skill_type": skill_type, "recipe_id": recipe_id}
        _record(db, character, skill_type, recipe_id, False, {}, data)
        return False, "配方类型不匹配。", data, {}, []

    required_realm = recipe.get("required_realm")
    if required_realm and not _realm_at_least(character.realm, required_realm):
        data = {"reason": "required_realm", "required_realm": required_realm, "recipe_id": recipe_id}
        _record(db, character, skill_type, recipe_id, False, {}, data)
        return False, f"境界不足：制作{recipe['name']}至少需要{required_realm}。", data, {}, []

    unlock_item = recipe.get("unlock_item")
    if unlock_item and not has_item(db, character, unlock_item, 1):
        data = {"reason": "recipe_locked", "unlock_item": unlock_item, "recipe_id": recipe_id}
        _record(db, character, skill_type, recipe_id, False, {}, data)
        return False, f"尚未学会配方：需要{item_name(unlock_item)}。", data, {}, []

    mana_cost = get_life_skill_mana_cost(character, recipe)
    if character.mana < mana_cost:
        cost = {"mana": mana_cost}
        data = {"reason": "insufficient_mana", "recipe_id": recipe_id}
        _record(db, character, skill_type, recipe_id, False, cost, data)
        return False, f"法力不足：制作{recipe['name']}需要 {mana_cost} 点法力。", data, cost, []

    required_items = recipe.get("required_items", [])
    for item in required_items:
        if not has_item(db, character, item["code"], int(item.get("quantity", 1))):
            cost = {"mana": mana_cost, "items": required_items}
            data = {"reason": "missing_material", "item": item["code"], "recipe_id": recipe_id}
            _record(db, character, skill_type, recipe_id, False, cost, data)
            return False, f"缺少材料：{item_name(item['code'])} x{item.get('quantity', 1)}", data, cost, []

    character.mana -= mana_cost
    for item in required_items:
        consume_item_by_code(db, character, item["code"], int(item.get("quantity", 1)))

    cost = {"mana": mana_cost, "items": required_items}
    success_rate = get_life_skill_success_rate(character, recipe)
    success = random.random() <= success_rate
    rewards: list[dict] = []
    data = {"recipe_id": recipe_id, "skill_type": skill_type, "success_rate": success_rate, "recipe": recipe}
    if success:
        if recipe.get("output_effect_id"):
            active_effect = activate_formation_effect(db, character.user, recipe["output_effect_id"])
            data.update({"output_effect_id": recipe["output_effect_id"], "active_effect": active_effect})
            _record(db, character, skill_type, recipe_id, True, cost, data)
            return True, f"{recipe['name']}布置完成，获得效果：{active_effect.get('effect_name', '临时效果')}。", data, cost, [{"type": "active_effect", **active_effect}]
        ok, message, payload = add_item_to_main_bag(db, character, recipe["output_item_id"], int(recipe.get("output_count", 1)))
        if not ok:
            data.update({"reason": "inventory_full", "stored": False, "item": payload})
            _record(db, character, skill_type, recipe_id, False, cost, data)
            return False, message, data, cost, []
        rewards.append({"type": "item", **(payload or {})})
        data.update({"output_item_id": recipe["output_item_id"], "output_count": int(recipe.get("output_count", 1)), "stored": True})
        _record(db, character, skill_type, recipe_id, True, cost, data)
        return True, f"{recipe['name']}制作完成。{message}", data, cost, rewards

    data["reason"] = "craft_failed"
    _record(db, character, skill_type, recipe_id, False, cost, data)
    return False, f"{recipe['name']}制作失败，材料与法力已消耗。", data, cost, []


def _record(db: Session, character: Character, skill_type: str, recipe_id: str, success: bool, cost: dict, data: dict) -> None:
    db.add(
        LifeSkillRecord(
            character_id=character.id,
            skill_type=skill_type,
            recipe_id=recipe_id,
            success=success,
            cost_json=cost,
            result_json=data,
        )
    )
    db.flush()


def _realm_at_least(current: str, required: str) -> bool:
    if current not in REALM_NAMES or required not in REALM_NAMES:
        return False
    return REALM_NAMES.index(current) >= REALM_NAMES.index(required)
