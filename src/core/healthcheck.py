import sys
import os
import importlib.util
import shutil
from typing import Any, Dict, List

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

def check_espeak() -> Dict[str, Any]:
    """Lightweight eSpeak NG detection without importing TTS engines."""
    configured = os.getenv("PHONEMIZER_ESPEAK_PATH")
    if configured:
        return {"available": True, "path": configured, "source": "env"}

    binary = shutil.which("espeak-ng") or shutil.which("espeak")
    if binary:
        return {"available": True, "path": binary, "source": "path"}

    common_paths = [
        r"C:\Program Files\eSpeak NG",
        r"C:\Program Files (x86)\eSpeak NG",
        r"C:\Program Files\eSpeak",
        r"C:\Program Files (x86)\eSpeak",
    ]
    for path in common_paths:
        if os.path.exists(os.path.join(path, "espeak-ng.exe")) or os.path.exists(os.path.join(path, "espeak.exe")):
            return {"available": True, "path": path, "source": "common_path"}

    return {"available": False, "path": None, "source": None}

def run_healthcheck_structured() -> Dict[str, Any]:
    """Return structured lightweight health data for API consumers."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    packages: List[Dict[str, Any]] = []
    package_map = {
        "PyTorch (torch)": ("torch", True),
        "WhisperX": ("whisperx", True),
        "Gradio": ("gradio", False),
        "Kokoro": ("kokoro", False),
        "Piper (piper)": ("piper", False),
    }

    all_ok = True
    for label, (pkg, critical) in package_map.items():
        installed = check_package(pkg)
        if critical and not installed:
            all_ok = False
        packages.append({
            "label": label,
            "package": pkg,
            "installed": installed,
            "critical": critical,
            "status": "ok" if installed else ("error" if critical else "warning"),
        })

    cuda_status, cuda_available, gpu_name = get_cuda_info()
    ffmpeg_available = check_ffmpeg()
    if not ffmpeg_available:
        all_ok = False

    espeak = check_espeak()
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HF_HUB_TOKEN")
    hf_home = os.getenv("HF_HOME", "Default system cache")
    offline_mode = os.getenv("HF_HUB_OFFLINE") == "1"

    from src.core.paths import TRANSCRIPTIONS_DIR, SPEECH_DIR, VOICES_DIR, MODEL_CACHE_DIR, TTS_CACHE_DIR, TEMP_DIR
    directories = []
    for name, path in {
        "Transcriptions Directory": TRANSCRIPTIONS_DIR,
        "Speech Directory": SPEECH_DIR,
        "Voices Directory": VOICES_DIR,
        "Model Cache Directory": MODEL_CACHE_DIR,
        "TTS Cache Directory": TTS_CACHE_DIR,
        "Temp Directory": TEMP_DIR,
    }.items():
        exists = os.path.exists(path)
        directories.append({"name": name, "path": path, "exists": exists, "status": "ok" if exists else "warning"})

    return {
        "success": all_ok,
        "python_version": sys.version.split()[0],
        "project_root": project_root,
        "packages": packages,
        "cuda": {
            "status": cuda_status,
            "available": cuda_available,
            "gpu_name": gpu_name,
        },
        "ffmpeg": {"available": ffmpeg_available},
        "espeak": espeak,
        "huggingface": {
            "token_configured": bool(hf_token),
            "token_status": "Found (Masked)" if hf_token else "Not found / Not configured",
            "hf_home": hf_home,
            "offline_mode": offline_mode,
        },
        "directories": directories,
    }

def run_healthcheck() -> bool:
    """Runs a complete environment diagnostics check."""
    health = run_healthcheck_structured()
    print("==================================================")
    print("           SPEECH STUDIO HEALTHCHECK              ")
    print("==================================================")
    
    # 1. Python version and project root
    print(f"Python Version: {health['python_version']}")
    print(f"Project Root:   {health['project_root']}")
    print("--------------------------------------------------")
    
    # 2. Package import checks
    all_ok = health["success"]
    for package in health["packages"]:
        label = package["label"]
        if package["installed"]:
            print(f"[OK] Package '{label}' is installed.")
        elif package["critical"]:
            print(f"[ERROR] Critical package '{label}' is MISSING!")
        else:
            print(f"[WARN] Optional package '{label}' is missing.")
                
    # 3. Hardware / CUDA status
    cuda = health["cuda"]
    if cuda["available"]:
        print(f"[OK] CUDA status: {cuda['status']} ({cuda['gpu_name']})")
    else:
        print(f"[WARN] CUDA status: {cuda['status']}")
        
    # 4. FFmpeg
    if health["ffmpeg"]["available"]:
        print("[OK] FFmpeg found in PATH.")
    else:
        print("[ERROR] FFmpeg NOT found in PATH. Audio conversions (like MP3) will fail!")
        
    # 5. eSpeak NG
    if health["espeak"]["available"]:
        print(f"[OK] eSpeak NG found and configured at: {health['espeak']['path'] or 'System PATH'}")
    else:
        print("[WARN] eSpeak NG executable not found in PATH.\n"
              "       Kokoro/Piper may still work if a bundled Python/DLL loader is available.\n"
              "       If synthesis fails with phoneme/phonemizer errors, install eSpeak NG manually.")
        
    # 6. Environment variables (protecting HF_TOKEN)
    print("--------------------------------------------------")
    print(f"HF_TOKEN:         {health['huggingface']['token_status']}")
    print(f"HF_HOME:          {health['huggingface']['hf_home']}")
    
    offline_mode = "Active (HF_HUB_OFFLINE = 1)" if health["huggingface"]["offline_mode"] else "Inactive"
    print(f"HF_HUB_OFFLINE:   {offline_mode}")
    
    # 7. Directories checks
    print("--------------------------------------------------")
    for directory in health["directories"]:
        if directory["exists"]:
            print(f"[OK] {directory['name']} exists at: {directory['path']}")
        else:
            try:
                os.makedirs(directory["path"], exist_ok=True)
                print(f"[OK] {directory['name']} created at: {directory['path']}")
            except Exception as e:
                print(f"[ERROR] Failed to create {directory['name']} at {directory['path']}: {e}")
                all_ok = False
                
    print("==================================================")
    if all_ok:
        print("[STATUS] Healthcheck completed successfully.")
    else:
        print("[STATUS] Healthcheck completed with warnings/errors. See details above.")
    print("==================================================")
    return all_ok
