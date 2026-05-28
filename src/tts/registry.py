import os
from typing import Dict, Type, List, Any
from src.tts.base import BaseTTSEngine

# A list of voices we support, with metadata.
# Especially highlighting Portuguese (pt-br) support.
VOICE_MAPPING = {
    "kokoro": {
        "pt_br_dora": {
            "id": "pf_dora",
            "name": "Dora (Feminino - PT-BR)",
            "lang": "pt-br"
        },
        "pt_br_alex": {
            "id": "pm_alex",
            "name": "Alex (Masculino - PT-BR)",
            "lang": "pt-br"
        },
        "en_us_bella": {
            "id": "af_bella",
            "name": "Bella (Female - US)",
            "lang": "en-us"
        },
        "en_us_sarah": {
            "id": "af_sarah",
            "name": "Sarah (Female - US)",
            "lang": "en-us"
        },
        "en_us_adam": {
            "id": "am_adam",
            "name": "Adam (Male - US)",
            "lang": "en-us"
        },
        "en_us_michael": {
            "id": "am_michael",
            "name": "Michael (Male - US)",
            "lang": "en-us"
        }
    },
    "piper": {
        # Piper Portuguese voices can be loaded dynamically or from custom path.
        # Usually, piper voices are files (.onnx), but we can map some defaults.
        "pt_br_lula": {
            "id": "pt_BR-lula-medium",
            "name": "Lula (Masculino - PT-BR)",
            "lang": "pt-br"
        },
        "pt_br_faber": {
            "id": "pt_BR-faber-medium",
            "name": "Faber (Masculino - PT-BR)",
            "lang": "pt-br"
        }
    }
}

class TTSRegistry:
    _engines: Dict[str, Type[BaseTTSEngine]] = {}

    @classmethod
    def register(cls, name: str, engine_cls: Type[BaseTTSEngine]):
        """Register a new TTS engine class."""
        cls._engines[name.lower()] = engine_cls

    @classmethod
    def get_engine_class(cls, name: str) -> Type[BaseTTSEngine]:
        """Get the engine class by name."""
        name_lower = name.lower()
        if name_lower not in cls._engines:
            raise ValueError(f"Motor TTS '{name}' nao esta registrado. Motores disponiveis: {list(cls._engines.keys())}")
        return cls._engines[name_lower]

    @classmethod
    def create_engine(cls, name: str, voice_id: str, device: str = "cpu", cache_dir: str = None, **kwargs) -> BaseTTSEngine:
        """Instantiate an engine with the given config."""
        engine_cls = cls.get_engine_class(name)
        
        # Check if the voice is a registered alias. If so, resolve to the engine-specific ID.
        voice_id_resolved = cls.resolve_voice(name, voice_id)
        
        return engine_cls(voice_id=voice_id_resolved, device=device, cache_dir=cache_dir, **kwargs)

    @classmethod
    def get_registered_engines(cls) -> List[str]:
        """List names of all registered engines."""
        return list(cls._engines.keys())

    @classmethod
    def get_available_engines(cls) -> List[str]:
        """List names of registered engines that are actually installed and available."""
        available = []
        for name, engine_cls in cls._engines.items():
            try:
                if engine_cls.is_available():
                    available.append(name)
            except Exception:
                pass
        return available

    @classmethod
    def resolve_voice(cls, engine: str, voice_id: str) -> str:
        """Resolve a voice alias to the engine's internal representation."""
        engine_lower = engine.lower()
        if engine_lower in VOICE_MAPPING and voice_id in VOICE_MAPPING[engine_lower]:
            return VOICE_MAPPING[engine_lower][voice_id]["id"]
        return voice_id

    @classmethod
    def get_voices_metadata(cls, engine: str = None) -> List[Dict[str, Any]]:
        """Get list of voices metadata for dropdowns and display."""
        metadata = []
        engines_to_check = [engine.lower()] if engine else VOICE_MAPPING.keys()
        
        for eng in engines_to_check:
            if eng in VOICE_MAPPING:
                for alias, info in VOICE_MAPPING[eng].items():
                    metadata.append({
                        "engine": eng,
                        "alias": alias,
                        "id": info["id"],
                        "name": info["name"],
                        "lang": info["lang"]
                    })
        return metadata

# Register default engines
from src.tts.kokoro_engine import KokoroEngine
from src.tts.piper_engine import PiperEngine

TTSRegistry.register("kokoro", KokoroEngine)
TTSRegistry.register("piper", PiperEngine)

