from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentOwnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    avatarUrl: str | None = None
    organization: str | None = None


class DocumentCreate(BaseModel):
    title: str
    content: list[dict[str, Any]] = Field(default_factory=list)
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
    ownerOrganization: str | None = None
    owner: DocumentOwnerOut
    createdAt: datetime
    updatedAt: datetime
    lastOpenedAt: datetime | None = None
    status: str
    tags: list[str] = Field(default_factory=list)


class DocumentListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: list[dict[str, Any]]
    summary: str | None = None
    contentText: str
    categoryId: str | None = None
    ownerId: str
    ownerName: str
    ownerAvatarUrl: str | None = None
    ownerOrganization: str | None = None
    owner: DocumentOwnerOut | None = None
    createdAt: datetime
    updatedAt: datetime
    lastOpenedAt: datetime | None = None
    status: str
    tags: list[str] = Field(default_factory=list)


class DocumentListMeta(BaseModel):
    page: int
    pageSize: int
    total: int
    totalPages: int
    hasNext: bool
    hasPrev: bool


class DocumentSpellCheckIn(BaseModel):
    title: str | None = None
    content: list[dict[str, Any]] = Field(default_factory=list)


class DocumentSpellCheckIssueOut(BaseModel):
    type: str
    original: str
    suggestion: str
    start: int
    end: int


class DocumentSpellCheckSectionOut(BaseModel):
    originalText: str
    correctedText: str
    issues: list[DocumentSpellCheckIssueOut]


class DocumentSpellCheckSummaryOut(BaseModel):
    issueCount: int


class DocumentSpellCheckOut(BaseModel):
    title: DocumentSpellCheckSectionOut
    body: DocumentSpellCheckSectionOut
    summary: DocumentSpellCheckSummaryOut
