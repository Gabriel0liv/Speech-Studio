import sys
import os
import importlib.util

def check_package(name: str) -> bool:
    """Check if a Python package is installed without importing it."""
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False

def get_cuda_info():
    """Check CUDA status using torch if installed."""
    if not check_package("torch"):
        return "torch not installed", False, "N/A"
        
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            return "CUDA Available", True, gpu_name
        else:
            return "CUDA Unavailable (CPU only)", False, "N/A"
    except Exception as e:
        return f"Error checking CUDA: {e}", False, "N/A"

def check_ffmpeg() -> bool:
    """Verify that FFmpeg is installed and accessible in the system path."""
    try:
        import subprocess
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        return True
    except Exception:
        return False

def run_healthcheck() -> bool:
    """Runs a complete environment diagnostics check."""
    print("==================================================")
    print("           SPEECH STUDIO HEALTHCHECK              ")
    print("==================================================")
    
    # 1. Python version and project root
    print(f"Python Version: {sys.version.split()[0]}")
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f"Project Root:   {project_root}")
    print("--------------------------------------------------")
    
    # 2. Package import checks
    packages = {
        "PyTorch (torch)": "torch",
        "WhisperX": "whisperx",
        "Gradio": "gradio",
        "Kokoro": "kokoro",
        "Piper (piper)": "piper"
    }
    
    all_ok = True
    for label, pkg in packages.items():
        if check_package(pkg):
            print(f"[OK] Package '{label}' is installed.")
        else:
            if pkg in ["torch", "whisperx"]:
                print(f"[ERROR] Critical package '{label}' is MISSING!")
                all_ok = False
            else:
                print(f"[WARN] Optional package '{label}' is missing.")
                
    # 3. Hardware / CUDA status
    cuda_status, cuda_available, gpu_name = get_cuda_info()
    if cuda_available:
        print(f"[OK] CUDA status: {cuda_status} ({gpu_name})")
    else:
        print(f"[WARN] CUDA status: {cuda_status}")
        
    # 4. FFmpeg
    if check_ffmpeg():
        print("[OK] FFmpeg found in PATH.")
    else:
        print("[ERROR] FFmpeg NOT found in PATH. Audio conversions (like MP3) will fail!")
        all_ok = False
        
    # 5. eSpeak NG
    # Import setup_espeak locally to avoid dependency loops
    from src.tts.kokoro_engine import setup_espeak
    if setup_espeak():
        espeak_path = os.getenv("PHONEMIZER_ESPEAK_PATH", "System PATH")
        print(f"[OK] eSpeak NG found and configured at: {espeak_path}")
    else:
        print("[WARN] eSpeak NG executable not found in PATH.\n"
              "       Kokoro/Piper may still work if a bundled Python/DLL loader is available.\n"
              "       If synthesis fails with phoneme/phonemizer errors, install eSpeak NG manually.")
        
    # 6. Environment variables (protecting HF_TOKEN)
    print("--------------------------------------------------")
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HF_HUB_TOKEN")
    token_status = "Found (Masked)" if hf_token else "Not found / Not configured"
    print(f"HF_TOKEN:         {token_status}")
    print(f"HF_HOME:          {os.getenv('HF_HOME', 'Default system cache')}")
    
    offline_mode = "Active (HF_HUB_OFFLINE = 1)" if os.getenv("HF_HUB_OFFLINE") == "1" else "Inactive"
    print(f"HF_HUB_OFFLINE:   {offline_mode}")
    
    # 7. Directories checks
    from src.core.paths import TRANSCRIPTIONS_DIR, SPEECH_DIR, VOICES_DIR, MODEL_CACHE_DIR, TTS_CACHE_DIR, TEMP_DIR
    dirs = {
        "Transcriptions Directory": TRANSCRIPTIONS_DIR,
        "Speech Directory": SPEECH_DIR,
        "Voices Directory": VOICES_DIR,
        "Model Cache Directory": MODEL_CACHE_DIR,
        "TTS Cache Directory": TTS_CACHE_DIR,
        "Temp Directory": TEMP_DIR
    }
    
    print("--------------------------------------------------")
    for name, path in dirs.items():
        if os.path.exists(path):
            print(f"[OK] {name} exists at: {path}")
        else:
            try:
                os.makedirs(path, exist_ok=True)
                print(f"[OK] {name} created at: {path}")
            except Exception as e:
                print(f"[ERROR] Failed to create {name} at {path}: {e}")
                all_ok = False
                
    print("==================================================")
    if all_ok:
        print("[STATUS] Healthcheck completed successfully.")
    else:
        print("[STATUS] Healthcheck completed with warnings/errors. See details above.")
    print("==================================================")
    return all_ok
