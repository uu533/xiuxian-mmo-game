from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import LoginRequest, RegisterRequest, TokenResponse
from backend.services.auth_service import create_user, login_user

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = create_user(db, payload.username, payload.password)
    token = login_user(db, payload.username, payload.password)
    return TokenResponse(token=token, username=user.username)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    token = login_user(db, payload.username, payload.password)
    return TokenResponse(token=token, username=payload.username)
