import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.core.database import get_connection

def is_history_enabled() -> bool:
    """Check if job history is globally enabled in app settings."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_settings WHERE key = 'history_enabled'")
            row = cursor.fetchone()
            if row:
                return row[0].lower() == "true"
    except Exception:
        pass
    return True

def create_job(
    job_type: str,
    input_kind: str,
    input_path: Optional[str] = None,
    input_name: Optional[str] = None,
    text_snippet: Optional[str] = None,
    output_dir: Optional[str] = None,
    primary_output_path: Optional[str] = None,
    output_format: Optional[str] = None,
    engine: Optional[str] = None,
    model: Optional[str] = None,
    voice: Optional[str] = None,
    language: Optional[str] = None,
    device: Optional[str] = None,
    metadata_json: Optional[str] = None
) -> Optional[int]:
    """
    Log a new STT/TTS job in running status.
    Returns the newly created job ID or None if disabled or failed.
    """
    if not is_history_enabled():
        return None
        
    try:
        created_at = datetime.now().isoformat()
        status = "running"
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO jobs (
                    job_type, status, created_at, input_kind, input_path, input_name,
                    text_snippet, output_dir, primary_output_path, output_format,
                    engine, model, voice, language, device, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_type, status, created_at, input_kind, input_path, input_name,
                text_snippet, output_dir, primary_output_path, output_format,
                engine, model, voice, language, device, metadata_json
            ))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"[WARN] Nao foi possivel salvar historico: {e}")
        return None

def update_job_success(
    job_id: int,
    primary_output_path: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    text_snippet: Optional[str] = None,
    metadata_json: Optional[str] = None
) -> None:
    """Mark a logged job as successfully completed."""
    if job_id is None:
        return
        
    try:
        completed_at = datetime.now().isoformat()
        
        # Build dynamic updates
        updates = ["status = 'success'", "completed_at = ?"]
        params = [completed_at]
        
        if primary_output_path is not None:
            updates.append("primary_output_path = ?")
            params.append(primary_output_path)
            
        if duration_seconds is not None:
            updates.append("duration_seconds = ?")
            params.append(duration_seconds)
            
        if text_snippet is not None:
            updates.append("text_snippet = ?")
            params.append(text_snippet)
            
        if metadata_json is not None:
            updates.append("metadata_json = ?")
            params.append(metadata_json)
            
        params.append(job_id)
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE jobs 
                SET {', '.join(updates)}
                WHERE id = ?
            """, tuple(params))
            conn.commit()
    except Exception as e:
        print(f"[WARN] Nao foi possivel atualizar status do historico: {e}")

def update_job_failure(job_id: int, error_message: str) -> None:
    """Mark a logged job as failed with an error message."""
    if job_id is None:
        return
        
    try:
        completed_at = datetime.now().isoformat()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE jobs 
                SET status = 'failed', completed_at = ?, error_message = ?
                WHERE id = ?
            """, (completed_at, error_message, job_id))
            conn.commit()
    except Exception as e:
        print(f"[WARN] Nao foi possivel atualizar status do historico: {e}")

def list_jobs(limit: int = 50, job_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve recent jobs from database."""
    try:
        query = "SELECT * FROM jobs"
        params = []
        if job_type:
            query += " WHERE job_type = ?"
            params.append(job_type)
            
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"[WARN] Nao foi possivel listar historico: {e}")
        return []

def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single job by its ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"[WARN] Nao foi possivel obter detalhes do job {job_id}: {e}")
        return None

def delete_job(job_id: int) -> None:
    """Delete a single job entry from database."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            conn.commit()
    except Exception as e:
        print(f"[WARN] Nao foi possivel remover registro {job_id}: {e}")

def clear_history(job_type: Optional[str] = None) -> None:
    """Clear jobs history (DB rows only, preserving disk files)."""
    try:
        query = "DELETE FROM jobs"
        params = []
        if job_type:
            query += " WHERE job_type = ?"
            params.append(job_type)
            
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            conn.commit()
            print(f"[*] Historico de {job_type if job_type else 'todos os'} jobs limpo com sucesso.")
    except Exception as e:
        print(f"[WARN] Nao foi possivel limpar historico: {e}")
