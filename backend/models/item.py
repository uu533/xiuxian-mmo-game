from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class ItemTemplate(Base):
    __tablename__ = "item_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    grade: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    description: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    stackable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_stack: Mapped[int] = mapped_column(Integer, default=99, nullable=False)
    effects_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    instances: Mapped[list["ItemInstance"]] = relationship(back_populates="template")
    slots: Mapped[list["InventorySlot"]] = relationship(back_populates="item_template")


class ItemInstance(Base):
    __tablename__ = "item_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_template_id: Mapped[int] = mapped_column(ForeignKey("item_templates.id"), index=True, nullable=False)
    owner_character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True, nullable=False)
    durability: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    exp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rarity: Mapped[str] = mapped_column(String(8), default="白", nullable=False)
    bound: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    extra_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    template: Mapped[ItemTemplate] = relationship(back_populates="instances")
    owner: Mapped["Character"] = relationship(back_populates="item_instances")
