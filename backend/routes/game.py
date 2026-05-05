from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import ActionResponse, LogResponse, MeResponse
from backend.services.auth_service import get_current_user
from backend.services.game_service import breakthrough, explore, me_payload, train

router = APIRouter(tags=["game"])


@router.get("/me", response_model=MeResponse)
def get_me(current_user: User = Depends(get_current_user)) -> dict:
    return me_payload(current_user)


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


@router.get("/logs", response_model=list[LogResponse])
def get_logs(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
) -> list:
    safe_limit = min(max(limit, 1), 100)
    return sorted(current_user.logs, key=lambda log: log.id, reverse=True)[:safe_limit]
