from __future__ import annotations

import asyncio
import dataclasses
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from libs.config import FormatConfig
from libs.converter import FormatConverter
from web.sessions import SessionManager

router = APIRouter(prefix="/api")

_CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"
_META_PATTERN = re.compile(r"<!-- format-it-meta\n.*?\n-->\n*", re.DOTALL)

session_manager: SessionManager | None = None


def _get_session_manager() -> SessionManager:
    if session_manager is None:
        raise RuntimeError("SessionManager not initialized")
    return session_manager


def _load_config(config_name: str, session_tmp_dir: Path) -> FormatConfig:
    config_path = _CONFIGS_DIR / config_name
    if not config_path.exists():
        config_path = _CONFIGS_DIR / "default.toml"
    config = FormatConfig.from_toml(config_path)
    return dataclasses.replace(
        config,
        input_dir=session_tmp_dir,
        output_dir=session_tmp_dir,
        tmp_dir=session_tmp_dir,
    )


def _strip_metadata(md_text: str) -> tuple[str, str]:
    match = _META_PATTERN.search(md_text)
    if match:
        metadata_block = match.group(0)
        clean = md_text[match.end() :]
        return clean, metadata_block
    return md_text, ""


@router.get("/configs")
async def list_configs():
    configs = []
    if _CONFIGS_DIR.exists():
        for f in sorted(_CONFIGS_DIR.glob("*.toml")):
            configs.append({"name": f.stem, "filename": f.name})
    if not configs:
        configs.append({"name": "默认配置", "filename": "default.toml"})
    return {"configs": configs}


@router.post("/upload")
async def upload_file(file: UploadFile, config: str = "default.toml"):
    if not file.filename or not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="仅支持 .docx 文件")

    sm = _get_session_manager()
    sm.cleanup_expired()
    session = sm.create(config_name=config)

    input_path = session.tmp_dir / file.filename
    session.input_file = input_path
    session.original_filename = file.filename

    content = await file.read()
    input_path.write_bytes(content)

    session.status = "processing"

    fmt_config = _load_config(config, session.tmp_dir)

    try:
        from libs.user_interaction import AutoUserInteraction

        ui = AutoUserInteraction(log=session.log)
        converter = FormatConverter(fmt_config, ui)

        loop = asyncio.get_event_loop()
        md_path = await loop.run_in_executor(None, converter.convert_word_to_markdown, input_path)

        session.md_file = md_path
        md_text = md_path.read_text(encoding="utf-8")
        clean_md, metadata_block = _strip_metadata(md_text)
        session.metadata_block = metadata_block
        session.status = "ready"
        session.log.append("转换完成，可编辑 Markdown")

        return {
            "session_id": session.id,
            "markdown": clean_md,
            "original_filename": file.filename,
            "log": session.log,
        }
    except Exception as e:
        session.status = "error"
        session.log.append(f"错误: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/generate")
async def generate_word(request: dict):
    session_id = request.get("session_id", "")
    edited_md = request.get("markdown", "")

    sm = _get_session_manager()
    session = sm.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    full_md = session.metadata_block + "\n" + edited_md
    md_path = session.tmp_dir / "edited.md"
    md_path.write_text(full_md, encoding="utf-8")

    fmt_config = _load_config(session.config_name, session.tmp_dir)

    try:
        from libs.user_interaction import SilentUserInteraction

        ui = SilentUserInteraction()
        converter = FormatConverter(fmt_config, ui)

        stem = Path(session.original_filename).stem
        output_path = session.tmp_dir / f"{stem}_formatted.docx"

        loop = asyncio.get_event_loop()
        result_path = await loop.run_in_executor(
            None, converter.convert_markdown_to_word, md_path, output_path
        )

        session.output_file = result_path

        return {
            "download_url": f"/api/download/{session.id}",
            "filename": result_path.name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/download/{session_id}")
async def download_file(session_id: str):
    sm = _get_session_manager()
    session = sm.get(session_id)
    if not session or not session.output_file or not session.output_file.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=session.output_file,
        filename=session.output_file.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
