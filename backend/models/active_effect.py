from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base
from backend.utils.time_utils import utc_now


class ActiveEffect(Base):
    __tablename__ = "active_effects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True, nullable=False)
    effect_type: Mapped[str] = mapped_column(String(48), index=True, nullable=False)
    source_item_or_recipe: Mapped[str] = mapped_column(String(96), nullable=False)
    remaining_uses: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    character: Mapped["Character"] = relationship(back_populates="active_effects")
