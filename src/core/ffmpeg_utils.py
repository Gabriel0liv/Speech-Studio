import subprocess
import shutil

def check_ffmpeg() -> bool:
    """Verify that FFmpeg is installed and accessible in the system path."""
    try:
        # Run ffmpeg -version with subprocess to check binary health
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def convert_wav_to_mp3(wav_path: str, mp3_path: str) -> str:
    """
    Convert a WAV audio file to MP3 format using FFmpeg.
    """
    if not check_ffmpeg():
        raise RuntimeError("FFmpeg não foi encontrado no PATH do sistema. A conversão para MP3 não é possível.")
        
    cmd = [
        "ffmpeg", "-y",
        "-i", wav_path,
        "-codec:a", "libmp3lame",
        "-qscale:a", "2",  # Variable Bit Rate (VBR), high quality (~190 kbps)
        mp3_path
    ]
    
    try:
        # Execute quiet conversion
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return mp3_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"A conversão do FFmpeg falhou:\n{e.stderr}")
