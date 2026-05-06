from fastapi import APIRouter

from backend.database import db_summary
from backend.services.simulation_service import run_simulation

router = APIRouter(tags=["dev"])


@router.get("/dev/health")
def dev_health() -> dict:
    return {"ok": True, "message": "Xiuxian MMO API is healthy"}


@router.get("/dev/db-summary")
def dev_db_summary() -> dict:
    return db_summary()


@router.get("/dev/simulation")
def dev_simulation(hours: float = 1, with_sect: bool = False) -> dict:
    return run_simulation(hours, with_sect=with_sect)
