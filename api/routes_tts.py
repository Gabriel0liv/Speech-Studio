from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.utils import (
    acquire_heavy_job,
    artifact_payload,
    collect_artifacts,
    create_temp_text_file,
    heavy_job_busy_message,
    local_path_to_file_url,
    make_api_output_dir,
    make_api_output_path,
    python_command,
    release_heavy_job,
    run_subprocess,
)
from src.tts.ptbr_text import analyze_ptbr_text


router = APIRouter(prefix="/tts", tags=["tts"])


class AnalyzeTextRequest(BaseModel):
    text: str
    language: str = "pt-br"


class TtsRequest(BaseModel):
    text: str
    engine: str = "kokoro"
    voice: str = "pt_br_dora"
    format: str = "wav"
    preview_chars: int = Field(default=300, ge=10, le=2000)
    speed: float = Field(default=1.0, gt=0, le=3)
    normalize_ptbr: bool = False
    analyze_ptbr: bool = False
    preset: Optional[str] = None


class CompareVoicesRequest(BaseModel):
    text: Optional[str] = None
    language: str = "pt-br"
    normalize_ptbr: bool = False


@router.post("/analyze-text")
def analyze_text(request: AnalyzeTextRequest):
    return {
        "success": True,
        "language": request.language,
        "analysis": analyze_ptbr_text(request.text),
    }


def _build_tts_command(request: TtsRequest, output_path: Path, preview: bool) -> tuple[List[str], Dict[str, Any]]:
    temp_input = create_temp_text_file(request.text)
    command = python_command(
        "synthesize.py",
        "--input",
        str(temp_input),
        "--engine",
        request.engine,
        "--voice",
        request.voice,
        "--format",
        request.format,
        "--output",
        str(output_path),
        "--speed",
        str(request.speed),
    )
    if preview:
        command.extend(["--preview", "--preview-chars", str(request.preview_chars)])
    if request.normalize_ptbr:
        command.append("--normalize-ptbr")
    if request.analyze_ptbr:
        command.append("--analyze-ptbr")
    if request.preset:
        command.extend(["--preset", request.preset])
    return command, {"temp_input": temp_input}


def _tts_response(result: Dict[str, Any], output_path: Path, analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "success": result["success"] and output_path.exists(),
        "audio_path": str(output_path.resolve()) if output_path.exists() else None,
        "audio_url": local_path_to_file_url(output_path) if output_path.exists() else None,
        "analysis": analysis,
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "returncode": result["returncode"],
        "logs": result["logs"],
        "error": result["error"],
    }


@router.post("/preview")
def generate_preview(request: TtsRequest):
    if not acquire_heavy_job():
        raise HTTPException(status_code=409, detail=heavy_job_busy_message())

    output_path = make_api_output_path("api_preview", request.format)
    analysis = analyze_ptbr_text(request.text) if request.analyze_ptbr else None
    context: Dict[str, Any] = {}
    try:
        command, context = _build_tts_command(request, output_path, preview=True)
        result = run_subprocess(command, timeout_seconds=600)
        return _tts_response(result, output_path, analysis=analysis)
    finally:
        temp_input = context.get("temp_input")
        if temp_input and Path(temp_input).exists():
            Path(temp_input).unlink(missing_ok=True)
        release_heavy_job()


@router.post("/generate")
def generate_full_tts(request: TtsRequest):
    if not acquire_heavy_job():
        raise HTTPException(status_code=409, detail=heavy_job_busy_message())

    output_path = make_api_output_path("api_tts", request.format)
    analysis = analyze_ptbr_text(request.text) if request.analyze_ptbr else None
    context: Dict[str, Any] = {}
    try:
        command, context = _build_tts_command(request, output_path, preview=False)
        result = run_subprocess(command, timeout_seconds=1200)
        return _tts_response(result, output_path, analysis=analysis)
    finally:
        temp_input = context.get("temp_input")
        if temp_input and Path(temp_input).exists():
            Path(temp_input).unlink(missing_ok=True)
        release_heavy_job()


@router.post("/compare-voices")
def compare_voices(request: CompareVoicesRequest):
    if not acquire_heavy_job():
        raise HTTPException(status_code=409, detail=heavy_job_busy_message())

    output_dir = make_api_output_dir("api_compare", parent="speech/voice_compare")
    temp_input: Optional[Path] = None
    try:
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

        result = run_subprocess(command, timeout_seconds=1800)
        artifacts = [artifact_payload(path) for path in collect_artifacts(output_dir, {".wav", ".mp3", ".json", ".md"})]
        report_json = output_dir / "compare_report.json"
        report_md = output_dir / "compare_report.md"
        return {
            "success": result["success"],
            "output_dir": str(output_dir.resolve()),
            "report_json_path": str(report_json.resolve()) if report_json.exists() else None,
            "report_md_path": str(report_md.resolve()) if report_md.exists() else None,
            "report_json_url": local_path_to_file_url(report_json) if report_json.exists() else None,
            "report_md_url": local_path_to_file_url(report_md) if report_md.exists() else None,
            "generated_files": artifacts,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "returncode": result["returncode"],
            "logs": result["logs"],
            "error": result["error"],
        }
    finally:
        if temp_input and temp_input.exists():
            temp_input.unlink(missing_ok=True)
        release_heavy_job()
