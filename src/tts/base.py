from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np

class BaseTTSEngine(ABC):
    """
    Abstract base class defining the interface for all Text-to-Speech engines.
    """
    def __init__(self, voice_id: str, device: str = "cpu", cache_dir: str = None, **kwargs):
        self.voice_id = voice_id
        self.device = device
        self.cache_dir = cache_dir
        self.extra_args = kwargs

    @abstractmethod
    def synthesize(self, text: str, output_path: str, format: str = "wav") -> str:
        """
        Synthesize text and save the output audio file directly.
        
        Args:
            text: The text string to synthesize.
            output_path: Path where the output file should be saved.
            format: Output format ('wav' or 'mp3').
            
        Returns:
            The absolute path of the generated audio file.
        """
        pass

    @abstractmethod
    def synthesize_to_array(self, text: str) -> Tuple[np.ndarray, int]:
        """
        Synthesize text and return raw numpy array and sample rate.
        Useful for chunk concatenation and memory-based operations.
        
        Args:
            text: The text string to synthesize.
            
        Returns:
            A tuple of (audio_data_numpy_array, sample_rate_hz).
        """
        pass

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """
        Check if the engine dependencies and tools (e.g., binaries, packages) are installed.
        
        Returns:
            True if the engine can be used, False otherwise.
        """
        pass

    @abstractmethod
    def get_supported_voices(self) -> List[str]:
        """
        Get a list of voice IDs natively supported by this engine.
        
        Returns:
            A list of voice IDs/codes.
        """
        pass
