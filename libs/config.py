from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import tomli_w

from libs.models import HEADING_ROLES, ParagraphRole

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

_DEFAULTS_PATH = Path(__file__).resolve().parent.parent / "configs" / "default.toml"


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@dataclass(frozen=True)
class PaperConfig:
    size: str = ""
    width_mm: float = 0.0
    height_mm: float = 0.0
    margin_top_mm: float = 0.0
    margin_bottom_mm: float = 0.0
    margin_left_mm: float = 0.0
    margin_right_mm: float = 0.0
    footer_distance_mm: float = 0.0


@dataclass(frozen=True)
class FontSpec:
    name: str = ""
    size_pt: float = 0.0
    alt_name: str = ""
    sequence_pattern: str = ""
    bold: bool = False
    indent: bool = False


@dataclass(frozen=True)
class PageNumberConfig:
    enabled: bool = True
    format: str = "— 1 —"
    font_name: str = "SimSun"
    size_pt: float = 14.0
    odd_align: str = "right"
    even_align: str = "left"


@dataclass(frozen=True)
class DetectionConfig:
    line_length_threshold: int = 7
    use_font_size_detection: bool = True
    use_sequence_number_detection: bool = True
    use_line_length_detection: bool = True
    font_size_tolerance_pt: float = 1.0


@dataclass(frozen=True)
class FormatConfig:
    name: str = ""
    description: str = ""
    paper: PaperConfig = field(default_factory=PaperConfig)
    title_font: FontSpec = field(default_factory=FontSpec)
    subtitle_font: FontSpec = field(default_factory=FontSpec)
    body_font: FontSpec = field(default_factory=FontSpec)
    heading_fonts: dict[int, FontSpec] = field(default_factory=dict)
    number_font: str = ""
    body_chars_per_line: int = 0
    body_lines_per_page: int = 0
    body_line_spacing_pt: float = 0.0
    space_before_pt: float = 0.0
    space_after_pt: float = 0.0
    page_number: PageNumberConfig = field(default_factory=PageNumberConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    input_dir: Path = field(default_factory=lambda: Path("input"))
    output_dir: Path = field(default_factory=lambda: Path("output"))
    tmp_dir: Path = field(default_factory=lambda: Path("tmp"))

    @classmethod
    def defaults(cls) -> FormatConfig:
        return cls.from_toml(_DEFAULTS_PATH)

    def font_for_role(self, role: ParagraphRole, heading_level: int | None = None) -> FontSpec:
        if role == ParagraphRole.TITLE:
            return self.title_font
        if role == ParagraphRole.SUBTITLE:
            return self.subtitle_font
        if role in HEADING_ROLES:
            level = heading_level or 1
            return self.heading_fonts.get(level, self.body_font)
        return self.body_font

    @classmethod
    def from_toml(cls, path: Path) -> FormatConfig:
        data = cls._load_merged(path)

        paper_data = data.get("paper", {})
        paper = PaperConfig(
            size=paper_data.get("size", ""),
            width_mm=paper_data.get("width_mm", 0.0),
            height_mm=paper_data.get("height_mm", 0.0),
            margin_top_mm=paper_data.get("margin_top_mm", 0.0),
            margin_bottom_mm=paper_data.get("margin_bottom_mm", 0.0),
            margin_left_mm=paper_data.get("margin_left_mm", 0.0),
            margin_right_mm=paper_data.get("margin_right_mm", 0.0),
            footer_distance_mm=paper_data.get("footer_distance_mm", 0.0),
        )

        fonts_data = data.get("fonts", {})

        title_data = fonts_data.get("title", {})
        title_font = FontSpec(
            name=title_data.get("name", ""),
            size_pt=title_data.get("size_pt", 0.0),
            alt_name=title_data.get("alt_name", ""),
            bold=title_data.get("bold", False),
        )

        subtitle_data = fonts_data.get("subtitle", {})
        subtitle_font = FontSpec(
            name=subtitle_data.get("name", ""),
            size_pt=subtitle_data.get("size_pt", 0.0),
            alt_name=subtitle_data.get("alt_name", ""),
            bold=subtitle_data.get("bold", False),
        )

        body_data = fonts_data.get("body", {})
        body_font = FontSpec(
            name=body_data.get("name", ""),
            size_pt=body_data.get("size_pt", 0.0),
            alt_name=body_data.get("alt_name", ""),
        )

        heading_fonts: dict[int, FontSpec] = {}
        for level, key in [(1, "heading_1"), (2, "heading_2"), (3, "heading_3"), (4, "heading_4")]:
            h_data = fonts_data.get(key, {})
            heading_fonts[level] = FontSpec(
                name=h_data.get("name", ""),
                size_pt=h_data.get("size_pt", 0.0),
                alt_name=h_data.get("alt_name", ""),
                sequence_pattern=h_data.get("sequence_pattern", ""),
                bold=h_data.get("bold", False),
                indent=h_data.get("indent", False),
            )

        det_data = data.get("detection", {})
        detection = DetectionConfig(
            line_length_threshold=det_data.get("line_length_threshold", 7),
            use_font_size_detection=det_data.get("use_font_size_detection", True),
            use_sequence_number_detection=det_data.get("use_sequence_number_detection", True),
            use_line_length_detection=det_data.get("use_line_length_detection", True),
            font_size_tolerance_pt=det_data.get("font_size_tolerance_pt", 1.0),
        )

        pn_data = data.get("page_number", {})
        page_number = PageNumberConfig(
            enabled=pn_data.get("enabled", True),
            format=pn_data.get("format", "— 1 —"),
            font_name=pn_data.get("font_name", "SimSun"),
            size_pt=pn_data.get("size_pt", 14.0),
            odd_align=pn_data.get("odd_align", "right"),
            even_align=pn_data.get("even_align", "left"),
        )

        paths_data = data.get("paths", {})
        proj_data = data.get("project", {})
        return cls(
            name=proj_data.get("name", ""),
            description=proj_data.get("description", ""),
            paper=paper,
            title_font=title_font,
            subtitle_font=subtitle_font,
            body_font=body_font,
            heading_fonts=heading_fonts,
            number_font=fonts_data.get("number_font", ""),
            body_chars_per_line=body_data.get("chars_per_line", 0),
            body_lines_per_page=body_data.get("lines_per_page", 0),
            body_line_spacing_pt=body_data.get("line_spacing_pt", 0.0),
            space_before_pt=body_data.get("space_before_pt", 0.0),
            space_after_pt=body_data.get("space_after_pt", 0.0),
            page_number=page_number,
            detection=detection,
            input_dir=Path(paths_data.get("input_dir", "input")),
            output_dir=Path(paths_data.get("output_dir", "output")),
            tmp_dir=Path(paths_data.get("tmp_dir", "tmp")),
        )

    @staticmethod
    def _load_merged(path: Path) -> dict:
        base: dict = {}
        if _DEFAULTS_PATH.exists():
            with open(_DEFAULTS_PATH, "rb") as f:
                base = tomllib.load(f)

        if path.exists() and path.resolve() != _DEFAULTS_PATH.resolve():
            with open(path, "rb") as f:
                user_data = tomllib.load(f)
            return _deep_merge(base, user_data)

        if path.exists():
            with open(path, "rb") as f:
                return tomllib.load(f)

        return base

    def to_toml(self, path: Path) -> None:
        data: dict = {
            "project": {
                "name": self.name,
                "description": self.description,
            },
            "paper": {
                "size": self.paper.size,
                "width_mm": self.paper.width_mm,
                "height_mm": self.paper.height_mm,
                "margin_top_mm": self.paper.margin_top_mm,
                "margin_bottom_mm": self.paper.margin_bottom_mm,
                "margin_left_mm": self.paper.margin_left_mm,
                "margin_right_mm": self.paper.margin_right_mm,
                "footer_distance_mm": self.paper.footer_distance_mm,
            },
            "fonts": {
                "number_font": self.number_font,
                "title": {
                    "name": self.title_font.name,
                    "size_pt": self.title_font.size_pt,
                    "alt_name": self.title_font.alt_name,
                    "bold": self.title_font.bold,
                },
                "subtitle": {
                    "name": self.subtitle_font.name,
                    "size_pt": self.subtitle_font.size_pt,
                    "alt_name": self.subtitle_font.alt_name,
                    "bold": self.subtitle_font.bold,
                },
                "body": {
                    "name": self.body_font.name,
                    "size_pt": self.body_font.size_pt,
                    "alt_name": self.body_font.alt_name,
                    "chars_per_line": self.body_chars_per_line,
                    "lines_per_page": self.body_lines_per_page,
                    "line_spacing_pt": self.body_line_spacing_pt,
                    "space_before_pt": self.space_before_pt,
                    "space_after_pt": self.space_after_pt,
                },
                **{
                    f"heading_{lv}": {
                        "name": self.heading_fonts[lv].name,
                        "size_pt": self.heading_fonts[lv].size_pt,
                        "alt_name": self.heading_fonts[lv].alt_name,
                        "sequence_pattern": self.heading_fonts[lv].sequence_pattern,
                        "bold": self.heading_fonts[lv].bold,
                        "indent": self.heading_fonts[lv].indent,
                    }
                    for lv in range(1, 5)
                },
            },
            "page_number": {
                "enabled": self.page_number.enabled,
                "format": self.page_number.format,
                "font_name": self.page_number.font_name,
                "size_pt": self.page_number.size_pt,
                "odd_align": self.page_number.odd_align,
                "even_align": self.page_number.even_align,
            },
            "detection": {
                "line_length_threshold": self.detection.line_length_threshold,
                "use_font_size_detection": self.detection.use_font_size_detection,
                "use_sequence_number_detection": self.detection.use_sequence_number_detection,
                "use_line_length_detection": self.detection.use_line_length_detection,
                "font_size_tolerance_pt": self.detection.font_size_tolerance_pt,
            },
            "paths": {
                "input_dir": str(self.input_dir),
                "output_dir": str(self.output_dir),
                "tmp_dir": str(self.tmp_dir),
            },
        }
        with open(path, "wb") as f:
            tomli_w.dump(data, f)
