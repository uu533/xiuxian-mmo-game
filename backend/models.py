from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    character: Mapped["Character"] = relationship(back_populates="user", cascade="all, delete-orphan")
    logs: Mapped[list["Log"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    tokens: Mapped[list["AuthToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    inventory: Mapped[list["InventoryItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(24), default="师兄", nullable=False)
    realm: Mapped[str] = mapped_column(String(24), default="炼气一层", nullable=False)
    cultivation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cultivation_cap: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    spiritual_root: Mapped[str] = mapped_column(String(24), default="五行杂灵根", nullable=False)
    age: Mapped[int] = mapped_column(Integer, default=16, nullable=False)
    lifespan: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    hp: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    mana: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    attack: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    defense: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    inner_demon: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    luck: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    spirit_stones: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    action_points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    max_action_points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    action_spent_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    age_progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_action_recovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped[User] = relationship(back_populates="character")


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped[User] = relationship(back_populates="logs")


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    token: Mapped[str] = mapped_column(String(96), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped[User] = relationship(back_populates="tokens")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped[User] = relationship(back_populates="inventory")
