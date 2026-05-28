from fastapi import APIRouter

from src.core.presets import list_speaker_profiles, list_tts_presets


router = APIRouter(tags=["presets"])


@router.get("/presets")
def get_presets():
    return {"success": True, "presets": list_tts_presets()}


@router.get("/speaker-profiles")
def get_speaker_profiles():
    return {"success": True, "speaker_profiles": list_speaker_profiles()}
