from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class InventorySlot(Base):
    __tablename__ = "inventory_slots"
    __table_args__ = (
        UniqueConstraint("character_id", "container_type", "container_id", "slot_index", name="uq_inventory_slot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True, nullable=False)
    container_type: Mapped[str] = mapped_column(String(32), default="main_bag", nullable=False)
    container_id: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    slot_index: Mapped[int] = mapped_column(Integer, nullable=False)
    item_template_id: Mapped[int | None] = mapped_column(ForeignKey("item_templates.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    item_instance_id: Mapped[int | None] = mapped_column(ForeignKey("item_instances.id"), nullable=True)

    character: Mapped["Character"] = relationship(back_populates="inventory_slots")
    item_template: Mapped["ItemTemplate | None"] = relationship(back_populates="slots")
    item_instance: Mapped["ItemInstance | None"] = relationship()
