from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.shared import Mm, Pt

from libs.config import FormatConfig
from libs.fonts import FontResolver
from libs.models import DocumentStructure, ParagraphNode, ParagraphRole


class WordWriter:
    def __init__(self, config: FormatConfig) -> None:
        self._config = config

    def write(self, doc: DocumentStructure, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        document = Document()

        self._setup_page_layout(document)

        for node in doc.paragraphs:
            if node.role == ParagraphRole.TABLE:
                self._write_table(document, node.text)
                continue
            if node.role == ParagraphRole.PAGE_NUMBER:
                continue
            self._write_paragraph(document, node)

        self._add_page_numbers(document)

        document.save(str(path))
        return path

    def _setup_page_layout(self, document: Document) -> None:
        section = document.sections[0]
        section.page_width = Mm(self._config.paper.width_mm)
        section.page_height = Mm(self._config.paper.height_mm)
        section.top_margin = Mm(self._config.paper.margin_top_mm)
        section.bottom_margin = Mm(self._config.paper.margin_bottom_mm)
        section.left_margin = Mm(self._config.paper.margin_left_mm)
        section.right_margin = Mm(self._config.paper.margin_right_mm)

    def _write_paragraph(self, document: Document, node: ParagraphNode) -> None:
        if node.images:
            for img_path in node.images:
                try:
                    if img_path.exists():
                        document.add_picture(str(img_path), width=Mm(156))
                except Exception:
                    pass
            return

        if not node.text.strip():
            return

        para = document.add_paragraph()

        # Set alignment
        if node.role == ParagraphRole.TITLE:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            font_spec = self._config.title_font
        elif node.role in (ParagraphRole.HEADING_1, ParagraphRole.HEADING_2,
                           ParagraphRole.HEADING_3, ParagraphRole.HEADING_4):
            para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            level = node.heading_level or 1
            font_spec = self._config.heading_fonts.get(level, self._config.body_font)
        else:
            para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            font_spec = self._config.body_font

        # Set paragraph format
        pf = para.paragraph_format
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = Pt(self._config.body_line_spacing_pt)

        if node.role == ParagraphRole.BODY:
            pf.first_line_indent = Pt(font_spec.size_pt * 2)
        else:
            pf.first_line_indent = Pt(0)

        # Write text with font handling
        self._write_runs(para, node.text, font_spec, node.role)

    def _write_runs(self, para, text: str, font_spec, role: ParagraphRole) -> None:
        resolved_font = FontResolver.resolve(font_spec.name)
        if not resolved_font:
            resolved_font = font_spec.alt_name or "SimSun"

        # Split text at digit boundaries for number font
        parts = self._split_text_for_numbers(text)

        for part_text, is_number in parts:
            run = para.add_run(part_text)
            run.font.size = Pt(font_spec.size_pt)
            if is_number:
                run.font.name = self._config.number_font
            else:
                run.font.name = resolved_font
            # Set East Asian font
            rPr = run._element.get_or_add_rPr()
            rFonts = rPr.find(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts"
            )
            if rFonts is None:
                from docx.oxml import OxmlElement
                rFonts = OxmlElement("w:rFonts")
                rPr.insert(0, rFonts)
            if is_number:
                rFonts.set(
                    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii",
                    self._config.number_font,
                )
                rFonts.set(
                    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hAnsi",
                    self._config.number_font,
                )
            else:
                rFonts.set(
                    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia",
                    resolved_font,
                )

    @staticmethod
    def _split_text_for_numbers(text: str) -> list[tuple[str, bool]]:
        parts: list[tuple[str, bool]] = []
        current = ""
        in_number = False
        for ch in text:
            is_digit = ch.isdigit() or ch in ".,-%‰°"
            if is_digit != in_number and current:
                parts.append((current, in_number))
                current = ""
                in_number = is_digit
            if not current:
                in_number = is_digit
            current += ch
        if current:
            parts.append((current, in_number))
        return parts

    def _write_table(self, document: Document, md_text: str) -> None:
        lines = [l for l in md_text.split("\n") if l.strip()]
        if not lines:
            return
        # Parse markdown table
        rows_data: list[list[str]] = []
        for line in lines:
            if line.strip().startswith("|") and "---" not in line:
                cells = [c.strip() for c in line.strip("|").split("|")]
                rows_data.append(cells)

        if not rows_data:
            return

        col_count = len(rows_data[0])
        table = document.add_table(rows=len(rows_data), cols=col_count)
        table.style = "Table Grid"

        for i, row_data in enumerate(rows_data):
            for j, cell_text in enumerate(row_data):
                if j < col_count:
                    table.rows[i].cells[j].text = cell_text

    def _add_page_numbers(self, document: Document) -> None:
        section = document.sections[0]
        footer = section.footer
        footer.is_linked_to_previous = False
        para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn

        run = para.add_run()
        fld_char_begin = OxmlElement("w:fldChar")
        fld_char_begin.set(qn("w:fldCharType"), "begin")
        run._element.append(fld_char_begin)

        run2 = para.add_run()
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = " PAGE "
        run2._element.append(instr)

        run3 = para.add_run()
        fld_char_end = OxmlElement("w:fldChar")
        fld_char_end.set(qn("w:fldCharType"), "end")
        run3._element.append(fld_char_end)

        for r in [run, run2, run3]:
            r.font.name = "Times New Roman"
            r.font.size = Pt(14)
