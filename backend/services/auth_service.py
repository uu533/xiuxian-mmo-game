import hashlib
import hmac
import secrets

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import AuthToken, Character, Log, User
from backend.services.realm_service import STARTING_CULTIVATION_CAP, STARTING_REALM
from backend.services.spiritual_root_service import random_spiritual_root


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, expected = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return hmac.compare_digest(digest.hex(), expected)


def create_user(db: Session, username: str, password: str) -> User:
    exists = db.query(User).filter(User.username == username).first()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")

    root = random_spiritual_root()
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    db.flush()

    character = Character(
        user_id=user.id,
        realm=STARTING_REALM,
        cultivation_cap=STARTING_CULTIVATION_CAP,
        spiritual_root=root.name,
        luck=root.base_luck + secrets.randbelow(9),
        hp=100 + secrets.randbelow(16),
        mana=60 + secrets.randbelow(16),
        attack=12 + secrets.randbelow(5),
        defense=6 + secrets.randbelow(4),
    )
    db.add(character)
    db.add(Log(user_id=user.id, content=f"你觉醒「{root.name}」，踏上修仙之路。{root.description}"))
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, username: str, password: str) -> str:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = secrets.token_urlsafe(48)
    db.add(AuthToken(user_id=user.id, token=token))
    db.add(Log(user_id=user.id, content="你回到洞府，重新接续修行。"))
    db.commit()
    return token


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少 token")
    token_value = authorization.removeprefix("Bearer ").strip()
    token = db.query(AuthToken).filter(AuthToken.token == token_value).first()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 无效")
    return token.user

