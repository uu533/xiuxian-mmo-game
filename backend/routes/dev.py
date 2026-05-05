from fastapi import APIRouter

from backend.database import db_summary

router = APIRouter(tags=["dev"])


@router.get("/dev/health")
def dev_health() -> dict:
    return {"ok": True, "message": "Xiuxian MMO API is healthy"}


@router.get("/dev/db-summary")
def dev_db_summary() -> dict:
    return db_summary()
