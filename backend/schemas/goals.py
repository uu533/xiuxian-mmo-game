# Goal Chain Schemas
# MVP - read-only API, no player state modification

from typing import List, Optional
from pydantic import BaseModel


class GoalSchema(BaseModel):
    """Single goal recommendation"""
    id: str
    category: str  # "short_term" or "long_term"
    title: str
    reason: str
    progress_text: Optional[str] = None
    requirements: List[str]
    recommended_action: str
    benefits: str
    priority: int


class GoalsResponse(BaseModel):
    """GET /goals/current response"""
    goals: List[GoalSchema]