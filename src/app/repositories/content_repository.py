from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document import Category, Comment, Document, DocumentReaction, Template
from app.models.enums import ReactionType


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Category]:
        return self.db.execute(select(Category).order_by(Category.parent_id.asc().nullsfirst(), Category.order.asc(), Category.created_at.asc())).scalars().all()

    def get(self, category_id: str) -> Category | None:
        return self.db.get(Category, category_id)

    def create(self, name: str, parent_id: str | None, order: int) -> Category:
        row = Category(name=name, parent_id=parent_id, order=order)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save(self, row: Category) -> Category:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: Category) -> None:
        self.db.delete(row)
        self.db.commit()


class TemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Template]:
        return self.db.execute(select(Template).order_by(Template.updated_at.desc())).scalars().all()

    def get(self, template_id: str) -> Template | None:
        return self.db.get(Template, template_id)

    def create(self, name: str, content: str, created_by: str) -> Template:
        row = Template(name=name, content=content, created_by=created_by)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save(self, row: Template) -> Template:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: Template) -> None:
        self.db.delete(row)
        self.db.commit()


class CollaborationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_document(self, document_id: str) -> Document | None:
        return self.db.get(Document, document_id)

    def get_reaction(self, document_id: str, user_id: str) -> DocumentReaction | None:
        stmt = select(DocumentReaction).where(DocumentReaction.document_id == document_id, DocumentReaction.user_id == user_id, DocumentReaction.type == ReactionType.like.value)
        return self.db.execute(stmt).scalar_one_or_none()

    def add_like(self, document_id: str, user_id: str) -> None:
        row = DocumentReaction(document_id=document_id, user_id=user_id, type=ReactionType.like.value, created_at=datetime.now(timezone.utc))
        self.db.add(row)
        self.db.commit()

    def remove_reaction(self, row: DocumentReaction) -> None:
        self.db.delete(row)
        self.db.commit()

    def like_count(self, document_id: str) -> int:
        stmt = select(func.count(DocumentReaction.id)).where(DocumentReaction.document_id == document_id, DocumentReaction.type == ReactionType.like.value)
        return self.db.execute(stmt).scalar_one()

    def list_comments(self, document_id: str) -> list[Comment]:
        stmt = select(Comment).where(Comment.document_id == document_id).order_by(Comment.created_at.asc())
        return self.db.execute(stmt).scalars().all()

    def get_comment(self, comment_id: str) -> Comment | None:
        return self.db.get(Comment, comment_id)

    def create_comment(self, document_id: str, author_id: str, content: str) -> Comment:
        row = Comment(document_id=document_id, author_id=author_id, content=content)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save_comment(self, row: Comment) -> Comment:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete_comment(self, row: Comment) -> None:
        self.db.delete(row)
        self.db.commit()


class StatsRepository:
    def __init__(self, db: Session):
        self.db = db

    def total_documents(self) -> int:
        return self.db.execute(select(func.count(Document.id))).scalar_one()

    def my_documents(self, user_id: str) -> int:
        return self.db.execute(select(func.count(Document.id)).where(Document.owner_id == user_id)).scalar_one()

    def recent_docs(self, limit: int = 5) -> list[Document]:
        return self.db.execute(select(Document).order_by(Document.updated_at.desc()).limit(limit)).scalars().all()

    def recent_my_docs(self, user_id: str, limit: int = 5) -> list[Document]:
        return self.db.execute(select(Document).where(Document.owner_id == user_id).order_by(Document.updated_at.desc()).limit(limit)).scalars().all()

    def upload_trend_rows(self):
        stmt = select(func.to_char(Document.created_at, 'IYYY-"W"IW').label('label'), Document.owner_id, func.count(Document.id).label('count')).group_by('label', Document.owner_id).order_by('label')
        return self.db.execute(stmt).all()

    def my_upload_trend_rows(self, user_id: str):
        stmt = select(func.to_char(Document.created_at, 'YYYY-MM').label('label'), func.count(Document.id).label('count')).where(Document.owner_id == user_id).group_by('label').order_by('label')
        return self.db.execute(stmt).all()
