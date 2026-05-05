from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=64)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    token: str
    username: str


class InventoryResponse(BaseModel):
    slot_index: int
    name: str | None
    quantity: int


class CharacterResponse(BaseModel):
    title: str
    unlocked_titles: list[str]
    life_status: str
    sect_name: str | None
    sect_branch: str | None
    sect_position: str
    identity_status: str
    realm: str
    cultivation: int
    cultivation_cap: int
    spiritual_root: str
    age: int
    lifespan: int
    hp: int
    mana: int
    max_mana: int
    attack: int
    defense: int
    spirit_stones: int
    attack_base: int
    defense_base: int
    attack_bonus: int
    defense_bonus: int
    mana_bonus: int


class MeResponse(BaseModel):
    username: str
    character: CharacterResponse
    inventory: list[InventoryResponse]


class ActionResponse(BaseModel):
    message: str
    character: CharacterResponse
    inventory: list[InventoryResponse]


class TitleRequest(BaseModel):
    title: str = Field(min_length=1, max_length=24)


class LogResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
