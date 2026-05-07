from sqlalchemy.orm import Session

from backend.models import GameLog


def list_for_character(db: Session, character_id: int, limit: int = 30) -> list[GameLog]:
    return (
        db.query(GameLog)
        .filter(GameLog.character_id == character_id)
        .order_by(GameLog.id.desc())
        .limit(limit)
        .all()
    )
