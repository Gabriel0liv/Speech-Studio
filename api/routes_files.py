from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.utils import resolve_safe_file


router = APIRouter(prefix="/files", tags=["files"])


@router.get("/{category}/{file_path:path}")
def serve_generated_file(category: str, file_path: str):
    target = resolve_safe_file(category, file_path)
    if target is None:
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado ou nao permitido.")
    return FileResponse(target)
