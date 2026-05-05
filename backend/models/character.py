from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base
from backend.utils.time_utils import utc_now


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(24), default="师兄", nullable=False)
    realm: Mapped[str] = mapped_column(String(24), default="炼气一层", nullable=False)
    realm_stage: Mapped[str] = mapped_column(String(16), default="炼气", nullable=False)
    cultivation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cultivation_cap: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    spiritual_root: Mapped[str] = mapped_column(String(24), default="五行杂灵根", nullable=False)
    age: Mapped[int] = mapped_column(Integer, default=16, nullable=False)
    lifespan: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    hp: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    max_hp: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    mana: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    max_mana: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    base_attack: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    base_defense: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    hidden_luck: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    hidden_inner_demon: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spirit_stones: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    sect_id: Mapped[int | None] = mapped_column(ForeignKey("sects.id"), nullable=True)
    sect_position: Mapped[str] = mapped_column(String(32), default="散修", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped["User"] = relationship(back_populates="character")
    sect: Mapped["Sect | None"] = relationship(back_populates="characters")
    inventory_slots: Mapped[list["InventorySlot"]] = relationship(back_populates="character", cascade="all, delete-orphan")
    item_instances: Mapped[list["ItemInstance"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    methods: Mapped[list["CharacterMethod"]] = relationship(back_populates="character", cascade="all, delete-orphan")
    artifacts: Mapped[list["CharacterArtifact"]] = relationship(back_populates="character", cascade="all, delete-orphan")
    action_records: Mapped[list["ActionRecord"]] = relationship(back_populates="character", cascade="all, delete-orphan")
    game_logs: Mapped[list["GameLog"]] = relationship(back_populates="character", cascade="all, delete-orphan")
    derived_stats: Mapped["CharacterDerivedStats | None"] = relationship(back_populates="character", cascade="all, delete-orphan", uselist=False)
    tasks: Mapped[list["CharacterTask"]] = relationship(back_populates="character", cascade="all, delete-orphan")


class CharacterDerivedStats(Base):
    __tablename__ = "character_derived_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), unique=True, index=True, nullable=False)
    final_attack: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    final_defense: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    final_mana: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    cultivation_speed: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    breakthrough_bonus: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    character: Mapped[Character] = relationship(back_populates="derived_stats")
