from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base
from backend.utils.time_utils import utc_now


class Sect(Base):
    __tablename__ = "sects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    faction: Mapped[str] = mapped_column(String(24), index=True, default="righteous", nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_player_created: Mapped[bool] = mapped_column(Integer, default=0, nullable=False)
    leader_character_id: Mapped[int | None] = mapped_column(ForeignKey("characters.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    members: Mapped[list["SectMember"]] = relationship(back_populates="sect", cascade="all, delete-orphan")
    tasks: Mapped[list["SectTask"]] = relationship(back_populates="sect", cascade="all, delete-orphan")
    reputation_logs: Mapped[list["SectReputationLog"]] = relationship(back_populates="sect", cascade="all, delete-orphan")
    characters: Mapped[list["Character"]] = relationship(back_populates="sect", foreign_keys="Character.sect_id")


class SectMember(Base):
    __tablename__ = "sect_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sect_id: Mapped[int] = mapped_column(ForeignKey("sects.id"), index=True, nullable=False)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True, nullable=False)
    position: Mapped[str] = mapped_column(String(32), default="outer_disciple", nullable=False)
    contribution: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reputation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_task_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)

    sect: Mapped[Sect] = relationship(back_populates="members")
    character: Mapped["Character"] = relationship()


class SectTask(Base):
    __tablename__ = "sect_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sect_id: Mapped[int] = mapped_column(ForeignKey("sects.id"), index=True, nullable=False)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True, nullable=False)
    task_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    task_type: Mapped[str] = mapped_column(String(48), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", index=True, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    reward_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sect: Mapped[Sect] = relationship(back_populates="tasks")
    character: Mapped["Character"] = relationship()


class SectReputationLog(Base):
    __tablename__ = "sect_reputation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True, nullable=False)
    sect_id: Mapped[int | None] = mapped_column(ForeignKey("sects.id"), index=True, nullable=True)
    faction: Mapped[str] = mapped_column(String(24), index=True, nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    sect: Mapped[Sect | None] = relationship(back_populates="reputation_logs")
    character: Mapped["Character"] = relationship()
