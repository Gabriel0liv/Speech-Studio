from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Query

from api.utils import local_path_to_file_url, remove_safe_output_path
from src.core.history import clear_history, list_jobs


router = APIRouter(tags=["history"])


def _job_type_label(job_type: str | None) -> str:
    normalized = (job_type or "").lower()
    if normalized == "tts":
        return "TTS"
    if normalized in {"stt", "transcription"}:
        return "STT"
    return (job_type or "JOB").upper()


def _relative_time(created_at: str | None) -> str | None:
    if not created_at:
        return None
    try:
        created = datetime.fromisoformat(created_at)
        now = datetime.now(created.tzinfo or timezone.utc)
        delta = now - created
        minutes = max(int(delta.total_seconds() // 60), 0)
        if minutes < 1:
            return "agora"
        if minutes < 60:
            return f"há {minutes} min"
        hours = minutes // 60
        if hours < 24:
            return f"há {hours} h"
        days = hours // 24
        return f"há {days} dia(s)"
    except Exception:
        return created_at


@router.get("/history")
def get_history(limit: int = Query(default=50, ge=1, le=200)):
    jobs = list_jobs(limit=limit)
    for job in jobs:
        primary_output = job.get("primary_output_path")
        job["file_url"] = local_path_to_file_url(Path(primary_output)) if primary_output else None
        job["type"] = _job_type_label(job.get("job_type"))
        job["name"] = job.get("input_name") or job.get("text_snippet") or f"job_{job.get('id')}"
        job["time"] = _relative_time(job.get("created_at"))
    return {"success": True, "jobs": jobs}


@router.delete("/history")
def delete_history(delete_files: bool = Query(default=False)):
    deleted_paths = 0
    if delete_files:
        for job in list_jobs(limit=10000):
            primary_output = job.get("primary_output_path")
            output_dir = job.get("output_dir")
            if primary_output and remove_safe_output_path(Path(primary_output)):
                deleted_paths += 1
            elif output_dir and remove_safe_output_path(Path(output_dir)):
                deleted_paths += 1

    clear_history()
    return {
        "success": True,
        "delete_files": delete_files,
        "deleted_paths": deleted_paths,
        "message": "Historico limpo com sucesso.",
    }
