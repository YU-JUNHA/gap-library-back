from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.services.draft_cleanup_scheduler import DraftCleanupScheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = DraftCleanupScheduler()
    await scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
uploads_root = Path(settings.file_storage_root)
uploads_root.mkdir(parents=True, exist_ok=True)
app.mount(settings.file_public_prefix, StaticFiles(directory=uploads_root), name="uploads")
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
def health_check():
    return {"data": {"status": "ok"}}
