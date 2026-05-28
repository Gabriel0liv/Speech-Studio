from __future__ import annotations

import subprocess
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable, Dict, List, Literal, Optional
from uuid import uuid4

from api.utils import acquire_heavy_job_blocking, get_project_root, release_heavy_job


JobStatus = Literal["queued", "running", "success", "error", "cancelled"]
ProgressMode = Literal["exact", "estimated", "indeterminate"]
ParserCallback = Callable[[str, str, Dict[str, Any]], Dict[str, Any] | None]
FinalizeCallback = Callable[[Dict[str, Any]], Dict[str, Any]]
RunnerCallback = Callable[[Dict[str, Any]], Dict[str, Any]]

MAX_TAIL_LINES = 80
RECENT_JOBS = deque(maxlen=100)
JOBS: Dict[str, Dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()


def _utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _trim_tail(lines: List[str]) -> List[str]:
    return lines[-MAX_TAIL_LINES:]


def _update_job(job_id: str, **updates: Any) -> Dict[str, Any]:
    with JOBS_LOCK:
        job = JOBS[job_id]
        job.update(updates)
        return dict(job)


def create_job(job_type: str, payload: Optional[Dict[str, Any]] = None, command: Optional[List[str]] = None) -> Dict[str, Any]:
    job_id = uuid4().hex
    job = {
        "job_id": job_id,
        "type": job_type,
        "status": "queued",
        "stage": "queued",
        "progress": 0,
        "progress_mode": "indeterminate",
        "message": "Job aguardando inicializacao.",
        "created_at": _utc_now(),
        "started_at": None,
        "finished_at": None,
        "command": command or [],
        "payload": payload or {},
        "stdout_tail": [],
        "stderr_tail": [],
        "logs_tail": [],
        "result": None,
        "error": None,
    }
    with JOBS_LOCK:
        JOBS[job_id] = job
        RECENT_JOBS.appendleft(job_id)
    return dict(job)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        return dict(job) if job else None


def get_job_logs(job_id: str) -> Optional[Dict[str, Any]]:
    job = get_job(job_id)
    if not job:
        return None
    return {
        "job_id": job_id,
        "stdout_tail": job["stdout_tail"],
        "stderr_tail": job["stderr_tail"],
        "logs_tail": job["logs_tail"],
    }


def list_active_jobs() -> List[Dict[str, Any]]:
    with JOBS_LOCK:
        return [
            dict(job)
            for job in JOBS.values()
            if job["status"] in {"queued", "running"}
        ]


def list_recent_jobs(limit: int = 20) -> List[Dict[str, Any]]:
    with JOBS_LOCK:
        items: List[Dict[str, Any]] = []
        for job_id in list(RECENT_JOBS)[:limit]:
            job = JOBS.get(job_id)
            if job:
                items.append(dict(job))
        return items


def active_heavy_job() -> Optional[Dict[str, Any]]:
    active_jobs = list_active_jobs()
    return active_jobs[0] if active_jobs else None


def update_progress(
    job_id: str,
    *,
    stage: Optional[str] = None,
    progress: Optional[int] = None,
    progress_mode: Optional[ProgressMode] = None,
    message: Optional[str] = None,
) -> None:
    updates: Dict[str, Any] = {}
    if stage is not None:
        updates["stage"] = stage
    if progress is not None:
        updates["progress"] = max(0, min(progress, 100))
    if progress_mode is not None:
        updates["progress_mode"] = progress_mode
    if message is not None:
        updates["message"] = message
    if updates:
        _update_job(job_id, **updates)


def _append_log(job_id: str, stream: str, line: str) -> None:
    with JOBS_LOCK:
        job = JOBS[job_id]
        if stream == "stdout":
            job["stdout_tail"] = _trim_tail([*job["stdout_tail"], line])
        else:
            job["stderr_tail"] = _trim_tail([*job["stderr_tail"], line])
        job["logs_tail"] = _trim_tail([*job["logs_tail"], f"[{stream}] {line}"])


def _reader_thread(stream_name: str, handle, queue: Queue) -> None:
    try:
        for raw_line in iter(handle.readline, ""):
            queue.put((stream_name, raw_line.rstrip("\r\n")))
    finally:
        handle.close()


def _finalize_status(job_id: str, *, status: JobStatus, result: Optional[Dict[str, Any]], error: Optional[str]) -> None:
    current = get_job(job_id) or {}
    _update_job(
        job_id,
        status=status,
        stage="success" if status == "success" else status,
        progress=100 if status == "success" else current.get("progress", 0),
        progress_mode="exact" if status == "success" else "indeterminate",
        finished_at=_utc_now(),
        result=result,
        error=error,
        message=result.get("message") if result and result.get("message") else error or ("Job concluido." if status == "success" else "Job falhou."),
    )


def run_job_in_background(
    job_id: str,
    command: List[str],
    *,
    parser: Optional[ParserCallback] = None,
    finalize: Optional[FinalizeCallback] = None,
    cleanup: Optional[Callable[[], None]] = None,
    timeout_seconds: int = 1800,
) -> None:
    def _worker() -> None:
        process: Optional[subprocess.Popen[str]] = None
        try:
            update_progress(
                job_id,
                stage="queued",
                progress=0,
                progress_mode="indeterminate",
                message="Job aguardando recurso local.",
            )
            acquire_heavy_job_blocking()
            _update_job(job_id, status="running", started_at=_utc_now())
            update_progress(
                job_id,
                stage="starting",
                progress=1,
                progress_mode="indeterminate",
                message="Processo iniciado.",
            )

            process = subprocess.Popen(
                command,
                cwd=str(get_project_root()),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )

            queue: Queue = Queue()
            stdout_thread = threading.Thread(target=_reader_thread, args=("stdout", process.stdout, queue), daemon=True)
            stderr_thread = threading.Thread(target=_reader_thread, args=("stderr", process.stderr, queue), daemon=True)
            stdout_thread.start()
            stderr_thread.start()

            started = time.time()
            while True:
                try:
                    stream, line = queue.get(timeout=0.2)
                    _append_log(job_id, stream, line)
                    if parser:
                        parsed = parser(stream, line, get_job(job_id) or {})
                        if parsed:
                            update_progress(job_id, **parsed)
                except Empty:
                    pass

                if process.poll() is not None and queue.empty():
                    break

                if time.time() - started > timeout_seconds:
                    process.kill()
                    _finalize_status(
                        job_id,
                        status="error",
                        result=None,
                        error=f"Processo excedeu o timeout de {timeout_seconds}s.",
                    )
                    return

            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)

            returncode = process.returncode
            stdout = "\n".join((get_job(job_id) or {}).get("stdout_tail", []))
            stderr = "\n".join((get_job(job_id) or {}).get("stderr_tail", []))
            logs = "\n".join((get_job(job_id) or {}).get("logs_tail", []))
            base_result = {
                "success": returncode == 0,
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
                "logs": logs,
                "command": command,
                "error": None if returncode == 0 else "Processo terminou com erro.",
                "message": "Job concluido com sucesso." if returncode == 0 else "Processo terminou com erro.",
            }

            final_result = finalize(base_result) if finalize else base_result
            if returncode == 0 and final_result.get("success", True):
                _finalize_status(job_id, status="success", result=final_result, error=None)
            else:
                _finalize_status(
                    job_id,
                    status="error",
                    result=final_result,
                    error=final_result.get("error") or base_result["message"],
                )
        except Exception as exc:
            _finalize_status(job_id, status="error", result=None, error=str(exc))
        finally:
            if cleanup:
                try:
                    cleanup()
                except Exception:
                    pass
            release_heavy_job()

    threading.Thread(target=_worker, daemon=True).start()


def run_callable_job_in_background(
    job_id: str,
    runner: RunnerCallback,
    *,
    cleanup: Optional[Callable[[], None]] = None,
) -> None:
    def _worker() -> None:
        try:
            update_progress(job_id, stage="queued", progress=0, progress_mode="indeterminate", message="Job aguardando recurso local.")
            acquire_heavy_job_blocking()
            _update_job(job_id, status="running", started_at=_utc_now())
            result = runner(get_job(job_id) or {})
            if result.get("success"):
                _finalize_status(job_id, status="success", result=result, error=None)
            else:
                _finalize_status(job_id, status="error", result=result, error=result.get("error") or "Job falhou.")
        except Exception as exc:
            _finalize_status(job_id, status="error", result=None, error=str(exc))
        finally:
            if cleanup:
                try:
                    cleanup()
                except Exception:
                    pass
            release_heavy_job()

    threading.Thread(target=_worker, daemon=True).start()
