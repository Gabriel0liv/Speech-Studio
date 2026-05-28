from __future__ import annotations

import os
import sys
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Iterable, List
from urllib.parse import quote
from uuid import uuid4


HEAVY_JOB_LOCK = threading.Lock()
FORBIDDEN_SUFFIXES = {
    ".db", ".sqlite", ".sqlite3", ".db-shm", ".db-wal", ".env",
    ".onnx", ".pt", ".pth", ".bin", ".safetensors", ".ckpt",
}


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_project_path(*parts: str) -> Path:
    return get_project_root().joinpath(*parts)


SAFE_FILE_CATEGORIES: Dict[str, Path] = {
    "speech": resolve_project_path("outputs", "speech"),
    "transcripts": resolve_project_path("outputs", "transcriptions"),
    "voice_compare": resolve_project_path("outputs", "speech", "voice_compare"),
}


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_temp_text_file(text: str) -> Path:
    temp_dir = ensure_directory(resolve_project_path("temp"))
    with NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", prefix="api_text_", dir=temp_dir, delete=False) as handle:
        handle.write(text)
        return Path(handle.name)


def save_upload_file(upload) -> Path:
    upload_dir = ensure_directory(resolve_project_path("temp", "uploads"))
    suffix = Path(upload.filename or "").suffix
    target = upload_dir / f"api_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}{suffix}"
    with target.open("wb") as handle:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    upload.file.close()
    return target


def make_api_output_path(prefix: str, extension: str) -> Path:
    extension = extension if extension.startswith(".") else f".{extension}"
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}{extension}"
    return ensure_directory(resolve_project_path("outputs", "speech")) / filename


def make_api_output_dir(prefix: str, parent: str = "transcriptions") -> Path:
    base = resolve_project_path("outputs", parent)
    name = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
    return ensure_directory(base / name)


def acquire_heavy_job() -> bool:
    return HEAVY_JOB_LOCK.acquire(blocking=False)


def release_heavy_job() -> None:
    if HEAVY_JOB_LOCK.locked():
        HEAVY_JOB_LOCK.release()


def run_subprocess(command: List[str], timeout_seconds: int) -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            cwd=str(get_project_root()),
        )
        logs = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part).strip()
        return {
            "success": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "logs": logs,
            "error": None if completed.returncode == 0 else "Processo terminou com erro.",
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        logs = "\n".join(part for part in [stdout.strip(), stderr.strip()] if part).strip()
        return {
            "success": False,
            "returncode": -1,
            "stdout": stdout,
            "stderr": stderr,
            "logs": logs,
            "error": f"Processo excedeu o timeout de {timeout_seconds}s.",
        }
    except Exception as exc:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "",
            "logs": "",
            "error": str(exc),
        }


def is_safe_file(path: Path) -> bool:
    suffixes = {suffix.lower() for suffix in path.suffixes}
    if suffixes & FORBIDDEN_SUFFIXES:
        return False
    forbidden_parts = {"voices", "model_cache", "tts_cache", "uploads"}
    return not any(part.lower() in forbidden_parts for part in path.parts)


def resolve_safe_file(category: str, file_path: str) -> Path | None:
    base_dir = SAFE_FILE_CATEGORIES.get(category)
    if base_dir is None:
        return None

    base_dir = base_dir.resolve()
    candidate = (base_dir / file_path).resolve()
    try:
        candidate.relative_to(base_dir)
    except ValueError:
        return None

    if not candidate.is_file() or not is_safe_file(candidate):
        return None
    return candidate


def relative_file_path(category: str, path: Path) -> str | None:
    base_dir = SAFE_FILE_CATEGORIES.get(category)
    if base_dir is None:
        return None

    try:
        relative = path.resolve().relative_to(base_dir.resolve())
        return relative.as_posix()
    except ValueError:
        return None


def local_path_to_file_url(path: Path) -> str | None:
    resolved = path.resolve()
    for category, base_dir in sorted(SAFE_FILE_CATEGORIES.items(), key=lambda item: len(item[1].parts), reverse=True):
        try:
            relative = resolved.relative_to(base_dir.resolve()).as_posix()
            return f"http://127.0.0.1:8000/api/files/{category}/{quote(relative)}"
        except ValueError:
            continue
    return None


def artifact_payload(path: Path) -> Dict[str, Any]:
    return {
        "name": path.name,
        "local_path": str(path.resolve()),
        "file_url": local_path_to_file_url(path),
    }


def collect_artifacts(root: Path, suffixes: Iterable[str]) -> List[Path]:
    allowed = {suffix.lower() for suffix in suffixes}
    artifacts: List[Path] = []
    if not root.exists():
        return artifacts

    for candidate in sorted(root.rglob("*")):
        if candidate.is_file() and candidate.suffix.lower() in allowed and is_safe_file(candidate):
            artifacts.append(candidate.resolve())
    return artifacts


def heavy_job_busy_message() -> str:
    return "Ja existe um job de audio em execucao. Aguarde terminar antes de iniciar outro."


def python_command(*args: str) -> List[str]:
    return [sys.executable, *args]
