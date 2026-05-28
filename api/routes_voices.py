from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.jobs import create_job, run_callable_job_in_background, run_job_in_background, update_progress
from api.routes_tts import _job_created_response, _tts_progress_parser, _tts_response
from api.utils import (
    collect_artifacts,
    heavy_job_busy_message,
    heavy_job_is_running,
    local_path_to_file_url,
    make_api_output_path,
    python_command,
    resolve_project_path,
    run_subprocess,
)


router = APIRouter(prefix="/voices", tags=["voices"])
VOICE_SAMPLE_TEXT = (
    "Olá! Esta é uma amostra da minha voz em português brasileiro. "
    "Use este preview para avaliar ritmo, naturalidade e pronúncia antes de gerar o áudio completo."
)
VOICE_SPECS = {
    "pt_br_dora": {"engine": "kokoro", "filename": "kokoro_dora.wav"},
    "pt_br_alex": {"engine": "kokoro", "filename": "kokoro_alex.wav"},
    "pt_br_santa": {"engine": "kokoro", "filename": "kokoro_santa.wav"},
    "pt_br_faber": {"engine": "piper", "filename": "piper_faber.wav"},
    "pt_br_edresson": {"engine": "piper", "filename": "piper_edresson.wav"},
}


def _sample_dir() -> Path:
    return resolve_project_path("outputs", "speech", "voice_samples")


def _sample_path(voice_alias: str) -> Path:
    spec = VOICE_SPECS[voice_alias]
    return _sample_dir() / spec["filename"]


def _sample_payload(voice_alias: str) -> dict:
    path = _sample_path(voice_alias)
    exists = path.exists()
    spec = VOICE_SPECS[voice_alias]
    return {
        "voice_alias": voice_alias,
        "engine": spec["engine"],
        "filename": spec["filename"],
        "exists": exists,
        "sample_path": str(path.resolve()) if exists else None,
        "sample_url": local_path_to_file_url(path) if exists else None,
    }


@router.get("/samples")
def get_voice_samples():
    _sample_dir().mkdir(parents=True, exist_ok=True)
    return {"success": True, "samples": [_sample_payload(alias) for alias in VOICE_SPECS]}


def _ensure_capacity() -> None:
    if heavy_job_is_running():
        raise HTTPException(status_code=409, detail=heavy_job_busy_message())


@router.post("/samples/generate/{voice_alias}")
def generate_voice_sample(voice_alias: str):
    if voice_alias not in VOICE_SPECS:
        raise HTTPException(status_code=404, detail="Voz nao suportada para amostra.")
    _ensure_capacity()

    output_path = _sample_path(voice_alias)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    spec = VOICE_SPECS[voice_alias]
    command = python_command(
        "synthesize.py",
        "--text",
        VOICE_SAMPLE_TEXT,
        "--engine",
        spec["engine"],
        "--voice",
        voice_alias,
        "--format",
        "wav",
        "--output",
        str(output_path),
        "--normalize-ptbr",
    )
    job = create_job("voice_sample", {"voice_alias": voice_alias, "output_path": str(output_path.resolve())}, command)
    run_job_in_background(
        job["job_id"],
        command,
        parser=_tts_progress_parser,
        finalize=lambda result: {
            **_tts_response(result, output_path),
            "voice_alias": voice_alias,
            "sample_url": local_path_to_file_url(output_path) if output_path.exists() else None,
        },
        timeout_seconds=900,
    )
    return _job_created_response(job)


@router.post("/samples/generate")
def generate_all_voice_samples():
    _ensure_capacity()
    job = create_job("voice_samples_generate_all", {"voices": list(VOICE_SPECS)})

    def runner(job_state: dict) -> dict:
        _sample_dir().mkdir(parents=True, exist_ok=True)
        results = []
        total = len(VOICE_SPECS)
        for index, (voice_alias, spec) in enumerate(VOICE_SPECS.items(), start=1):
            update_progress(
                job_state["job_id"],
                stage="voice_samples",
                progress=10 + int((index - 1) / total * 80),
                progress_mode="exact",
                message=f"Gerando amostra {index} de {total}: {voice_alias}",
            )
            output_path = _sample_path(voice_alias)
            command = python_command(
                "synthesize.py",
                "--text",
                VOICE_SAMPLE_TEXT,
                "--engine",
                spec["engine"],
                "--voice",
                voice_alias,
                "--format",
                "wav",
                "--output",
                str(output_path),
                "--normalize-ptbr",
            )
            result = run_subprocess(command, timeout_seconds=900)
            results.append(
                {
                    "voice_alias": voice_alias,
                    "success": result["success"] and output_path.exists(),
                    "sample_path": str(output_path.resolve()) if output_path.exists() else None,
                    "sample_url": local_path_to_file_url(output_path) if output_path.exists() else None,
                    "logs": result["logs"],
                    "error": result["error"],
                }
            )

        files = collect_artifacts(_sample_dir(), {".wav"})
        success = all(item["success"] for item in results)
        return {
            "success": success,
            "generated_files": [{"name": path.name, "local_path": str(path.resolve()), "file_url": local_path_to_file_url(path)} for path in files],
            "samples": results,
            "message": "Amostras de voz geradas." if success else "Algumas amostras falharam.",
            "error": None if success else "Uma ou mais amostras falharam.",
        }

    run_callable_job_in_background(job["job_id"], runner=runner)
    return _job_created_response(job)
