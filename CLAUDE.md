# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

format-it reformats Chinese government Word documents (.docx) to comply with the GB/T 9704 national standard. The pipeline: Word → Markdown (user reviews) → formatted Word.

## Commands

```bash
# Install dependencies
uv sync

# Run Web UI (default: http://127.0.0.1:8000)
uv run python main.py

# Run Web UI on all interfaces
uv run python main.py --public

# CLI (headless, no interaction)
uv run python cli.py input.docx
uv run python cli.py --md-only input.docx
uv run python cli.py --from-md edited.md

# Generate default config
uv run python cli.py --init-config
```

## Architecture

### Pipeline Data Flow

All data flows through `DocumentStructure` (a flat list of `ParagraphNode` objects). Each pipeline stage reads and mutates this structure:

```
WordReader → DocumentStructure → HeadingDetector (detect + resolve) → sequence normalization → MarkdownWriter → .md file
.md file → MarkdownReader → DocumentStructure → WordWriter → .docx
```

The orchestrator is `FormatConverter` in `libs/converter.py`. It composes all modules but contains no business logic itself.

### Key Design: Metadata Round-Trip

Markdown files contain a JSON metadata block in `<!-- format-it-meta ... -->` that stores per-paragraph font name, size, role, and heading level. `MarkdownReader` parses this to restore font info lost in the Markdown intermediate. Without it, the Word→MD→Word round trip would lose all font information.

### Key Design: Abstract User Interaction

`UserInteraction` ABC in `libs/user_interaction.py` defines 7 abstract methods for all human interaction (confirm headings, select files, etc). Three concrete implementations exist in the same file:
- `AutoUserInteraction` — applies smart defaults, used by Web UI Phase 1 (Word→MD)
- `SilentUserInteraction` — no-op, used by Web UI Phase 2 (MD→Word)
- `PrintUserInteraction` — prints progress to stdout, used by the headless CLI

### Heading Detection Algorithm

`HeadingDetector` in `libs/heading_detector.py` runs three independent strategies:

1. **Font size frequency**: Most common size = body text. Larger sizes or specific font names ("黑体" = H1, "楷体_GB2312" = H2) classify headings.
2. **Sequence number regex**: Matches `一、` (H1), `（二）` (H2), `3.` (H3), `（4）` (H4).
3. **Line length**: Paragraphs under threshold chars (default 7) flagged as candidates.

Conflict resolution: agreement → use it; disagreement → user confirms; only line length → user confirms; none → body.

Title detection runs *after* heading classification: first paragraph matching title font size, else first paragraph without a heading sequence prefix.

### Font Resolution

`FontResolver` in `libs/fonts.py` maps between canonical Chinese font names and system aliases. `normalize()` maps any alias → canonical (e.g., "FangSong" → "仿宋_GB2312"). `resolve()` maps canonical → first system alias. All heading levels use 16pt; differentiation relies on font name, not size.

### Config System

`FormatConfig` (frozen dataclass) in `libs/config.py` encodes all GB/T 9704 defaults. Configs live as TOML files in `configs/`. The `from_toml()`/`to_toml()` methods handle serialization manually.

### Web UI

FastAPI + single-page HTML/CSS/JS frontend in `web/`. The pipeline is split into two phases: upload .docx → auto-detect headings → display Markdown for editing → generate formatted .docx. Session management in `web/sessions.py` with per-upload temp dirs.

## Conventions

- Return value convention for heading levels: `-1` = title, `-2` = subtitle, `0` = not heading, `1-4` = heading level.
- Dominant font per paragraph is determined by character-count weighting across runs, not first/last run.
- `WordWriter._split_text_for_numbers()` separates digits from CJK text to apply Times New Roman to numerals only.
- Tables are stored as Markdown pipe-table strings in `ParagraphNode.text` with role `TABLE`.

## CI/CD

`.github/workflows/build.yml`: On push to `main`, reads version from `pyproject.toml`, builds with PyInstaller on Windows, publishes to GitHub Releases. Skips if tag already exists.
