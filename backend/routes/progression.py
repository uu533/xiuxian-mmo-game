from fastapi import APIRouter, Depends

from backend.models import User
from backend.services.auth_service import get_current_user
from backend.services.progression_service import artifacts_payload, methods_payload

router = APIRouter(tags=["progression"])


@router.get("/methods")
def get_methods(current_user: User = Depends(get_current_user)) -> list[dict]:
    return methods_payload(current_user.character)


@router.get("/artifacts")
def get_artifacts(current_user: User = Depends(get_current_user)) -> list[dict]:
    return artifacts_payload(current_user.character)
