from pydantic import BaseModel, Field

from backend.schemas.character import CharacterResponse
from backend.schemas.inventory import InventorySlotResponse


class ActionExecuteRequest(BaseModel):
    action_type: str = Field(min_length=1, max_length=48)
    params: dict = Field(default_factory=dict)


class ActionResultResponse(BaseModel):
    success: bool
    message: str
    character: CharacterResponse
    rewards: list[dict]
    cost: dict
    logs: list[str]
    inventory: list[InventorySlotResponse]


ActionResponse = ActionResultResponse
