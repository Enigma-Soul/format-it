# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

format-it reformats Chinese government Word documents (.docx) to comply with the GB/T 9704 national standard. The pipeline: Word → Markdown (user reviews) → formatted Word. All UI strings and comments are in Chinese.

## Commands

```bash
# Install dependencies
uv sync

# Web UI (default: http://127.0.0.1:8000)
uv run python main.py
uv run python main.py --public          # listen 0.0.0.0
uv run python main.py --port 9000       # custom port

# CLI (headless, no interaction)
uv run python cli.py input.docx                     # full pipeline
uv run python cli.py --md-only input.docx           # only Word -> MD
uv run python cli.py --from-md edited.md            # only MD -> Word
uv run python cli.py -c custom.toml input.docx      # custom config
uv run python cli.py --init-config                  # generate default.toml

# Build (outputs to dist/format-it/)
uv run pyinstaller --noconfirm --onedir --name format-it main.py
```

No test suite exists currently.

## Architecture

### Pipeline Data Flow

All data flows through `DocumentStructure` (a flat list of `ParagraphNode` objects). Each pipeline stage reads and mutates this structure:

```
WordReader → DocumentStructure → HeadingDetector (detect + resolve) → sequence normalization → MarkdownWriter → .md file
.md file → MarkdownReader → DocumentStructure → WordWriter → .docx
```

The orchestrator is `FormatConverter` in `libs/converter.py`. It composes all modules but contains no business logic itself — it only sequences pipeline stages and delegates to the `UserInteraction` interface.

### Key Design: Metadata Round-Trip

Markdown files contain a JSON metadata block in `<!-- format-it-meta ... -->` that stores per-paragraph font name, size, role, and heading level. `MarkdownReader` parses this to restore font info lost in the Markdown intermediate. Without it, the Word→MD→Word round trip would lose all font information. The Web UI strips this block before showing Markdown and re-attaches it on save (see `_strip_metadata` in `web/routes.py`).

### Key Design: Abstract User Interaction

`UserInteraction` ABC in `libs/user_interaction.py` defines 8 abstract methods for all human interaction (confirm headings, select files, etc). Three concrete implementations exist in the same file:
- `AutoUserInteraction` — applies smart defaults, logs to a list; used by Web UI Phase 1 (Word→MD)
- `SilentUserInteraction` — complete no-op; used by Web UI Phase 2 (MD→Word)
- `PrintUserInteraction` — prints progress to stdout; used by headless CLI

All three use the same conflict resolution logic: prefer `font_level` over `sequence_level`, treat unknown paragraphs as body, auto-classify subtitles.

### Web UI Two-Phase Flow

FastAPI app in `web/` with a single-page frontend (`web/static/index.html`). The pipeline splits into two API calls:

1. `POST /api/upload` — uploads .docx, runs Word→MD with `AutoUserInteraction` in a thread executor, returns clean Markdown (metadata stripped)
2. `POST /api/generate` — takes edited Markdown + session_id, re-attaches metadata, runs MD→Word with `SilentUserInteraction`, returns download URL

Additional endpoints: `GET /api/configs` (list TOML configs), `GET /api/download/{session_id}` (serve generated .docx).

Sessions are managed by `SessionManager` in `web/sessions.py` with per-upload temp dirs under `tmp/web/{session_id}/` and 30-minute expiry. Each session overrides `FormatConfig` paths via `dataclasses.replace()`.

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

`FormatConfig` (frozen dataclass) in `libs/config.py` encodes all GB/T 9704 defaults. Configs live as TOML files in `configs/`. `from_toml()` deep-merges user config over `configs/default.toml` defaults via `_deep_merge()`. Override per-session with `dataclasses.replace(config, tmp_dir=..., output_dir=...)`.

### Number Font Splitting

`WordWriter._split_text_for_numbers()` separates digit characters (including `.,-%‰°`) from CJK text within a paragraph. Digits get Times New Roman, CJK text gets the resolved font. Done at the XML level via `w:rFonts` attributes.

### Page Numbering

`WordWriter` supports odd/even page footers with field codes. The format parser (`_parse_page_format`) supports Arabic (1), Chinese (一), Roman upper (I), and Roman lower (i) numeral styles. Even-page footers use raw XML since python-docx doesn't natively support them.

## Conventions

- Heading level values: `-1` = title, `-2` = subtitle, `0` = not heading, `1-4` = heading level.
- Markdown heading mapping: TITLE/SUBTITLE → `#`, H1 → `##`, H2 → `###`, H3 → `####`, H4 → `#####`.
- Dominant font per paragraph is determined by character-count weighting across runs, not first/last run.
- Tables are stored as Markdown pipe-table strings in `ParagraphNode.text` with role `TABLE`.
- Images extracted to `{stem}_images/` directories, re-embedded at 156mm width during writing.

## Commit Convention

commit 时不加 `Co-Authored-By` 行。

## CI/CD

`.github/workflows/build.yml`: On push to `main`, reads version from `pyproject.toml`, builds with PyInstaller `--onedir` on Windows, zips the output, publishes to GitHub Releases. Skips if tag already exists.
