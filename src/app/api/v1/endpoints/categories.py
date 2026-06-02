from fastapi import APIRouter

from app.api.deps.auth import DbSession
from app.schemas.content import CategoryCreate, CategoryMove, CategoryUpdate
from app.services.content_service import CategoryService

router = APIRouter()


@router.get("/tree")
def get_tree(db: DbSession):
    return {"data": CategoryService(db).tree()}


@router.post("")
def create_category(payload: CategoryCreate, db: DbSession):
    row = CategoryService(db).create(payload.name, payload.parentId)
    return {"data": {"id": row.id, "name": row.name, "parentId": row.parent_id, "order": row.order, "createdAt": row.created_at, "updatedAt": row.updated_at}}


@router.patch("/{category_id}")
def update_category(category_id: str, payload: CategoryUpdate, db: DbSession):
    row = CategoryService(db).update(category_id, payload.name)
    return {"data": {"id": row.id, "name": row.name, "parentId": row.parent_id, "order": row.order, "createdAt": row.created_at, "updatedAt": row.updated_at}}


@router.delete("/{category_id}")
def delete_category(category_id: str, db: DbSession):
    CategoryService(db).delete(category_id)
    return {"data": {"deleted": True, "categoryId": category_id}}


@router.post("/{category_id}/move")
def move_category(category_id: str, payload: CategoryMove, db: DbSession):
    row = CategoryService(db).move(category_id, payload.newParentId, payload.newOrder)
    return {"data": {"id": row.id, "name": row.name, "parentId": row.parent_id, "order": row.order, "createdAt": row.created_at, "updatedAt": row.updated_at}}
