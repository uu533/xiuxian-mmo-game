from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.services.auth_service import get_current_user
from backend.services.sect_service import available_tasks, list_sects, my_tasks, sect_me_payload, shop_payload

router = APIRouter(tags=["sect"])


@router.get("/sects")
def get_sects(db: Session = Depends(get_db)) -> list[dict]:
    return list_sects(db)


@router.get("/sects/me")
def get_my_sect(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    return sect_me_payload(db, current_user.character)


@router.get("/sects/tasks")
def get_sect_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict]:
    return available_tasks(db, current_user.character)


@router.get("/sects/tasks/me")
def get_my_sect_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict]:
    return my_tasks(db, current_user.character)


@router.get("/sects/shop")
def get_sect_shop(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict]:
    return shop_payload(db, current_user.character)
