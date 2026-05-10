from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from libs.models import DetectedHeading
from libs.tui import MultiSelect, SelectOption, _read_key

_console = Console()


class UserInteraction(ABC):
    @abstractmethod
    def choose_detection_methods(self) -> tuple[bool, bool, bool, bool]:
        """Returns: (use_font_size, use_sequence_number, use_line_length, preserve_images)"""
        ...

    @abstractmethod
    def confirm_heading_level(
        self,
        heading: DetectedHeading,
        font_level: Optional[int],
        sequence_level: Optional[int],
    ) -> int:
        """Resolve a conflict. Return heading level 1-4, 0=not heading."""
        ...

    @abstractmethod
    def confirm_unknown_paragraph(
        self,
        text: str,
        char_count: int,
        font_info: Optional[str],
    ) -> Optional[int]:
        """Return heading level (1-4) if it is a heading, None otherwise."""
        ...

    @abstractmethod
    def select_input_file(self, available_files: list[str]) -> int:
        """Return index into available_files."""
        ...

    @abstractmethod
    def prompt_continue(self, message: str) -> bool:
        ...

    @abstractmethod
    def display_progress(self, message: str) -> None:
        ...


class TUIUserInteraction(UserInteraction):
    def choose_detection_methods(self) -> tuple[bool, bool, bool, bool]:
        opts = [
            SelectOption("字体大小判断", "font", "按字体大小和字体名判断标题级别"),
            SelectOption("序号格式判断", "seq", "按 一、/（二）/3./（4） 判断"),
            SelectOption("行内字数判断", "len", "不足阈值的行标记为标题候选"),
            SelectOption("保留图片", "img", "提取并保留文档中的图片"),
        ]
        selected = MultiSelect(
            options=opts,
            default=["font", "seq", "len", "img"],
            title="检测方法配置",
        ).run()
        if selected is None:
            return True, True, True, True
        return (
            "font" in selected,
            "seq" in selected,
            "len" in selected,
            "img" in selected,
        )

    def confirm_heading_level(
        self,
        heading: DetectedHeading,
        font_level: Optional[int],
        sequence_level: Optional[int],
    ) -> int:
        _console.print(Panel(
            Text.assemble(
                ("标题级别冲突\n\n", "bold yellow"),
                ("  文本: ", "dim"), (f"{heading.text}\n", "bold"),
                ("  字体检测: ", "dim"), (f"{font_level} 级\n", "cyan" if font_level else "dim"),
                ("  序号检测: ", "dim"), (f"{sequence_level} 级\n", "green" if sequence_level else "dim"),
            ),
            border_style="yellow",
        ))
        opts = [
            SelectOption("一级标题", "1", "一、"),
            SelectOption("二级标题", "2", "（二）"),
            SelectOption("三级标题", "3", "3."),
            SelectOption("四级标题", "4", "（4）"),
            SelectOption("非标题", "0", "标记为正文"),
        ]
        # pre-select the font_level option if it exists
        default_sel = [str(font_level)] if font_level and 1 <= font_level <= 4 else []
        selected = MultiSelect(
            options=opts,
            default=default_sel,
            title="请选择标题级别",
            visible_count=5,
            single=True,
        ).run()
        if selected is None:
            return font_level or sequence_level or 0
        return int(selected[0]) if selected else 0

    def confirm_unknown_paragraph(
        self,
        text: str,
        char_count: int,
        font_info: Optional[str],
    ) -> Optional[int]:
        _console.print(Panel(
            Text.assemble(
                ("疑似标题\n\n", "bold magenta"),
                ("  文本: ", "dim"), (f"{text}\n", "bold"),
                ("  字数: ", "dim"), (f"{char_count}", "bold"),
                ("  字体: ", "dim"), (f"{font_info or '未知'}\n", "bold"),
            ),
            border_style="magenta",
        ))
        opts = [
            SelectOption("非标题（正文）", "body"),
            SelectOption("一级标题", "1"),
            SelectOption("二级标题", "2"),
            SelectOption("三级标题", "3"),
            SelectOption("四级标题", "4"),
        ]
        selected = MultiSelect(
            options=opts,
            default=["body"],
            title="请判断该段落类型",
            visible_count=5,
            single=True,
        ).run()
        if selected is None or "body" in selected:
            return None
        if selected:
            return int(selected[0])
        return None

    def select_input_file(self, available_files: list[str]) -> int:
        opts = [SelectOption(f, str(i)) for i, f in enumerate(available_files)]
        selected = MultiSelect(
            options=opts,
            title="选择输入文件",
            single=True,
        ).run()
        if selected:
            return int(selected[0])
        return 0

    def prompt_continue(self, message: str) -> bool:
        _console.print(Panel(message, border_style="blue"))
        _console.print("[dim]按 Enter 继续，Esc 取消[/dim]")
        key = _read_key()
        return key == "enter"

    def display_progress(self, message: str) -> None:
        _console.print(f"  [dim]›[/dim] {message}")
