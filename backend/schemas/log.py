from datetime import datetime

from pydantic import BaseModel


class LogResponse(BaseModel):
    id: int
    type: str
    content: str
    data_json: dict
    created_at: datetime
