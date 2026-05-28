from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.jobs import create_job, run_job_in_background
from api.routes_stt import _stt_progress_parser, _stt_response
from api.routes_tts import (
    CompareVoicesRequest,
    TtsRequest,
    _build_tts_command,
    _compare_response,
    _job_created_response,
    _tts_progress_parser,
    _tts_response,
)
from api.utils import (
    create_temp_text_file,
    heavy_job_busy_message,
    heavy_job_is_running,
    make_api_output_dir,
    make_api_output_path,
    python_command,
    save_upload_file,
)
from src.tts.ptbr_text import analyze_ptbr_text


router = APIRouter(prefix="/jobs", tags=["jobs-actions"])


def _ensure_async_capacity() -> None:
    if heavy_job_is_running():
        raise HTTPException(status_code=409, detail=heavy_job_busy_message())


@router.post("/tts/preview")
def create_tts_preview_job(request: TtsRequest):
    _ensure_async_capacity()
    output_path = make_api_output_path("api_preview", request.format)
    analysis = analyze_ptbr_text(request.text) if request.analyze_ptbr else None
    command, context = _build_tts_command(request, output_path, preview=True)
    job = create_job("tts_preview", {"output_path": str(output_path.resolve()), "analysis": analysis}, command)

    def cleanup() -> None:
        temp_input = context.get("temp_input")
        if temp_input and Path(temp_input).exists():
            Path(temp_input).unlink(missing_ok=True)

    run_job_in_background(
        job["job_id"],
        command,
        parser=_tts_progress_parser,
        finalize=lambda result: _tts_response(result, output_path, analysis=analysis),
        cleanup=cleanup,
        timeout_seconds=600,
    )
    return _job_created_response(job)


@router.post("/tts/generate")
def create_tts_generate_job(request: TtsRequest):
    _ensure_async_capacity()
    output_path = make_api_output_path("api_tts", request.format)
    analysis = analyze_ptbr_text(request.text) if request.analyze_ptbr else None
    command, context = _build_tts_command(request, output_path, preview=False)
    job = create_job("tts_generate", {"output_path": str(output_path.resolve()), "analysis": analysis}, command)

    def cleanup() -> None:
        temp_input = context.get("temp_input")
        if temp_input and Path(temp_input).exists():
            Path(temp_input).unlink(missing_ok=True)

    run_job_in_background(
        job["job_id"],
        command,
        parser=_tts_progress_parser,
        finalize=lambda result: _tts_response(result, output_path, analysis=analysis),
        cleanup=cleanup,
        timeout_seconds=1200,
    )
    return _job_created_response(job)


@router.post("/tts/compare-voices")
def create_compare_voices_job(request: CompareVoicesRequest):
    _ensure_async_capacity()
    output_dir = make_api_output_dir("api_compare", parent="speech/voice_compare")
    temp_input: Optional[Path] = None
    command = python_command(
        "synthesize.py",
        "--compare-voices",
        "--language",
        request.language,
        "--output-dir",
        str(output_dir),
    )
    if request.normalize_ptbr:
        command.append("--normalize-ptbr")
    if request.text:
        temp_input = create_temp_text_file(request.text)
        command.extend(["--input", str(temp_input)])

    job = create_job("tts_compare", {"output_dir": str(output_dir.resolve())}, command)

    def cleanup() -> None:
        if temp_input and temp_input.exists():
            temp_input.unlink(missing_ok=True)

    run_job_in_background(
        job["job_id"],
        command,
        parser=_tts_progress_parser,
        finalize=lambda result: _compare_response(result, output_dir),
        cleanup=cleanup,
        timeout_seconds=1800,
    )
    return _job_created_response(job)


@router.post("/stt/transcribe")
def create_stt_job(
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
    _ensure_async_capacity()
    upload_path = save_upload_file(file)
    output_dir = make_api_output_dir("api_stt", parent="transcriptions")

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

    job = create_job("stt_transcribe", {"output_dir": str(output_dir.resolve()), "filename": file.filename}, command)

    def cleanup() -> None:
        upload_path.unlink(missing_ok=True)

    run_job_in_background(
        job["job_id"],
        command,
        parser=_stt_progress_parser,
        finalize=lambda result: _stt_response(result, output_dir, no_diarization),
        cleanup=cleanup,
        timeout_seconds=7200,
    )
    return _job_created_response(job)
