from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import DbSession, get_current_user
from app.models.user import User
from app.schemas.admin import AdminUserRoleUpdate
from app.services.admin_service import AdminService
from app.services.signup_request_service import SignupRequestService

router = APIRouter()


@router.get("/users")
def list_users(
    db: DbSession,
    current_user: User = Depends(get_current_user),
    q: str | None = None,
    role: str | None = None,
    page: int = 1,
    page_size: int = Query(20, alias="pageSize"),
):
    rows, total = AdminService(db).list_users(
        q=q,
        role=role,
        page=page,
        page_size=page_size,
        admin_user=current_user,
    )
    return {
        "data": [
            {
                "id": row.id,
                "name": row.name,
                "email": row.email,
                "role": row.role.value,
                "organization": row.organization,
                "avatarUrl": row.avatar_url,
                "createdAt": row.created_at,
            }
            for row in rows
        ],
        "meta": {"page": page, "pageSize": page_size, "total": total},
    }


@router.patch("/users/{user_id}/role")
def update_role(user_id: str, payload: AdminUserRoleUpdate, db: DbSession, current_user: User = Depends(get_current_user)):
    updated = AdminService(db).update_user_role(user_id=user_id, role=payload.role, admin_user=current_user)
    return {
        "data": {
            "id": updated.id,
            "name": updated.name,
            "email": updated.email,
            "role": updated.role.value,
            "organization": updated.organization,
            "avatarUrl": updated.avatar_url,
            "createdAt": updated.created_at,
        }
    }


@router.get("/signup-requests")
def list_signup_requests(db: DbSession, current_user: User = Depends(get_current_user)):
    service = SignupRequestService(db)
    service.ensure_admin(current_user)
    rows = service.list_pending()
    return {
        "data": [
            {
                "id": row.id,
                "name": row.name,
                "email": row.email,
                "status": row.status.value,
                "requestedAt": row.requested_at,
            }
            for row in rows
        ]
    }


@router.post("/signup-requests/{request_id}/approve")
def approve_signup(request_id: str, db: DbSession, current_user: User = Depends(get_current_user)):
    row, user = SignupRequestService(db).approve(request_id=request_id, admin_user=current_user)
    return {
        "data": {
            "requestId": row.id,
            "status": row.status.value,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "createdAt": user.created_at,
            },
        }
    }


@router.post("/signup-requests/{request_id}/reject")
def reject_signup(request_id: str, db: DbSession, current_user: User = Depends(get_current_user)):
    row = SignupRequestService(db).reject(request_id=request_id, admin_user=current_user)
    return {"data": {"requestId": row.id, "status": row.status.value}}
