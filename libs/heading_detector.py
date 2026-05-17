from __future__ import annotations

import re
from collections import Counter
from typing import Optional

from libs.config import FormatConfig
from libs.fonts import FontResolver
from libs.models import (
    DetectedHeading,
    DocumentStructure,
    HEADING_ROLES,
    ParagraphNode,
    ParagraphRole,
)
from libs.user_interaction import UserInteraction

CN_NUMERALS = "一二三四五六七八九十"

SEQUENCE_PATTERNS = {
    1: re.compile(rf"^[{CN_NUMERALS}]+、"),
    2: re.compile(rf"^（[{CN_NUMERALS}]+）"),
    3: re.compile(r"^\d+[.．]"),
    4: re.compile(r"^（\d+）"),
}

EXTRACT_CN_NUM = re.compile(rf"[{CN_NUMERALS}]+")
EXTRACT_ARABIC_NUM = re.compile(r"\d+")

HEADING_ROLE_MAP = {
    1: ParagraphRole.HEADING_1,
    2: ParagraphRole.HEADING_2,
    3: ParagraphRole.HEADING_3,
    4: ParagraphRole.HEADING_4,
}

FONT_NAME_TO_LEVEL: dict[str, int] = {
    "黑体": 1,
    "楷体_GB2312": 2,
}


class HeadingDetector:
    def __init__(self, config: FormatConfig) -> None:
        self._config = config

    def detect_all(
        self,
        paragraphs: list[ParagraphNode],
        use_font_size: bool = True,
        use_sequence: bool = True,
        use_line_length: bool = True,
    ) -> list[DetectedHeading]:
        size_freq = self._analyze_font_size_frequency(paragraphs) if use_font_size else {}
        font_levels = self._classify_by_font_size(paragraphs, size_freq) if use_font_size else [None] * len(paragraphs)
        seq_levels = self._classify_by_sequence(paragraphs) if use_sequence else [None] * len(paragraphs)
        line_flags = self._classify_by_line_length(paragraphs) if use_line_length else [False] * len(paragraphs)

        results: list[DetectedHeading] = []
        for i, para in enumerate(paragraphs):
            results.append(DetectedHeading(
                paragraph_index=i,
                text=para.text,
                char_count=len(para.text),
                detected_font_name=self._get_dominant_font_name(para),
                sequence_match_level=seq_levels[i],
                font_size_match_level=font_levels[i],
                line_length_match=line_flags[i],
            ))
        return results

    def resolve_conflicts(
        self,
        headings: list[DetectedHeading],
        ui: UserInteraction,
    ) -> list[DetectedHeading]:
        for h in headings:
            font_lv = h.font_size_match_level
            seq_lv = h.sequence_match_level

            if font_lv is not None and seq_lv is not None:
                if font_lv == seq_lv:
                    h.final_level = font_lv
                else:
                    h.final_level = ui.confirm_heading_level(h, font_lv, seq_lv)
            elif font_lv is not None:
                h.final_level = font_lv
            elif seq_lv is not None:
                h.final_level = seq_lv
            elif h.line_length_match:
                result = ui.confirm_unknown_paragraph(
                    h.text, h.char_count, h.detected_font_name,
                )
                h.final_level = result
            else:
                h.final_level = None

        return headings

    def apply_to_document(
        self,
        doc: DocumentStructure,
        headings: list[DetectedHeading],
        ui: UserInteraction,
    ) -> DocumentStructure:
        for h in headings:
            para = doc.paragraphs[h.paragraph_index]
            if h.final_level is None or h.final_level == 0:
                para.role = ParagraphRole.BODY
                para.heading_level = None
            elif h.final_level == -1:
                para.role = ParagraphRole.TITLE
                para.heading_level = None
            elif h.final_level == -2:
                para.role = ParagraphRole.SUBTITLE
                para.heading_level = None
            else:
                para.role = HEADING_ROLE_MAP.get(h.final_level, ParagraphRole.BODY)
                para.heading_level = h.final_level

        # Detect title: largest font, first non-empty paragraph with title font
        self._detect_title(doc)
        self._confirm_subtitle_after_title(doc, ui)
        return doc

    def normalize_heading_sequences(
        self,
        paragraphs: list[ParagraphNode],
    ) -> None:
        counters: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}
        for para in paragraphs:
            if para.heading_level is None or para.heading_level == 0:
                continue
            if para.role in (ParagraphRole.TITLE, ParagraphRole.SUBTITLE):
                continue
            level = para.heading_level
            counters[level] += 1
            idx = counters[level]

            stripped, existing_num = self._strip_existing_sequence(para.text, level)
            new_seq = self._format_sequence(level, idx)
            para.text = new_seq + stripped

            if para.runs:
                para.runs[0].text = new_seq + stripped

    # --- Font size frequency ---

    def _analyze_font_size_frequency(
        self, paragraphs: list[ParagraphNode],
    ) -> dict[float, int]:
        counter: Counter[float] = Counter()
        for para in paragraphs:
            if not para.text.strip():
                continue
            size = self._get_dominant_font_size(para)
            if size and size > 0:
                counter[size] += 1
        return dict(counter)

    def _classify_by_font_size(
        self,
        paragraphs: list[ParagraphNode],
        size_freq: dict[float, int],
    ) -> list[Optional[int]]:
        if not size_freq:
            return [None] * len(paragraphs)

        body_size = max(size_freq, key=size_freq.get)
        title_size = self._config.title_font.size_pt
        tolerance = self._config.detection.font_size_tolerance_pt

        results: list[Optional[int]] = []
        for para in paragraphs:
            if not para.text.strip():
                results.append(None)
                continue

            size = self._get_dominant_font_size(para)
            font_name = self._get_dominant_font_name(para)

            if size is None or size <= 0:
                results.append(None)
                continue

            # Title detection by size
            if abs(size - title_size) <= tolerance and size > body_size + tolerance:
                results.append(None)  # Title is handled separately
                continue

            # Heading font name takes priority for same-size headings
            if font_name and abs(size - self._config.body_font.size_pt) <= tolerance:
                normalized = FontResolver.normalize(font_name)
                if normalized in FONT_NAME_TO_LEVEL:
                    results.append(FONT_NAME_TO_LEVEL[normalized])
                    continue
                # Check config heading fonts
                for lv, spec in self._config.heading_fonts.items():
                    if normalized == FontResolver.normalize(spec.name):
                        results.append(lv)
                        break
                else:
                    results.append(None)
                continue

            # Size larger than body suggests some heading level
            if size > body_size + tolerance:
                for lv in [1, 2, 3, 4]:
                    spec = self._config.heading_fonts.get(lv)
                    if spec and abs(size - spec.size_pt) <= tolerance:
                        results.append(lv)
                        break
                else:
                    results.append(None)
            else:
                results.append(None)

        return results

    # --- Sequence number matching ---

    def _classify_by_sequence(
        self, paragraphs: list[ParagraphNode],
    ) -> list[Optional[int]]:
        results: list[Optional[int]] = []
        for para in paragraphs:
            text = para.text.strip()
            if not text:
                results.append(None)
                continue
            matched = None
            for level in [1, 2, 3, 4]:
                if SEQUENCE_PATTERNS[level].match(text):
                    matched = level
                    break
            results.append(matched)
        return results

    # --- Line length ---

    def _classify_by_line_length(
        self, paragraphs: list[ParagraphNode],
    ) -> list[bool]:
        threshold = self._config.detection.line_length_threshold
        return [len(para.text.strip()) < threshold and bool(para.text.strip()) for para in paragraphs]

    # --- Title detection ---

    def _detect_title(self, doc: DocumentStructure) -> None:
        title_size = self._config.title_font.size_pt
        tolerance = self._config.detection.font_size_tolerance_pt
        # Priority 1: first non-empty paragraph with title font size
        for para in doc.paragraphs:
            if not para.text.strip():
                continue
            size = self._get_dominant_font_size(para)
            if size and abs(size - title_size) <= tolerance:
                para.role = ParagraphRole.TITLE
                para.heading_level = None
                return
        # Priority 2: first non-empty paragraph that doesn't start with a heading sequence
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            has_seq = any(SEQUENCE_PATTERNS[lv].match(text) for lv in [1, 2, 3, 4])
            if not has_seq:
                para.role = ParagraphRole.TITLE
                para.heading_level = None
                return

    def _confirm_subtitle_after_title(self, doc: DocumentStructure, ui: UserInteraction) -> None:
        title_idx = None
        for i, para in enumerate(doc.paragraphs):
            if para.role == ParagraphRole.TITLE:
                title_idx = i
                break
        if title_idx is None:
            return

        # Collect subtitle candidates: non-empty paragraphs immediately after title
        # Stop at the first real heading (H1-H4 with a sequence number) or BODY content
        candidates: list[ParagraphNode] = []
        for para in doc.paragraphs[title_idx + 1:]:
            if not para.text.strip():
                continue
            # A heading with a matched sequence number is a real heading, stop here
            if para.role in HEADING_ROLES and para.heading_level:
                break
            candidates.append(para)
            break  # Only ask about the first non-empty paragraph

        if not candidates:
            return

        candidate = candidates[0]
        font_info = self._get_dominant_font_name(candidate)
        result = ui.confirm_subtitle(
            candidate.text.strip(),
            font_info,
        )
        if result is None:
            return
        if result == -1:
            candidate.role = ParagraphRole.TITLE
        elif result == -2:
            candidate.role = ParagraphRole.SUBTITLE
        elif 1 <= result <= 4:
            candidate.role = HEADING_ROLE_MAP.get(result, ParagraphRole.BODY)
            candidate.heading_level = result

    # --- Sequence formatting helpers ---

    @staticmethod
    def _strip_existing_sequence(text: str, level: int) -> tuple[str, Optional[int]]:
        text = text.strip()
        pattern = SEQUENCE_PATTERNS.get(level)
        if not pattern:
            return text, None
        m = pattern.match(text)
        if not m:
            return text, None
        prefix = m.group()
        rest = text[m.end():]

        if level in (1, 2):
            nums = EXTRACT_CN_NUM.findall(prefix)
            if nums:
                return rest, _from_chinese_numeral(nums[0])
        else:
            nums = EXTRACT_ARABIC_NUM.findall(prefix)
            if nums:
                return rest, int(nums[0])
        return text, None

    @staticmethod
    def _format_sequence(level: int, index: int) -> str:
        if level == 1:
            return f"{_to_chinese_numeral(index)}、"
        elif level == 2:
            return f"（{_to_chinese_numeral(index)}）"
        elif level == 3:
            return f"{index}."
        elif level == 4:
            return f"（{index}）"
        return ""

    # --- Font helpers ---

    @staticmethod
    def _get_dominant_font_size(para: ParagraphNode) -> Optional[float]:
        if not para.runs:
            return None
        sizes: Counter[float] = Counter()
        for run in para.runs:
            if run.text.strip() and run.font.size_pt > 0:
                sizes[run.font.size_pt] += len(run.text)
        if not sizes:
            return None
        return max(sizes, key=sizes.get)

    @staticmethod
    def _get_dominant_font_name(para: ParagraphNode) -> Optional[str]:
        if not para.runs:
            return None
        names: Counter[str] = Counter()
        for run in para.runs:
            if run.text.strip() and run.font.name:
                names[run.font.name] += len(run.text)
        if not names:
            return None
        return max(names, key=names.get)


def _to_chinese_numeral(n: int) -> str:
    digits = "零一二三四五六七八九"
    if n <= 0:
        return ""
    if n < 10:
        return digits[n]
    if n < 20:
        if n == 10:
            return "十"
        return "十" + digits[n - 10]
    if n < 100:
        tens = n // 10
        ones = n % 10
        result = digits[tens] + "十"
        if ones:
            result += digits[ones]
        return result
    return str(n)


def _from_chinese_numeral(s: str) -> int:
    digit_map = {c: i for i, c in enumerate("零一二三四五六七八九")}
    if len(s) == 1:
        return digit_map.get(s, 0)
    if s == "十":
        return 10
    if s.startswith("十"):
        return 10 + digit_map.get(s[1], 0)
    if s.endswith("十"):
        return digit_map.get(s[0], 0) * 10
    if "十" in s:
        parts = s.split("十")
        tens = digit_map.get(parts[0], 0)
        ones = digit_map.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
        return tens * 10 + ones
    return 0
