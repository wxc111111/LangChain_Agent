from datetime import datetime
from pydantic import BaseModel


class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime | None = None


class UserListResponse(BaseModel):
    total: int
    items: list[UserResponse]
