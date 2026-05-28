from fastapi import APIRouter, Query

from api.utils import local_path_to_file_url
from src.core.history import list_jobs


router = APIRouter(tags=["history"])


@router.get("/history")
def get_history(limit: int = Query(default=50, ge=1, le=200)):
    jobs = list_jobs(limit=limit)
    for job in jobs:
        primary_output = job.get("primary_output_path")
        job["file_url"] = local_path_to_file_url(__import__("pathlib").Path(primary_output)) if primary_output else None
    return {"success": True, "jobs": jobs}
