from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Optional

from rich.console import Console, Group
from rich.live import Live
from rich.text import Text


def _read_key() -> str:
    """跨平台单键读取，返回标准化名称。"""
    if sys.platform == "win32":
        import msvcrt
        ch = msvcrt.getwch()
        if ch == "\r":   return "enter"
        if ch == "\x1b": return "escape"
        if ch == "\t":   return "tab"
        if ch == " ":    return "space"
        if ch in ("\x00", "\xe0"):
            return {"H": "up", "P": "down", "K": "left", "M": "right"}.get(msvcrt.getwch(), "")
        return ""
    import termios, tty, select
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd); ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if ch in ("\r", "\n"): return "enter"
    if ch == "\t":         return "tab"
    if ch == " ":          return "space"
    if ch == "\x1b":
        if not select.select([sys.stdin], [], [], 0.05)[0]: return "escape"
        c2 = sys.stdin.read(1)
        if c2 == "Z": return "shift+tab"
        if c2 == "[":
            return {"A": "up", "B": "down", "C": "right", "D": "left"}.get(sys.stdin.read(1), "")
        return "escape"
    return ""


@dataclass
class SelectOption:
    label: str
    value: str
    description: str = ""


@dataclass
class Tab:
    title: str
    content: str


class MultiSelect:
    """↑/↓ 移动 · Space 切换 · Enter 确认 · a 全选 · 1-9 编号 · Esc 取消"""

    def __init__(self, options: list[dict | SelectOption], *, default: Optional[list[str]] = None,
                 title: str = "", visible_count: int = 7, single: bool = False) -> None:
        self._opts = [o if isinstance(o, SelectOption) else SelectOption(**o) for o in options]
        self._sel: set[str] = set(default or [])
        self._title = title
        self._vc = min(visible_count, len(self._opts))
        self._single = single
        self._focus = 0
        self._scroll = 0

    def run(self) -> list[str] | None:
        if not self._opts: return []
        console = Console()
        with Live(console=console, refresh_per_second=30, vertical_overflow="visible") as live:
            while True:
                live.update(self._render())
                n = len(self._opts)
                key = _read_key()
                if key in ("up", "k") and self._focus > 0:          self._focus -= 1
                elif key in ("down", "j") and self._focus < n - 1:  self._focus += 1
                elif key == "pageup":   self._focus = max(0, self._focus - self._vc)
                elif key == "pagedown": self._focus = min(n - 1, self._focus + self._vc)
                elif key == "space":
                    val = self._opts[self._focus].value
                    if self._single:
                        self._sel = {val}
                    else:
                        self._sel ^= {val}
                elif key == "enter":
                    if self._single and not self._sel:
                        self._sel = {self._opts[self._focus].value}
                    return sorted(self._sel)
                elif key == "a":
                    if not self._single:
                        self._sel = set() if len(self._sel) == n else {o.value for o in self._opts}
                elif key == "escape":   return None
                elif key.isdigit() and key != "0" and int(key) - 1 < n:
                    self._sel ^= {self._opts[int(key) - 1].value}
                else: continue
                # clamp scroll
                if self._focus < self._scroll:                     self._scroll = self._focus
                elif self._focus >= self._scroll + self._vc:       self._scroll = self._focus - self._vc + 1
        return None

    def _render(self) -> Group:
        n = len(self._opts)
        lines: list[Text] = []
        for i, opt in enumerate(self._opts[self._scroll:self._scroll + self._vc]):
            ri = self._scroll + i
            focused, selected = self._focus == ri, opt.value in self._sel
            arrow = "▲" if i == 0 and self._scroll > 0 else "▼" if i == self._vc - 1 and self._scroll + self._vc < n else " "
            t = Text(f"{arrow} ")
            t.append("❯ " if focused else "  ", "bold cyan" if focused else "")
            t.append(f"[{'x' if selected else ' '}] ", "bold green" if selected else "")
            t.append(opt.label, "bold cyan" if focused else "")
            if opt.description: t.append(f"  {opt.description}", "dim")
            lines.append(t)
        if self._title:
            if self._single:
                cur = next((o.label for o in self._opts if o.value in self._sel), "")
                tag = f"  [{cur}]" if cur else ""
                lines.insert(0, Text(f"{self._title}{tag}", "bold"))
            else:
                lines.insert(0, Text(f"{self._title}  ({len(self._sel)}/{n})", "bold"))
            lines.insert(1, Text())
        hint = "  ↑/↓ 移动  Enter 确认  Esc 取消" if self._single else "  ↑/↓ 移动  Space 切换  Enter 确认  a 全选  Esc 取消"
        lines += [Text(), Text(hint, "dim")]
        return Group(*lines)


class Tabs:
    """←/→ 切换 Tab · Enter/Esc 退出"""

    def __init__(self, tabs: list[Tab], *, title: str = "", color: str = "bright_blue", default: int = 0) -> None:
        self._tabs, self._title, self._color = tabs, title, color
        self._cur = max(0, min(default, len(tabs) - 1)) if tabs else 0

    def run(self) -> int:
        if not self._tabs: return -1
        console = Console()
        with Live(console=console, refresh_per_second=30, vertical_overflow="visible") as live:
            while True:
                live.update(self._render())
                key = _read_key()
                if key in ("right", "tab"):      self._cur = (self._cur + 1) % len(self._tabs)
                elif key in ("left", "shift+tab"): self._cur = (self._cur - 1) % len(self._tabs)
                elif key in ("enter", "escape", "q"): break
        return self._cur

    def _render(self) -> Group:
        from rich.markdown import Markdown
        hdr = []
        if self._title: hdr.append(Text(f"{self._title} ", f"bold {self._color}"))
        for i, t in enumerate(self._tabs):
            hdr.append(Text(f" {t.title} ", f"bold {self._color}" if i == self._cur else "dim"))
        return Group(
            Text.assemble(*hdr), Text(),
            Markdown(self._tabs[self._cur].content) if self._tabs[self._cur].content else Text(),
            Text(), Text("  ←/→ 切换 Tab  Enter 退出", "dim"),
        )


if __name__ == "__main__":
    c = Console()
    c.print("[bold]=== MultiSelect Demo ===[/bold]\n")
    r = MultiSelect(options=[
        {"label": "Bash",     "value": "bash",    "description": "Execute shell commands"},
        {"label": "FileEdit", "value": "edit",     "description": "Edit files in place"},
        {"label": "FileRead", "value": "read",     "description": "Read file contents"},
        {"label": "FileWrite","value": "write",    "description": "Create or overwrite files"},
        {"label": "WebFetch", "value": "web",      "description": "Fetch URLs"},
        {"label": "Glob",     "value": "glob",     "description": "Fast file pattern matching"},
        {"label": "Grep",     "value": "grep",     "description": "Search file contents"},
        {"label": "Notebook", "value": "notebook", "description": "Edit Jupyter notebooks"},
    ], default=["bash", "read"], title="Select tools").run()
    c.print(f"\n[bold]Result:[/bold] {r}")
    c.print("\n[bold]=== Tabs Demo ===[/bold]\n")
    i = Tabs(tabs=[
        Tab("Status",  "## Session\n\n- **Model:** claude-sonnet-4\n- **Cost:** $0.03"),
        Tab("Config",  "## Config\n\n- **theme:** dark\n- **vim:** off"),
        Tab("History", "## Activity\n\n1. Read `main.py`\n2. Ran `pytest`"),
    ], title="Session").run()
    c.print(f"\n[bold]Result:[/bold] tab {i}")
