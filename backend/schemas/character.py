from pydantic import BaseModel, Field

from backend.schemas.inventory import InventorySlotResponse


class CharacterResponse(BaseModel):
    id: int
    name: str
    title: str
    unlocked_titles: list[str]
    life_status: str
    realm: str
    realm_stage: str
    cultivation: int
    cultivation_cap: int
    spiritual_root: str
    age: int
    lifespan: int
    hp: int
    max_hp: int
    mana: int
    max_mana: int
    scout_talisman_charges: int
    guard_talisman_charges: int
    swift_talisman_charges: int
    active_effects: list[dict] = Field(default_factory=list)
    attack: int
    defense: int
    base_attack: int
    base_defense: int
    attack_bonus: int
    defense_bonus: int
    cultivation_speed: float
    breakthrough_rate: float
    spirit_stones: int
    sect_id: int | None
    sect_name: str | None
    sect_position: str
    identity_status: str
    auto_cultivation: dict | None = None


class MeResponse(BaseModel):
    username: str
    character: CharacterResponse
    inventory: list[InventorySlotResponse]
    tasks: list[dict] = []
    active_task: dict | None = None


class TitleRequest(BaseModel):
    title: str = Field(min_length=1, max_length=24)
