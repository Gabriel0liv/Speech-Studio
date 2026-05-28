from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_dashboard import router as dashboard_router
from api.routes_files import router as files_router
from api.routes_health import router as health_router
from api.routes_history import router as history_router
from api.routes_job_actions import router as job_actions_router
from api.routes_jobs import router as jobs_router
from api.routes_presets import router as presets_router
from api.routes_stt import router as stt_router
from api.routes_tts import router as tts_router
from api.routes_voices import router as voices_router
from src.core.database import initialize_database


app = FastAPI(title="Speech Studio API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/")
def root_status():
    return {"success": True, "service": "speech-studio-api"}


@app.get("/api")
def api_status():
    return {"success": True, "service": "speech-studio-api"}


@app.get("/api/models")
def get_models():
    from src.tts.registry import TTSRegistry, VOICE_MAPPING

    engines = []
    voices = []
    try:
        registered_engines = TTSRegistry.get_registered_engines()
    except Exception:
        registered_engines = list(VOICE_MAPPING.keys())

    try:
        available_engines = set(TTSRegistry.get_available_engines())
    except Exception:
        available_engines = set()

    for engine_name in registered_engines:
        engine_available = engine_name in available_engines
        engine_status = "ready" if engine_available else "missing_dependency"
        engines.append({
            "name": engine_name,
            "status": engine_status,
            "installed_locally": engine_available,
        })

        seen_aliases = set()
        for alias, info in VOICE_MAPPING.get(engine_name, {}).items():
            if alias in seen_aliases or not alias.startswith("pt_br_"):
                continue
            seen_aliases.add(alias)
            metadata = {
                "engine": engine_name,
                "alias": alias,
                "id": info["id"],
                "name": info["name"],
                "lang": info["lang"],
                "gender": info.get("gender", "Desconhecido"),
                "style": info.get("style", "Padrao"),
                "source": info.get("source", "unknown"),
                "license_note": info.get("license_note", "Verifique os termos de licenca antes do uso comercial."),
            }
            try:
                status_info = TTSRegistry.get_voice_status(engine_name, alias)
            except Exception:
                status_info = {
                    "installed_locally": False,
                    "requires_download": False,
                    "ready_to_use": False,
                    "available_in_registry": True,
                    "status_description": "Status indisponivel no ambiente atual.",
                }

            if status_info["ready_to_use"]:
                voice_status = "ready" if status_info["installed_locally"] else "requires_download"
            elif status_info["available_in_registry"]:
                voice_status = "available_with_warning" if engine_available else "missing_dependency"
            else:
                voice_status = "not_installed"

            voices.append({
                **metadata,
                "status": voice_status,
                "installed_locally": status_info["installed_locally"],
                "requires_download": status_info["requires_download"],
                "ready_to_use": status_info["ready_to_use"],
                "status_description": status_info["status_description"],
            })

    return {"success": True, "engines": engines, "voices": voices}


app.include_router(health_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(presets_router, prefix="/api")
app.include_router(tts_router, prefix="/api")
app.include_router(stt_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(job_actions_router, prefix="/api")
app.include_router(voices_router, prefix="/api")
app.include_router(files_router, prefix="/api")
