from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

from api.jobs import active_heavy_job
from api.routes_history import _job_type_label
from api.utils import local_path_to_file_url, output_storage_size_mb
from src.core.database import get_connection
from src.core.healthcheck import run_healthcheck_structured
from src.tts.registry import VOICE_MAPPING


router = APIRouter(tags=["dashboard"])


def _today_prefix() -> str:
    return datetime.now().date().isoformat()


def _fetch_recent_jobs(limit: int = 6) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = [dict(row) for row in cursor.fetchall()]

    for row in rows:
        primary_output = row.get("primary_output_path")
        row["file_url"] = local_path_to_file_url(Path(primary_output)) if primary_output else None
        row["type"] = _job_type_label(row.get("job_type"))
        row["name"] = row.get("input_name") or row.get("text_snippet") or f"job_{row.get('id')}"
    return rows


@router.get("/dashboard")
def get_dashboard():
    health = run_healthcheck_structured()
    with get_connection() as conn:
        cursor = conn.cursor()
        today = f"{_today_prefix()}%"

        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE created_at LIKE ? AND lower(job_type) = 'stt'", (today,))
        transcriptions_today = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE created_at LIKE ? AND lower(job_type) = 'tts'", (today,))
        tts_today = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'success'")
        jobs_success = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('failed', 'error')")
        jobs_failed = cursor.fetchone()[0] or 0

    unique_ptbr_voices = {
        alias
        for engine, voices in VOICE_MAPPING.items()
        for alias in voices
        if engine in {"kokoro", "piper"} and alias.startswith("pt_br_")
    }
    packages = {item["label"]: item for item in health["packages"]}
    success_rate = round((jobs_success / total_jobs) * 100, 2) if total_jobs else 0.0

    return {
        "success": True,
        "transcriptions_today": transcriptions_today,
        "tts_today": tts_today,
        "total_jobs": total_jobs,
        "jobs_success": jobs_success,
        "jobs_failed": jobs_failed,
        "success_rate": success_rate,
        "available_voices": len(unique_ptbr_voices),
        "storage_used_mb": output_storage_size_mb(),
        "recent_jobs": _fetch_recent_jobs(),
        "system_health": {
            "cuda": {"available": health["cuda"]["available"], "label": health["cuda"]["gpu_name"] if health["cuda"]["available"] else health["cuda"]["status"]},
            "ffmpeg": {"available": health["ffmpeg"]["available"], "label": "OK" if health["ffmpeg"]["available"] else "Ausente"},
            "espeak": {"available": health["espeak"]["available"], "label": "OK" if health["espeak"]["available"] else "Ausente"},
            "hf_token": {"available": health["huggingface"]["token_configured"], "label": "OK" if health["huggingface"]["token_configured"] else "Ausente"},
            "kokoro": {"available": packages.get("Kokoro", {}).get("installed", False), "label": "Pronto" if packages.get("Kokoro", {}).get("installed", False) else "Ausente"},
            "piper": {"available": packages.get("Piper (piper)", {}).get("installed", False), "label": "Pronto" if packages.get("Piper (piper)", {}).get("installed", False) else "Ausente"},
            "whisperx": {"available": packages.get("WhisperX", {}).get("installed", False), "label": "Pronto" if packages.get("WhisperX", {}).get("installed", False) else "Ausente"},
        },
        "active_job": active_heavy_job(),
    }
