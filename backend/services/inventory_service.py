from sqlalchemy.orm import Session

from backend.models import Character, InventorySlot, ItemInstance, ItemTemplate
from backend.repositories.inventory_repo import get_main_slots, get_template_by_code

MAIN_BAG_SLOTS = 81


def ensure_main_bag_slots(db: Session, character: Character) -> None:
    existing = {
        slot.slot_index
        for slot in get_main_slots(db, character.id)
    }
    for index in range(1, MAIN_BAG_SLOTS + 1):
        if index not in existing:
            db.add(
                InventorySlot(
                    character_id=character.id,
                    container_type="main_bag",
                    container_id=0,
                    slot_index=index,
                    quantity=0,
                )
            )
    db.flush()


def inventory_payload(db: Session, character: Character) -> list[dict]:
    ensure_main_bag_slots(db, character)
    return [slot_payload(slot) for slot in get_main_slots(db, character.id)]


def slot_payload(slot: InventorySlot) -> dict:
    template = slot.item_template
    return {
        "slot_index": slot.slot_index,
        "container_type": slot.container_type,
        "container_id": slot.container_id,
        "item_template_id": slot.item_template_id,
        "item_instance_id": slot.item_instance_id,
        "code": template.code if template else None,
        "name": template.name if template else None,
        "type": template.type if template else None,
        "grade": template.grade if template else None,
        "quantity": slot.quantity,
        "stackable": template.stackable if template else True,
    }


def add_item_to_main_bag(db: Session, character: Character, item_code: str, quantity: int = 1) -> tuple[bool, str, dict | None]:
    ensure_main_bag_slots(db, character)
    template = get_template_by_code(db, item_code)
    if not template:
        return False, f"未知物品模板：{item_code}", None

    if template.stackable:
        remaining = quantity
        for slot in get_main_slots(db, character.id):
            if slot.item_template_id == template.id and slot.quantity < template.max_stack:
                add_count = min(remaining, template.max_stack - slot.quantity)
                slot.quantity += add_count
                remaining -= add_count
                if remaining <= 0:
                    db.flush()
                    return True, f"获得 {template.name} x{quantity}", {"code": item_code, "name": template.name, "quantity": quantity}
        for slot in get_main_slots(db, character.id):
            if slot.item_template_id is None:
                add_count = min(remaining, template.max_stack)
                slot.item_template_id = template.id
                slot.quantity = add_count
                remaining -= add_count
                if remaining <= 0:
                    db.flush()
                    return True, f"获得 {template.name} x{quantity}", {"code": item_code, "name": template.name, "quantity": quantity}
        db.flush()
        gained = quantity - remaining
        if gained > 0:
            return False, f"背包空间不足，只收纳了 {template.name} x{gained}", {"code": item_code, "name": template.name, "quantity": gained}
        return False, f"背包已满，无法获得 {template.name}", None

    for _ in range(quantity):
        slot = next((value for value in get_main_slots(db, character.id) if value.item_template_id is None), None)
        if not slot:
            return False, f"背包已满，无法获得 {template.name}", None
        instance = ItemInstance(item_template_id=template.id, owner_character_id=character.id, bound=False, extra_json={})
        db.add(instance)
        db.flush()
        slot.item_template_id = template.id
        slot.item_instance_id = instance.id
        slot.quantity = 1
    db.flush()
    return True, f"获得 {template.name} x{quantity}", {"code": item_code, "name": template.name, "quantity": quantity}


def consume_slot_item(db: Session, character: Character, slot_index: int, quantity: int = 1) -> tuple[bool, str, ItemTemplate | None]:
    slot = (
        db.query(InventorySlot)
        .filter(
            InventorySlot.character_id == character.id,
            InventorySlot.container_type == "main_bag",
            InventorySlot.container_id == 0,
            InventorySlot.slot_index == slot_index,
        )
        .first()
    )
    if not slot or not slot.item_template:
        return False, "该背包格没有可使用物品。", None
    if slot.quantity < quantity:
        return False, "物品数量不足。", None
    template = slot.item_template
    slot.quantity -= quantity
    if slot.quantity <= 0:
        slot.item_template_id = None
        slot.item_instance_id = None
        slot.quantity = 0
    db.flush()
    return True, f"使用 {template.name} x{quantity}", template
