import os
from dotenv import load_dotenv
from src.core.paths import PROJECT_ROOT

# Load environment variables from .env at startup
env_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=env_path)

def configure_hf_environment(cache_dir_override=None, offline_override=None):
    """
    Configure Hugging Face environment variables before ML libraries are loaded.
    Priority: Override parameters > .env file values > system defaults.
    """
    # 1. Resolve HF Home Cache Directory
    hf_home = cache_dir_override or os.getenv("HF_HOME")
    if hf_home:
        # Standardize path separators for Windows / Python consistency
        hf_home = hf_home.replace("\\", "/")
        os.makedirs(hf_home, exist_ok=True)
        os.environ["HF_HOME"] = hf_home
        os.environ["HF_HUB_CACHE"] = os.path.join(hf_home, "hub").replace("\\", "/")
    
    # 2. Resolve HF Offline Mode
    is_offline = False
    if offline_override is not None:
        is_offline = bool(offline_override)
    else:
        is_offline = (os.getenv("HF_HUB_OFFLINE") == "1")
        
    if is_offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
    else:
        # Keep online checks active
        if "HF_HUB_OFFLINE" in os.environ:
            del os.environ["HF_HUB_OFFLINE"]

    return {
        "hf_home": os.environ.get("HF_HOME", "Default system cache"),
        "hf_hub_cache": os.environ.get("HF_HUB_CACHE", "Default HF cache"),
        "hf_offline": os.environ.get("HF_HUB_OFFLINE") == "1"
    }

# Run initial configuration from environment variables / .env values
configure_hf_environment()
