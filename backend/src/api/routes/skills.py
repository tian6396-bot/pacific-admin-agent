"""Skill 列表与确认闸路由。"""

from fastapi import APIRouter, HTTPException, status

from pycore.api.responses import success_response
from src.api.deps import CurrentUser, DbSession
from src.models.skill import SkillCancelRequest, SkillConfirmRequest
from src.services.skill_service import SkillService

router = APIRouter(prefix="/skills", tags=["skills"])


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("")
async def list_skills(db: DbSession, user: CurrentUser):
    _ = user
    items = await SkillService(db).list_skills()
    return success_response(data=[i.model_dump(mode="json") for i in items])


@router.get("/runs/{run_id}")
async def get_run(run_id: str, db: DbSession, user: CurrentUser):
    try:
        run = await SkillService(db).get_run(user, run_id)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=run.model_dump(mode="json"))


@router.post("/runs/{run_id}/confirm")
async def confirm_run(
    run_id: str,
    db: DbSession,
    user: CurrentUser,
    body: SkillConfirmRequest = SkillConfirmRequest(),
):
    _ = body
    try:
        run = await SkillService(db).confirm(user, run_id)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=run.model_dump(mode="json"), message="已确认并执行")


@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    db: DbSession,
    user: CurrentUser,
    body: SkillCancelRequest = SkillCancelRequest(),
):
    try:
        run = await SkillService(db).cancel(user, run_id, body.reason or "")
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return success_response(data=run.model_dump(mode="json"), message="已取消")


@router.get("/{skill_id}")
async def get_skill(skill_id: str, db: DbSession, user: CurrentUser):
    _ = user
    try:
        skill, nodes = await SkillService(db).get_skill_detail(skill_id)
    except (FileNotFoundError, ValueError) as exc:
        raise _http_error(exc) from exc
    return success_response(
        data={
            "skill": skill.model_dump(mode="json"),
            "nodes": [n.model_dump(mode="json") for n in nodes],
        }
    )
