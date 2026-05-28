import os
import wave
import urllib.request
import urllib.error
import numpy as np
from typing import List, Tuple
from src.tts.base import BaseTTSEngine
from src.core.paths import VOICES_DIR

# Canonical URL base for the Piper Voices repository (rhasspy/piper-voices v1.0.0)
_PIPER_VOICES_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"

# Maps internal model ID -> relative URL path (without filename extension)
_PIPER_URL_MAP = {
    "pt_BR-faber-medium":   "pt/pt_BR/faber/medium/pt_BR-faber-medium",
    "pt_BR-edresson-low":   "pt/pt_BR/edresson/low/pt_BR-edresson-low",
}


def download_piper_voice(voice_id_or_path: str) -> str:
    """
    Ensure the Piper voice model file (.onnx) and config (.onnx.json) are present.
    If voice_id_or_path is an alias (e.g. pt_br_faber), it resolves via the registry
    and downloads both files if missing.
    If it is a local absolute path, it checks if it exists.
    Returns the absolute path to the .onnx file.
    """
    # 1. Resolve voice model file path
    if os.path.isabs(voice_id_or_path) or voice_id_or_path.endswith(".onnx"):
        # Already a concrete path
        onnx_path = os.path.abspath(voice_id_or_path)
    else:
        # It is an alias — resolve via registry
        from src.tts.registry import VOICE_MAPPING
        resolved_id = voice_id_or_path
        if voice_id_or_path in VOICE_MAPPING.get("piper", {}):
            resolved_id = VOICE_MAPPING["piper"][voice_id_or_path]["id"]
        onnx_path = os.path.join(VOICES_DIR, f"{resolved_id}.onnx")

    json_path = onnx_path + ".json"

    # 2. Already downloaded — nothing to do
    if os.path.exists(onnx_path) and os.path.exists(json_path):
        return onnx_path

    # 3. Identify the base model name and look it up in the URL map
    voice_basename = os.path.splitext(os.path.basename(onnx_path))[0]

    if voice_basename not in _PIPER_URL_MAP:
        raise FileNotFoundError(
            f"Arquivo de modelo do Piper nao foi encontrado em: {onnx_path}.\n"
            "Coloque os arquivos .onnx e .onnx.json correspondentes na pasta 'voices/' "
            "ou use uma das vozes portuguesas mapeadas (pt_br_faber ou pt_br_edresson)."
        )

    relative_path = _PIPER_URL_MAP[voice_basename]
    os.makedirs(VOICES_DIR, exist_ok=True)

    print(f"[*] Baixando modelo de voz Piper '{voice_basename}'...")
    for ext in ["", ".json"]:
        file_url = f"{_PIPER_VOICES_BASE_URL}/{relative_path}.onnx{ext}?download=true"
        dest_path = onnx_path + (ext if ext else "")
        try:
            urllib.request.urlretrieve(file_url, dest_path)
        except urllib.error.HTTPError as e:
            # Clean up any partial download
            if os.path.exists(dest_path):
                os.remove(dest_path)
            if e.code == 404:
                raise RuntimeError(
                    f"Modelo de voz Piper nao encontrado no repositorio oficial (HTTP 404).\n"
                    f"URL tentada: {file_url}\n"
                    "Verifique se a voz existe no registry ou atualize a lista de vozes."
                )
            raise RuntimeError(
                f"Erro HTTP {e.code} ao baixar {file_url}: {e.reason}"
            )
        except Exception as e:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise RuntimeError(f"Erro ao baixar arquivo {file_url} para {dest_path}: {e}")

    return onnx_path


class PiperEngine(BaseTTSEngine):
    """
    Piper Text-to-Speech Engine wrapper.
    Uses onnxruntime and the piper-tts Python package (piper.PiperVoice).
    """
    def __init__(self, voice_id: str, device: str = "cpu", cache_dir: str = None, **kwargs):
        super().__init__(voice_id, device, cache_dir, **kwargs)
        self._voice = None
        self._resolved_model_path = None

    @classmethod
    def is_available(cls) -> bool:
        """Check if piper-tts and onnxruntime are installed."""
        try:
            import piper          # noqa: F401
            import onnxruntime    # noqa: F401
            from src.tts.kokoro_engine import setup_espeak
            return setup_espeak()  # Piper also needs espeak-ng for phonemisation
        except ImportError:
            return False

    def _load_voice(self):
        """Lazy load and cache the PiperVoice instance."""
        if self._voice is None:
            if not self.is_available():
                raise RuntimeError(
                    "O motor Piper nao esta disponivel. Verifique se instalou o 'piper-tts' "
                    "e se possui o 'espeak-ng' configurado no sistema."
                )

            # Set up espeak-ng environment variables so piper can find phonemes
            from src.tts.kokoro_engine import setup_espeak
            setup_espeak()

            # Download model + config if not present locally
            try:
                self._resolved_model_path = download_piper_voice(self.voice_id)
            except (FileNotFoundError, RuntimeError) as exc:
                raise RuntimeError(str(exc))

            from piper import PiperVoice
            config_path = self._resolved_model_path + ".json"
            use_cuda = (self.device.lower() == "cuda")

            try:
                self._voice = PiperVoice.load(
                    self._resolved_model_path,
                    config_path=config_path if os.path.exists(config_path) else None,
                    use_cuda=use_cuda,
                )
            except Exception as e:
                raise RuntimeError(
                    f"Falha ao carregar o modelo Piper em {self._resolved_model_path}: {e}\n"
                    "Erro na API do Piper. A versao instalada pode usar outro metodo de sintese. "
                    "Verifique piper_engine.py."
                )

        return self._voice

    def synthesize_to_array(self, text: str) -> Tuple[np.ndarray, int]:
        """
        Synthesize text using Piper and return waveform as float32 numpy array + sample rate.
        Uses synthesize_wav into an in-memory wave buffer to avoid any temp files.
        """
        import io
        voice = self._load_voice()
        sample_rate = getattr(voice.config, "sample_rate", 22050)

        buf = io.BytesIO()
        try:
            with wave.open(buf, "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)
        except AttributeError:
            # Fallback path for older piper builds
            chunks = list(voice.synthesize(text))
            raw_pcm = b"".join(
                (chunk.audio_int16 if hasattr(chunk, "audio_int16") else bytes(chunk))
                for chunk in chunks
            )
            if not raw_pcm:
                raise ValueError("Nenhum audio foi gerado pelo Piper para o texto fornecido.")
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(raw_pcm)

        buf.seek(0)
        with wave.open(buf, "rb") as wf:
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        audio_int16 = np.frombuffer(raw, dtype=np.int16)
        audio_float = audio_int16.astype(np.float32) / 32768.0
        return audio_float, sample_rate

    def synthesize(self, text: str, output_path: str, format: str = "wav") -> str:
        """
        Synthesize text and save to output_path (WAV or MP3).

        Uses PiperVoice.synthesize_wav() which writes directly to a wave.Wave_write
        object — this is the stable, documented API in the current piper-tts package.
        """
        voice = self._load_voice()
        format = format.lower()

        # Helper: write a WAV using the current piper-tts API
        def _write_wav(path: str):
            try:
                with wave.open(path, "wb") as wav_file:
                    voice.synthesize_wav(text, wav_file)
            except AttributeError:
                # Fallback: older builds expose synthesize() as a generator of AudioChunk
                try:
                    chunks = list(voice.synthesize(text))
                    # Each AudioChunk has .audio_int16 (bytes) and voice.config.sample_rate
                    sample_rate = getattr(voice.config, "sample_rate", 22050)
                    raw_pcm = b"".join(
                        (chunk.audio_int16 if hasattr(chunk, "audio_int16") else bytes(chunk))
                        for chunk in chunks
                    )
                    if not raw_pcm:
                        raise ValueError("Nenhum audio foi gerado pelo Piper para o texto fornecido.")
                    with wave.open(path, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)       # 16-bit PCM
                        wf.setframerate(sample_rate)
                        wf.writeframes(raw_pcm)
                except Exception as inner_e:
                    raise RuntimeError(
                        f"Erro na API do Piper. A versao instalada pode usar outro metodo de "
                        f"sintese. Verifique piper_engine.py.\nDetalhe: {inner_e}"
                    )

        if format == "wav":
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            _write_wav(output_path)
            return output_path

        elif format == "mp3":
            from src.core.paths import TEMP_DIR
            from src.core.ffmpeg_utils import convert_wav_to_mp3
            import time
            os.makedirs(TEMP_DIR, exist_ok=True)
            temp_wav = os.path.join(TEMP_DIR, f"temp_piper_{os.getpid()}_{int(time.time())}.wav")
            try:
                _write_wav(temp_wav)
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                convert_wav_to_mp3(temp_wav, output_path)
            finally:
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
            return output_path

        else:
            raise ValueError(f"Formato '{format}' nao suportado. Use 'wav' ou 'mp3'.")

    def get_supported_voices(self) -> List[str]:
        """Return voices supported natively in Piper by our registry mapping."""
        from src.tts.registry import VOICE_MAPPING
        return list(VOICE_MAPPING.get("piper", {}).keys())
