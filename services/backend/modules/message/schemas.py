from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class MessageFull(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_id: int
    user_id: int
    content: str
    timestamp: datetime


class MessagesPagination(BaseModel):
    messages: List[MessageFull]
    limit: int
    offset: int
    total_count: int
