from fastapi import APIRouter, Depends

from app.api.deps.auth import DbSession, get_current_user
from app.models.user import User
from app.schemas.content import CommentUpdate
from app.services.content_service import CollaborationService

router = APIRouter()


@router.patch("/{comment_id}")
def update_comment(comment_id: str, payload: CommentUpdate, db: DbSession, current_user: User = Depends(get_current_user)):
    row = CollaborationService(db).update_comment(comment_id, payload.content, current_user)
    return {"data": {"id": row.id, "documentId": row.document_id, "authorId": row.author_id, "content": row.content, "createdAt": row.created_at, "updatedAt": row.updated_at}}


@router.delete("/{comment_id}")
def delete_comment(comment_id: str, db: DbSession, current_user: User = Depends(get_current_user)):
    CollaborationService(db).delete_comment(comment_id, current_user)
    return {"data": {"deleted": True, "commentId": comment_id}}
