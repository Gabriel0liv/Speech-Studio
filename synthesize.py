import argparse
import os
import sys
import warnings

# Suppress known-harmless third-party warnings before any heavy imports
warnings.filterwarnings("ignore", message=".*dropout option.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*weight_norm.*", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*Defaulting repo_id.*", category=UserWarning)

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


# ---------------------------------------------------------------------------
# Default comparison phrase for --compare-voices
# ---------------------------------------------------------------------------
_COMPARE_DEFAULT_TEXT = (
    "Olá! Tudo bem? Hoje eu vou te mostrar como transformar texto em áudio "
    "com uma voz brasileira mais natural. A ideia é testar ritmo, entonação, "
    "pausas e pronúncia de palavras comuns do português do Brasil."
)

# PT-BR voices to include in comparison (alias -> output filename stem)
_PTBR_COMPARE_VOICES = [
    ("kokoro", "pt_br_dora",     "kokoro_dora"),
    ("kokoro", "pt_br_alex",     "kokoro_alex"),
    ("kokoro", "pt_br_santa",    "kokoro_santa"),
    ("piper",  "pt_br_faber",    "piper_faber"),
    ("piper",  "pt_br_edresson", "piper_edresson"),
]


def _suppress_warnings_if_not_verbose(verbose: bool):
    """Suppress known harmless warnings unless --verbose is set."""
    if not verbose:
        warnings.filterwarnings("ignore", message=".*dropout option.*", category=UserWarning)
        warnings.filterwarnings("ignore", message=".*weight_norm.*", category=FutureWarning)
        warnings.filterwarnings("ignore", message=".*Defaulting repo_id.*", category=UserWarning)
        warnings.filterwarnings("ignore", message=".*CUDAExecutionProvider.*", category=UserWarning)
        warnings.filterwarnings("ignore", message=".*Missing phoneme.*")


def _synthesize_single(engine_name, voice, text, output_path, fmt, device, speed, verbose=False):
    """
    Synthesize text using the given engine+voice. Returns (success, duration_or_error).
    Does not call sys.exit(); always returns.
    """
    import time
    try:
        TTSRegistry.validate_voice(engine_name, voice)
    except ValueError as e:
        return False, str(e)

    start = time.time()
    try:
        engine = TTSRegistry.create_engine(engine_name, voice_id=voice, device=device, speed=speed)
        chunks = chunk_text(text, max_chars=400)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if len(chunks) == 1:
            engine.synthesize(chunks[0], output_path, format=fmt)
        else:
            os.makedirs(TEMP_DIR, exist_ok=True)
            chunk_files = []
            try:
                for idx, chunk in enumerate(chunks):
                    cf = os.path.join(TEMP_DIR, f"chunk_{idx}_{os.getpid()}.wav")
                    engine.synthesize(chunk, cf, format="wav")
                    chunk_files.append(cf)
                if fmt == "mp3":
                    merged = os.path.join(TEMP_DIR, f"merged_{os.getpid()}.wav")
                    merge_wav_files(chunk_files, merged)
                    convert_wav_to_mp3(merged, output_path)
                    os.remove(merged)
                else:
                    merge_wav_files(chunk_files, output_path)
            finally:
                for cf in chunk_files:
                    if os.path.exists(cf):
                        try:
                            os.remove(cf)
                        except Exception:
                            pass
        return True, time.time() - start
    except Exception as e:
        return False, str(e)


def run_compare_voices(text: str, output_dir: str, device: str, verbose: bool = False):
    """
    Run synthesis for all PT-BR voices, saving WAVs and a compare report.
    Continues even if individual voices fail.
    """
    import json
    import time

    os.makedirs(output_dir, exist_ok=True)
    _suppress_warnings_if_not_verbose(verbose)

    results = []
    print(f"\n[*] Iniciando comparativo de vozes PT-BR...")
    print(f"    Texto: {text[:80]}{'...' if len(text) > 80 else ''}")
    print(f"    Pasta de saida: {os.path.abspath(output_dir)}\n")

    for engine_name, voice_alias, filename_stem in _PTBR_COMPARE_VOICES:
        output_path = os.path.join(output_dir, f"{filename_stem}.wav")
        from src.tts.registry import VOICE_MAPPING
        resolved_id = VOICE_MAPPING.get(engine_name, {}).get(voice_alias, {}).get("id", voice_alias)

        print(f"  -> {filename_stem} ({engine_name}/{voice_alias})...", end=" ", flush=True)
        success, result = _synthesize_single(engine_name, voice_alias, text, output_path, "wav", device, 1.0, verbose)

        if success:
            print(f"OK ({result:.1f}s)")
            results.append({
                "voice_alias": voice_alias,
                "engine": engine_name,
                "resolved_voice_id": resolved_id,
                "status": "success",
                "output_path": os.path.abspath(output_path),
                "error": None,
                "duration_seconds": round(result, 2)
            })
        else:
            print(f"FALHOU")
            if verbose:
                print(f"     Erro: {result}")
            results.append({
                "voice_alias": voice_alias,
                "engine": engine_name,
                "resolved_voice_id": resolved_id,
                "status": "failed",
                "output_path": None,
                "error": str(result),
                "duration_seconds": None
            })

    # Write JSON report
    report_json = os.path.join(output_dir, "compare_report.json")
    with open(report_json, "w", encoding="utf-8") as f:
        json.dump({"text": text, "results": results}, f, ensure_ascii=False, indent=2)

    # Write Markdown report
    report_md = os.path.join(output_dir, "compare_report.md")
    with open(report_md, "w", encoding="utf-8") as f:
        f.write("# Comparativo de Vozes PT-BR\n\n")
        f.write(f"**Texto usado:**\n> {text}\n\n")
        f.write("| Voz | Motor | Status | Duração (s) | Arquivo |\n")
        f.write("|-----|-------|--------|-------------|--------|\n")
        for r in results:
            status_icon = "✅" if r["status"] == "success" else "❌"
            dur = f"{r['duration_seconds']}s" if r["duration_seconds"] else "—"
            path = os.path.basename(r["output_path"]) if r["output_path"] else r["error"]
            f.write(f"| {r['voice_alias']} | {r['engine'].upper()} | {status_icon} {r['status']} | {dur} | {path} |\n")

    successes = sum(1 for r in results if r["status"] == "success")
    print(f"\n[+] Comparativo concluido: {successes}/{len(results)} vozes geradas com sucesso.")
    print(f"    Relatorio JSON: {os.path.abspath(report_json)}")
    print(f"    Relatorio MD:   {os.path.abspath(report_md)}\n")
    return results


def main():
    parser = argparse.ArgumentParser(description="Professional local Text-to-Speech synthesizer.")
    parser.add_argument("--text", type=str, help="Text to synthesize directly.")
    parser.add_argument("--input", type=str, help="Path to a text file to synthesize.")
    parser.add_argument("--engine", type=str, default=None, choices=["kokoro", "piper"], help="TTS engine (default: None, resolves to preset or kokoro).")
    parser.add_argument("--voice", type=str, help="Voice name/alias or path to custom ONNX model (for piper).")
    parser.add_argument("--output", type=str, help="Output audio file path.")
    parser.add_argument("--output-dir", type=str, help="Output directory (used with --compare-voices).", dest="output_dir")
    parser.add_argument("--format", type=str, choices=["wav", "mp3"], help="Output format (wav or mp3).")
    parser.add_argument("--language", type=str, help="Language hint, e.g. pt-br (informational, used with --compare-voices).")
    parser.add_argument("--preview", action="store_true", help="Synthesize only a short preview of the text.")
    parser.add_argument("--preview-chars", type=int, help="Number of characters for preview (default: 300).")
    parser.add_argument("--device", type=str, help="Computation device (cpu or cuda).")
    parser.add_argument("--speed", type=float, help="Speech speed multiplier (default: 1.0).")
    parser.add_argument("--preset", type=str, help="Preset name, alias, or ID to load default configuration values.")
    parser.add_argument("--no-history", action="store_true", help="Disable job logging in local history database.")
    parser.add_argument("--save-full-text", action="store_true", help="Store full text in history database instead of text snippet.")
    parser.add_argument("--analyze-ptbr", action="store_true", help="Analyze input text for common PT-BR accent/quality issues.")
    parser.add_argument("--normalize-ptbr", action="store_true", help="Apply conservative PT-BR accent normalization before synthesis.")
    parser.add_argument("--compare-voices", action="store_true", help="Generate audio with all available PT-BR voices for comparison.")
    parser.add_argument("--verbose", action="store_true", help="Show detailed debug output including suppressed warnings.")
    parser.add_argument("--healthcheck", action="store_true", help="Executa o diagnostico do sistema e encerra.")

    args = parser.parse_args()

    # Suppress warnings unless --verbose
    _suppress_warnings_if_not_verbose(args.verbose)

    # 0. Healthcheck mode
    if args.healthcheck:
        from src.core.healthcheck import run_healthcheck
        success = run_healthcheck()
        sys.exit(0 if success else 1)

    # Initialize database and seed defaults on launch
    from src.core.database import initialize_database
    initialize_database()

    # -----------------------------------------------------------------
    # COMPARE-VOICES mode (special early path)
    # -----------------------------------------------------------------
    if args.compare_voices:
        text = args.text or _COMPARE_DEFAULT_TEXT
        if args.input and not args.text:
            try:
                with open(args.input, "r", encoding="utf-8") as f:
                    text = f.read().strip() or text
            except Exception:
                pass

        if args.normalize_ptbr:
            from src.tts.ptbr_text import normalize_basic_ptbr_text
            text = normalize_basic_ptbr_text(text)
            print("[*] Normalizacao PT-BR aplicada.")

        if args.analyze_ptbr:
            from src.tts.ptbr_text import analyze_ptbr_text, print_analysis_report
            analysis = analyze_ptbr_text(text)
            print_analysis_report(analysis, verbose=args.verbose)

        output_dir = args.output_dir or os.path.join("outputs", "speech", "voice_compare")
        device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
        run_compare_voices(text, output_dir, device, verbose=args.verbose)
        sys.exit(0)

    # -----------------------------------------------------------------
    # ANALYZE-ONLY mode (no synthesis args required)
    # -----------------------------------------------------------------
    if args.analyze_ptbr and not args.text and not args.input:
        print("[!] Erro: --analyze-ptbr requer --text ou --input.")
        sys.exit(1)

    # 0.5. Load Preset values if specified
    preset_data = {}
    preset_resolved_name = None
    if args.preset:
        from src.core.presets import get_tts_preset
        p = get_tts_preset(args.preset)
        if p:
            preset_data = p
            preset_resolved_name = p["name"]
            print(f"[*] A carregar preset '{p['name']}' como configuracao base.")
        else:
            print(f"[!] AVISO: Preset '{args.preset}' nao encontrado. Usando defaults.")

    # 1. Validate inputs
    if not args.text and not args.input:
        if args.analyze_ptbr:
            parser.print_help()
            print("\n[!] Erro: Deve fornecer o texto (--text) ou um arquivo de entrada (--input).")
            sys.exit(1)
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
        voice = "pt_br_dora" if engine_name == "kokoro" else "pt_br_faber"

    fmt = args.format
    if fmt is None:
        fmt = preset_data.get("output_format")
    if not fmt:
        if args.output:
            _, ext = os.path.splitext(args.output.lower())
            fmt = "mp3" if ext == ".mp3" else "wav"
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
            with open(args.input, "r", encoding="latin-1") as f:
                text = f.read()

    text = text.strip()
    if not text:
        print("[!] Erro: O texto de entrada esta vazio.")
        sys.exit(1)

    # PT-BR Analysis (always runs before normalization/synthesis)
    if args.analyze_ptbr:
        from src.tts.ptbr_text import analyze_ptbr_text, print_analysis_report
        analysis = analyze_ptbr_text(text)
        print_analysis_report(analysis, verbose=args.verbose)

    # PT-BR Normalization
    if args.normalize_ptbr:
        from src.tts.ptbr_text import normalize_basic_ptbr_text
        original_text = text
        text = normalize_basic_ptbr_text(text)
        if text != original_text:
            print("[*] Normalizacao PT-BR aplicada.")
        else:
            print("[*] Normalizacao PT-BR: nenhuma substituicao necessaria.")

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

    # 2.8. Log job in database
    job_id = None
    if not args.no_history:
        import json
        from src.core.presets import get_setting
        from src.core.history import create_job

        save_full = args.save_full_text or (get_setting("save_full_text_history", "false").lower() == "true")
        snippet = text[:300] + "..." if len(text) > 300 else text

        meta = {
            "preset_used": preset_resolved_name,
            "preset_requested": args.preset,
            "speed": speed,
            "preview_mode": args.preview,
            "normalized_ptbr": args.normalize_ptbr,
        }
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
    chunks = chunk_text(text, max_chars=400)
    print(f"[*] Texto dividido em {len(chunks)} fragmentos para sintese.")

    if len(chunks) == 1:
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
            for cf in chunk_files:
                if os.path.exists(cf):
                    try:
                        os.remove(cf)
                    except Exception:
                        pass


if __name__ == "__main__":
    main()
