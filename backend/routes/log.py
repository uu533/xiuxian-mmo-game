from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.repositories.log_repo import list_for_character
from backend.schemas import LogResponse
from backend.services.auth_service import get_current_user

router = APIRouter(tags=["log"])


@router.get("/logs", response_model=list[LogResponse])
def get_logs(
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    safe_limit = min(max(limit, 1), 100)
    return [
        {"id": log.id, "type": log.type, "content": log.content, "data_json": log.data_json, "created_at": log.created_at}
        for log in list_for_character(db, current_user.character.id, safe_limit)
    ]
