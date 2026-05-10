import random

from sqlalchemy.orm import Session

from backend.configs.recipes import (
    LIFE_SKILL_MANA_COSTS,
    get_all_recipes,
    get_recipe_by_id,
    get_recipes_by_type,
)
from backend.models import Character, User
from backend.repositories.inventory_repo import get_template_by_code
from backend.services.inventory_service import (
    add_item_to_main_bag,
    consume_item_by_code,
    has_item,
)


def get_available_recipes(character: Character, skill_type: str) -> list[dict]:
    recipes = get_recipes_by_type(skill_type)
    available = []
    for recipe in recipes:
        if not _recipe_unlocked(character, recipe):
            continue
        available.append({
            "id": recipe["id"],
            "name": recipe["name"],
            "skill_type": recipe["skill_type"],
            "required_items": recipe["required_items"],
            "mana_cost": recipe["mana_cost"],
            "success_rate": recipe["success_rate"],
            "output_item_id": recipe["output_item_id"],
            "output_count": recipe["output_count"],
            "description": recipe.get("description", ""),
        })
    return available


def execute_recipe(db: Session, user: User, character: Character, recipe_id: str) -> tuple[bool, str, dict]:
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        return False, f"未知配方：{recipe_id}", {}

    ok, message = _validate_recipe(db, character, recipe)
    if not ok:
        return False, message, {}

    ok, message = _spend_mana_life_skill(character, recipe)
    if not ok:
        return False, message, {}

    ok, message = _consume_materials(db, character, recipe)
    if not ok:
        character.mana += recipe["mana_cost"]
        return False, message, {}

    output_ok, output_message, output_data = _create_output_item(db, character, recipe)
    if not output_ok:
        _refund_materials(db, character, recipe)
        character.mana += recipe["mana_cost"]
        return False, output_message, {}

    _record_life_skill_log(db, user, character, recipe)
    return True, f"使用 {recipe['name']}，{output_message}", output_data


def _recipe_unlocked(character: Character, recipe: dict) -> bool:
    required_realm = recipe.get("required_realm", "炼气")
    if required_realm == "炼气":
        return True
    if required_realm == "筑基":
        return character.realm not in ("炼气一层",)
    return True


def _validate_recipe(db: Session, character: Character, recipe: dict) -> tuple[bool, str]:
    required_sect = recipe.get("required_sect")
    if required_sect:
        return False, f"该配方需要加入特定宗门 [{required_sect}]。"

    if recipe.get("required_contribution", 0) > 0:
        return False, f"该配方需要宗门贡献 {recipe['required_contribution']}。"

    return True, ""


def _spend_mana_life_skill(character: Character, recipe: dict) -> tuple[bool, str]:
    cost = recipe["mana_cost"]
    if character.mana < cost:
        return False, f"法力不足，炼制需要 {cost} 点法力，当前只有 {character.mana} 点。"
    character.mana -= cost
    return True, ""


def _consume_materials(db: Session, character: Character, recipe: dict) -> tuple[bool, str]:
    required_items = recipe.get("required_items", {})
    for item_code, quantity in required_items.items():
        if not has_item(db, character, item_code, quantity):
            return False, f"材料 {item_code} 不足，需要 {quantity} 个。"
    for item_code, quantity in required_items.items():
        consume_item_by_code(db, character, item_code, quantity)
    return True, ""


def _refund_materials(db: Session, character: Character, recipe: dict) -> None:
    required_items = recipe.get("required_items", {})
    for item_code, quantity in required_items.items():
        add_item_to_main_bag(db, character, item_code, quantity)


def _create_output_item(db: Session, character: Character, recipe: dict) -> tuple[bool, str, dict]:
    output_item_id = recipe["output_item_id"]
    output_count = recipe["output_count"]
    success_rate = recipe.get("success_rate", 1.0)

    if random.random() > success_rate:
        return False, "炼制失败，材料浪费。", {"success": False, "recipe_id": recipe["id"]}

    ok, message, data = add_item_to_main_bag(db, character, output_item_id, output_count)
    if not ok:
        return False, f"炼制成功，但背包空间不足：{message}", {"success": False, "recipe_id": recipe["id"], "packed": False}
    return True, f"成功产出 {data.get('name', output_item_id)} x{output_count}", {
        "success": True,
        "recipe_id": recipe["id"],
        "output_item_id": output_item_id,
        "output_count": output_count,
        "packed": True,
    }


def _record_life_skill_log(db: Session, user: User, character: Character, recipe: dict) -> None:
    from backend.services.log_service import write_log
    write_log(db, user, recipe["skill_type"], f"使用生活技能 {recipe['name']}", {"recipe_id": recipe["id"]})
