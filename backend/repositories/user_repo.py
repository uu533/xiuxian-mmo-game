from sqlalchemy.orm import Session

from backend.models import AuthToken, User


def get_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_by_token(db: Session, token_value: str) -> User | None:
    token = db.query(AuthToken).filter(AuthToken.token == token_value).first()
    return token.user if token else None


def add_token(db: Session, user_id: int, token_value: str) -> None:
    db.add(AuthToken(user_id=user_id, token=token_value))
