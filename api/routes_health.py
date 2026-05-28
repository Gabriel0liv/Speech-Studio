from fastapi import APIRouter

from src.core.healthcheck import run_healthcheck_structured


router = APIRouter(tags=["health"])


@router.get("/health")
def get_health():
    return run_healthcheck_structured()
