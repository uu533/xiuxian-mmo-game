from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import MeResponse, TitleRequest
from backend.services.auth_service import get_current_user
from backend.services.character_service import character_payload, set_title
from backend.services.inventory_service import inventory_payload
from backend.services.log_service import write_log
from backend.services.task_service import active_task_payload, ensure_character_tasks, tasks_payload

router = APIRouter(tags=["character"])


@router.get("/character/me", response_model=MeResponse)
def get_character_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    ensure_character_tasks(db, current_user.character)
    payload = {
        "username": current_user.username,
        "character": character_payload(current_user.character),
        "inventory": inventory_payload(db, current_user.character),
        "tasks": tasks_payload(current_user.character),
        "active_task": active_task_payload(current_user.character),
    }
    db.commit()
    return payload


@router.get("/me", response_model=MeResponse)
def get_me_compat(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return get_character_me(db, current_user)


@router.post("/character/title")
def set_character_title(
    payload: TitleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = set_title(db, current_user, payload.title)
    write_log(db, current_user, "system", result["message"], {"title": payload.title, "success": result["success"]})
    db.commit()
    return {
        "success": result["success"],
        "message": result["message"],
        "character": character_payload(current_user.character),
        "rewards": [],
        "cost": {},
        "logs": [result["message"]],
        "inventory": inventory_payload(db, current_user.character),
    }
