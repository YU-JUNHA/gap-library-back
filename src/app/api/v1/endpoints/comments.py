from fastapi import APIRouter, Depends

from app.api.deps.auth import DbSession, get_current_user
from app.models.user import User
from app.schemas.content import CommentUpdate
from app.schemas.content import to_comment_out
from app.services.content_service import CollaborationService

router = APIRouter()


@router.patch("/{comment_id}")
def update_comment(comment_id: str, payload: CommentUpdate, db: DbSession, current_user: User = Depends(get_current_user)):
    row = CollaborationService(db).update_comment(comment_id, payload.content, current_user)
    return {"data": to_comment_out(row, row.author).model_dump()}


@router.delete("/{comment_id}")
def delete_comment(comment_id: str, db: DbSession, current_user: User = Depends(get_current_user)):
    CollaborationService(db).delete_comment(comment_id, current_user)
    return {"data": {"deleted": True, "commentId": comment_id}}
