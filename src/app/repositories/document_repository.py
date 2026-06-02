from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(
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
    ) -> tuple[list[Document], int]:
        stmt: Select = select(Document)
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
            stmt = stmt.order_by(Document.owner_name.asc(), Document.created_at.desc(), Document.id.desc())
        else:
            sort_column = Document.created_at
            stmt = stmt.order_by(sort_column.asc() if order == "asc" else sort_column.desc(), Document.id.desc())

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = self.db.execute(stmt).scalars().all()
        total = self.db.execute(count_stmt).scalar_one()
        return rows, total

    def get(self, document_id: str) -> Document | None:
        return self.db.get(Document, document_id)

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
