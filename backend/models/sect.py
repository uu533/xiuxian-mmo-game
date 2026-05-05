from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base
from backend.utils.time_utils import utc_now


class Sect(Base):
    __tablename__ = "sects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    members: Mapped[list["SectMember"]] = relationship(back_populates="sect", cascade="all, delete-orphan")
    characters: Mapped[list["Character"]] = relationship(back_populates="sect")


class SectMember(Base):
    __tablename__ = "sect_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sect_id: Mapped[int] = mapped_column(ForeignKey("sects.id"), index=True, nullable=False)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True, nullable=False)
    position: Mapped[str] = mapped_column(String(32), default="外门弟子", nullable=False)
    contribution: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    sect: Mapped[Sect] = relationship(back_populates="members")
    character: Mapped["Character"] = relationship()
