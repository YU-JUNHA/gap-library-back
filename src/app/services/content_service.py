from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Category, Comment, Document, Template
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.content_repository import CategoryRepository, CollaborationRepository, StatsRepository, TemplateRepository
from app.services.document_service import extract_content_text
from app.services.document_storage import MarkdownDocumentStorage, markdown_to_content_blocks


class CategoryService:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def tree(self):
        rows = self.repo.list_all()
        return [
            {"id": r.id, "name": r.name, "parentId": r.parent_id, "order": r.order, "createdAt": r.created_at, "updatedAt": r.updated_at}
            for r in rows
        ]

    def create(self, name: str, parent_id: str | None):
        return self.repo.create(name=name, parent_id=parent_id, order=0)

    def update(self, category_id: str, name: str):
        row = self.repo.get(category_id)
        if not row:
            raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")
        row.name = name
        return self.repo.save(row)

    def delete(self, category_id: str):
        row = self.repo.get(category_id)
        if not row:
            raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")
        self.repo.delete(row)

    def move(self, category_id: str, new_parent_id: str | None, new_order: int):
        row = self.repo.get(category_id)
        if not row:
            raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")
        row.parent_id = new_parent_id
        row.order = new_order
        return self.repo.save(row)


class TemplateService:
    def __init__(self, db: Session):
        self.repo = TemplateRepository(db)
        self.collab = CollaborationRepository(db)
        self.document_storage = MarkdownDocumentStorage(settings.document_storage_root)
        self.document_storage.ensure_root()

    def list(self):
        return self.repo.list()

    def get(self, template_id: str):
        row = self.repo.get(template_id)
        if not row:
            raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다.")
        return row

    def create(self, name: str, content: str, user: User):
        return self.repo.create(name=name, content=content, created_by=user.id)

    def update(self, template_id: str, name: str | None, content: str | None):
        row = self.get(template_id)
        if name is not None:
            row.name = name
        if content is not None:
            row.content = content
        return self.repo.save(row)

    def delete(self, template_id: str):
        row = self.get(template_id)
        self.repo.delete(row)

    def apply(self, template_id: str, document_id: str):
        template = self.get(template_id)
        doc = self.collab.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        markdown = template.content
        self.document_storage.save(doc.id, markdown)
        doc.content_path = self.document_storage.relative_path(doc.id)
        doc.content = []
        doc.content_text = extract_content_text(markdown_to_content_blocks(markdown))
        self.collab.db.add(doc)
        self.collab.db.commit()
        self.collab.db.refresh(doc)
        return doc


class CollaborationService:
    def __init__(self, db: Session):
        self.repo = CollaborationRepository(db)

    @staticmethod
    def ensure_editable(doc: Document, user: User):
        if doc.owner_id != user.id and user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")

    def add_like(self, document_id: str, user: User):
        doc = self.repo.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        if not self.repo.get_reaction(document_id, user.id):
            self.repo.add_like(document_id, user.id)

    def remove_like(self, document_id: str, user: User):
        row = self.repo.get_reaction(document_id, user.id)
        if row:
            self.repo.remove_reaction(row)

    def reaction_summary(self, document_id: str, user: User):
        doc = self.repo.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        liked = self.repo.get_reaction(document_id, user.id) is not None
        return {"likeCount": self.repo.like_count(document_id), "likedByMe": liked}

    def list_comments(self, document_id: str):
        doc = self.repo.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        return self.repo.list_comments(document_id)

    def create_comment(self, document_id: str, content: str, user: User):
        doc = self.repo.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        return self.repo.create_comment(document_id, user.id, content)

    def update_comment(self, comment_id: str, content: str, user: User):
        row = self.repo.get_comment(comment_id)
        if not row:
            raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
        if row.author_id != user.id and user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        row.content = content
        return self.repo.save_comment(row)

    def delete_comment(self, comment_id: str, user: User):
        row = self.repo.get_comment(comment_id)
        if not row:
            raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
        if row.author_id != user.id and user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        self.repo.delete_comment(row)


class StatsService:
    def __init__(self, db: Session):
        self.repo = StatsRepository(db)

    def dashboard(self, user: User):
        total = self.repo.total_documents()
        mine = self.repo.my_documents(user.id)
        recent = self.repo.recent_docs()
        points = []
        for label, owner_id, count in self.repo.upload_trend_rows():
            points.append({"label": label, "userName": owner_id, "count": count})
        return {
            "totalDocuments": total,
            "myDocuments": mine,
            "recentEditedDocuments": [{"id": d.id, "title": d.title, "updatedAt": d.updated_at, "ownerName": d.owner_id} for d in recent],
            "uploadTrend": {"unit": "week", "points": points},
        }

    def mypage(self, user: User):
        recent = self.repo.recent_my_docs(user.id)
        points = [{"label": label, "count": count} for label, count in self.repo.my_upload_trend_rows(user.id)]
        return {
            "uploadedFileCount": self.repo.my_documents(user.id),
            "recentUploads": [{"documentId": d.id, "title": d.title, "updatedAt": d.updated_at} for d in recent],
            "myUploadTrend": {"unit": "month", "points": points},
        }
