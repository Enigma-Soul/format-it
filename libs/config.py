from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import tomli_w

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


@dataclass(frozen=True)
class PaperConfig:
    size: str = "A4"
    width_mm: float = 210.0
    height_mm: float = 297.0
    margin_top_mm: float = 37.0
    margin_bottom_mm: float = 35.0
    margin_left_mm: float = 28.0
    margin_right_mm: float = 26.0


@dataclass(frozen=True)
class FontSpec:
    name: str
    size_pt: float
    alt_name: str = ""
    sequence_pattern: str = ""


@dataclass(frozen=True)
class DetectionConfig:
    line_length_threshold: int = 7
    use_font_size_detection: bool = True
    use_sequence_number_detection: bool = True
    use_line_length_detection: bool = True
    preserve_images: bool = True
    font_size_tolerance_pt: float = 1.0


@dataclass(frozen=True)
class FormatConfig:
    paper: PaperConfig = field(default_factory=PaperConfig)
    title_font: FontSpec = field(default_factory=lambda: FontSpec("方正小标宋简体", 22.0, "SimSun"))
    body_font: FontSpec = field(default_factory=lambda: FontSpec("仿宋_GB2312", 16.0, "FangSong"))
    heading_fonts: dict[int, FontSpec] = field(default_factory=lambda: {
        1: FontSpec("黑体", 16.0, "SimHei", r"^[一二三四五六七八九十]+、"),
        2: FontSpec("楷体_GB2312", 16.0, "KaiTi", r"^（[一二三四五六七八九十]+）"),
        3: FontSpec("仿宋_GB2312", 16.0, "FangSong", r"^\d+[.．]"),
        4: FontSpec("仿宋_GB2312", 16.0, "FangSong", r"^（\d+）"),
    })
    number_font: str = "Times New Roman"
    body_chars_per_line: int = 28
    body_lines_per_page: int = 22
    body_line_spacing_pt: float = 28.9
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    input_dir: Path = field(default_factory=lambda: Path("input"))
    output_dir: Path = field(default_factory=lambda: Path("output"))
    tmp_dir: Path = field(default_factory=lambda: Path("tmp"))

    @classmethod
    def defaults(cls) -> FormatConfig:
        return cls()

    @classmethod
    def from_toml(cls, path: Path) -> FormatConfig:
        if not path.exists():
            return cls.defaults()
        with open(path, "rb") as f:
            data = tomllib.load(f)
        paper_data = data.get("paper", {})
        paper = PaperConfig(
            size=paper_data.get("size", "A4"),
            width_mm=paper_data.get("width_mm", 210.0),
            height_mm=paper_data.get("height_mm", 297.0),
            margin_top_mm=paper_data.get("margin_top_mm", 37.0),
            margin_bottom_mm=paper_data.get("margin_bottom_mm", 35.0),
            margin_left_mm=paper_data.get("margin_left_mm", 28.0),
            margin_right_mm=paper_data.get("margin_right_mm", 26.0),
        )
        fonts_data = data.get("fonts", {})
        title_data = fonts_data.get("title", {})
        title_font = FontSpec(
            name=title_data.get("name", "方正小标宋简体"),
            size_pt=title_data.get("size_pt", 22.0),
            alt_name=title_data.get("alt_name", "SimSun"),
        )
        body_data = fonts_data.get("body", {})
        body_font = FontSpec(
            name=body_data.get("name", "仿宋_GB2312"),
            size_pt=body_data.get("size_pt", 16.0),
            alt_name=body_data.get("alt_name", "FangSong"),
        )
        heading_fonts: dict[int, FontSpec] = {}
        for level, key in [(1, "heading_1"), (2, "heading_2"), (3, "heading_3"), (4, "heading_4")]:
            h_data = fonts_data.get(key, {})
            heading_fonts[level] = FontSpec(
                name=h_data.get("name", cls.defaults().heading_fonts[level].name),
                size_pt=h_data.get("size_pt", 16.0),
                alt_name=h_data.get("alt_name", cls.defaults().heading_fonts[level].alt_name),
                sequence_pattern=h_data.get("sequence_pattern", cls.defaults().heading_fonts[level].sequence_pattern),
            )
        det_data = data.get("detection", {})
        detection = DetectionConfig(
            line_length_threshold=det_data.get("line_length_threshold", 7),
            use_font_size_detection=det_data.get("use_font_size_detection", True),
            use_sequence_number_detection=det_data.get("use_sequence_number_detection", True),
            use_line_length_detection=det_data.get("use_line_length_detection", True),
            preserve_images=det_data.get("preserve_images", True),
            font_size_tolerance_pt=det_data.get("font_size_tolerance_pt", 1.0),
        )
        paths_data = data.get("paths", {})
        return cls(
            paper=paper,
            title_font=title_font,
            body_font=body_font,
            heading_fonts=heading_fonts,
            number_font=fonts_data.get("number_font", "Times New Roman"),
            body_chars_per_line=body_data.get("chars_per_line", 28),
            body_lines_per_page=body_data.get("lines_per_page", 22),
            body_line_spacing_pt=body_data.get("line_spacing_pt", 28.9),
            detection=detection,
            input_dir=Path(paths_data.get("input_dir", "input")),
            output_dir=Path(paths_data.get("output_dir", "output")),
            tmp_dir=Path(paths_data.get("tmp_dir", "tmp")),
        )

    def to_toml(self, path: Path) -> None:
        data: dict = {
            "paper": {
                "size": self.paper.size,
                "width_mm": self.paper.width_mm,
                "height_mm": self.paper.height_mm,
                "margin_top_mm": self.paper.margin_top_mm,
                "margin_bottom_mm": self.paper.margin_bottom_mm,
                "margin_left_mm": self.paper.margin_left_mm,
                "margin_right_mm": self.paper.margin_right_mm,
            },
            "fonts": {
                "number_font": self.number_font,
                "title": {
                    "name": self.title_font.name,
                    "size_pt": self.title_font.size_pt,
                    "alt_name": self.title_font.alt_name,
                },
                "body": {
                    "name": self.body_font.name,
                    "size_pt": self.body_font.size_pt,
                    "alt_name": self.body_font.alt_name,
                    "chars_per_line": self.body_chars_per_line,
                    "lines_per_page": self.body_lines_per_page,
                    "line_spacing_pt": self.body_line_spacing_pt,
                },
                "heading_1": {
                    "name": self.heading_fonts[1].name,
                    "size_pt": self.heading_fonts[1].size_pt,
                    "alt_name": self.heading_fonts[1].alt_name,
                    "sequence_pattern": self.heading_fonts[1].sequence_pattern,
                },
                "heading_2": {
                    "name": self.heading_fonts[2].name,
                    "size_pt": self.heading_fonts[2].size_pt,
                    "alt_name": self.heading_fonts[2].alt_name,
                    "sequence_pattern": self.heading_fonts[2].sequence_pattern,
                },
                "heading_3": {
                    "name": self.heading_fonts[3].name,
                    "size_pt": self.heading_fonts[3].size_pt,
                    "alt_name": self.heading_fonts[3].alt_name,
                    "sequence_pattern": self.heading_fonts[3].sequence_pattern,
                },
                "heading_4": {
                    "name": self.heading_fonts[4].name,
                    "size_pt": self.heading_fonts[4].size_pt,
                    "alt_name": self.heading_fonts[4].alt_name,
                    "sequence_pattern": self.heading_fonts[4].sequence_pattern,
                },
            },
            "detection": {
                "line_length_threshold": self.detection.line_length_threshold,
                "use_font_size_detection": self.detection.use_font_size_detection,
                "use_sequence_number_detection": self.detection.use_sequence_number_detection,
                "use_line_length_detection": self.detection.use_line_length_detection,
                "preserve_images": self.detection.preserve_images,
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
