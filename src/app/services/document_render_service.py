from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RenderBlock:
    type: str
    text: str
    level: int = 0


def extract_text_from_node(node: Any) -> str:
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


class DocumentRenderService:
    def blocks_from_content(self, content: list[dict[str, Any]]) -> list[RenderBlock]:
        blocks: list[RenderBlock] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type") or "paragraph"
            text = extract_text_from_node(block)
            if not text:
                continue
            if block_type == "heading":
                level = block.get("attrs", {}).get("level", 1)
                try:
                    heading_level = max(1, min(int(level), 6))
                except (TypeError, ValueError):
                    heading_level = 1
                blocks.append(RenderBlock(type="heading", text=text, level=heading_level))
                continue
            blocks.append(RenderBlock(type="paragraph", text=text))
        return blocks

    def text_from_content(self, content: list[dict[str, Any]]) -> str:
        return "\n\n".join(block.text for block in self.blocks_from_content(content))
