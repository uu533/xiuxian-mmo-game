from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import ActionResponse, LogResponse, MeResponse, TitleRequest
from backend.services.auth_service import get_current_user
from backend.services.game_service import (
    breakthrough,
    explore,
    meditate_restore_mana,
    me_payload,
    pill_restore_mana,
    set_title,
    spirit_stone_restore_mana,
    train,
)

router = APIRouter(tags=["game"])


@router.get("/me", response_model=MeResponse)
def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    payload = me_payload(current_user)
    db.commit()
    return payload


@router.post("/action/train", response_model=ActionResponse)
def train_action(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return train(db, current_user)


@router.post("/action/explore", response_model=ActionResponse)
def explore_action(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return explore(db, current_user)


@router.post("/action/breakthrough", response_model=ActionResponse)
def breakthrough_action(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return breakthrough(db, current_user)


@router.post("/action/meditate", response_model=ActionResponse)
def meditate_action(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return meditate_restore_mana(db, current_user)


@router.post("/action/spirit-stone", response_model=ActionResponse)
def spirit_stone_action(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return spirit_stone_restore_mana(db, current_user)


@router.post("/action/pill", response_model=ActionResponse)
def pill_action(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return pill_restore_mana(db, current_user)


@router.post("/character/title", response_model=ActionResponse)
def set_character_title(
    payload: TitleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return set_title(db, current_user, payload.title)


@router.get("/logs", response_model=list[LogResponse])
def get_logs(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
) -> list:
    safe_limit = min(max(limit, 1), 100)
    return sorted(current_user.logs, key=lambda log: log.id, reverse=True)[:safe_limit]
