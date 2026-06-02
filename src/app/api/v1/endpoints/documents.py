from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps.auth import DbSession, get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.content import CommentCreate, ReactionCreate
from app.schemas.document import DocumentCreate, DocumentListItemOut, DocumentListMeta, DocumentOut, DocumentUpdate
from app.services.content_service import CollaborationService
from app.services.document_service import DocumentService

router = APIRouter()


def to_document_out(document: Document, *, content: list[dict] | None = None) -> DocumentOut:
    return DocumentOut(
        **{
            "id": document.id,
            "title": document.title,
            "content": content if content is not None else document.content,
            "contentText": document.content_text,
            "summary": document.summary,
            "categoryId": document.category_id,
            "ownerId": document.owner_id,
            "ownerName": document.owner_name,
            "ownerAvatarUrl": document.owner_avatar_url,
            "owner": {
                "id": document.owner_id,
                "name": document.owner_name,
                "avatarUrl": document.owner_avatar_url,
            },
            "createdAt": document.created_at,
            "updatedAt": document.updated_at,
            "status": document.status.value,
        }
    )


def to_document_list_item_out(document: Document) -> DocumentListItemOut:
    return DocumentListItemOut(
        id=document.id,
        title=document.title,
        summary=document.summary,
        contentText=document.content_text,
        categoryId=document.category_id,
        ownerId=document.owner_id,
        ownerName=document.owner_name,
        ownerAvatarUrl=document.owner_avatar_url,
        createdAt=document.created_at,
        updatedAt=document.updated_at,
        status=document.status.value,
    )


@router.get("")
def list_documents(
    db: DbSession,
    q: str | None = None,
    category_id: str | None = Query(None, alias="categoryId"),
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

    docs, total = service.list_documents(
        q=q,
        category_id=category_id,
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
        "data": [to_document_list_item_out(doc).model_dump() for doc in docs],
        "meta": meta.model_dump(),
    }


@router.post("")
def create_document(payload: DocumentCreate, db: DbSession, current_user: User = Depends(get_current_user)):
    service = DocumentService(db)
    doc = service.create_document(
        title=payload.title,
        content=payload.content,
        category_id=payload.categoryId,
        status=payload.status,
        owner=current_user,
    )
    return {"data": to_document_out(doc, content=service.get_document_content(doc))}


@router.get("/{document_id}")
def get_document(document_id: str, db: DbSession):
    service = DocumentService(db)
    doc = service.get_document(document_id)
    return {"data": to_document_out(doc, content=service.get_document_content(doc))}


@router.patch("/{document_id}")
def patch_document(
    document_id: str,
    payload: DocumentUpdate,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    doc = service.get_document(document_id)
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
    return {"data": to_document_out(updated, content=service.get_document_content(updated))}


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
    CollaborationService(db).add_like(document_id, current_user)
    return {"data": {"ok": True}}


@router.delete("/{document_id}/reactions")
def remove_reaction(document_id: str, db: DbSession, current_user: User = Depends(get_current_user)):
    CollaborationService(db).remove_like(document_id, current_user)
    return {"data": {"ok": True}}


@router.get("/{document_id}/reactions")
def get_reactions(document_id: str, db: DbSession, current_user: User = Depends(get_current_user)):
    return {"data": CollaborationService(db).reaction_summary(document_id, current_user)}


@router.get("/{document_id}/comments")
def list_comments(document_id: str, db: DbSession):
    rows = CollaborationService(db).list_comments(document_id)
    return {"data": [{"id": r.id, "documentId": r.document_id, "authorId": r.author_id, "content": r.content, "createdAt": r.created_at, "updatedAt": r.updated_at} for r in rows]}


@router.post("/{document_id}/comments")
def create_comment(document_id: str, payload: CommentCreate, db: DbSession, current_user: User = Depends(get_current_user)):
    r = CollaborationService(db).create_comment(document_id, payload.content, current_user)
    return {"data": {"id": r.id, "documentId": r.document_id, "authorId": r.author_id, "content": r.content, "createdAt": r.created_at, "updatedAt": r.updated_at}}
