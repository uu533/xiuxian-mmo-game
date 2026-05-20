from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import ActionExecuteRequest, ActionResponse
from backend.services.action_service import execute_action
from backend.services.auth_service import get_current_user

router = APIRouter(tags=["action"])


@router.post("/action/execute", response_model=ActionResponse)
def execute(
    payload: ActionExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return execute_action(db, current_user, payload.action_type, payload.params)


@router.post("/action/execute-tick", response_model=dict)
def execute_tick(
    payload: ActionExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    专用端点用于 auto_cultivation_tick，避免 ActionResponse schema 过滤掉 new_log 字段。
    """
    return execute_action(db, current_user, payload.action_type, payload.params)


@router.post("/action/train", response_model=ActionResponse)
def train_compat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    return execute_action(db, current_user, "train", {})


@router.post("/action/explore", response_model=ActionResponse)
def explore_compat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    return execute_action(db, current_user, "explore", {})


@router.post("/action/breakthrough", response_model=ActionResponse)
def breakthrough_compat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    return execute_action(db, current_user, "breakthrough", {})


@router.post("/action/meditate", response_model=ActionResponse)
def meditate_compat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    return execute_action(db, current_user, "recover_mana_meditate", {})


@router.post("/action/spirit-stone", response_model=ActionResponse)
def spirit_stone_compat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    return execute_action(db, current_user, "recover_mana_stone", {})


@router.post("/action/pill", response_model=ActionResponse)
def pill_compat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    from backend.services.inventory_service import inventory_payload

    slot = next((item for item in inventory_payload(db, current_user.character) if item["code"] == "mana_pill"), None)
    return execute_action(db, current_user, "use_item", {"slot_index": slot["slot_index"] if slot else 0})
