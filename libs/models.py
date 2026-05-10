from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional


class ParagraphRole(Enum):
    TITLE = auto()
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


@dataclass
class FontInfo:
    name: str
    size_pt: float
    bold: bool = False
    italic: bool = False
    color_rgb: Optional[str] = None


@dataclass
class InlineRun:
    text: str
    font: FontInfo
    is_page_break: bool = False
    is_line_break: bool = False


@dataclass
class DetectedHeading:
    paragraph_index: int
    text: str
    char_count: int
    detected_font_size: Optional[float] = None
    detected_font_name: Optional[str] = None
    sequence_match_level: Optional[int] = None
    font_size_match_level: Optional[int] = None
    line_length_match: bool = False
    final_level: Optional[int] = None
    needs_user_confirmation: bool = False


@dataclass
class ParagraphNode:
    index: int
    role: ParagraphRole
    text: str
    runs: list[InlineRun] = field(default_factory=list)
    heading_level: Optional[int] = None
    images: list[Path] = field(default_factory=list)
    raw_xml_element: Optional[object] = None


@dataclass
class DocumentStructure:
    paragraphs: list[ParagraphNode] = field(default_factory=list)
    images: list[Path] = field(default_factory=list)
    source_file: Optional[Path] = None
    metadata: dict = field(default_factory=dict)
