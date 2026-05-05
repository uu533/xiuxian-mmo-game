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
    name: str
    quantity: int


class CharacterResponse(BaseModel):
    realm: str
    cultivation: int
    cultivation_cap: int
    spiritual_root: str
    age: int
    lifespan: int
    hp: int
    mana: int
    attack: int
    defense: int
    inner_demon: int
    luck: int
    spirit_stones: int
    action_points: int
    max_action_points: int
    action_spent_total: int
    age_progress: int


class MeResponse(BaseModel):
    username: str
    character: CharacterResponse
    inventory: list[InventoryResponse]


class ActionResponse(BaseModel):
    message: str
    character: CharacterResponse
    inventory: list[InventoryResponse]


class LogResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
