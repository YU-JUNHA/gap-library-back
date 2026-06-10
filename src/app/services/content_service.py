from calendar import monthrange
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Category, Comment, Document, Template
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.content_repository import CategoryRepository, CollaborationRepository, StatsRepository, TemplateRepository
from app.services.document_service import extract_content_text
from app.services.document_storage import markdown_to_content_blocks


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
        blocks = markdown_to_content_blocks(markdown)
        doc.content = blocks
        doc.content_path = ""
        doc.content_text = extract_content_text(blocks)
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
        return self.reaction_summary(document_id, user)

    def remove_like(self, document_id: str, user: User):
        row = self.repo.get_reaction(document_id, user.id)
        if row:
            self.repo.remove_reaction(row)
        return self.reaction_summary(document_id, user)

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
        return self.repo.list_comments_with_author(document_id)

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
    _kst = ZoneInfo("Asia/Seoul")

    def __init__(self, db: Session):
        self.repo = StatsRepository(db)

    def dashboard(self, user: User, *, draft_limit: int = 5):
        total = self.repo.total_documents()
        mine = self.repo.my_documents(user.id)
        recent = self.repo.recent_docs()
        draft_documents = [
            {
                "id": document.id,
                "title": document.title,
                "updatedAt": document.updated_at,
                "categoryId": document.category_id,
                "categoryName": category_name,
                "ownerId": document.owner_id,
                "ownerName": document.owner_name,
                "summary": document.summary,
            }
            for document, category_name in self.repo.recent_draft_docs(user.id, limit=draft_limit)
        ]
        points = []
        for label, owner_id, count in self.repo.upload_trend_rows():
            points.append({"label": label, "userName": owner_id, "count": count})
        return {
            "totalDocuments": total,
            "myDocuments": mine,
            "recentEditedDocuments": [{"id": d.id, "title": d.title, "updatedAt": d.updated_at, "ownerName": d.owner_name} for d in recent],
            "draftDocuments": draft_documents,
            "uploadTrend": {"unit": "week", "points": points},
        }

    def _trend_period(self, unit: str) -> tuple[date, date]:
        today = datetime.now(self._kst).date()
        if unit == "week":
            start_date = today - timedelta(days=(today.weekday() + 1) % 7)
            end_date = start_date + timedelta(days=6)
            return start_date, end_date
        if unit == "month":
            start_date = today.replace(day=1)
            end_date = today.replace(day=monthrange(today.year, today.month)[1])
            return start_date, end_date
        if unit == "year":
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
            return start_date, end_date
        raise HTTPException(status_code=422, detail="지원하지 않는 unit 값입니다.")

    def _build_mypage_trend(self, user_id: str, unit: str):
        period_start, period_end = self._trend_period(unit)
        daily_rows = self.repo.my_upload_daily_rows(user_id, period_start, period_end)
        daily_counts = {period_start + timedelta(days=offset): 0 for offset in range((period_end - period_start).days + 1)}
        for day, count in daily_rows:
            daily_counts[day] = count

        if unit == "week":
            labels = ["일", "월", "화", "수", "목", "금", "토"]
            points = [
                {"label": labels[offset], "count": daily_counts[period_start + timedelta(days=offset)]}
                for offset in range(7)
            ]
        elif unit == "month":
            week_ranges = [
                ("1주차", 1, 7),
                ("2주차", 8, 14),
                ("3주차", 15, 21),
                ("4주차", 22, 28),
                ("5주차", 29, period_end.day),
            ]
            points = []
            for label, start_day, end_day in week_ranges:
                if start_day > period_end.day:
                    continue
                upper = min(end_day, period_end.day)
                count = sum(
                    daily_counts.get(date(period_start.year, period_start.month, day), 0)
                    for day in range(start_day, upper + 1)
                )
                points.append({"label": label, "count": count})
        elif unit == "year":
            points = []
            for month in range(1, 13):
                month_start = date(period_start.year, month, 1)
                month_end = date(period_start.year, month, monthrange(period_start.year, month)[1])
                count = sum(
                    daily_counts.get(month_start + timedelta(days=offset), 0)
                    for offset in range((month_end - month_start).days + 1)
                )
                points.append({"label": f"{month}월", "count": count})
        else:
            raise HTTPException(status_code=422, detail="지원하지 않는 unit 값입니다.")

        return {
            "unit": unit,
            "periodStart": period_start.isoformat(),
            "periodEnd": period_end.isoformat(),
            "points": points,
        }

    def mypage(self, user: User, unit: str = "month"):
        recent = self.repo.recent_my_docs(user.id)
        return {
            "uploadedFileCount": self.repo.my_documents(user.id),
            "recentUploads": [{"documentId": d.id, "title": d.title, "updatedAt": d.updated_at} for d in recent],
            "myUploadTrend": self._build_mypage_trend(user.id, unit),
        }
