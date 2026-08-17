from __future__ import annotations

from abc import ABC, abstractmethod

from libs.models import DetectedHeading


class UserInteraction(ABC):
    @abstractmethod
    def choose_detection_methods(self) -> tuple[bool, bool, bool]:
        """Returns: (use_font_size, use_sequence_number, use_line_length)"""
        ...

    @abstractmethod
    def confirm_heading_level(
        self,
        heading: DetectedHeading,
        font_level: int | None,
        sequence_level: int | None,
    ) -> int:
        """Resolve a conflict. -1=title, -2=subtitle, 0=not heading, 1-4=heading level."""
        ...

    @abstractmethod
    def confirm_unknown_paragraph(
        self,
        text: str,
        char_count: int,
        font_info: str | None,
    ) -> int | None:
        """Return heading level (1-4) / -1=title / -2=subtitle, None=body."""
        ...

    @abstractmethod
    def confirm_subtitle(self, text: str, font_info: str | None) -> int | None:
        """Prompt user to classify the paragraph after the title. -2=subtitle, None=body."""
        ...

    @abstractmethod
    def select_input_files(self, available_files: list[str]) -> list[int]:
        """Return indices into available_files, empty if cancelled."""
        ...

    @abstractmethod
    def select_config(self, config_files: list[str]) -> int:
        """Return index into config_files, -1 if cancelled."""
        ...

    @abstractmethod
    def prompt_continue(self, message: str) -> bool: ...

    @abstractmethod
    def display_progress(self, message: str) -> None: ...


class AutoUserInteraction(UserInteraction):
    """Non-interactive implementation that applies smart defaults.
    Used for Web Phase 1 (Word -> MD) and headless CLI."""

    def __init__(self, log: list[str] | None = None) -> None:
        self._log = log if log is not None else []

    def choose_detection_methods(self) -> tuple[bool, bool, bool]:
        return True, True, True

    def confirm_heading_level(
        self,
        heading: DetectedHeading,
        font_level: int | None,
        sequence_level: int | None,
    ) -> int:
        if font_level is not None:
            return font_level
        if sequence_level is not None:
            return sequence_level
        return 0

    def confirm_unknown_paragraph(
        self,
        text: str,
        char_count: int,
        font_info: str | None,
    ) -> int | None:
        return None

    def confirm_subtitle(self, text: str, font_info: str | None) -> int | None:
        return -2

    def select_input_files(self, available_files: list[str]) -> list[int]:
        return list(range(len(available_files)))

    def select_config(self, config_files: list[str]) -> int:
        return 0

    def prompt_continue(self, message: str) -> bool:
        return True

    def display_progress(self, message: str) -> None:
        self._log.append(message)


class SilentUserInteraction(UserInteraction):
    """No-op implementation for Web Phase 2 (MD -> Word)."""

    def choose_detection_methods(self) -> tuple[bool, bool, bool]:
        return True, True, True

    def confirm_heading_level(
        self,
        heading: DetectedHeading,
        font_level: int | None,
        sequence_level: int | None,
    ) -> int:
        if font_level is not None:
            return font_level
        if sequence_level is not None:
            return sequence_level
        return 0

    def confirm_unknown_paragraph(
        self,
        text: str,
        char_count: int,
        font_info: str | None,
    ) -> int | None:
        return None

    def confirm_subtitle(self, text: str, font_info: str | None) -> int | None:
        return -2

    def select_input_files(self, available_files: list[str]) -> list[int]:
        return list(range(len(available_files)))

    def select_config(self, config_files: list[str]) -> int:
        return 0

    def prompt_continue(self, message: str) -> bool:
        return True

    def display_progress(self, message: str) -> None:
        pass


class PrintUserInteraction(UserInteraction):
    """Non-interactive implementation that prints progress to stdout.
    Used for the headless CLI."""

    def choose_detection_methods(self) -> tuple[bool, bool, bool]:
        return True, True, True

    def confirm_heading_level(
        self,
        heading: DetectedHeading,
        font_level: int | None,
        sequence_level: int | None,
    ) -> int:
        if font_level is not None:
            return font_level
        if sequence_level is not None:
            return sequence_level
        return 0

    def confirm_unknown_paragraph(
        self,
        text: str,
        char_count: int,
        font_info: str | None,
    ) -> int | None:
        return None

    def confirm_subtitle(self, text: str, font_info: str | None) -> int | None:
        return -2

    def select_input_files(self, available_files: list[str]) -> list[int]:
        return list(range(len(available_files)))

    def select_config(self, config_files: list[str]) -> int:
        return 0

    def prompt_continue(self, message: str) -> bool:
        return True

    def display_progress(self, message: str) -> None:
        print(f"  {message}")
