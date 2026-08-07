"""认证相关请求 / 响应模型。"""

from typing import Literal

from pydantic import BaseModel, Field

UserRole = Literal["employee", "agent", "admin"]


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class UserPublic(BaseModel):
    id: str
    name: str
    username: str
    role: UserRole
    department: str | None = None


class TokenResponse(BaseModel):
    token: str
    user: UserPublic
