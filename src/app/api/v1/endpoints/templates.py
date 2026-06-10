from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps.auth import DbSession, get_current_user
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.content import TemplateApply, TemplateCreate, TemplateUpdate
from app.services.content_service import TemplateService

router = APIRouter()


@router.get("")
def list_templates(db: DbSession):
    rows = TemplateService(db).list()
    return {"data": [{"id": r.id, "name": r.name, "content": r.content, "createdBy": r.created_by, "createdAt": r.created_at, "updatedAt": r.updated_at} for r in rows]}


@router.post("")
def create_template(payload: TemplateCreate, db: DbSession, current_user: User = Depends(get_current_user)):
    r = TemplateService(db).create(payload.name, payload.content, current_user)
    return {"data": {"id": r.id, "name": r.name, "content": r.content, "createdBy": r.created_by, "createdAt": r.created_at, "updatedAt": r.updated_at}}


@router.get("/{template_id}")
def get_template(template_id: str, db: DbSession):
    r = TemplateService(db).get(template_id)
    return {"data": {"id": r.id, "name": r.name, "content": r.content, "createdBy": r.created_by, "createdAt": r.created_at, "updatedAt": r.updated_at}}


@router.patch("/{template_id}")
def update_template(template_id: str, payload: TemplateUpdate, db: DbSession, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")
    r = TemplateService(db).update(template_id, payload.name, payload.content)
    return {"data": {"id": r.id, "name": r.name, "content": r.content, "createdBy": r.created_by, "createdAt": r.created_at, "updatedAt": r.updated_at}}


@router.delete("/{template_id}")
def delete_template(template_id: str, db: DbSession, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")
    TemplateService(db).delete(template_id)
    return {"data": {"deleted": True, "templateId": template_id}}


@router.post("/{template_id}/apply")
def apply_template(template_id: str, payload: TemplateApply, db: DbSession):
    d = TemplateService(db).apply(template_id, payload.documentId)
    return {"data": {"documentId": d.id, "updatedAt": d.updated_at}}
