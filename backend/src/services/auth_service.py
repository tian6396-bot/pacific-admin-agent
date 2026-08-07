"""认证服务：登录、JWT、演示账号种子。"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import create_access_token, hash_password, verify_password
from src.db.models import User
from src.models.auth import TokenResponse, UserPublic
from src.repositories.user import UserRepository

DEMO_USERS = (
    {
        "username": "emp",
        "password": "123456",
        "name": "张敏",
        "role": "employee",
        "department": "行政部",
    },
    {
        "username": "agent",
        "password": "123456",
        "name": "王敏",
        "role": "agent",
        "department": "财务组",
    },
    {
        "username": "admin",
        "password": "123456",
        "name": "陈浩",
        "role": "admin",
        "department": "运营中心",
    },
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)

    def to_public(self, user: User) -> UserPublic:
        return UserPublic(
            id=user.id,
            name=user.name,
            username=user.username,
            role=user.role,  # type: ignore[arg-type]
            department=user.department,
        )

    async def login(self, username: str, password: str) -> TokenResponse:
        user = await self.users.get_by_username(username)
        if user is None or not user.is_active:
            raise PermissionError("账号或密码错误")
        if not verify_password(password, user.hashed_password):
            raise PermissionError("账号或密码错误")

        token = create_access_token(subject=user.id, role=user.role, extra={"username": user.username})
        return TokenResponse(token=token, user=self.to_public(user))

    async def get_user(self, user_id: str) -> User | None:
        return await self.users.get_by_id(user_id)

    async def ensure_demo_users(self) -> None:
        for item in DEMO_USERS:
            existing = await self.users.get_by_username(item["username"])
            if existing:
                continue
            user = User(
                id=str(uuid.uuid4()),
                username=item["username"],
                hashed_password=hash_password(item["password"]),
                name=item["name"],
                role=item["role"],
                department=item["department"],
                is_active=True,
            )
            await self.users.create(user)
