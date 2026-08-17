from __future__ import annotations

import shutil
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Session:
    id: str
    created_at: float
    tmp_dir: Path
    input_file: Path | None = None
    md_file: Path | None = None
    output_file: Path | None = None
    metadata_block: str = ""
    config_name: str = ""
    status: str = "idle"  # idle | processing | ready | error
    log: list[str] = field(default_factory=list)
    original_filename: str = ""


class SessionManager:
    def __init__(self, base_tmp_dir: Path, max_age_seconds: int = 1800) -> None:
        self._base = base_tmp_dir / "web"
        self._base.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, Session] = {}
        self._max_age = max_age_seconds

    def create(self, config_name: str = "") -> Session:
        sid = uuid.uuid4().hex[:12]
        tmp_dir = self._base / sid
        tmp_dir.mkdir(parents=True, exist_ok=True)
        session = Session(
            id=sid,
            created_at=time.time(),
            tmp_dir=tmp_dir,
            config_name=config_name,
        )
        self._sessions[sid] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session and session.tmp_dir.exists():
            shutil.rmtree(session.tmp_dir, ignore_errors=True)

    def cleanup_expired(self) -> None:
        now = time.time()
        expired = [sid for sid, s in self._sessions.items() if now - s.created_at > self._max_age]
        for sid in expired:
            self.remove(sid)
