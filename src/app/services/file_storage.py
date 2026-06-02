from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status


class LocalFileStorage:
    def __init__(self, root: str, public_prefix: str):
        self.root = Path(root)
        self.public_prefix = public_prefix.rstrip("/")

    def ensure_root(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    async def save_avatar(self, *, user_id: str, file: UploadFile) -> str:
        content_type = file.content_type or ""
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미지 파일만 업로드할 수 있습니다.")

        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"}:
            suffix = ".png" if content_type == "image/png" else ".jpg"

        avatar_dir = self.root / "avatars" / user_id
        avatar_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid4().hex}{suffix}"
        save_path = avatar_dir / filename
        content = await file.read()
        save_path.write_bytes(content)

        return f"{self.public_prefix}/avatars/{user_id}/{filename}"
