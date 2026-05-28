import os
from typing import Dict, Type, List, Any, Tuple
from src.tts.base import BaseTTSEngine

# A list of voices we support, with metadata.
# Especially highlighting Portuguese (pt-br) support.
VOICE_MAPPING = {
    "kokoro": {
        "pt_br_dora": {
            "engine": "kokoro",
            "alias": "pt_br_dora",
            "id": "pf_dora",
            "name": "Dora (Feminino - PT-BR)",
            "lang": "pt-br",
            "gender": "Feminino",
            "style": "Suave / Natural",
            "source": "hf_cache",
            "license_note": "Licenca nao comercial do modelo Kokoro. Verifique os termos antes do uso comercial."
        },
        "dora": {
            "engine": "kokoro",
            "alias": "dora",
            "id": "pf_dora",
            "name": "Dora (Feminino - PT-BR)",
            "lang": "pt-br",
            "gender": "Feminino",
            "style": "Suave / Natural",
            "source": "hf_cache",
            "license_note": "Licenca nao comercial do modelo Kokoro. Verifique os termos antes do uso comercial."
        },
        "kokoro_dora": {
            "engine": "kokoro",
            "alias": "kokoro_dora",
            "id": "pf_dora",
            "name": "Dora (Feminino - PT-BR)",
            "lang": "pt-br",
            "gender": "Feminino",
            "style": "Suave / Natural",
            "source": "hf_cache",
            "license_note": "Licenca nao comercial do modelo Kokoro. Verifique os termos antes do uso comercial."
        },
        "pt_br_alex": {
            "engine": "kokoro",
            "alias": "pt_br_alex",
            "id": "pm_alex",
            "name": "Alex (Masculino - PT-BR)",
            "lang": "pt-br",
            "gender": "Masculino",
            "style": "Natural",
            "source": "hf_cache",
            "license_note": "Licenca nao comercial do modelo Kokoro. Verifique os termos antes do uso comercial."
        },
        "alex": {
            "engine": "kokoro",
            "alias": "alex",
            "id": "pm_alex",
            "name": "Alex (Masculino - PT-BR)",
            "lang": "pt-br",
            "gender": "Masculino",
            "style": "Natural",
            "source": "hf_cache",
            "license_note": "Licenca nao comercial do modelo Kokoro. Verifique os termos antes do uso comercial."
        },
        "kokoro_alex": {
            "engine": "kokoro",
            "alias": "kokoro_alex",
            "id": "pm_alex",
            "name": "Alex (Masculino - PT-BR)",
            "lang": "pt-br",
            "gender": "Masculino",
            "style": "Natural",
            "source": "hf_cache",
            "license_note": "Licenca nao comercial do modelo Kokoro. Verifique os termos antes do uso comercial."
        },
        "pt_br_santa": {
            "engine": "kokoro",
            "alias": "pt_br_santa",
            "id": "pm_santa",
            "name": "Santa (Masculino - PT-BR)",
            "lang": "pt-br",
            "gender": "Masculino",
            "style": "Grave / Narrativo",
            "source": "hf_cache",
            "license_note": "Licenca nao comercial do modelo Kokoro. Verifique os termos antes do uso comercial."
        },
        "santa": {
            "engine": "kokoro",
            "alias": "santa",
            "id": "pm_santa",
            "name": "Santa (Masculino - PT-BR)",
            "lang": "pt-br",
            "gender": "Masculino",
            "style": "Grave / Narrativo",
            "source": "hf_cache",
            "license_note": "Licenca nao comercial do modelo Kokoro. Verifique os termos antes do uso comercial."
        },
        "kokoro_santa": {
            "engine": "kokoro",
            "alias": "kokoro_santa",
            "id": "pm_santa",
            "name": "Santa (Masculino - PT-BR)",
            "lang": "pt-br",
            "gender": "Masculino",
            "style": "Grave / Narrativo",
            "source": "hf_cache",
            "license_note": "Licenca nao comercial do modelo Kokoro. Verifique os termos antes do uso comercial."
        },
        "en_us_bella": {
            "engine": "kokoro",
            "alias": "en_us_bella",
            "id": "af_bella",
            "name": "Bella (Female - US)",
            "lang": "en-us",
            "gender": "Female",
            "style": "Clara / Profissional",
            "source": "hf_cache",
            "license_note": "Licenca nao comercial do modelo Kokoro. Verifique os termos antes do uso comercial."
        },
        "en_us_sarah": {
            "engine": "kokoro",
            "alias": "en_us_sarah",
            "id": "af_sarah",
            "name": "Sarah (Female - US)",
            "lang": "en-us",
            "gender": "Female",
            "style": "Suave / Natural",
            "source": "hf_cache",
            "license_note": "Licenca nao comercial do modelo Kokoro. Verifique os termos antes do uso comercial."
        },
        "en_us_adam": {
            "engine": "kokoro",
            "alias": "en_us_adam",
            "id": "am_adam",
            "name": "Adam (Male - US)",
            "lang": "en-us",
            "gender": "Male",
            "style": "Grave / Narrativa",
            "source": "hf_cache",
            "license_note": "Licenca nao comercial do modelo Kokoro. Verifique os termos antes do uso comercial."
        },
        "en_us_michael": {
            "engine": "kokoro",
            "alias": "en_us_michael",
            "id": "am_michael",
            "name": "Michael (Male - US)",
            "lang": "en-us",
            "gender": "Male",
            "style": "Clara / Profissional",
            "source": "hf_cache",
            "license_note": "Licenca nao comercial do modelo Kokoro. Verifique os termos antes do uso comercial."
        }
    },
    "piper": {
        "pt_br_faber": {
            "engine": "piper",
            "alias": "pt_br_faber",
            "id": "pt_BR-faber-medium",
            "name": "Faber (Masculino - PT-BR)",
            "lang": "pt-br",
            "gender": "Masculino",
            "style": "Narrativo",
            "source": "downloadable",
            "license_note": "Licenca CC-BY-NC-SA. Verifique a licenca do modelo antes do uso comercial."
        },
        "faber": {
            "engine": "piper",
            "alias": "faber",
            "id": "pt_BR-faber-medium",
            "name": "Faber (Masculino - PT-BR)",
            "lang": "pt-br",
            "gender": "Masculino",
            "style": "Narrativo",
            "source": "downloadable",
            "license_note": "Licenca CC-BY-NC-SA. Verifique a licenca do modelo antes do uso comercial."
        },
        "piper_faber": {
            "engine": "piper",
            "alias": "piper_faber",
            "id": "pt_BR-faber-medium",
            "name": "Faber (Masculino - PT-BR)",
            "lang": "pt-br",
            "gender": "Masculino",
            "style": "Narrativo",
            "source": "downloadable",
            "license_note": "Licenca CC-BY-NC-SA. Verifique a licenca do modelo antes do uso comercial."
        },
        "pt_br_edresson": {
            "engine": "piper",
            "alias": "pt_br_edresson",
            "id": "pt_BR-edresson-low",
            "name": "Edresson (Masculino - PT-BR)",
            "lang": "pt-br",
            "gender": "Masculino",
            "style": "Natural / Conversacional",
            "source": "downloadable",
            "license_note": "Licenca CC-BY-NC-SA. Verifique a licenca do modelo antes do uso comercial."
        },
        "edresson": {
            "engine": "piper",
            "alias": "edresson",
            "id": "pt_BR-edresson-low",
            "name": "Edresson (Masculino - PT-BR)",
            "lang": "pt-br",
            "gender": "Masculino",
            "style": "Natural / Conversacional",
            "source": "downloadable",
            "license_note": "Licenca CC-BY-NC-SA. Verifique a licenca do modelo antes do uso comercial."
        },
        "piper_edresson": {
            "engine": "piper",
            "alias": "piper_edresson",
            "id": "pt_BR-edresson-low",
            "name": "Edresson (Masculino - PT-BR)",
            "lang": "pt-br",
            "gender": "Masculino",
            "style": "Natural / Conversacional",
            "source": "downloadable",
            "license_note": "Licenca CC-BY-NC-SA. Verifique a licenca do modelo antes do uso comercial."
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
                        "lang": info["lang"],
                        "gender": info.get("gender", "Desconhecido"),
                        "style": info.get("style", "Padrao"),
                        "source": info.get("source", "unknown"),
                        "license_note": info.get("license_note", "Verifique os termos de licenca antes do uso comercial.")
                    })
        return metadata

    @classmethod
    def get_voice_status(cls, engine: str, voice_id: str) -> dict:
        """
        Check if a voice model is installed locally without downloading or loading models.
        Returns a dictionary with status flags: available_in_registry, installed_locally,
        requires_download, ready_to_use, status_description.
        """
        engine_lower = engine.lower()
        
        # Check if voice is in registry
        in_registry = False
        if engine_lower in VOICE_MAPPING and voice_id in VOICE_MAPPING[engine_lower]:
            in_registry = True
            
        # Check if engine is available
        try:
            engine_cls = cls.get_engine_class(engine_lower)
            engine_available = engine_cls.is_available()
        except Exception:
            engine_available = False
            
        # Piper custom ONNX files check
        is_custom_piper = engine_lower == "piper" and (os.path.isabs(voice_id) or voice_id.endswith(".onnx"))
        if is_custom_piper:
            onnx_path = os.path.abspath(voice_id)
            json_path = onnx_path + ".json"
            installed = os.path.exists(onnx_path) and os.path.exists(json_path)
            return {
                "available_in_registry": False,
                "installed_locally": installed,
                "requires_download": False,
                "ready_to_use": installed and engine_available,
                "status_description": "Instalado (Voz customizada)" if installed else "Arquivo ONNX/JSON nao encontrado"
            }

        if not in_registry:
            return {
                "available_in_registry": False,
                "installed_locally": False,
                "requires_download": False,
                "ready_to_use": False,
                "status_description": f"Voz '{voice_id}' nao cadastrada no registry do motor '{engine_lower}'"
            }
            
        if not engine_available:
            return {
                "available_in_registry": True,
                "installed_locally": False,
                "requires_download": False,
                "ready_to_use": False,
                "status_description": f"Motor '{engine_lower}' nao instalado ou indisponivel no ambiente"
            }
            
        # Resolve alias if needed
        resolved_id = cls.resolve_voice(engine_lower, voice_id)
            
        if engine_lower == "kokoro":
            # For Kokoro, if the engine is available and setup_espeak passes,
            # we just check if it's cached or needs download on first use.
            from src.tts.kokoro_engine import setup_espeak
            espeak_ok = setup_espeak()
            if not espeak_ok:
                return {
                    "available_in_registry": True,
                    "installed_locally": False,
                    "requires_download": False,
                    "ready_to_use": False,
                    "status_description": "Falta espeak-ng no sistema (necessario para Kokoro)"
                }
            
            # Check HF cache
            hf_home = os.environ.get("HF_HOME")
            if not hf_home:
                hf_home = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
            is_cached = False
            if hf_home:
                kokoro_cache = os.path.join(hf_home, "hub", "models--hexgrad--Kokoro-82M")
                if os.path.exists(kokoro_cache):
                    is_cached = True
            
            if is_cached:
                return {
                    "available_in_registry": True,
                    "installed_locally": True,
                    "requires_download": False,
                    "ready_to_use": True,
                    "status_description": "Instalado (Cache HF local)"
                }
            else:
                return {
                    "available_in_registry": True,
                    "installed_locally": False,
                    "requires_download": True,
                    "ready_to_use": True,
                    "status_description": "Disponivel para download (Baixara pesos no primeiro uso)"
                }
                
        elif engine_lower == "piper":
            from src.tts.kokoro_engine import setup_espeak
            espeak_ok = setup_espeak()
            if not espeak_ok:
                return {
                    "available_in_registry": True,
                    "installed_locally": False,
                    "requires_download": False,
                    "ready_to_use": False,
                    "status_description": "Falta espeak-ng no sistema (necessario para Piper)"
                }

            from src.core.paths import VOICES_DIR
            onnx_path = os.path.join(VOICES_DIR, f"{resolved_id}.onnx")
            json_path = onnx_path + ".json"
            
            if os.path.exists(onnx_path) and os.path.exists(json_path):
                return {
                    "available_in_registry": True,
                    "installed_locally": True,
                    "requires_download": False,
                    "ready_to_use": True,
                    "status_description": "Instalado (Arquivos locais)"
                }
            else:
                return {
                    "available_in_registry": True,
                    "installed_locally": False,
                    "requires_download": True,
                    "ready_to_use": True,
                    "status_description": "Disponivel para download (Baixara no primeiro uso)"
                }
                
        return {
            "available_in_registry": True,
            "installed_locally": False,
            "requires_download": False,
            "ready_to_use": False,
            "status_description": "Desconhecido"
        }

    @classmethod
    def validate_voice(cls, engine: str, voice_id: str) -> bool:
        """
        Validates if the selected voice/engine combination is valid.
        Raises ValueError if voice is invalid and not a direct file path.
        """
        engine_lower = engine.lower()
        if engine_lower not in VOICE_MAPPING:
            raise ValueError(
                f"Motor '{engine}' nao suportado. Motores disponiveis: {list(VOICE_MAPPING.keys())}"
            )
            
        # Allow directONNX path for Piper
        if engine_lower == "piper" and (os.path.isabs(voice_id) or voice_id.endswith(".onnx")):
            return True
            
        if voice_id not in VOICE_MAPPING[engine_lower]:
            supported_aliases = list(VOICE_MAPPING[engine_lower].keys())
            raise ValueError(
                f"A voz '{voice_id}' nao e suportada pelo motor '{engine}'.\n"
                f"Vozes disponiveis no registry: {supported_aliases}.\n"
                f"Para o Piper, voce tambem pode passar o caminho direto para um arquivo '.onnx' local."
            )
        return True

# Register default engines
from src.tts.kokoro_engine import KokoroEngine
from src.tts.piper_engine import PiperEngine

TTSRegistry.register("kokoro", KokoroEngine)
TTSRegistry.register("piper", PiperEngine)
