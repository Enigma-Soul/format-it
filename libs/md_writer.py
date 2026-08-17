from __future__ import annotations

import json
from pathlib import Path

from libs.config import FormatConfig
from libs.fonts import FontResolver
from libs.models import DocumentStructure, ParagraphRole

ROLE_TO_MD_LEVEL: dict[ParagraphRole, int] = {
    ParagraphRole.TITLE: 1,
    ParagraphRole.SUBTITLE: 1,
    ParagraphRole.HEADING_1: 2,
    ParagraphRole.HEADING_2: 3,
    ParagraphRole.HEADING_3: 4,
    ParagraphRole.HEADING_4: 5,
}


class MarkdownWriter:
    def __init__(self, config: FormatConfig) -> None:
        self._config = config

    def write(self, doc: DocumentStructure, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []

        # Metadata block
        lines.append(self._build_metadata_block(doc))
        lines.append("")

        for node in doc.paragraphs:
            if node.role == ParagraphRole.TABLE:
                lines.append(node.text)
                lines.append("")
                continue

            if node.role in ROLE_TO_MD_LEVEL:
                level = ROLE_TO_MD_LEVEL[node.role]
                prefix = "#" * level
                lines.append(f"{prefix} {node.text}")
            elif node.text.strip():
                lines.append(node.text)

            if node.images:
                for img_path in node.images:
                    lines.append(f"![image]({img_path})")

            lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def _build_metadata_block(self, doc: DocumentStructure) -> str:
        meta = {
            "source": str(doc.source_file) if doc.source_file else "",
            "paragraphs": [],
        }
        for node in doc.paragraphs:
            spec = self._config.font_for_role(node.role, node.heading_level)
            para_meta: dict = {
                "idx": node.index,
                "role": node.role.name,
                "font": FontResolver.normalize(spec.name),
                "size_pt": spec.size_pt,
            }
            if node.heading_level:
                para_meta["heading_level"] = node.heading_level
            meta["paragraphs"].append(para_meta)

        json_str = json.dumps(meta, ensure_ascii=False, indent=2)
        return f"<!-- format-it-meta\n{json_str}\n-->"
