from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DocumentOwnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    avatarUrl: str | None = None


class DocumentCreate(BaseModel):
    title: str
    content: list[dict[str, Any]] = []
    categoryId: str | None = None
    status: str = "draft"


class DocumentUpdate(BaseModel):
    title: str | None = None
    content: list[dict[str, Any]] | None = None
    categoryId: str | None = None
    summary: str | None = None
    status: str | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: list[dict[str, Any]]
    contentText: str
    summary: str | None = None
    categoryId: str | None = None
    ownerId: str
    ownerName: str
    ownerAvatarUrl: str | None = None
    owner: DocumentOwnerOut
    createdAt: datetime
    updatedAt: datetime
    status: str


class DocumentListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    summary: str | None = None
    contentText: str
    categoryId: str | None = None
    ownerId: str
    ownerName: str
    ownerAvatarUrl: str | None = None
    createdAt: datetime
    updatedAt: datetime
    status: str


class DocumentListMeta(BaseModel):
    page: int
    pageSize: int
    total: int
    totalPages: int
    hasNext: bool
    hasPrev: bool
