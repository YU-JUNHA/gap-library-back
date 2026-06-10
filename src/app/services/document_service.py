from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.base import str_id
from app.models.document import Document
from app.models.enums import DocumentStatus, UserRole
from app.models.user import User
from app.repositories.document_repository import DocumentRepository


def extract_content_text(content: list[dict]) -> str:
    texts: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            text = node.get("text")
            if isinstance(text, str):
                texts.append(text)
            for value in node.values():
                if isinstance(value, (dict, list)):
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(content)
    return " ".join(t.strip() for t in texts if t.strip())


class DocumentService:
    def __init__(self, db: Session):
        self.repo = DocumentRepository(db)

    def list_documents(
        self,
        *,
        q: str | None,
        category_id: str | None,
        uncategorized: bool,
        owner_id: str | None,
        status: str | None,
        sort: str,
        order: str,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[Document, User]], int]:
        return self.repo.list(
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

    def create_document(self, *, title: str, content: list[dict], category_id: str | None, status: str, owner: User) -> Document:
        try:
            doc_status = DocumentStatus(status)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="유효하지 않은 status 입니다.") from exc

        document_id = str_id()
        document = Document(
            id=document_id,
            title=title,
            content=content,
            content_text=extract_content_text(content),
            content_path="",
            category_id=category_id,
            owner_name=owner.name,
            owner_avatar_url=owner.avatar_url,
            status=doc_status,
            owner_id=owner.id,
        )
        return self.repo.create(document)

    def get_document(self, document_id: str) -> Document:
        doc = self.repo.get(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        return doc

    def get_document_with_owner(self, document_id: str) -> tuple[Document, User]:
        row = self.repo.get_with_owner(document_id)
        if not row:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        return row

    def get_document_content(self, document: Document) -> list[dict]:
        return document.content or []

    def update_document(self, document: Document, payload: dict) -> Document:
        if "title" in payload and payload["title"] is not None:
            document.title = payload["title"]
        if "summary" in payload:
            document.summary = payload["summary"]
        if "category_id" in payload:
            document.category_id = payload["category_id"]
        if "status" in payload and payload["status"] is not None:
            try:
                document.status = DocumentStatus(payload["status"])
            except ValueError as exc:
                raise HTTPException(status_code=422, detail="유효하지 않은 status 입니다.") from exc
        if "content" in payload and payload["content"] is not None:
            document.content = payload["content"]
            document.content_text = extract_content_text(payload["content"])

        return self.repo.update(document)

    def delete_document(self, document: Document) -> None:
        self.repo.delete(document)

    def purge_expired_drafts(self, *, retention_days: int = 30, batch_size: int = 100) -> dict[str, int]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        deleted_documents = 0

        while True:
            documents = self.repo.list_expired_drafts(cutoff=cutoff, limit=batch_size)
            if not documents:
                break

            self.repo.delete_many(documents)
            deleted_documents += len(documents)

        return {
            "deletedDocuments": deleted_documents,
            "deletedFiles": 0,
            "missingFiles": 0,
            "failedFileDeletes": 0,
        }

    def mark_opened(self, document: Document) -> Document:
        document.last_opened_at = datetime.now(timezone.utc)
        return self.repo.update(document)

    @staticmethod
    def ensure_document_readable(document: Document, user: User) -> None:
        if document.status == DocumentStatus.draft and document.owner_id != user.id and user.role != UserRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")

    @staticmethod
    def ensure_document_owner_or_admin(document: Document, user: User) -> None:
        if document.owner_id != user.id and user.role != UserRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")
