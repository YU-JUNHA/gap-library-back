from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.user import User


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(
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
        stmt: Select = select(Document, User).join(User, Document.owner_id == User.id)
        count_stmt = select(func.count(Document.id))

        if q:
            like_q = f"%{q}%"
            search_filter = or_(
                Document.title.ilike(like_q),
                Document.summary.ilike(like_q),
                Document.content_text.ilike(like_q),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)
        elif uncategorized:
            stmt = stmt.where(Document.category_id.is_(None))
            count_stmt = count_stmt.where(Document.category_id.is_(None))
        elif category_id:
            stmt = stmt.where(Document.category_id == category_id)
            count_stmt = count_stmt.where(Document.category_id == category_id)
        if owner_id:
            stmt = stmt.where(Document.owner_id == owner_id)
            count_stmt = count_stmt.where(Document.owner_id == owner_id)
        if status:
            stmt = stmt.where(Document.status == status)
            count_stmt = count_stmt.where(Document.status == status)

        if sort == "updatedAt":
            sort_column = Document.updated_at
            stmt = stmt.order_by(sort_column.asc() if order == "asc" else sort_column.desc(), Document.id.desc())
        elif sort == "author":
            stmt = stmt.order_by(User.name.asc(), Document.created_at.desc(), Document.id.desc())
        else:
            sort_column = Document.created_at
            stmt = stmt.order_by(sort_column.asc() if order == "asc" else sort_column.desc(), Document.id.desc())

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = self.db.execute(stmt).all()
        total = self.db.execute(count_stmt).scalar_one()
        return rows, total

    def get(self, document_id: str) -> Document | None:
        return self.db.get(Document, document_id)

    def get_with_owner(self, document_id: str) -> tuple[Document, User] | None:
        stmt = select(Document, User).join(User, Document.owner_id == User.id).where(Document.id == document_id)
        row = self.db.execute(stmt).first()
        if row is None:
            return None
        return row[0], row[1]

    def list_expired_drafts(self, *, cutoff: datetime, limit: int) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.status == "draft", Document.updated_at < cutoff)
            .order_by(Document.updated_at.asc(), Document.id.asc())
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def delete_many(self, documents: list[Document]) -> None:
        for document in documents:
            self.db.delete(document)
        self.db.commit()

    def create(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete(self, document: Document) -> None:
        self.db.delete(document)
        self.db.commit()
