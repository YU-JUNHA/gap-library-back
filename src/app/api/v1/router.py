from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, categories, comments, documents, signup_requests, stats, templates, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(signup_requests.router, prefix="/signup-requests", tags=["signup-requests"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
