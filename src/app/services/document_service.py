from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.base import str_id
from app.models.document import Document
from app.models.enums import DocumentStatus, UserRole
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.services.document_storage import (
    MarkdownDocumentStorage,
    content_blocks_to_markdown,
    markdown_to_content_blocks,
)


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
        self.storage = MarkdownDocumentStorage(settings.document_storage_root)
        self.storage.ensure_root()

    def list_documents(
        self,
        *,
        q: str | None,
        category_id: str | None,
        owner_id: str | None,
        status: str | None,
        sort: str,
        order: str,
        page: int,
        page_size: int,
    ):
        return self.repo.list(
            q=q,
            category_id=category_id,
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
        markdown = content_blocks_to_markdown(content)
        content_path = self.storage.save(document_id, markdown)

        document = Document(
            id=document_id,
            title=title,
            content=[],
            content_text=extract_content_text(content),
            content_path=content_path,
            category_id=category_id,
            owner_name=owner.name,
            owner_avatar_url=owner.avatar_url,
            status=doc_status,
            owner_id=owner.id,
        )
        try:
            return self.repo.create(document)
        except Exception:
            self.storage.delete(content_path)
            raise

    def get_document(self, document_id: str) -> Document:
        doc = self.repo.get(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        return doc

    def get_document_content(self, document: Document) -> list[dict]:
        if document.content_path and self.storage.exists(document.content_path):
            markdown = self.storage.read(document.content_path)
            return markdown_to_content_blocks(markdown)

        markdown = content_blocks_to_markdown(document.content or [])
        if not markdown.strip():
            markdown = document.content_text or ""

        content_path = self.storage.save(document.id, markdown)
        document.content_path = content_path
        self.repo.update(document)
        return markdown_to_content_blocks(markdown)

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
            markdown = content_blocks_to_markdown(payload["content"])
            content_path = document.content_path or self.storage.relative_path(document.id)
            self.storage.save(document.id, markdown)
            document.content_path = content_path
            document.content = []
            document.content_text = extract_content_text(payload["content"])

        return self.repo.update(document)

    def delete_document(self, document: Document) -> None:
        if document.content_path:
            self.storage.delete(document.content_path)
        self.repo.delete(document)

    def mark_opened(self, document: Document) -> Document:
        document.last_opened_at = datetime.now(timezone.utc)
        return self.repo.update(document)

    @staticmethod
    def ensure_document_owner_or_admin(document: Document, user: User) -> None:
        if document.owner_id != user.id and user.role != UserRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")
