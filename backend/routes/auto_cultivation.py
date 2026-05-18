"""
自动修行只读接口
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.services.auth_service import get_current_user
from backend.services.auto_cultivation_service import get_auto_cultivation_status

router = APIRouter(tags=["auto_cultivation"])


@router.get("/auto-cultivation/status")
def get_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    只读接口：返回当前自动修行状态
    不修改任何玩家数据
    """
    return get_auto_cultivation_status(db, current_user.character)