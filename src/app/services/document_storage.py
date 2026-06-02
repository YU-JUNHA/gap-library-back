from __future__ import annotations

from pathlib import Path
from typing import Any


def _extract_text(node: Any) -> str:
    texts: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            text = value.get("text")
            if isinstance(text, str):
                texts.append(text)
            for nested in value.values():
                if isinstance(nested, (dict, list)):
                    walk(nested)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(node)
    return "".join(texts).strip()


def content_blocks_to_markdown(content: list[dict[str, Any]]) -> str:
    if not content:
        return ""

    paragraphs: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        text = _extract_text(block)
        if not text:
            continue
        if block_type == "heading":
            level = block.get("attrs", {}).get("level", 1)
            try:
                level_num = max(1, min(int(level), 6))
            except (TypeError, ValueError):
                level_num = 1
            paragraphs.append(f"{'#' * level_num} {text}")
        else:
            paragraphs.append(text)

    return "\n\n".join(paragraphs)


def markdown_to_content_blocks(markdown: str) -> list[dict[str, Any]]:
    text = markdown.strip()
    if not text:
        return []

    blocks: list[dict[str, Any]] = []
    for chunk in [part.strip() for part in text.split("\n\n") if part.strip()]:
        lines = chunk.splitlines()
        first_line = lines[0].strip()
        if first_line.startswith("#"):
            heading_level = len(first_line) - len(first_line.lstrip("#"))
            heading_text = first_line[heading_level:].strip()
            if heading_text:
                blocks.append(
                    {
                        "type": "heading",
                        "attrs": {"level": max(1, min(heading_level, 6))},
                        "content": [{"type": "text", "text": heading_text}],
                    }
                )
                continue
        blocks.append(
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": chunk}],
            }
        )
    return blocks


class MarkdownDocumentStorage:
    def __init__(self, root: str):
        self.root = Path(root)

    def ensure_root(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def relative_path(self, document_id: str) -> str:
        return f"documents/{document_id}.md"

    def resolve(self, relative_path: str) -> Path:
        return self.root / relative_path

    def save(self, document_id: str, markdown: str) -> str:
        self.ensure_root()
        relative_path = self.relative_path(document_id)
        path = self.resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
        return relative_path

    def read(self, relative_path: str) -> str:
        path = self.resolve(relative_path)
        return path.read_text(encoding="utf-8")

    def exists(self, relative_path: str) -> bool:
        return self.resolve(relative_path).exists()

    def delete(self, relative_path: str) -> None:
        path = self.resolve(relative_path)
        if path.exists():
            path.unlink()
