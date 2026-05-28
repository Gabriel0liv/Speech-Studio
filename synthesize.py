import argparse
import os
import sys
import torch

# Ensure package root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Early healthcheck exit to avoid loading heavy dependencies (like torch, registry, config)
if "--healthcheck" in sys.argv:
    from src.core.healthcheck import run_healthcheck
    success = run_healthcheck()
    sys.exit(0 if success else 1)

import torch
import src.core.config  # Configure HF environment and load .env

from src.core.paths import SPEECH_DIR, TEMP_DIR
from src.core.audio_utils import merge_wav_files
from src.core.ffmpeg_utils import convert_wav_to_mp3
from src.tts.registry import TTSRegistry
from src.tts.text_chunking import chunk_text

def main():
    parser = argparse.ArgumentParser(description="Professional local Text-to-Speech synthesizer.")
    parser.add_argument("--text", type=str, help="Text to synthesize directly.")
    parser.add_argument("--input", type=str, help="Path to a text file to synthesize.")
    parser.add_argument("--engine", type=str, default=None, choices=["kokoro", "piper"], help="TTS engine (default: None, resolves to preset or kokoro).")
    parser.add_argument("--voice", type=str, help="Voice name/alias or path to custom ONNX model (for piper).")
    parser.add_argument("--output", type=str, help="Output audio file path.")
    parser.add_argument("--format", type=str, choices=["wav", "mp3"], help="Output format (wav or mp3). If not specified, inferred from output extension, preset, or defaults to wav.")
    parser.add_argument("--preview", action="store_true", help="Synthesize only a short preview of the text.")
    parser.add_argument("--preview-chars", type=int, help="Number of characters for preview (default: 300).")
    parser.add_argument("--device", type=str, help="Computation device (cpu or cuda).")
    parser.add_argument("--speed", type=float, help="Speech speed multiplier (default: 1.0).")
    parser.add_argument("--preset", type=str, help="Preset name or ID to load default configuration values.")
    parser.add_argument("--no-history", action="store_true", help="Disable job logging in local history database.")
    parser.add_argument("--save-full-text", action="store_true", help="Store full text in history database instead of text snippet.")
    parser.add_argument("--healthcheck", action="store_true", help="Executa o diagnostico do sistema e encerra")
    
    args = parser.parse_args()
    
    # 0. Run healthcheck if requested
    if args.healthcheck:
        from src.core.healthcheck import run_healthcheck
        success = run_healthcheck()
        sys.exit(0 if success else 1)
        
    # Initialize database and seed defaults on launch
    from src.core.database import initialize_database
    initialize_database()
        
    # 0.5. Load Preset values if specified
    preset_data = {}
    if args.preset:
        from src.core.presets import get_tts_preset
        p = get_tts_preset(args.preset)
        if p:
            preset_data = p
            print(f"[*] A carregar preset '{p['name']}' como configuracao base.")
        else:
            print(f"[!] AVISO: Preset '{args.preset}' nao encontrado no banco de dados. Usando defaults.")
            
    # 1. Validate inputs
    if not args.text and not args.input:
        parser.print_help()
        print("\n[!] Erro: Deve fornecer o texto (--text) ou um arquivo de entrada (--input).")
        sys.exit(1)
        
    # 1.5. Resolve parameter priorities: CLI > Preset > Default
    engine_name = args.engine
    if engine_name is None:
        engine_name = preset_data.get("engine")
    if engine_name is None:
        engine_name = "kokoro"
    engine_name = engine_name.lower()
    
    voice = args.voice
    if voice is None:
        voice = preset_data.get("voice")
    if voice is None:
        voice = "pt_br_dora" if engine_name == "kokoro" else "pt_br_lula"
        
    fmt = args.format
    if fmt is None:
        fmt = preset_data.get("output_format")
    if not fmt:
        if args.output:
            _, ext = os.path.splitext(args.output.lower())
            if ext == ".mp3":
                fmt = "mp3"
            else:
                fmt = "wav"
        else:
            fmt = "wav"
            
    speed = args.speed
    if speed is None:
        speed = preset_data.get("speed")
    if speed is None:
        speed = 1.0
    speed = float(speed)
    
    preview_chars = args.preview_chars
    if preview_chars is None:
        preview_chars = preset_data.get("preview_chars")
    if preview_chars is None:
        preview_chars = 300
    preview_chars = int(preview_chars)
    
    device = args.device
    if not device:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
    # Get text content
    if args.text:
        text = args.text
    else:
        if not os.path.exists(args.input):
            print(f"[!] Erro: Arquivo de entrada nao encontrado: {args.input}")
            sys.exit(1)
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            # Fallback to general read if UTF-8 fails
            with open(args.input, "r", encoding="latin-1") as f:
                text = f.read()
                
    text = text.strip()
    if not text:
        print("[!] Erro: O texto de entrada esta vazio.")
        sys.exit(1)
        
    # Slice text for preview if requested
    if args.preview:
        print(f"[*] Modo preview ativo. Limitando texto aos primeiros {preview_chars} caracteres.")
        text = text[:preview_chars]
            
    # Resolve output path
    output_path = args.output
    if not output_path:
        import time
        suffix = "preview" if args.preview else "full"
        output_path = os.path.join(SPEECH_DIR, f"speech_{engine_name}_{suffix}_{int(time.time())}.{fmt}")
        
    # Ensure parent dir exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # 2.5 Validate voice before initializing engine
    try:
        TTSRegistry.validate_voice(engine_name, voice)
    except ValueError as e:
        print(f"\n[!] Erro de validacao de voz:")
        print(f"    {e}")
        sys.exit(1)
        
    # 2.8. Log job in database (wrapped inside history module to never crash)
    job_id = None
    if not args.no_history:
        import json
        from src.core.presets import get_setting
        from src.core.history import create_job
        
        save_full = args.save_full_text or (get_setting("save_full_text_history", "false").lower() == "true")
        snippet = text[:300] + "..." if len(text) > 300 else text
        
        meta = {"preset_used": args.preset, "speed": speed, "preview_mode": args.preview}
        if save_full:
            meta["full_text"] = text
            meta["save_full_text"] = True
            
        input_kind = "text"
        input_path_val = None
        input_name_val = None
        if args.input:
            input_kind = "file"
            input_path_val = os.path.abspath(args.input)
            input_name_val = os.path.basename(args.input)
            
        job_id = create_job(
            job_type="tts",
            input_kind=input_kind,
            input_path=input_path_val,
            input_name=input_name_val,
            text_snippet=snippet,
            output_dir=os.path.dirname(os.path.abspath(output_path)),
            primary_output_path=os.path.abspath(output_path),
            output_format=fmt,
            engine=engine_name,
            voice=voice,
            device=device,
            metadata_json=json.dumps(meta)
        )
        
    # 3. Create engine instance
    print(f"[*] A inicializar motor '{engine_name}' com a voz '{voice}' (velocidade: {speed}) no dispositivo '{device.upper()}'...")
    import time
    start_time = time.time()
    try:
        engine = TTSRegistry.create_engine(engine_name, voice_id=voice, device=device, speed=speed)
    except Exception as e:
        print(f"\n[!] Falha ao carregar o motor '{engine_name}':")
        print(f"    {e}")
        print("\nPara resolver, execute './install_tts.ps1' para instalar os pacotes de TTS,")
        print("e verifique se o 'espeak-ng' esta instalado no sistema.")
        if job_id is not None:
            from src.core.history import update_job_failure
            update_job_failure(job_id, str(e))
        sys.exit(1)
        
    # 4. Synthesize text
    # We split the text into chunks of 400 characters (safe sentence splits)
    # to avoid truncation issues or quality loss in neural generators
    chunks = chunk_text(text, max_chars=400)
    print(f"[*] Texto dividido em {len(chunks)} fragmentos para sintese.")
    
    if len(chunks) == 1:
        # Simple case, single chunk
        print("[*] A sintetizar...")
        try:
            engine.synthesize(chunks[0], output_path, format=fmt)
            print(f"[+] Sintese concluida com sucesso! Arquivo salvo em:\n    {os.path.abspath(output_path)}")
            if job_id is not None:
                from src.core.history import update_job_success
                update_job_success(job_id, duration_seconds=time.time() - start_time)
        except Exception as e:
            print(f"\n[!] Erro durante a sintese:")
            print(f"    {e}")
            if job_id is not None:
                from src.core.history import update_job_failure
                update_job_failure(job_id, str(e))
            sys.exit(1)
    else:
        # Multiple chunks: synthesize each chunk to a temp wav file, then merge
        print("[*] A sintetizar fragmentos sequencialmente...")
        os.makedirs(TEMP_DIR, exist_ok=True)
        chunk_files = []
        try:
            for idx, chunk in enumerate(chunks):
                chunk_file = os.path.join(TEMP_DIR, f"chunk_{idx}_{os.getpid()}.wav")
                print(f"    -> Fragmento {idx + 1}/{len(chunks)} ({len(chunk)} caracteres)...")
                engine.synthesize(chunk, chunk_file, format="wav")
                chunk_files.append(chunk_file)
                
            print("[*] A mesclar fragmentos de audio...")
            # If target format is mp3, we merge to a temp wav first, then convert, to avoid lossy concatenations
            if fmt == "mp3":
                temp_merged_wav = os.path.join(TEMP_DIR, f"merged_temp_{os.getpid()}.wav")
                merge_wav_files(chunk_files, temp_merged_wav)
                print("[*] A converter audio mesclado para MP3...")
                convert_wav_to_mp3(temp_merged_wav, output_path)
                if os.path.exists(temp_merged_wav):
                    os.remove(temp_merged_wav)
            else:
                merge_wav_files(chunk_files, output_path)
                
            print(f"[+] Sintese de multiplos fragmentos concluida com sucesso! Arquivo salvo em:\n    {os.path.abspath(output_path)}")
            if job_id is not None:
                from src.core.history import update_job_success
                update_job_success(job_id, duration_seconds=time.time() - start_time)
            
        except Exception as e:
            print(f"\n[!] Erro durante a sintese em lote:")
            print(f"    {e}")
            if job_id is not None:
                from src.core.history import update_job_failure
                update_job_failure(job_id, str(e))
            sys.exit(1)
        finally:
            # Clean up chunks
            for cf in chunk_files:
                if os.path.exists(cf):
                    try:
                        os.remove(cf)
                    except Exception:
                        pass

if __name__ == "__main__":
    main()
