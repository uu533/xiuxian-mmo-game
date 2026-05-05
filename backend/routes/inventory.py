from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import InventorySlotResponse
from backend.services.auth_service import get_current_user
from backend.services.inventory_service import inventory_payload

router = APIRouter(tags=["inventory"])


@router.get("/inventory", response_model=list[InventorySlotResponse])
def get_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    payload = inventory_payload(db, current_user.character)
    db.commit()
    return payload
