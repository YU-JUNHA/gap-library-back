from urllib.parse import urljoin

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.deps.auth import DbSession, get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.content import CommentCreate, ReactionCreate, ReactionSummaryOut, to_comment_out
from app.schemas.document import (
    DocumentCreate,
    DocumentListItemOut,
    DocumentListMeta,
    DocumentOut,
    DocumentSpellCheckIn,
    DocumentSpellCheckOut,
    DocumentUpdate,
)
from app.services.content_service import CollaborationService
from app.services.document_spell_check_service import DocumentSpellCheckService
from app.services.document_service import DocumentService

router = APIRouter()


def _normalize_avatar_url(request: Request, avatar_url: str | None) -> str | None:
    if not avatar_url:
        return None
    if avatar_url.startswith(("http://", "https://", "//")):
        return avatar_url
    return urljoin(str(request.base_url), avatar_url)


def to_document_out(document: Document, owner: User, request: Request, *, content: list[dict] | None = None) -> DocumentOut:
    avatar_url = _normalize_avatar_url(request, owner.avatar_url)
    return DocumentOut(
        **{
            "id": document.id,
            "title": document.title,
            "content": content if content is not None else document.content,
            "contentText": document.content_text,
            "summary": document.summary,
            "categoryId": document.category_id,
            "ownerId": document.owner_id,
            "ownerName": owner.name,
            "ownerAvatarUrl": avatar_url,
            "ownerOrganization": owner.organization,
            "owner": {
                "id": owner.id,
                "name": owner.name,
                "avatarUrl": avatar_url,
                "organization": owner.organization,
            },
            "createdAt": document.created_at,
            "updatedAt": document.updated_at,
            "lastOpenedAt": document.last_opened_at,
            "status": document.status.value,
            "tags": [],
        }
    )


def to_document_list_item_out(document: Document, owner: User, request: Request) -> DocumentListItemOut:
    avatar_url = _normalize_avatar_url(request, owner.avatar_url)
    return DocumentListItemOut(
        id=document.id,
        title=document.title,
        content=document.content,
        summary=document.summary,
        contentText=document.content_text,
        categoryId=document.category_id,
        ownerId=document.owner_id,
        ownerName=owner.name,
        ownerAvatarUrl=avatar_url,
        ownerOrganization=owner.organization,
        owner={
            "id": owner.id,
            "name": owner.name,
            "avatarUrl": avatar_url,
            "organization": owner.organization,
        },
        createdAt=document.created_at,
        updatedAt=document.updated_at,
        lastOpenedAt=document.last_opened_at,
        status=document.status.value,
        tags=[],
    )


@router.get("")
def list_documents(
    request: Request,
    db: DbSession,
    q: str | None = None,
    category_id: str | None = Query(None, alias="categoryId"),
    uncategorized: bool = Query(False),
    owner_id: str | None = Query(None, alias="ownerId"),
    status: str | None = None,
    sort: str = Query("createdAt"),
    order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1),
):
    service = DocumentService(db)
    valid_sorts = {"createdAt", "updatedAt", "author"}
    valid_orders = {"asc", "desc"}
    if sort not in valid_sorts:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="지원하지 않는 sort 값입니다.")
    if order not in valid_orders:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="지원하지 않는 order 값입니다.")
    if uncategorized and category_id is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="uncategorized 와 categoryId 를 동시에 사용할 수 없습니다.")

    docs, total = service.list_documents(
        q=q,
        category_id=category_id,
        uncategorized=uncategorized,
        owner_id=owner_id,
        status=status,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    meta = DocumentListMeta(
        page=page,
        pageSize=page_size,
        total=total,
        totalPages=total_pages,
        hasNext=page < total_pages,
        hasPrev=page > 1 and total_pages > 0,
    )
    return {
        "data": [to_document_list_item_out(doc, owner, request).model_dump() for doc, owner in docs],
        "meta": meta.model_dump(),
    }


@router.post("")
def create_document(payload: DocumentCreate, request: Request, db: DbSession, current_user: User = Depends(get_current_user)):
    service = DocumentService(db)
    doc = service.create_document(
        title=payload.title,
        content=payload.content,
        category_id=payload.categoryId,
        status=payload.status,
        owner=current_user,
    )
    return {"data": to_document_out(doc, current_user, request, content=service.get_document_content(doc))}


@router.post("/spell-check")
def spell_check_document(
    payload: DocumentSpellCheckIn,
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    result = DocumentSpellCheckService().check_document(payload.title, payload.content)
    return {"data": DocumentSpellCheckOut(**result).model_dump()}


@router.get("/{document_id}")
def get_document(document_id: str, request: Request, db: DbSession):
    service = DocumentService(db)
    doc, owner = service.get_document_with_owner(document_id)
    return {"data": to_document_out(doc, owner, request, content=service.get_document_content(doc))}


@router.patch("/{document_id}")
def patch_document(
    document_id: str,
    payload: DocumentUpdate,
    request: Request,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    doc, owner = service.get_document_with_owner(document_id)
    service.ensure_document_owner_or_admin(doc, current_user)
    updated = service.update_document(
        doc,
        {
            "title": payload.title,
            "content": payload.content,
            "category_id": payload.categoryId,
            "summary": payload.summary,
            "status": payload.status,
        },
    )
    return {"data": to_document_out(updated, owner, request, content=service.get_document_content(updated))}


@router.delete("/{document_id}")
def delete_document(document_id: str, db: DbSession, current_user: User = Depends(get_current_user)):
    service = DocumentService(db)
    doc = service.get_document(document_id)
    service.ensure_document_owner_or_admin(doc, current_user)
    service.delete_document(doc)
    return {"data": {"deleted": True, "documentId": document_id}}


@router.post("/{document_id}/open")
def open_document(document_id: str, db: DbSession):
    service = DocumentService(db)
    doc = service.get_document(document_id)
    opened = service.mark_opened(doc)
    return {"data": {"documentId": opened.id, "lastOpenedAt": opened.last_opened_at}}


@router.post("/{document_id}/reactions")
def add_reaction(document_id: str, payload: ReactionCreate, db: DbSession, current_user: User = Depends(get_current_user)):
    if payload.type != "like":
        return {"error": {"code": "VALIDATION_ERROR", "message": "지원하지 않는 reaction type 입니다.", "details": {}}}
    summary = CollaborationService(db).add_like(document_id, current_user)
    return {"data": ReactionSummaryOut(**summary).model_dump()}


@router.delete("/{document_id}/reactions")
def remove_reaction(document_id: str, db: DbSession, current_user: User = Depends(get_current_user)):
    summary = CollaborationService(db).remove_like(document_id, current_user)
    return {"data": ReactionSummaryOut(**summary).model_dump()}


@router.get("/{document_id}/reactions")
def get_reactions(document_id: str, db: DbSession, current_user: User = Depends(get_current_user)):
    return {"data": ReactionSummaryOut(**CollaborationService(db).reaction_summary(document_id, current_user)).model_dump()}


@router.get("/{document_id}/comments")
def list_comments(document_id: str, db: DbSession):
    rows = CollaborationService(db).list_comments(document_id)
    return {"data": [to_comment_out(comment, author).model_dump() for comment, author in rows]}


@router.post("/{document_id}/comments")
def create_comment(document_id: str, payload: CommentCreate, db: DbSession, current_user: User = Depends(get_current_user)):
    r = CollaborationService(db).create_comment(document_id, payload.content, current_user)
    return {"data": to_comment_out(r, current_user).model_dump()}
