from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.utils import (
    acquire_heavy_job,
    artifact_payload,
    collect_artifacts,
    heavy_job_busy_message,
    make_api_output_dir,
    python_command,
    release_heavy_job,
    run_subprocess,
    save_upload_file,
)


router = APIRouter(prefix="/stt", tags=["stt"])


@router.post("/transcribe")
def transcribe_file(
    file: UploadFile = File(...),
    model: str = Form("small"),
    language: Optional[str] = Form(None),
    device: str = Form("auto"),
    compute_type: str = Form("int8"),
    batch_size: int = Form(2),
    no_diarization: bool = Form(False),
    num_speakers: Optional[int] = Form(None),
    min_speakers: Optional[int] = Form(None),
    max_speakers: Optional[int] = Form(None),
    speaker_profile: Optional[str] = Form(None),
    formats: str = Form("txt json srt vtt"),
    vad_onset: float = Form(0.500),
    vad_offset: float = Form(0.363),
    chunk_size: int = Form(30),
):
    if not acquire_heavy_job():
        raise HTTPException(status_code=409, detail=heavy_job_busy_message())

    upload_path = save_upload_file(file)
    output_dir = make_api_output_dir("api_stt", parent="transcriptions")

    try:
        command = python_command(
            "transcribe.py",
            str(upload_path),
            "--output_dir",
            str(output_dir),
            "--model",
            model,
            "--device",
            device,
            "--compute_type",
            compute_type,
            "--batch_size",
            str(batch_size),
            "--formats",
            formats,
            "--vad-onset",
            str(vad_onset),
            "--vad-offset",
            str(vad_offset),
            "--chunk-size",
            str(chunk_size),
        )
        if language:
            command.extend(["--language", language])
        if no_diarization:
            command.append("--no-diarization")
        if num_speakers is not None:
            command.extend(["--num_speakers", str(num_speakers)])
        if min_speakers is not None:
            command.extend(["--min_speakers", str(min_speakers)])
        if max_speakers is not None:
            command.extend(["--max_speakers", str(max_speakers)])
        if speaker_profile:
            command.extend(["--speaker-profile", speaker_profile])

        result = run_subprocess(command, timeout_seconds=7200)
        if (not no_diarization) and (not result["success"]) and ("hf" in result["logs"].lower() or "pyannote" in result["logs"].lower()):
            result["error"] = "Falha na diarizacao. Verifique se o HF_TOKEN esta configurado ou execute com diarizacao desativada."

        artifacts = [artifact_payload(path) for path in collect_artifacts(output_dir, {".txt", ".json", ".srt", ".vtt"})]
        return {
            "success": result["success"],
            "output_dir": str(output_dir.resolve()),
            "artifacts": artifacts,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "returncode": result["returncode"],
            "logs": result["logs"],
            "error": result["error"],
        }
    finally:
        upload_path.unlink(missing_ok=True)
        release_heavy_job()
