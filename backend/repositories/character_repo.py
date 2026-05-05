from sqlalchemy.orm import Session

from backend.models import Character


def get_by_user_id(db: Session, user_id: int) -> Character | None:
    return db.query(Character).filter(Character.user_id == user_id).first()


def get_by_id(db: Session, character_id: int) -> Character | None:
    return db.query(Character).filter(Character.id == character_id).first()
