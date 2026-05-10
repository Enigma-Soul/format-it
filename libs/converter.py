from __future__ import annotations

from pathlib import Path

from libs.config import FormatConfig
from libs.heading_detector import HeadingDetector
from libs.md_reader import MarkdownReader
from libs.md_writer import MarkdownWriter
from libs.models import DocumentStructure, ParagraphRole
from libs.user_interaction import UserInteraction
from libs.word_reader import WordReader
from libs.word_writer import WordWriter


class FormatConverter:
    def __init__(self, config: FormatConfig, ui: UserInteraction) -> None:
        self._config = config
        self._ui = ui
        self._ensure_directories()

    def convert_word_to_markdown(self, input_path: Path) -> Path:
        self._ui.display_progress(f"正在读取: {input_path}")

        doc = self._read_word(input_path)
        doc = self._detect_and_resolve(doc)

        md_path = self._config.tmp_dir / f"{input_path.stem}.md"
        self._ui.display_progress(f"正在写入 Markdown: {md_path}")
        md_writer = MarkdownWriter(self._config)
        md_writer.write(doc, md_path)

        self._ui.display_progress("Markdown 生成完毕")
        return md_path

    def convert_markdown_to_word(self, md_path: Path, output_path: Path | None = None) -> Path:
        if output_path is None:
            output_path = self._config.output_dir / f"{md_path.stem}_formatted.docx"

        self._ui.display_progress(f"正在读取 Markdown: {md_path}")
        md_reader = MarkdownReader(self._config)
        doc = md_reader.read(md_path)

        self._ui.display_progress(f"正在写入 Word: {output_path}")
        word_writer = WordWriter(self._config)
        word_writer.write(doc, output_path)

        self._ui.display_progress("Word 生成完毕")
        return output_path

    def run_full_pipeline(self, input_path: Path) -> Path:
        md_path = self.convert_word_to_markdown(input_path)

        self._ui.prompt_continue(
            f"请检查 Markdown 文件: {md_path}\n"
            "编辑完成后按 Enter 继续..."
        )

        output_path = self._config.output_dir / f"{input_path.stem}_formatted.docx"
        return self.convert_markdown_to_word(md_path, output_path)

    def run_interactive(self) -> None:
        input_dir = self._config.input_dir
        if not input_dir.exists():
            self._ui.display_progress(f"输入目录不存在: {input_dir}")
            return

        files = list(input_dir.glob("*.docx"))
        if not files:
            self._ui.display_progress("输入目录中没有 .docx 文件")
            return

        file_names = [f.name for f in files]
        idx = self._ui.select_input_file(file_names)
        self.run_full_pipeline(files[idx])

    # --- Internal pipeline stages ---

    def _read_word(self, path: Path) -> DocumentStructure:
        tmp_dir = self._config.tmp_dir
        tmp_dir.mkdir(parents=True, exist_ok=True)
        reader = WordReader(self._config, tmp_dir)
        return reader.read(path)

    def _detect_and_resolve(self, doc: DocumentStructure) -> DocumentStructure:
        use_font, use_seq, use_len, _ = self._ui.choose_detection_methods()

        # Override config detection settings
        detector = HeadingDetector(self._config)

        self._ui.display_progress("正在检测标题...")
        headings = detector.detect_all(
            doc.paragraphs,
            use_font_size=use_font,
            use_sequence=use_seq,
            use_line_length=use_len,
        )

        self._ui.display_progress("正在解决冲突...")
        headings = detector.resolve_conflicts(headings, self._ui)

        doc = detector.apply_to_document(doc, headings)

        self._ui.display_progress("正在格式化序号...")
        detector.normalize_heading_sequences(doc.paragraphs)

        return doc

    def _ensure_directories(self) -> None:
        for d in [self._config.input_dir, self._config.output_dir, self._config.tmp_dir]:
            Path(d).mkdir(parents=True, exist_ok=True)
