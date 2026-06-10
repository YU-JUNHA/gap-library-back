from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import DbSession, get_current_user
from app.models.user import User
from app.services.content_service import StatsService

router = APIRouter()


@router.get("/dashboard")
def dashboard_stats(
    db: DbSession,
    draft_limit: int = Query(5, alias="draftLimit", ge=1, le=20),
    current_user: User = Depends(get_current_user),
):
    return {"data": StatsService(db).dashboard(current_user, draft_limit=draft_limit)}


@router.get("/mypage")
def mypage_stats(
    db: DbSession,
    unit: Literal["week", "month", "year"] = Query("month"),
    current_user: User = Depends(get_current_user),
):
    return {"data": StatsService(db).mypage(current_user, unit=unit)}
