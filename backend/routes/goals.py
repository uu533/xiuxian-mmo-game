# Goal Chain Routes
# GET /goals/current - read-only goal recommendations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.services.goal_service import get_current_goals
from backend.services.auth_service import get_current_user


router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("/current")
def get_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get current goal recommendations for the player.
    READ-ONLY API: This endpoint does NOT modify any player state.
    """
    if not current_user.character:
        raise HTTPException(status_code=404, detail="角色不存在")

    try:
        goals = get_current_goals(db, current_user.character)
    except Exception:
        import logging
        logging.exception("目标链生成失败")
        raise HTTPException(status_code=500, detail="获取修行建议失败，请稍后再试。") from None
    return {"goals": goals}