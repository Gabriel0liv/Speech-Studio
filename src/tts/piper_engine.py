import os
import urllib.request
import numpy as np
from typing import List, Tuple
from src.tts.base import BaseTTSEngine
from src.core.paths import VOICES_DIR

def download_piper_voice(voice_id_or_path: str) -> str:
    """
    Ensure the Piper voice model file (.onnx) and config (.onnx.json) are present.
    If voice_id_or_path is an alias (e.g., pt_br_lula), it downloads the files if missing.
    If it is a local path, it checks if it exists.
    Returns the absolute path to the .onnx file.
    """
    # 1. Resolve voice model file path
    if os.path.isabs(voice_id_or_path) or voice_id_or_path.endswith(".onnx"):
        # It's already a path
        onnx_path = os.path.abspath(voice_id_or_path)
    else:
        # It's an alias, map to standard filename in VOICES_DIR
        from src.tts.registry import VOICE_MAPPING
        resolved_id = voice_id_or_path
        if voice_id_or_path in VOICE_MAPPING.get("piper", {}):
            resolved_id = VOICE_MAPPING["piper"][voice_id_or_path]["id"]
        
        onnx_path = os.path.join(VOICES_DIR, f"{resolved_id}.onnx")

    json_path = onnx_path + ".json"

    # If already exists, we are done
    if os.path.exists(onnx_path) and os.path.exists(json_path):
        return onnx_path

    # 2. If it does not exist, check if we can download it
    voice_basename = os.path.splitext(os.path.basename(onnx_path))[0]
    
    url_mapping = {
        "pt_BR-lula-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/lula/medium",
        "pt_BR-faber-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/faber/medium",
    }

    if voice_basename not in url_mapping:
        raise FileNotFoundError(
            f"Arquivo de modelo do Piper nao foi encontrado em: {onnx_path}.\n"
            "Coloque os arquivos .onnx e .onnx.json correspondentes na pasta 'voices/' "
            "ou use uma das vozes portuguesas mapeadas (pt_br_lula ou pt_br_faber)."
        )

    base_url = url_mapping[voice_basename]
    os.makedirs(VOICES_DIR, exist_ok=True)

    print(f"[*] Baixando modelo de voz Piper '{voice_basename}'...")
    for ext in ["", ".json"]:
        file_url = f"{base_url}/{voice_basename}.onnx{ext}?download=true"
        dest_path = onnx_path + ext
        try:
            urllib.request.urlretrieve(file_url, dest_path)
        except Exception as e:
            # Clean up partial download
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise RuntimeError(f"Erro ao baixar arquivo {file_url} para {dest_path}: {e}")

    return onnx_path

class PiperEngine(BaseTTSEngine):
    """
    Piper Text-to-Speech Engine wrapper.
    Uses onnxruntime and piper-tts Python package.
    """
    def __init__(self, voice_id: str, device: str = "cpu", cache_dir: str = None, **kwargs):
        super().__init__(voice_id, device, cache_dir, **kwargs)
        self._voice = None
        self._resolved_model_path = None

    @classmethod
    def is_available(cls) -> bool:
        """
        Check if piper-tts and onnxruntime are installed.
        """
        try:
            import piper
            import onnxruntime
            from src.tts.kokoro_engine import setup_espeak
            return setup_espeak()  # Piper also needs espeak-ng for phonemes
        except ImportError:
            return False

    def _load_voice(self):
        """
        Lazy load and cache PiperVoice instance.
        """
        if self._voice is None:
            if not self.is_available():
                raise RuntimeError(
                    "O motor Piper nao esta disponivel. Verifique se instalou o 'piper-tts' "
                    "e se possui o 'espeak-ng' no sistema."
                )

            # Setup espeak-ng environment variables
            from src.tts.kokoro_engine import setup_espeak
            setup_espeak()

            # Ensure model and config are downloaded
            self._resolved_model_path = download_piper_voice(self.voice_id)

            from piper.voice import PiperVoice
            try:
                # Load PiperVoice using the onnx model path
                # Piper internally parses the .onnx.json config file automatically
                self._voice = PiperVoice.load(self._resolved_model_path)
            except Exception as e:
                raise RuntimeError(f"Falha ao carregar o modelo Piper em {self._resolved_model_path}: {e}")

        return self._voice

    def synthesize_to_array(self, text: str) -> Tuple[np.ndarray, int]:
        """
        Synthesize text using Piper and return waveform as numpy array.
        """
        voice = self._load_voice()
        
        try:
            # Piper voice config contains the model's sample rate
            # Fall back to 22050 if config is missing sample_rate
            sample_rate = getattr(voice.config, "sample_rate", 22050)
            
            # Synthesize text chunks directly into a stream of raw bytes
            audio_bytes = b"".join(voice.synthesize_stream_raw(text))
            
            if not audio_bytes:
                raise ValueError("Nenhum audio foi gerado pelo Piper para o texto fornecido.")
                
            # Convert signed 16-bit PCM bytes to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Normalize to float32 in [-1.0, 1.0] range
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            return audio_float, sample_rate
            
        except Exception as e:
            raise RuntimeError(f"Erro durante a sintese de audio com Piper: {e}")

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
            temp_wav = os.path.join(TEMP_DIR, "temp_piper.wav")
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
        Return voices supported natively in Piper by our registry mapping.
        """
        from src.tts.registry import VOICE_MAPPING
        return list(VOICE_MAPPING.get("piper", {}).keys())
