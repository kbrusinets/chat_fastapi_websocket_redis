from pydantic import BaseModel


class UserBase(BaseModel):
    id: int
    name: str