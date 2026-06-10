from __future__ import annotations

from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from fastapi import HTTPException

from app.services.document_render_service import DocumentRenderService


@lru_cache(maxsize=1)
def _get_kiwi():
    try:
        from kiwipiepy import Kiwi
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="맞춤법 검사 기능을 위한 kiwipiepy가 설치되지 않았습니다.") from exc
    return Kiwi()


class DocumentSpellCheckService:
    def __init__(self):
        self.renderer = DocumentRenderService()

    def check_document(self, title: str | None, content: list[dict[str, Any]]) -> dict[str, Any]:
        title_result = self._check_text(title or "")
        body_result = self._check_content(content)
        return {
            "title": title_result,
            "body": body_result,
            "summary": {
                "issueCount": len(title_result["issues"]) + len(body_result["issues"]),
            },
        }

    def _check_content(self, content: list[dict[str, Any]]) -> dict[str, Any]:
        paragraphs = self.renderer.blocks_from_content(content)
        issues: list[dict[str, Any]] = []
        corrected_blocks: list[str] = []
        offset = 0

        for index, block in enumerate(paragraphs):
            original = block.text
            corrected = self._correct_text(original)
            corrected_blocks.append(corrected)
            issues.extend(self._build_issues(original, corrected, offset))
            offset += len(original)
            if index < len(paragraphs) - 1:
                offset += 2

        original_text = "\n\n".join(block.text for block in paragraphs)
        corrected_text = "\n\n".join(corrected_blocks)
        return {
            "originalText": original_text,
            "correctedText": corrected_text,
            "issues": issues,
        }

    def _check_text(self, text: str) -> dict[str, Any]:
        corrected = self._correct_text(text) if text.strip() else text
        issues = self._build_issues(text, corrected, 0) if text.strip() else []
        return {
            "originalText": text,
            "correctedText": corrected,
            "issues": issues,
        }

    def _correct_text(self, text: str) -> str:
        kiwi = _get_kiwi()
        corrected = kiwi.space(text)
        return corrected.strip()

    def _build_issues(self, original: str, corrected: str, base_offset: int) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        matcher = SequenceMatcher(a=original, b=corrected)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            original_part = original[i1:i2]
            suggestion_part = corrected[j1:j2]
            issue_type = "spacing" if self._is_spacing_only(original_part, suggestion_part) else "correction"
            issues.append(
                {
                    "type": issue_type,
                    "original": original_part,
                    "suggestion": suggestion_part,
                    "start": base_offset + i1,
                    "end": base_offset + i2,
                }
            )
        return issues

    @staticmethod
    def _is_spacing_only(original: str, suggestion: str) -> bool:
        return "".join(original.split()) == "".join(suggestion.split())
