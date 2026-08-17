from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


class ParagraphRole(Enum):
    TITLE = auto()
    SUBTITLE = auto()
    HEADING_1 = auto()
    HEADING_2 = auto()
    HEADING_3 = auto()
    HEADING_4 = auto()
    BODY = auto()
    RECIPIENT = auto()
    ATTACHMENT_NOTE = auto()
    SIGNATURE = auto()
    DATE = auto()
    HEADER = auto()
    FOOTER = auto()
    PAGE_NUMBER = auto()
    TABLE = auto()
    UNKNOWN = auto()


HEADING_ROLES = frozenset(
    {
        ParagraphRole.HEADING_1,
        ParagraphRole.HEADING_2,
        ParagraphRole.HEADING_3,
        ParagraphRole.HEADING_4,
    }
)


@dataclass
class FontInfo:
    name: str
    size_pt: float
    bold: bool = False
    italic: bool = False
    color_rgb: str | None = None


@dataclass
class InlineRun:
    text: str
    font: FontInfo


@dataclass
class DetectedHeading:
    paragraph_index: int
    text: str
    char_count: int
    detected_font_name: str | None = None
    sequence_match_level: int | None = None
    font_size_match_level: int | None = None
    line_length_match: bool = False
    final_level: int | None = None


@dataclass
class ParagraphNode:
    index: int
    role: ParagraphRole
    text: str
    runs: list[InlineRun] = field(default_factory=list)
    heading_level: int | None = None
    images: list[Path] = field(default_factory=list)


@dataclass
class DocumentStructure:
    paragraphs: list[ParagraphNode] = field(default_factory=list)
    images: list[Path] = field(default_factory=list)
    source_file: Path | None = None
    metadata: dict = field(default_factory=dict)
