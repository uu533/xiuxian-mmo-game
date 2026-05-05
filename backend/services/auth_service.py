import secrets

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.configs.realms import STARTING_REALM
from backend.database import get_db
from backend.models import Character, User
from backend.repositories import user_repo
from backend.services.calc_service import sync_base_and_caps
from backend.services.inventory_service import ensure_main_bag_slots
from backend.services.log_service import write_log
from backend.services.spiritual_root_service import random_spiritual_root
from backend.utils.security import hash_password, make_token, verify_password
from backend.utils.time_utils import utc_now


def create_user(db: Session, username: str, password: str) -> User:
    exists = user_repo.get_by_username(db, username)
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")

    root = random_spiritual_root()
    user = User(username=username, password_hash=hash_password(password), status="active")
    db.add(user)
    db.flush()

    character = Character(
        user_id=user.id,
        name=username,
        title="师兄",
        realm=STARTING_REALM.name,
        realm_stage=STARTING_REALM.stage,
        cultivation_cap=STARTING_REALM.cultivation_cap,
        spiritual_root=root.name,
        hidden_luck=root.base_luck + secrets.randbelow(9),
        hp=100 + secrets.randbelow(16),
        mana=100,
        sect_position="散修",
    )
    sync_base_and_caps(character)
    db.add(character)
    db.flush()
    ensure_main_bag_slots(db, character)
    write_log(db, user, "system", f"你觉醒「{root.name}」，踏上修仙之路。{root.description}", {"spiritual_root": root.name})
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, username: str, password: str) -> str:
    user = user_repo.get_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="账号状态不可登录")

    token = make_token()
    user.last_login_at = utc_now()
    user_repo.add_token(db, user.id, token)
    if user.character:
        write_log(db, user, "system", "你回到洞府，重新接续修行。", {})
    db.commit()
    return token


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少 token")
    token_value = authorization.removeprefix("Bearer ").strip()
    user = user_repo.get_by_token(db, token_value)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 无效")
    return user
