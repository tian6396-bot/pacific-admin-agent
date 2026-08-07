"""认证路由。"""

from fastapi import APIRouter, HTTPException, status

from pycore.api.responses import success_response
from src.api.deps import CurrentUser, DbSession
from src.models.auth import LoginRequest
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginRequest, db: DbSession):
    service = AuthService(db)
    try:
        result = await service.login(body.username, body.password)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return success_response(data=result.model_dump(), message="登录成功")


@router.get("/me")
async def me(user: CurrentUser, db: DbSession):
    service = AuthService(db)
    return success_response(data=service.to_public(user).model_dump())
