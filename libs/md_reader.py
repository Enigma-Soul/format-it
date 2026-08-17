from __future__ import annotations

import json
import re
from pathlib import Path

from libs.config import FormatConfig
from libs.fonts import FontResolver
from libs.models import DocumentStructure, FontInfo, InlineRun, ParagraphNode, ParagraphRole

MD_LEVEL_TO_ROLE: dict[int, ParagraphRole] = {
    1: ParagraphRole.TITLE,
    2: ParagraphRole.HEADING_1,
    3: ParagraphRole.HEADING_2,
    4: ParagraphRole.HEADING_3,
    5: ParagraphRole.HEADING_4,
}

HEADING_ROLE_TO_LEVEL: dict[ParagraphRole, int] = {
    ParagraphRole.HEADING_1: 1,
    ParagraphRole.HEADING_2: 2,
    ParagraphRole.HEADING_3: 3,
    ParagraphRole.HEADING_4: 4,
}


class MarkdownReader:
    def __init__(self, config: FormatConfig) -> None:
        self._config = config

    def read(self, path: Path) -> DocumentStructure:
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")

        metadata, clean_lines = self._extract_metadata(lines)

        paragraphs: list[ParagraphNode] = []
        idx = 0
        for line in clean_lines:
            stripped = line.rstrip()
            if not stripped:
                continue

            # Image line
            if stripped.startswith("![") and "](" in stripped:
                img_path = self._extract_image_path(stripped)
                if img_path:
                    node = ParagraphNode(
                        index=idx,
                        role=ParagraphRole.BODY,
                        text="",
                        images=[img_path],
                    )
                    paragraphs.append(node)
                    idx += 1
                continue

            # Table line
            if stripped.startswith("|"):
                node = ParagraphNode(
                    index=idx,
                    role=ParagraphRole.TABLE,
                    text=stripped,
                )
                paragraphs.append(node)
                idx += 1
                continue

            # Heading line
            m = re.match(r"^(#{1,5})\s+(.*)", stripped)
            if m:
                level = len(m.group(1))
                text = m.group(2)
                role = MD_LEVEL_TO_ROLE.get(level, ParagraphRole.BODY)

                # Restore exact role from metadata (e.g. SUBTITLE vs TITLE)
                para_list = metadata.get("paragraphs", [])
                if idx < len(para_list):
                    meta_role = para_list[idx].get("role")
                    if meta_role:
                        try:
                            role = ParagraphRole[meta_role]
                        except KeyError:
                            pass

                heading_level = HEADING_ROLE_TO_LEVEL.get(role)

                # Try to restore font info from metadata
                runs = self._make_runs_from_meta(idx, metadata, text)

                node = ParagraphNode(
                    index=idx,
                    role=role,
                    text=text,
                    runs=runs,
                    heading_level=heading_level,
                )
                paragraphs.append(node)
                idx += 1
                continue

            # Body text
            runs = self._make_runs_from_meta(idx, metadata, stripped)
            node = ParagraphNode(
                index=idx,
                role=ParagraphRole.BODY,
                text=stripped,
                runs=runs,
            )
            paragraphs.append(node)
            idx += 1

        return DocumentStructure(
            paragraphs=paragraphs,
            source_file=path,
        )

    def _extract_metadata(self, lines: list[str]) -> tuple[dict, list[str]]:
        start = None
        end = None
        for i, line in enumerate(lines):
            if line.strip() == "<!-- format-it-meta":
                start = i
            if start is not None and line.strip() == "-->":
                end = i
                break
        if start is None or end is None:
            return {}, lines
        json_str = "\n".join(lines[start + 1 : end])
        try:
            metadata = json.loads(json_str)
        except json.JSONDecodeError:
            metadata = {}
        clean_lines = lines[:start] + lines[end + 1 :]
        return metadata, clean_lines

    def _make_runs_from_meta(
        self,
        idx: int,
        metadata: dict,
        text: str,
    ) -> list[InlineRun]:
        para_list = metadata.get("paragraphs", [])
        if idx < len(para_list):
            entry = para_list[idx]
            font_name = FontResolver.normalize(entry.get("font", self._config.body_font.name))
            size_pt = entry.get("size_pt", self._config.body_font.size_pt)
        else:
            font_name = self._config.body_font.name
            size_pt = self._config.body_font.size_pt
        return [InlineRun(text=text, font=FontInfo(name=font_name, size_pt=size_pt))]

    @staticmethod
    def _extract_image_path(line: str) -> Path | None:
        m = re.match(r"!\[.*?\]\((.+?)\)", line)
        if m:
            return Path(m.group(1))
        return None
