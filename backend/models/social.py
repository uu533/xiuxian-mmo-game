from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base
from backend.utils.time_utils import utc_now


class Friendship(Base):
    __tablename__ = "friendships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True, nullable=False)
    friend_character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    character: Mapped["Character"] = relationship(foreign_keys=[character_id])
    friend_character: Mapped["Character"] = relationship(foreign_keys=[friend_character_id])


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_character_id: Mapped[int | None] = mapped_column(ForeignKey("characters.id"), index=True, nullable=True)
    receiver_character_id: Mapped[int | None] = mapped_column(ForeignKey("characters.id"), index=True, nullable=True)
    channel_type: Mapped[str] = mapped_column(String(24), default="private", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    sender: Mapped["Character | None"] = relationship(foreign_keys=[sender_character_id])
    receiver: Mapped["Character | None"] = relationship(foreign_keys=[receiver_character_id])
