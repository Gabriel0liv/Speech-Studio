import os
import shutil
import numpy as np
from typing import List, Tuple
from src.tts.base import BaseTTSEngine

def setup_espeak() -> bool:
    """
    Search for espeak-ng on Windows and configure the PHONEMIZER_ESPEAK_PATH
    environment variable if found. Returns True if found, False otherwise.
    """
    if os.getenv("PHONEMIZER_ESPEAK_PATH"):
        return True

    # Check if espeak-ng/espeak is already in system PATH
    if shutil.which("espeak-ng") or shutil.which("espeak"):
        return True

    # Check standard installation directories on Windows
    common_paths = [
        r"C:\Program Files\eSpeak NG",
        r"C:\Program Files (x86)\eSpeak NG",
        r"C:\Program Files\eSpeak",
        r"C:\Program Files (x86)\eSpeak",
    ]
    for path in common_paths:
        if os.path.exists(os.path.join(path, "espeak-ng.exe")) or os.path.exists(os.path.join(path, "espeak.exe")):
            os.environ["PHONEMIZER_ESPEAK_PATH"] = path
            os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
            return True
            
    return False

def get_lang_code_for_voice(voice: str) -> str:
    """
    Resolve the Kokoro language code based on the voice ID prefix.
    """
    voice = voice.lower()
    if voice.startswith("pf_") or voice.startswith("pm_"):
        return "p"  # Portuguese (PT-BR)
    elif voice.startswith("bf_") or voice.startswith("bm_"):
        return "b"  # British English
    elif voice.startswith("ef_") or voice.startswith("em_"):
        return "e"  # Spanish
    elif voice.startswith("ff_") or voice.startswith("fm_"):
        return "f"  # French
    elif voice.startswith("hf_") or voice.startswith("hm_"):
        return "h"  # Hindi
    elif voice.startswith("if_") or voice.startswith("im_"):
        return "i"  # Italian
    elif voice.startswith("jf_") or voice.startswith("jm_"):
        return "j"  # Japanese
    elif voice.startswith("zf_") or voice.startswith("zm_"):
        return "z"  # Mandarin Chinese
    else:
        return "a"  # Default American English (af_*, am_*)

class KokoroEngine(BaseTTSEngine):
    """
    Kokoro-82M Text-to-Speech Engine.
    Uses PyTorch weights and requires espeak-ng for phonemization.
    """
    def __init__(self, voice_id: str, device: str = "cpu", cache_dir: str = None, **kwargs):
        super().__init__(voice_id, device, cache_dir, **kwargs)
        self._pipeline = None
        self._current_lang_code = None

    @classmethod
    def is_available(cls) -> bool:
        """
        Check if kokoro library is installed.
        """
        try:
            import kokoro
            import torch
            import soundfile
            return True
        except ImportError:
            return False

    def _get_pipeline(self, lang_code: str):
        """
        Lazy load and cache KPipeline instance.
        """
        if self._pipeline is None or self._current_lang_code != lang_code:
            if not self.is_available():
                raise RuntimeError(
                    "O pacote 'kokoro' nao esta instalado. Por favor, instale as dependencias "
                    "de TTS rodando './install_tts.ps1'."
                )
            
            # Set up espeak-ng paths before importing/instantiating
            setup_espeak()
            
            from kokoro import KPipeline
            try:
                # Pass repo_id explicitly to suppress the 'Defaulting repo_id' warning
                self._pipeline = KPipeline(
                    lang_code=lang_code,
                    device=self.device,
                    repo_id="hexgrad/Kokoro-82M"
                )
                self._current_lang_code = lang_code
            except Exception as e:
                # Provide user-friendly diagnostics if espeak is missing
                espeak_status = "detectado" if setup_espeak() else "NAO DETECTADO"
                raise RuntimeError(
                    f"Falha ao carregar a pipeline do Kokoro para lang='{lang_code}'.\n"
                    f"Status do espeak-ng no sistema: {espeak_status}.\n"
                    f"Erro original: {e}\n"
                    "Por favor, certifique-se de que o 'espeak-ng' esta instalado e adicionado ao PATH."
                )
        return self._pipeline

    def synthesize_to_array(self, text: str) -> Tuple[np.ndarray, int]:
        """
        Synthesize text using Kokoro and return waveform as numpy array.
        """
        lang_code = get_lang_code_for_voice(self.voice_id)
        pipeline = self._get_pipeline(lang_code)
        
        try:
            # Generate audio chunks. Speed default is 1.0.
            speed = float(self.extra_args.get("speed") or 1.0)
            generator = pipeline(text, voice=self.voice_id, speed=speed)
            audio_chunks = []
            
            for _, _, audio in generator:
                if audio is not None and len(audio) > 0:
                    audio_chunks.append(audio)
            
            if not audio_chunks:
                raise ValueError("Nenhum audio foi gerado pelo Kokoro para o texto fornecido.")
                
            full_audio = np.concatenate(audio_chunks)
            # Kokoro sample rate is fixed at 24000Hz
            return full_audio, 24000
            
        except Exception as e:
            raise RuntimeError(f"Erro durante a sintese de audio com Kokoro: {e}")

    def synthesize(self, text: str, output_path: str, format: str = "wav") -> str:
        """
        Synthesize text and save to output_path. Convert to MP3 if required.
        """
        audio_data, sr = self.synthesize_to_array(text)
        
        import soundfile as sf
        from src.core.paths import TEMP_DIR
        from src.core.ffmpeg_utils import convert_wav_to_mp3
        
        format = format.lower()
        if format == "wav":
            sf.write(output_path, audio_data, sr)
            return output_path
        elif format == "mp3":
            os.makedirs(TEMP_DIR, exist_ok=True)
            temp_wav = os.path.join(TEMP_DIR, "temp_kokoro.wav")
            try:
                sf.write(temp_wav, audio_data, sr)
                convert_wav_to_mp3(temp_wav, output_path)
            finally:
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
            return output_path
        else:
            raise ValueError(f"Formato '{format}' nao suportado. Use 'wav' ou 'mp3'.")

    def get_supported_voices(self) -> List[str]:
        """
        Return voices supported natively in Kokoro by our registry mapping.
        """
        from src.tts.registry import VOICE_MAPPING
        return list(VOICE_MAPPING.get("kokoro", {}).keys())
