from pydantic import BaseModel


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
