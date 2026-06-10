import asyncio
import logging
from contextlib import suppress

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.document_service import DocumentService


logger = logging.getLogger(__name__)


class DraftCleanupScheduler:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if not settings.draft_cleanup_enabled:
            logger.info("Draft cleanup scheduler is disabled.")
            return
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run_loop(), name="draft-cleanup-scheduler")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def _run_loop(self) -> None:
        interval_seconds = max(settings.draft_cleanup_interval_hours * 3600, 60)
        if settings.draft_cleanup_run_on_startup:
            await self._run_once()

        while True:
            await asyncio.sleep(interval_seconds)
            await self._run_once()

    async def _run_once(self) -> None:
        await asyncio.to_thread(self._run_sync_cleanup)

    def _run_sync_cleanup(self) -> None:
        db = SessionLocal()
        try:
            result = DocumentService(db).purge_expired_drafts(
                retention_days=settings.draft_cleanup_retention_days,
                batch_size=settings.draft_cleanup_batch_size,
            )
            logger.info("Expired draft cleanup finished: %s", result)
        except Exception:
            logger.exception("Expired draft cleanup failed.")
        finally:
            db.close()
