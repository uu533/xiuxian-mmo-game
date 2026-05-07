from sqlalchemy.orm import Session

from backend.models import User
from backend.services.action_service import execute_action
from backend.services.character_service import character_payload, set_title as set_character_title
from backend.services.inventory_service import inventory_payload
from backend.services.task_service import active_task_payload, ensure_character_tasks, tasks_payload


def me_payload(db: Session, user: User) -> dict:
    ensure_character_tasks(db, user.character)
    return {
        "username": user.username,
        "character": character_payload(user.character),
        "inventory": inventory_payload(db, user.character),
        "tasks": tasks_payload(user.character),
        "active_task": active_task_payload(user.character),
    }


def train(db: Session, user: User) -> dict:
    return execute_action(db, user, "train", {})


def explore(db: Session, user: User) -> dict:
    return execute_action(db, user, "explore", {})


def breakthrough(db: Session, user: User) -> dict:
    return execute_action(db, user, "breakthrough", {})


def meditate_restore_mana(db: Session, user: User) -> dict:
    return execute_action(db, user, "recover_mana_meditate", {})


def spirit_stone_restore_mana(db: Session, user: User) -> dict:
    return execute_action(db, user, "recover_mana_stone", {})


def pill_restore_mana(db: Session, user: User) -> dict:
    first_pill_slot = next((slot for slot in inventory_payload(db, user.character) if slot["code"] == "mana_pill"), None)
    if not first_pill_slot:
        return execute_action(db, user, "use_item", {"slot_index": 0})
    return execute_action(db, user, "use_item", {"slot_index": first_pill_slot["slot_index"]})


def set_title(db: Session, user: User, title: str) -> dict:
    result = set_character_title(db, user, title)
    db.commit()
    return {
        "success": result["success"],
        "message": result["message"],
        "character": character_payload(user.character),
        "rewards": [],
        "cost": {},
        "logs": [result["message"]],
        "inventory": inventory_payload(db, user.character),
    }
