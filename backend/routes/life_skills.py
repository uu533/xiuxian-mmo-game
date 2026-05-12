from fastapi import APIRouter

from backend.services.life_skill_service import get_all_recipes

router = APIRouter(prefix="/life-skills", tags=["life-skills"])


@router.get("/recipes")
def list_recipes() -> dict[str, list[dict]]:
    return get_all_recipes()