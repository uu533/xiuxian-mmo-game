from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class CharacterMethod(Base):
    __tablename__ = "character_methods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True, nullable=False)
    item_instance_id: Mapped[int | None] = mapped_column(ForeignKey("item_instances.id"), nullable=True)
    method_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    exp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    equipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    character: Mapped["Character"] = relationship(back_populates="methods")
    item_instance: Mapped["ItemInstance | None"] = relationship()


class CharacterArtifact(Base):
    __tablename__ = "character_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True, nullable=False)
    item_instance_id: Mapped[int | None] = mapped_column(ForeignKey("item_instances.id"), nullable=True)
    slot_type: Mapped[str] = mapped_column(String(32), default="main", nullable=False)
    equipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    character: Mapped["Character"] = relationship(back_populates="artifacts")
    item_instance: Mapped["ItemInstance | None"] = relationship()
