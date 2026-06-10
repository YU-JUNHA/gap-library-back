from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import Comment
from app.models.user import User


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    documentId: str
    content: str
    createdAt: datetime
    updatedAt: datetime
    authorId: str
    authorName: str
    authorAvatarUrl: str | None = None
    authorOrganization: str | None = None


class ReactionSummaryOut(BaseModel):
    likeCount: int
    likedByMe: bool


class CategoryCreate(BaseModel):
    name: str
    parentId: str | None = None


class CategoryUpdate(BaseModel):
    name: str


class CategoryMove(BaseModel):
    newParentId: str | None = None
    newOrder: int = 0
    includeChildren: bool = True


class TemplateCreate(BaseModel):
    name: str
    content: str


class TemplateUpdate(BaseModel):
    name: str | None = None
    content: str | None = None


class TemplateApply(BaseModel):
    documentId: str


class ReactionCreate(BaseModel):
    type: str


class CommentCreate(BaseModel):
    content: str


class CommentUpdate(BaseModel):
    content: str


def to_comment_out(comment: Comment, author: User) -> CommentOut:
    return CommentOut(
        id=comment.id,
        documentId=comment.document_id,
        content=comment.content,
        createdAt=comment.created_at,
        updatedAt=comment.updated_at,
        authorId=author.id,
        authorName=author.name,
        authorAvatarUrl=author.avatar_url,
        authorOrganization=author.organization,
    )
