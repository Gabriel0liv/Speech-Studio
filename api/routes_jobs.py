from fastapi import APIRouter, HTTPException, Query

from api.jobs import active_heavy_job, get_job, get_job_logs, list_active_jobs, list_recent_jobs


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/active")
def get_active_jobs():
    return {"success": True, "jobs": list_active_jobs(), "active_job": active_heavy_job()}


@router.get("/recent")
def get_recent_jobs(limit: int = Query(default=20, ge=1, le=100)):
    return {"success": True, "jobs": list_recent_jobs(limit)}


@router.get("/{job_id}")
def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")
    return {"success": True, **job}


@router.get("/{job_id}/logs")
def get_logs(job_id: str):
    logs = get_job_logs(job_id)
    if not logs:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")
    return {"success": True, **logs}
