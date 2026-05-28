#!/usr/bin/env python3
import os
import sys
import warnings
import logging

# Suppress warnings from torch, pyannote, lightning, huggingface_hub, etc.
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*symlinks.*")
warnings.filterwarnings("ignore", message=".*torchcodec.*")
warnings.filterwarnings("ignore", message=".*TensorFloat-32.*")

# Suppress noisy lightning logger outputs early
logging.getLogger("pytorch_lightning").setLevel(logging.ERROR)
logging.getLogger("lightning.pytorch").setLevel(logging.ERROR)
logging.getLogger("lightning.pytorch.utilities.migration.utils").setLevel(logging.ERROR)
logging.getLogger("pytorch_lightning.utilities.migration.utils").setLevel(logging.ERROR)
logging.getLogger("lightning.pytorch.utilities.migration").setLevel(logging.ERROR)
logging.getLogger("pytorch_lightning.utilities.migration").setLevel(logging.ERROR)

from dotenv import load_dotenv

# 1. Load environment variables from .env if present
load_dotenv()


# 2. Early parsing of HF cache and offline parameters before importing ML libraries
early_cache_dir = None
early_offline = False
for i, arg in enumerate(sys.argv):
    if arg == "--cache-dir" and i + 1 < len(sys.argv):
        early_cache_dir = sys.argv[i + 1]
    elif arg.startswith("--cache-dir="):
        early_cache_dir = arg.split("=", 1)[1]
    elif arg == "--offline":
        early_offline = True

# 3. Configure Hugging Face home & cache directories (priority: CLI arg > .env > default)
hf_home = early_cache_dir or os.getenv("HF_HOME")
if hf_home:
    hf_home = hf_home.replace("\\", "/")
    try:
        os.makedirs(hf_home, exist_ok=True)
    except Exception:
        pass
    os.environ["HF_HOME"] = hf_home
    os.environ["HF_HUB_CACHE"] = os.path.join(hf_home, "hub").replace("\\", "/")

# 4. Configure Hugging Face Hub offline mode
if early_offline or os.getenv("HF_HUB_OFFLINE") == "1":
    os.environ["HF_HUB_OFFLINE"] = "1"

# 5. Standard library imports
import subprocess
import json
import time
import argparse
import shutil

def check_ffmpeg():
    """Verify that FFmpeg is installed and accessible in the system path."""
    try:
        # Run ffmpeg -version
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n[!] ERRO: FFmpeg não foi encontrado.", file=sys.stderr)
        print("    Para processar vídeos e formatos variados de áudio, o FFmpeg é necessário.", file=sys.stderr)
        print("    Por favor, instale o FFmpeg e adicione a pasta 'bin' dele ao PATH do seu sistema.", file=sys.stderr)
        return False

def convert_to_wav(input_path, temp_dir):
    """
    Convert any input audio/video file to 16kHz mono PCM 16-bit WAV.
    Whisper and Pyannote operate best on this format.
    """
    os.makedirs(temp_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    temp_wav = os.path.join(temp_dir, f"{base_name}_temp_{int(time.time())}.wav")
    
    print(f"[*] A extrair/converter áudio de '{os.path.basename(input_path)}'...")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vn",                   # Disable video recording
        "-acodec", "pcm_s16le",   # PCM 16-bit
        "-ar", "16000",          # 16kHz sampling rate
        "-ac", "1",              # 1 channel (mono)
        temp_wav
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return temp_wav
    except subprocess.CalledProcessError as e:
        print(f"[!] ERRO: Falha na conversão de áudio com o FFmpeg:\n{e.stderr}", file=sys.stderr)
        return None

def format_timestamp(seconds, include_ms=True, ms_separator=","):
    """Convert float seconds into HH:MM:SS,mmm or HH:MM:SS.mmm format."""
    if seconds is None:
        seconds = 0.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if include_ms:
        milliseconds = int(round((seconds - int(seconds)) * 1000))
        if milliseconds >= 1000:
            milliseconds -= 1000
            secs += 1
            if secs >= 60:
                secs -= 60
                minutes += 1
                if minutes >= 60:
                    minutes -= 60
                    hours += 1
        return f"{hours:02d}:{minutes:02d}:{secs:02d}{ms_separator}{milliseconds:03d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def format_words_into_lines(words_list, max_chars=42):
    """Greedily wrap list of words into lines of max_chars character length."""
    lines = []
    current_line = []
    current_length = 0
    
    for word in words_list:
        added_length = len(word) + (1 if current_line else 0)
        if current_length + added_length <= max_chars:
            current_line.append(word)
            current_length += added_length
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
            
    if current_line:
        lines.append(" ".join(current_line))
        
    return lines

def group_words_into_cards(words, max_lines=2, max_chars=42, min_duration=1.0, max_duration=6.0):
    """
    Group words with timestamps into subtitle cards adhering to:
    - Max lines: 2
    - Max chars per line: 42
    - Min duration: 1.0s
    - Max duration: 6.0s
    - Split immediately on speaker change or silence gap (> 1.5s)
    """
    cards = []
    current_card_words = []
    
    for word_info in words:
        word_text = word_info.get("word", "").strip()
        if not word_text:
            continue
            
        start = word_info.get("start")
        end = word_info.get("end")
        speaker = word_info.get("speaker", "UNKNOWN")
        
        # Initialize first word in card
        if not current_card_words:
            if start is None:
                start = 0.0
            if end is None:
                end = start + 0.5
            current_card_words.append({
                "word": word_text,
                "start": start,
                "end": end,
                "speaker": speaker
            })
            continue
            
        card_start = current_card_words[0]["start"]
        card_speaker = current_card_words[0]["speaker"]
        
        split_reason = None
        
        # Check speaker transition
        if speaker != card_speaker:
            split_reason = "speaker_change"
            
        # Check silence gap
        elif start is not None and (start - current_card_words[-1]["end"]) > 1.5:
            split_reason = "silence_gap"
            
        # Check maximum card duration
        elif end is not None and (end - card_start) > max_duration:
            split_reason = "max_duration"
            
        # Check text length / lines wrap constraint
        if not split_reason:
            temp_words = current_card_words + [{
                "word": word_text,
                "start": start or current_card_words[-1]["end"],
                "end": end or (start or current_card_words[-1]["end"]) + 0.5,
                "speaker": speaker
            }]
            lines = format_words_into_lines([w["word"] for w in temp_words], max_chars)
            if len(lines) > max_lines:
                split_reason = "max_lines"
            elif any(len(line) > max_chars for line in lines):
                split_reason = "max_chars"
                
        # Split card if required
        if split_reason:
            card_text_lines = format_words_into_lines([w["word"] for w in current_card_words], max_chars)
            card_end = current_card_words[-1]["end"]
            
            # Enforce min_duration
            card_dur = card_end - card_start
            if card_dur < min_duration:
                max_extend = start if start is not None else card_start + min_duration
                card_end = min(card_start + min_duration, max_extend)
                
            cards.append({
                "start": card_start,
                "end": card_end,
                "speaker": card_speaker,
                "lines": card_text_lines
            })
            
            # Start new card with current word
            if start is None:
                start = card_end
            if end is None:
                end = start + 0.5
            current_card_words = [{
                "word": word_text,
                "start": start,
                "end": end,
                "speaker": speaker
            }]
        else:
            # Accumulate word in current card
            if start is None:
                start = current_card_words[-1]["end"]
            if end is None:
                end = start + 0.5
            current_card_words.append({
                "word": word_text,
                "start": start,
                "end": end,
                "speaker": speaker
            })
            
    # Add final card
    if current_card_words:
        card_start = current_card_words[0]["start"]
        card_speaker = current_card_words[0]["speaker"]
        card_end = current_card_words[-1]["end"]
        card_dur = card_end - card_start
        if card_dur < min_duration:
            card_end = card_start + min_duration
            
        card_text_lines = format_words_into_lines([w["word"] for w in current_card_words], max_chars)
        cards.append({
            "start": card_start,
            "end": card_end,
            "speaker": card_speaker,
            "lines": card_text_lines
        })
        
    return cards

def split_segment_without_words(segment_text, start_time, end_time, speaker="UNKNOWN", max_chars=42, max_lines=2, min_duration=1.0, max_duration=6.0):
    """
    Split a segment containing text but no word-level timestamps (fallback).
    Distributes time proportionally based on character length.
    """
    lines = format_words_into_lines(segment_text.split(), max_chars)
    total_dur = end_time - start_time
    
    if len(lines) <= max_lines and total_dur <= max_duration:
        if total_dur < min_duration:
            end_time = start_time + min_duration
        return [{
            "start": start_time,
            "end": end_time,
            "speaker": speaker,
            "lines": lines
        }]
        
    words_list = segment_text.split()
    total_chars = sum(len(w) for w in words_list)
    if total_chars == 0:
        return []
        
    simulated_words = []
    current_time = start_time
    for w in words_list:
        w_len = len(w)
        w_dur = total_dur * (w_len / total_chars)
        simulated_words.append({
            "word": w,
            "start": current_time,
            "end": current_time + w_dur,
            "speaker": speaker
        })
        current_time += w_dur
        
    return group_words_into_cards(simulated_words, max_lines, max_chars, min_duration, max_duration)

def format_card_for_subtitle(card, speaker_map=None, show_speaker=True):
    """Format subtitle lines, prepending speaker if configured and mapping name."""
    speaker = card.get("speaker")
    lines = card.get("lines", [])
    
    if not lines:
        return ""
        
    speaker_name = None
    if show_speaker and speaker and speaker != "UNKNOWN":
        if speaker_map:
            speaker_name = speaker_map.get(speaker, speaker)
        else:
            speaker_name = speaker
            
    if speaker_name:
        combined_text = f"{speaker_name}: " + " ".join(lines)
        formatted_lines = format_words_into_lines(combined_text.split(), max_chars=42)
        return "\n".join(formatted_lines[:2])
    else:
        return "\n".join(lines)

def export_txt(segments, file_path, speaker_map=None):
    """Export dialogue-grouped script style text file."""
    with open(file_path, "w", encoding="utf-8") as f:
        current_speaker = None
        current_block = []
        block_start = None
        
        for seg in segments:
            speaker = seg.get("speaker", "UNKNOWN")
            text = seg.get("text", "").strip()
            if not text:
                continue
                
            start = seg.get("start", 0.0)
            speaker_name = speaker
            if speaker_map and speaker in speaker_map:
                speaker_name = speaker_map[speaker]
                
            if current_speaker is None:
                current_speaker = speaker_name
                block_start = start
                current_block.append(text)
            elif speaker_name == current_speaker:
                current_block.append(text)
            else:
                timestamp = format_timestamp(block_start, include_ms=False)
                f.write(f"[{timestamp}] {current_speaker}:\n")
                f.write(" ".join(current_block) + "\n\n")
                
                current_speaker = speaker_name
                block_start = start
                current_block = [text]
                
        if current_block:
            timestamp = format_timestamp(block_start, include_ms=False)
            f.write(f"[{timestamp}] {current_speaker}:\n")
            f.write(" ".join(current_block) + "\n")

def export_srt(cards, file_path, speaker_map=None, show_speaker=True):
    """Export standard SubRip (.srt) subtitle file."""
    with open(file_path, "w", encoding="utf-8") as f:
        for idx, card in enumerate(cards, 1):
            start_str = format_timestamp(card["start"], include_ms=True, ms_separator=",")
            end_str = format_timestamp(card["end"], include_ms=True, ms_separator=",")
            text = format_card_for_subtitle(card, speaker_map, show_speaker)
            
            f.write(f"{idx}\n")
            f.write(f"{start_str} --> {end_str}\n")
            f.write(f"{text}\n\n")

def export_vtt(cards, file_path, speaker_map=None, show_speaker=True):
    """Export standard WebVTT (.vtt) subtitle file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for card in cards:
            start_str = format_timestamp(card["start"], include_ms=True, ms_separator=".")
            end_str = format_timestamp(card["end"], include_ms=True, ms_separator=".")
            text = format_card_for_subtitle(card, speaker_map, show_speaker)
            
            f.write(f"{start_str} --> {end_str}\n")
            f.write(f"{text}\n\n")

def export_json(result, file_path):
    """Export raw output dictionary to JSON."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

def process_file(file_path, args, speaker_map):
    """Transcribe, align, and diarize a single file."""
    print(f"\n" + "="*80)
    print(f"[*] A PROCESSAR: {file_path}")
    print("="*80)
    
    # Establish device
    device = args.device
    if device == "auto":
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Dispositivo de execução: {device.upper()}")
    
    # Initialize DB log entry
    job_id = None
    if not getattr(args, "no_history", False):
        try:
            from src.core.presets import get_setting
            from src.core.history import create_job
            import json
            
            if get_setting("history_enabled", "true").lower() == "true":
                input_kind = "file"
                input_path_val = os.path.abspath(file_path)
                input_name_val = os.path.basename(file_path)
                
                meta = {
                    "model": args.model,
                    "device": device,
                    "compute_type": args.compute_type,
                    "no_diarization": args.no_diarization,
                    "vad_onset": args.vad_onset,
                    "vad_offset": args.vad_offset,
                    "speaker_profile_used": getattr(args, "speaker_profile", None)
                }
                
                if args.input_path and os.path.isdir(args.input_path):
                    meta["source_folder"] = os.path.abspath(args.input_path)
                    meta["recursive"] = getattr(args, "recursive", False)
                    
                job_id = create_job(
                    job_type="stt",
                    input_kind=input_kind,
                    input_path=input_path_val,
                    input_name=input_name_val,
                    output_dir=os.path.abspath(args.output_dir),
                    engine="whisperx",
                    model=args.model,
                    language=args.language,
                    device=device,
                    metadata_json=json.dumps(meta)
                )
        except Exception as e:
            print(f"[WARN] Falha ao criar entrada no historico: {e}")

    temp_dir = "temp"
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    import time
    file_start_time = time.time()
    result_status = "failed"
    
    # Convert file to WAV
    audio_wav = convert_to_wav(file_path, temp_dir)
    if not audio_wav:
        print(f"[!] ERRO: Não foi possível obter o áudio de {file_path}. A saltar...")
        result_status = "failed"
        return "failed"
        
    try:
        import whisperx
        import warnings
        import logging
        warnings.filterwarnings("ignore")
        
        # Suppress noisy logger outputs from lightning and pyannote dynamically
        for name in list(logging.root.manager.loggerDict.keys()):
            if any(substring in name.lower() for substring in ["lightning", "pyannote", "pytorch"]):
                logging.getLogger(name).setLevel(logging.ERROR)
        
        # 1. Transcribe
        print(f"[*] A carregar modelo Whisper ({args.model})...")
        asr_options = {}
        if getattr(args, "initial_prompt", None):
            asr_options["initial_prompt"] = args.initial_prompt
            
        # Configure VAD options for speech sensitivity
        vad_options = {
            "vad_onset": args.vad_onset,
            "vad_offset": args.vad_offset,
            "chunk_size": args.chunk_size
        }
        
        try:
            model = whisperx.load_model(
                args.model,
                device,
                compute_type=args.compute_type,
                asr_options=asr_options,
                vad_options=vad_options
            )
        except Exception as e:
            err_msg = str(e)
            err_type = type(e).__name__.lower()
            if "localentrynotfound" in err_type or "offlinemodeisenabled" in err_type or "offline" in err_msg.lower() or os.environ.get("HF_HUB_OFFLINE") == "1":
                print(f"[!] ERRO: Modelo Whisper '{args.model}' não encontrado no cache e HF_HUB_OFFLINE=1 está ativo.", file=sys.stderr)
                print("    Por favor, desative o modo offline uma vez para permitir o download do modelo.", file=sys.stderr)
            elif "connection" in err_msg.lower() or "timeout" in err_msg.lower() or "reach" in err_msg.lower():
                print(f"[!] ERRO: Não foi possível ligar ao Hugging Face para transferir o modelo Whisper '{args.model}'.", file=sys.stderr)
                print("    Verifique a sua ligação à Internet ou use --offline se o modelo já estiver no cache.", file=sys.stderr)
            else:
                print(f"[!] ERRO ao carregar o modelo Whisper: {e}", file=sys.stderr)
            result_status = "failed"
            return "failed"
        
        print("[*] A transcrever...")
        transcription = model.transcribe(audio_wav, batch_size=args.batch_size, language=args.language)
        
        # Free Whisper GPU memory immediately to make space for alignment / diarization
        del model
        import gc
        if device == "cuda":
            import torch
            torch.cuda.empty_cache()
        gc.collect()
        
        if not transcription.get("segments"):
            print(f"[WARN] Nenhuma fala detectada em {file_path}")
            result_status = "no_speech"
            return "no_speech"
            
        detected_lang = transcription["language"]
        print(f"[*] Idioma detetado: {detected_lang}")
        
        # 2. Align
        print("[*] A carregar modelo de alinhamento...")
        try:
            model_a, metadata = whisperx.load_align_model(language_code=detected_lang, device=device)
            print("[*] A alinhar timestamps...")
            aligned_result = whisperx.align(
                transcription["segments"],
                model_a,
                metadata,
                audio_wav,
                device,
                return_char_alignments=False
            )
            
            # Free alignment GPU memory
            del model_a
            if device == "cuda":
                import torch
                torch.cuda.empty_cache()
            gc.collect()
            
        except Exception as e:
            err_msg = str(e)
            err_type = type(e).__name__.lower()
            if "localentrynotfound" in err_type or "offlinemodeisenabled" in err_type or "offline" in err_msg.lower() or os.environ.get("HF_HUB_OFFLINE") == "1":
                print(f"[!] AVISO: Modelo de alinhamento para '{detected_lang}' não encontrado no cache em modo offline. Usando timestamps brutos.")
            elif "connection" in err_msg.lower() or "timeout" in err_msg.lower() or "reach" in err_msg.lower():
                print(f"[!] AVISO: Não foi possível ligar ao Hugging Face para transferir o modelo de alinhamento para '{detected_lang}'. Usando timestamps brutos.")
            else:
                print(f"[!] AVISO: O alinhamento falhou ({e}). Usando timestamps de transcrição brutos.")
            aligned_result = transcription
            # WhisperX aligned results contain segment level lists of words, make sure it is populated
            for seg in aligned_result["segments"]:
                if "words" not in seg and "text" in seg:
                    # Create simulated word lists if not present
                    pass
        
        # 3. Speaker Diarization
        diarized = False
        result_final = aligned_result
        
        # Check token and diarization flag
        hf_token = args.hf_token or os.getenv("HF_TOKEN")
        
        if args.no_diarization:
            print("[*] Diarização desativada pelo utilizador.")
        elif not hf_token:
            print("[!] AVISO: HF_TOKEN não encontrado. Use --no-diarization para transcrever sem separar vozes ou configure HF_TOKEN no .env.")
            result_final = aligned_result
        else:
            print(f"[*] A carregar modelo de diarização ({args.diarize_model})...")
            try:
                from whisperx.diarize import DiarizationPipeline
                # Resolve cache directory for Hugging Face
                diarize_cache_dir = args.cache_dir or os.getenv("HF_HOME")
                if diarize_cache_dir:
                    diarize_cache_dir = diarize_cache_dir.replace("\\", "/")
                
                diarize_pipeline = DiarizationPipeline(
                    model_name=args.diarize_model,
                    token=hf_token,
                    device=device,
                    cache_dir=diarize_cache_dir
                )
                print("[*] A executar diarização (separação de vozes)...")
                diarize_segments = diarize_pipeline(
                    audio_wav,
                    min_speakers=args.min_speakers,
                    max_speakers=args.max_speakers,
                    num_speakers=args.num_speakers
                )
                
                print("[*] A associar vozes aos segmentos transcritos...")
                result_final = whisperx.assign_word_speakers(diarize_segments, aligned_result)
                diarized = True
                
                # Free diarization GPU memory
                del diarize_pipeline
                if device == "cuda":
                    import torch
                    torch.cuda.empty_cache()
                gc.collect()
                
            except Exception as e:
                err_msg = str(e)
                # Check for local entry not found / offline mode issues
                if "localentrynotfound" in type(e).__name__.lower() or "local entry not found" in err_msg.lower() or "offline" in err_msg.lower() or os.environ.get("HF_HUB_OFFLINE") == "1":
                    print("[!] ERRO: Modelo pyannote não encontrado no cache e HF_HUB_OFFLINE=1 está ativo. Desative o modo offline uma vez para baixar os modelos.", file=sys.stderr)
                # Check for Gated repo or access denied
                elif "gated" in err_msg.lower() or "gatedrepoerror" in type(e).__name__.lower() or "access denied" in err_msg.lower() or "403 client error" in err_msg.lower():
                    print("[!] ERRO: Acesso negado ao modelo pyannote. Verifique se você aceitou os termos do modelo no Hugging Face.", file=sys.stderr)
                # Check for token issues or generic access denied
                elif "unauthorized" in err_msg.lower() or "401 client error" in err_msg.lower() or "invalid token" in err_msg.lower():
                    print("[!] ERRO: Token do Hugging Face inválido ou não autorizado. Verifique o HF_TOKEN.", file=sys.stderr)
                else:
                    print(f"[!] ERRO: Falha na diarização ({e}).", file=sys.stderr)
                result_final = aligned_result
        
        # 4. Generate Subtitle Cards (SRT/VTT)
        print("[*] A gerar legendas e arquivos de exportação...")
        all_cards = []
        for seg in result_final["segments"]:
            seg_start = seg.get("start", 0.0)
            seg_end = seg.get("end", seg_start + 1.0)
            seg_text = seg.get("text", "").strip()
            speaker = seg.get("speaker", "UNKNOWN")
            
            # If word level timestamps are present, group by word constraints
            if "words" in seg and seg["words"]:
                # Map speaker to words if segment speaker is present
                word_list = []
                for w in seg["words"]:
                    # WhisperX returns words. Sometimes start/end is missing, we use default fallback
                    w_start = w.get("start")
                    w_end = w.get("end")
                    w_spk = w.get("speaker", speaker)
                    word_list.append({
                        "word": w.get("word", ""),
                        "start": w_start,
                        "end": w_end,
                        "speaker": w_spk
                    })
                cards = group_words_into_cards(word_list)
                all_cards.extend(cards)
            else:
                # Proportional splitting if word-level info is missing
                cards = split_segment_without_words(seg_text, seg_start, seg_end, speaker)
                all_cards.extend(cards)
                
        # 5. Export Files
        base_out = os.path.splitext(os.path.basename(file_path))[0]
        file_output_dir = os.path.join(output_dir, base_out)
        os.makedirs(file_output_dir, exist_ok=True)
        formats = args.formats.split()
        
        if "json" in formats:
            out_json = os.path.join(file_output_dir, f"{base_out}.json")
            export_json(result_final, out_json)
            print(f"[+] Exportado: {out_json}")
            
        if "txt" in formats:
            out_txt = os.path.join(file_output_dir, f"{base_out}.txt")
            export_txt(result_final["segments"], out_txt, speaker_map)
            print(f"[+] Exportado: {out_txt}")
            
        if "srt" in formats:
            out_srt = os.path.join(file_output_dir, f"{base_out}.srt")
            export_srt(all_cards, out_srt, speaker_map, show_speaker=diarized)
            print(f"[+] Exportado: {out_srt}")
            
        if "vtt" in formats:
            out_vtt = os.path.join(file_output_dir, f"{base_out}.vtt")
            export_vtt(all_cards, out_vtt, speaker_map, show_speaker=diarized)
            print(f"[+] Exportado: {out_vtt}")
            
        print(f"[OK] Ficheiro '{os.path.basename(file_path)}' concluído com sucesso!")
        result_status = "success"
        return "success"
        
    except Exception as e:
        err_msg = str(e)
        err_type = type(e).__name__.lower()
        if "localentrynotfound" in err_type or "offlinemodeisenabled" in err_type or "offline" in err_msg.lower() or os.environ.get("HF_HUB_OFFLINE") == "1":
            print(f"[!] ERRO: Falha ao carregar dependências ou modelos Hugging Face (modo offline ativo/erro de cache).", file=sys.stderr)
            print(f"    Detalhes: {e}", file=sys.stderr)
        elif "connection" in err_msg.lower() or "timeout" in err_msg.lower() or "reach" in err_msg.lower():
            print(f"[!] ERRO: Não foi possível ligar ao Hugging Face ou descarregar componentes necessários.", file=sys.stderr)
            print(f"    Detalhes: {e}", file=sys.stderr)
        else:
            print(f"[!] ERRO CRÍTICO no processamento do ficheiro: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
        result_status = "failed"
        return "failed"
        
    finally:
        # DB log updates
        if job_id is not None:
            try:
                from src.core.history import update_job_success, update_job_failure, get_job
                from src.core.presets import get_setting
                import json
                
                duration = time.time() - file_start_time
                if result_status in ("success", "no_speech"):
                    primary_path = None
                    text_snippet = None
                    if result_status == "no_speech":
                        text_snippet = "(Sem fala detectada)"
                    else:
                        base_out = os.path.splitext(os.path.basename(file_path))[0]
                        file_output_dir = os.path.join(output_dir, base_out)
                        formats = args.formats.split()
                        if "txt" in formats:
                            primary_path = os.path.join(file_output_dir, f"{base_out}.txt")
                            if os.path.exists(primary_path):
                                try:
                                    with open(primary_path, "r", encoding="utf-8") as f:
                                        text_snippet = f.read(300) + "..."
                                except Exception:
                                    pass
                        elif "json" in formats:
                            primary_path = os.path.join(file_output_dir, f"{base_out}.json")
                    
                    # Fetch existing metadata to preserve/extend it
                    meta = {}
                    try:
                        job_info = get_job(job_id)
                        if job_info and job_info.get("metadata_json"):
                            meta = json.loads(job_info["metadata_json"])
                    except Exception:
                        pass
                        
                    # Save full text if enabled
                    save_full = getattr(args, "save_full_text", False) or (get_setting("save_full_text_history", "false").lower() == "true")
                    if save_full:
                        full_text = None
                        if primary_path and os.path.exists(primary_path):
                            try:
                                with open(primary_path, "r", encoding="utf-8") as f:
                                    full_text = f.read()
                            except Exception:
                                pass
                        if full_text:
                            meta["full_text"] = full_text
                            meta["save_full_text"] = True
                            
                    update_job_success(
                        job_id,
                        primary_output_path=os.path.abspath(primary_path) if primary_path else None,
                        duration_seconds=duration,
                        text_snippet=text_snippet,
                        metadata_json=json.dumps(meta) if meta else None
                    )
                else:
                    update_job_failure(job_id, "Transcricao falhou ou foi abortada.")
            except Exception as e:
                print(f"[WARN] Falha ao atualizar historico: {e}")

        # Clean up temporary audio file unless keep-wav is active
        if not args.keep_wav and audio_wav and os.path.exists(audio_wav):
            try:
                os.remove(audio_wav)
                # Check if temp dir is empty, delete if it is
                if not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
            except Exception:
                pass

def run_interactive_wizard(args):
    print("======================================================================")
    print("[*] CONSOLE DE TRANSCRIÇÃO & DIARIZAÇÃO (Audio-to-Text)")
    print("======================================================================")
    print("Escolha uma opção de execução:")
    print()
    print("[1] Modo Completo (GPU + Modelo Medium + VAD Sensível) -- RECOMENDADO")
    print("    -> Ideal para qualquer áudio ou vídeo em português. Evita cortes de voz")
    print("       e detecta automaticamente a quantidade e as vozes dos falantes.")
    print()
    print("[2] Modo Rápido (GPU + Modelo Small)")
    print("    -> Transcreve muito mais rápido, mas pode cometer pequenos erros de concordância.")
    print()
    print("[3] Apenas Texto (Sem Diarização/Vozes)")
    print("    -> Transcreve o texto corrido rapidamente, sem tentar adivinhar quem está falando.")
    print()
    print("[4] Configuração Personalizada (Passo a Passo Guiado)")
    print("    -> Permite que você escolha os detalhes com ajuda e explicação de cada opção.")
    print()
    
    try:
        choice = input("Opção desejada [1]: ").strip()
    except KeyboardInterrupt:
        print("\n[!] Operação cancelada pelo utilizador.")
        sys.exit(0)
        
    if not choice:
        choice = "1"
        
    if choice not in ["1", "2", "3", "4"]:
        print("[!] Opção inválida. Usando o Modo Completo (Opção 1).")
        choice = "1"
        
    print("\n" + "-"*70)
    
    # Prompt for file path
    input_path = ""
    while True:
        try:
            path_prompt = input("Arraste o arquivo de áudio/vídeo para esta janela (ou digite o caminho):\n> ").strip()
        except KeyboardInterrupt:
            print("\n[!] Operação cancelada pelo utilizador.")
            sys.exit(0)
            
        # Clean up quotes from drag-and-drop in Windows
        if path_prompt.startswith('"') and path_prompt.endswith('"'):
            path_prompt = path_prompt[1:-1]
        elif path_prompt.startswith("'") and path_prompt.endswith("'"):
            path_prompt = path_prompt[1:-1]
            
        if not path_prompt:
            print("[!] Por favor, especifique um arquivo ou pasta.")
            continue
            
        if not os.path.exists(path_prompt):
            print(f"[!] ERRO: O caminho '{path_prompt}' não existe. Tente novamente.")
            continue
            
        input_path = path_prompt
        break
        
    args.input_path = input_path
    
    # Configure parameters based on option
    if choice == "1":
        # Preset 1: Full High Quality (Auto-detect speakers)
        args.device = "cuda"
        args.model = "medium"
        args.compute_type = "int8"
        args.batch_size = 1
        args.num_speakers = None
        args.language = "pt"
        args.vad_onset = 0.1
        args.vad_offset = 0.1
        args.no_diarization = False
    elif choice == "2":
        # Preset 2: Fast
        args.device = "cuda"
        args.model = "small"
        args.compute_type = "int8"
        args.batch_size = 2
        args.num_speakers = None
        args.language = "pt"
        args.vad_onset = 0.5
        args.vad_offset = 0.363
        args.no_diarization = False
    elif choice == "3":
        # Preset 3: Text Only
        args.device = "cuda"
        args.model = "small"
        args.compute_type = "int8"
        args.batch_size = 2
        args.no_diarization = True
        args.language = "pt"
    elif choice == "4":
        # Option 4: Custom Guided Wizard
        print("======================================================================")
        print("[CONFIGURAÇÃO PERSONALIZADA]")
        print("======================================================================")
        
        # 4.1 IA Model Size
        print("\n--- PASSO 1: Tamanho do Modelo de Inteligência Artificial ---")
        print("Modelos maiores são mais precisos, mas exigem mais do seu computador.")
        print("  1) small   - Rápido e leve (boa precisão geral)")
        print("  2) medium  - Ótimo equilíbrio para português (RECOMENDADO) [Padrão]")
        print("  3) large-v3 - Precisão máxima, exige placa de vídeo Nvidia potente")
        try:
            model_opt = input("Opção [2]: ").strip()
        except KeyboardInterrupt:
            print("\n[!] Operação cancelada pelo utilizador.")
            sys.exit(0)
            
        if model_opt == "1":
            args.model = "small"
        elif model_opt == "3":
            args.model = "large-v3"
        else:
            args.model = "medium"
            
        # 4.2 Language
        print("\n--- PASSO 2: Idioma do Áudio ---")
        print("Digite o código do idioma (ex: pt para português, en para inglês).")
        print("Pressione Enter para tentar auto-detectar automaticamente.")
        try:
            lang_opt = input("Idioma [pt]: ").strip()
        except KeyboardInterrupt:
            print("\n[!] Operação cancelada pelo utilizador.")
            sys.exit(0)
            
        if not lang_opt:
            args.language = "pt"
        else:
            args.language = lang_opt
            
        # 4.3 Diarization (Vozes)
        print("\n--- PASSO 3: Identificação de Vozes (Diarização) ---")
        print("Separar a fala de cada pessoa (ex: SPEAKER_00, SPEAKER_01)?")
        try:
            diar_opt = input("Ativar separação de vozes? [S/n]: ").strip().lower()
        except KeyboardInterrupt:
            print("\n[!] Operação cancelada pelo utilizador.")
            sys.exit(0)
            
        if diar_opt == "n":
            args.no_diarization = True
        else:
            args.no_diarization = False
            
        # 4.4 Number of Speakers (only if Diarization is enabled)
        if not args.no_diarization:
            print("\n--- PASSO 4: Quantidade de Pessoas Falando ---")
            print("Se souber o número exato de pessoas no áudio, ajuda a IA a não misturar as vozes.")
            print("Digite um número ou pressione Enter se não souber.")
            try:
                spk_opt = input("Número de falantes: ").strip()
            except KeyboardInterrupt:
                print("\n[!] Operação cancelada pelo utilizador.")
                sys.exit(0)
                
            if spk_opt.isdigit():
                args.num_speakers = int(spk_opt)
            else:
                args.num_speakers = None
                
        # 4.5 Dialogue Cut-off protection (VAD)
        print("\n--- PASSO 5: Proteção Contra Diálogos Cortados (VAD) ---")
        print("Se o áudio tiver falas baixas, rápidas ou sussurros, a IA padrão pode ignorar.")
        print("  S) Sim - Ativar máxima sensibilidade (evita cortes de fala, RECOMENDADO) [Padrão]")
        print("  N) Não - Usar detecção comum (adequado para áudios limpos e sem ruídos)")
        try:
            vad_opt = input("Ativar sensibilidade máxima? [S/n]: ").strip().lower()
        except KeyboardInterrupt:
            print("\n[!] Operação cancelada pelo utilizador.")
            sys.exit(0)
            
        if vad_opt == "n":
            args.vad_onset = 0.5
            args.vad_offset = 0.363
        else:
            args.vad_onset = 0.1
            args.vad_offset = 0.1
            
        # 4.6 Processing Device
        print("\n--- PASSO 6: Dispositivo de Execução ---")
        print("  1) CUDA - Usa a placa de vídeo Nvidia (MUITO mais rápido) [Padrão]")
        print("  2) CPU  - Usa o processador comum (lento)")
        try:
            dev_opt = input("Opção [1]: ").strip()
        except KeyboardInterrupt:
            print("\n[!] Operação cancelada pelo utilizador.")
            sys.exit(0)
            
        if dev_opt == "2":
            args.device = "cpu"
        else:
            args.device = "cuda"
            
        # Keep-wav and other defaults
        args.compute_type = "int8"
        args.batch_size = 1
        
    print("\n" + "="*70)
    print("[*] INICIANDO TRANSCRIÇÃO COM AS CONFIGURAÇÕES:")
    print(f"  - Arquivo: {args.input_path}")
    print(f"  - IA Model: {args.model}")
    print(f"  - Idioma: {args.language or 'Auto-detectar'}")
    print(f"  - Separação de Vozes: {'Desativado' if args.no_diarization else 'Ativado'}")
    if not args.no_diarization:
        print(f"  - N. de Interlocutores: {args.num_speakers if args.num_speakers else 'Auto-detectar'}")
    print(f"  - VAD Sensível (Evita cortes): {'Sim (onset=0.1)' if args.vad_onset == 0.1 else 'Não (padrão)'}")
    print(f"  - Hardware: {args.device.upper()}")
    print("="*70 + "\n")
    return args

def main():
    parser = argparse.ArgumentParser(
        description="Local Audio/Video Transcription and Speaker Diarization Pipeline using WhisperX & Pyannote"
    )
    
    parser.add_argument("input_path", nargs="?", default=None, help="Caminho do arquivo de áudio/vídeo ou diretório a transcrever")
    parser.add_argument("--model", default="small", help="Modelo do Whisper (ex: tiny, base, small, medium, large-v2, large-v3)")
    parser.add_argument("--language", default=None, help="Código do idioma (ex: pt, en, es). Auto-deteta se omitido.")
    parser.add_argument("--initial-prompt", default=None, help="Texto inicial para dar contexto e vocabulário ao Whisper (ex: nomes próprios, termos técnicos)")
    parser.add_argument("--compute_type", default="int8", help="Tipo de computação/precisão (int8, float16, float32)")
    parser.add_argument("--batch_size", type=int, default=2, help="Tamanho do batch para transcrição WhisperX")
    
    # Speaker options
    parser.add_argument("--num_speakers", type=int, default=None, help="Número exato de interlocutores (se conhecido)")
    parser.add_argument("--min_speakers", type=int, default=None, help="Número mínimo de interlocutores")
    parser.add_argument("--max_speakers", type=int, default=None, help="Número máximo de interlocutores")
    
    # Export and Directory settings
    parser.add_argument("--output_dir", default="outputs", help="Diretório para salvar as exportações")
    parser.add_argument("--formats", default="txt json srt vtt", help="Formatos de saída separados por espaço (ex: 'txt json srt vtt')")
    parser.add_argument("--no-diarization", action="store_true", help="Pula a etapa de diarização de interlocutores")
    parser.add_argument("--keep-wav", action="store_true", help="Mantém o arquivo WAV temporário de 16kHz")
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"], help="Dispositivo para rodar o modelo (auto, cuda, cpu)")
    parser.add_argument("--hf-token", default=None, help="Token do Hugging Face para o Pyannote (sobrescreve o .env)")
    parser.add_argument("--diarize-model", default="pyannote/speaker-diarization-community-1", help="Modelo de diarização no Hugging Face")
    parser.add_argument("--speaker-map", default=None, help="Caminho do JSON para mapear speakers (ex: {'SPEAKER_00': 'Nome'})")
    parser.add_argument("--recursive", action="store_true", help="Busca arquivos recursivamente se a entrada for uma pasta")
    parser.add_argument("--chunk-size", type=int, default=30, help="Tamanho do chunk para processamento do VAD em segundos (padrão: 30)")
    parser.add_argument("--vad-onset", type=float, default=0.500, help="Limiar de início de fala para o VAD (padrão: 0.500). Valores menores são mais sensíveis.")
    parser.add_argument("--vad-offset", type=float, default=0.363, help="Limiar de fim de fala para o VAD (padrão: 0.363). Valores menores mantêm segmentos mais longos.")
    parser.add_argument("--offline", action="store_true", help="Ativa o modo offline do Hugging Face Hub (exige modelos já em cache)")
    parser.add_argument("--cache-dir", default=None, help="Caminho do diretório de cache do Hugging Face (sobrescreve HF_HOME)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Inicia o assistente de console interativo guiado")
    parser.add_argument("--no-history", action="store_true", help="Desativa o registro da transcricao no historico local")
    parser.add_argument("--speaker-profile", default=None, help="Nome ou ID do perfil de interlocutores salvo no banco de dados")
    parser.add_argument("--save-full-text", action="store_true", help="Salva o texto completo no historico de transcricoes (no JSON de metadados)")
    
    args = parser.parse_args()
    
    if args.interactive or not args.input_path:
        args = run_interactive_wizard(args)
    
    
    # 0. Sync and verify Hugging Face environment variables from parsed CLI args
    if args.offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
    
    if args.cache_dir:
        cache_dir = args.cache_dir.replace("\\", "/")
        os.environ["HF_HOME"] = cache_dir
        os.environ["HF_HUB_CACHE"] = os.path.join(cache_dir, "hub").replace("\\", "/")
        try:
            os.makedirs(cache_dir, exist_ok=True)
        except Exception:
            pass
            
    if args.hf_token:
        os.environ["HF_TOKEN"] = args.hf_token

    # Print Hugging Face Configuration Summary
    hf_token_status = "encontrado" if (args.hf_token or os.getenv("HF_TOKEN")) else "não encontrado"
    hf_home_dir = os.environ.get("HF_HOME", "padrão do sistema")
    if "HF_HUB_CACHE" in os.environ:
        hf_hub_cache = os.environ["HF_HUB_CACHE"]
    elif "HF_HOME" in os.environ:
        hf_hub_cache = os.path.join(os.environ["HF_HOME"], "hub").replace("\\", "/")
    else:
        hf_hub_cache = "padrão do Hugging Face (geralmente ~/.cache/huggingface/hub)"
    hf_offline_status = "ativo" if os.environ.get("HF_HUB_OFFLINE") == "1" else "inativo"
    
    print("[*] Configurações do Hugging Face:")
    print(f"    - HF Token: {hf_token_status}")
    print(f"    - HF Home: {hf_home_dir}")
    print(f"    - HF Hub Cache: {hf_hub_cache}")
    print(f"    - HF Offline Mode: {hf_offline_status}")
    if os.environ.get("HF_HUB_OFFLINE") == "1":
        print("    [!] AVISO: Modo offline ativo. O pipeline usará apenas modelos em cache local.")
    print()
    
    # 1. FFmpeg Verification
    if not check_ffmpeg():
        sys.exit(1)
        
    # Initialize database and seed defaults
    from src.core.database import initialize_database
    initialize_database()

    # 2. Load Speaker Map / Profiles if provided
    speaker_map = {}
    
    # Try loading from speaker profile first
    if getattr(args, "speaker_profile", None):
        from src.core.presets import get_speaker_profile
        profile = get_speaker_profile(args.speaker_profile)
        if profile:
            try:
                speaker_map = json.loads(profile["mapping_json"])
                print(f"[*] Mapeamento de speakers carregado do perfil '{profile['name']}': {speaker_map}")
            except Exception as e:
                print(f"[!] AVISO: Erro ao analisar mapping_json do perfil '{args.speaker_profile}' ({e}). Ignorando...")
        else:
            print(f"[!] AVISO: Perfil de speakers '{args.speaker_profile}' nao encontrado no banco de dados. Ignorando...")
            
    # Explicit CLI argument overrides profile
    if args.speaker_map:
        if os.path.exists(args.speaker_map):
            try:
                with open(args.speaker_map, "r", encoding="utf-8") as smf:
                    cli_map = json.load(smf)
                    speaker_map.update(cli_map)
                print(f"[*] Mapeamento de speakers carregado/mesclado com CLI map: {speaker_map}")
            except Exception as e:
                print(f"[!] AVISO: Erro ao ler mapa de speakers do arquivo CLI ({e}). Ignorando...")
        else:
            print(f"[!] AVISO: Arquivo de mapeamento de speakers CLI '{args.speaker_map}' não encontrado. Ignorando...")
            
    # 3. Determine input files
    input_path = args.input_path
    media_extensions = {".mp3", ".wav", ".m4a", ".flac", ".mp4", ".mkv", ".mov", ".avi", ".webm", ".aac", ".ogg"}
    
    files_to_process = []
    if os.path.isdir(input_path):
        if args.recursive:
            for root, _, files in os.walk(input_path):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in media_extensions:
                        files_to_process.append(os.path.join(root, f))
        else:
            for f in os.listdir(input_path):
                ext = os.path.splitext(f)[1].lower()
                if ext in media_extensions:
                    files_to_process.append(os.path.join(input_path, f))
        
        # Sort files for deterministic order
        files_to_process.sort()
        print(f"[*] Encontrados {len(files_to_process)} arquivos de média para processar.")
    else:
        if os.path.exists(input_path):
            files_to_process.append(input_path)
        else:
            print(f"[!] ERRO: Caminho de entrada '{input_path}' não existe.", file=sys.stderr)
            sys.exit(1)
            
    if not files_to_process:
        print("[!] Nenhum arquivo de média compatível encontrado para processar.")
        sys.exit(0)
        
    # 4. Process all files
    com_fala = 0
    sem_fala = 0
    falhas = 0
    start_time = time.time()
    
    for f in files_to_process:
        status = process_file(f, args, speaker_map)
        if status == "success":
            com_fala += 1
        elif status == "no_speech":
            sem_fala += 1
        else:
            falhas += 1
            
    elapsed = time.time() - start_time
    total_analisados = len(files_to_process)
    print("\n" + "="*80)
    print(f"[OK] CONCLUÍDO! Arquivos analisados: {total_analisados} | com fala: {com_fala} | sem fala: {sem_fala} | falhas: {falhas} (tempo total: {elapsed:.1f} segundos)")
    print("="*80)

if __name__ == "__main__":
    main()
