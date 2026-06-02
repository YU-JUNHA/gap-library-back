from fastapi import APIRouter, Depends

from app.api.deps.auth import DbSession, get_current_user
from app.models.user import User
from app.services.content_service import StatsService

router = APIRouter()


@router.get("/dashboard")
def dashboard_stats(db: DbSession, current_user: User = Depends(get_current_user)):
    return {"data": StatsService(db).dashboard(current_user)}


@router.get("/mypage")
def mypage_stats(db: DbSession, current_user: User = Depends(get_current_user)):
    return {"data": StatsService(db).mypage(current_user)}
