from sqlalchemy.orm import Session

from backend.models import InventorySlot, ItemTemplate


def get_template_by_code(db: Session, code: str) -> ItemTemplate | None:
    return db.query(ItemTemplate).filter(ItemTemplate.code == code).first()


def get_main_slots(db: Session, character_id: int) -> list[InventorySlot]:
    return (
        db.query(InventorySlot)
        .filter(
            InventorySlot.character_id == character_id,
            InventorySlot.container_type == "main_bag",
            InventorySlot.container_id == 0,
        )
        .order_by(InventorySlot.slot_index)
        .all()
    )
