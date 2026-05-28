import os

# Root directory of the project (parent of src/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Outputs directories
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
TRANSCRIPTIONS_DIR = os.path.join(OUTPUTS_DIR, "transcriptions")
SPEECH_DIR = os.path.join(OUTPUTS_DIR, "speech")

# Temporary working directory
TEMP_DIR = os.path.join(PROJECT_ROOT, "temp")

# Voices cache and configurations
VOICES_DIR = os.path.join(PROJECT_ROOT, "voices")

# Local cache directories
MODEL_CACHE_DIR = os.path.join(PROJECT_ROOT, "model_cache")
TTS_CACHE_DIR = os.path.join(PROJECT_ROOT, "tts_cache")

def ensure_directories():
    """Ensure all required project directories exist on disk."""
    dirs = [
        OUTPUTS_DIR,
        TRANSCRIPTIONS_DIR,
        SPEECH_DIR,
        TEMP_DIR,
        VOICES_DIR,
        MODEL_CACHE_DIR,
        TTS_CACHE_DIR
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Run directory creation on import
ensure_directories()
