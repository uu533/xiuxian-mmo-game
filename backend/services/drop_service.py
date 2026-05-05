import random

from sqlalchemy.orm import Session

from backend.configs.drop_tables import DROP_TABLES
from backend.models import Character
from backend.services.inventory_service import add_item_to_main_bag
from backend.utils.random_utils import weighted_choice


def get_drop_items_by_realm(character: Character, rolls: int = 1) -> list[dict]:
    table = DROP_TABLES.get(character.realm_stage, DROP_TABLES["炼气"])
    drops: list[dict] = []
    for _ in range(max(1, rolls)):
        entry = weighted_choice(table, lambda item: item["weight"])
        quantity_range = entry.get("quantity", [1, 1])
        quantity = random.randint(int(quantity_range[0]), int(quantity_range[1]))
        drops.append({"code": entry["item"], "quantity": quantity})
    return drops


def grant_drop_items(db: Session, character: Character, rolls: int = 1) -> tuple[list[dict], list[str]]:
    rewards: list[dict] = []
    messages: list[str] = []
    for drop in get_drop_items_by_realm(character, rolls):
        ok, message, reward = add_item_to_main_bag(db, character, drop["code"], drop["quantity"])
        messages.append(message)
        if reward:
            rewards.append({"type": "item", **reward, "stored": ok})
    return rewards, messages
