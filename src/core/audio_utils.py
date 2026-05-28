import os
import numpy as np
import soundfile as sf

def merge_wav_files(wav_paths, output_path):
    """
    Concatenate multiple WAV files sequentially into a single WAV file.
    """
    if not wav_paths:
        return
        
    all_data = []
    target_sr = None
    
    for path in wav_paths:
        if not os.path.exists(path):
            continue
        data, sr = sf.read(path)
        if target_sr is None:
            target_sr = sr
        elif sr != target_sr:
            # Simple sample rate sanity check (raise exception if mismatched)
            raise ValueError(f"Frequência de amostragem incompatível em {path}: {sr}Hz (esperado {target_sr}Hz)")
        all_data.append(data)
        
    if not all_data:
        raise ValueError("Nenhum arquivo de áudio válido foi fornecido para mesclagem.")
        
    merged_data = np.concatenate(all_data, axis=0)
    sf.write(output_path, merged_data, target_sr)
    return output_path
