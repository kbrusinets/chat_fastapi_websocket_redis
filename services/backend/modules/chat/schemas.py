from pydantic import BaseModel, ConfigDict

from services.app.schemas import ChatTypeEnum


class ChatBase(BaseModel):
    name: str
    type: ChatTypeEnum

class ChatFull(ChatBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

class ChatProgress(BaseModel):
    max_common_progress: int
