import os
import sys
import subprocess
import torch

try:
    import gradio as gr
except ImportError:
    print("[!] Erro: O pacote 'gradio' nao esta instalado.")
    print("    Por favor, execute o script de instalacao de dependencias do TTS:")
    print("    powershell -ExecutionPolicy Bypass -File ./install_tts.ps1")
    sys.exit(1)

from src.core.paths import TRANSCRIPTIONS_DIR, SPEECH_DIR, TEMP_DIR
from src.tts.registry import TTSRegistry

def check_espeak_installed() -> bool:
    from src.tts.kokoro_engine import setup_espeak
    return setup_espeak()

def check_cuda_status():
    if torch.cuda.is_available():
        return f"🟢 Disponivel ({torch.cuda.get_device_name(0)})", "CUDA esta pronto para aceleracao por GPU."
    return "🟡 Indisponivel (CPU apenas)", "Os modelos rodarao em CPU (WhisperX sera lento)."

def check_ffmpeg_status():
    from src.core.ffmpeg_utils import check_ffmpeg
    if check_ffmpeg():
        return "🟢 Instalado", "FFmpeg esta configurado e pronto para conversoes MP3."
    return "🔴 Nao encontrado", "Instale o FFmpeg e adicione-o ao PATH do sistema para permitir conversao para MP3."

def check_kokoro_status():
    from src.tts.kokoro_engine import KokoroEngine
    if KokoroEngine.is_available():
        return "🟢 Disponivel", "Kokoro esta pronto para sintese de fala."
    return "🔴 Indisponivel", "Instale as dependencias executando './install_tts.ps1'."

def check_piper_status():
    from src.tts.piper_engine import PiperEngine
    if PiperEngine.is_available():
        return "🟢 Disponivel", "Piper esta pronto para sintese de fala."
    return "🔴 Indisponivel", "Instale as dependencias executando './install_tts.ps1'."

def check_espeak_status():
    if check_espeak_installed():
        return "🟢 Instalado / Configurado", "espeak-ng foi detectado no PATH ou pastas de instalacao padrao."
    return "🟡 Nao encontrado", "Kokoro/Piper podem ainda funcionar se um carregador Python/DLL embutido estiver disponivel. Se a sintese falhar, instale o eSpeak NG manualmente."

def get_system_status_html():
    cuda_val, cuda_note = check_cuda_status()
    ffmpeg_val, ffmpeg_note = check_ffmpeg_status()
    espeak_val, espeak_note = check_espeak_status()
    kokoro_val, kokoro_note = check_kokoro_status()
    piper_val, piper_note = check_piper_status()

    html = f"""
    <div style="font-family: sans-serif; padding: 10px;">
        <h3 style="margin-top: 0; color: #2b6cb0;">Status dos Componentes do Sistema</h3>
        <table style="width: 100%; border-collapse: collapse; text-align: left; margin-top: 15px;">
            <thead>
                <tr style="border-bottom: 2px solid #cbd5e0; color: #2d3748; background-color: #f7fafc;">
                    <th style="padding: 12px 10px; width: 25%;">Componente</th>
                    <th style="padding: 12px 10px; width: 25%;">Status</th>
                    <th style="padding: 12px 10px;">Detalhes / Orientacao</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">Placa Grafica (CUDA)</td>
                    <td style="padding: 12px 10px;">{cuda_val}</td>
                    <td style="padding: 12px 10px; color: #4a5568;">{cuda_note}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">FFmpeg</td>
                    <td style="padding: 12px 10px;">{ffmpeg_val}</td>
                    <td style="padding: 12px 10px; color: #4a5568;">{ffmpeg_note}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">eSpeak NG</td>
                    <td style="padding: 12px 10px;">{espeak_val}</td>
                    <td style="padding: 12px 10px; color: #4a5568;">{espeak_note}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">Motor Kokoro</td>
                    <td style="padding: 12px 10px;">{kokoro_val}</td>
                    <td style="padding: 12px 10px; color: #4a5568;">{kokoro_note}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">Motor Piper</td>
                    <td style="padding: 12px 10px;">{piper_val}</td>
                    <td style="padding: 12px 10px; color: #4a5568;">{piper_note}</td>
                </tr>
            </tbody>
        </table>
    </div>
    """
    return html

def get_voices_status_html() -> str:
    from src.tts.registry import TTSRegistry
    metadata = TTSRegistry.get_voices_metadata()
    
    html = """
    <div style="font-family: sans-serif; padding: 10px; margin-top: 20px;">
        <h3 style="color: #2b6cb0;">Vozes Registradas e Status de Instalacao</h3>
        <table style="width: 100%; border-collapse: collapse; text-align: left; margin-top: 15px;">
            <thead>
                <tr style="border-bottom: 2px solid #cbd5e0; color: #2d3748; background-color: #f7fafc;">
                    <th style="padding: 12px 10px; width: 20%;">Nome da Voz</th>
                    <th style="padding: 12px 10px; width: 12%;">Motor</th>
                    <th style="padding: 12px 10px; width: 12%;">Idioma</th>
                    <th style="padding: 12px 10px; width: 12%;">Genero</th>
                    <th style="padding: 12px 10px; width: 15%;">Status</th>
                    <th style="padding: 12px 10px;">Instrucoes de Obtencao / Uso</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for info in metadata:
        engine = info["engine"]
        alias = info["alias"]
        status = TTSRegistry.get_voice_status(engine, alias)
        
        status_emoji = "🟢" if status["installed_locally"] else "🟡"
        if not status["ready_to_use"]:
            status_emoji = "🔴"
            
        # Determine instruction
        if status["installed_locally"]:
            instruction = "Pronta para uso. Selecione esta voz na aba Text-to-Speech e clique em Gerar."
        elif status["requires_download"]:
            if engine == "kokoro":
                instruction = "Sera baixada automaticamente do Hugging Face no primeiro uso (requer conexao com internet)."
            elif engine == "piper":
                instruction = "Sera baixada automaticamente do repositorio oficial do Piper no primeiro uso (requer internet)."
            else:
                instruction = "Requer download. Inicie a sintese com essa voz para baixar automaticamente."
        else:
            instruction = f"Requer configuracao do motor '{engine}' ou espeak-ng."
            
        html += f"""
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">{info['name']}</td>
                    <td style="padding: 12px 10px;">{engine.upper()}</td>
                    <td style="padding: 12px 10px;">{info['lang']}</td>
                    <td style="padding: 12px 10px;">{info['gender']}</td>
                    <td style="padding: 12px 10px;">{status_emoji} {status['status_description']}</td>
                    <td style="padding: 12px 10px; color: #4a5568; font-size: 0.9em;">{instruction}</td>
                </tr>
        """
        
    html += """
            </tbody>
        </table>
    </div>
    """
    return html

def get_settings_html():
    from src.core.paths import TRANSCRIPTIONS_DIR, SPEECH_DIR, MODEL_CACHE_DIR, TTS_CACHE_DIR, VOICES_DIR
    
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HF_HUB_TOKEN")
    token_status = "🟢 Encontrado (Configurado nas variaveis de ambiente)" if hf_token else "🔴 Nao encontrado (Pode limitar o acesso a modelos privados, como pyannote diarization)"
    
    hf_home = os.environ.get("HF_HOME", "Padrao do sistema")
    hf_offline = "🟢 Ativo (Apenas carregamento local)" if os.environ.get("HF_HUB_OFFLINE") == "1" else "🔴 Inativo (Conexao a internet ativa)"
    
    html = f"""
    <div style="font-family: sans-serif; padding: 10px;">
        <h3 style="margin-top: 0; color: #2b6cb0;">Configuracoes e Diretorios Globais</h3>
        <table style="width: 100%; border-collapse: collapse; text-align: left; margin-top: 15px;">
            <thead>
                <tr style="border-bottom: 2px solid #cbd5e0; color: #2d3748; background-color: #f7fafc;">
                    <th style="padding: 12px 10px; width: 30%;">Configuracao</th>
                    <th style="padding: 12px 10px;">Valor / Caminho</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">Token Hugging Face</td>
                    <td style="padding: 12px 10px; color: #2d3748;">{token_status}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">Hugging Face Home (HF_HOME)</td>
                    <td style="padding: 12px 10px; color: #4a5568; font-family: monospace; font-size: 0.9em;">{hf_home}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">Modo Offline (HF_HUB_OFFLINE)</td>
                    <td style="padding: 12px 10px; color: #2d3748;">{hf_offline}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">Pasta de Transcricoes</td>
                    <td style="padding: 12px 10px; color: #4a5568; font-family: monospace; font-size: 0.9em;">{os.path.abspath(TRANSCRIPTIONS_DIR)}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">Pasta de Fala (TTS)</td>
                    <td style="padding: 12px 10px; color: #4a5568; font-family: monospace; font-size: 0.9em;">{os.path.abspath(SPEECH_DIR)}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">Pasta de Vozes Piper</td>
                    <td style="padding: 12px 10px; color: #4a5568; font-family: monospace; font-size: 0.9em;">{os.path.abspath(VOICES_DIR)}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">Cache de Modelos WhisperX</td>
                    <td style="padding: 12px 10px; color: #4a5568; font-family: monospace; font-size: 0.9em;">{os.path.abspath(MODEL_CACHE_DIR)}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px 10px; font-weight: bold;">Cache de Modelos TTS</td>
                    <td style="padding: 12px 10px; color: #4a5568; font-family: monospace; font-size: 0.9em;">{os.path.abspath(TTS_CACHE_DIR)}</td>
                </tr>
            </tbody>
        </table>
    </div>
    """
    return html

def transcribe_audio_ui(file_obj, model, language, device, compute_type, batch_size, diarize, num_speakers, min_speakers, max_speakers, speaker_profile=None):
    """
    Spawns transcribe.py in a separate subprocess to transcribe the audio/video.
    This frees VRAM completely when finished, preventing OOM crashes.
    """
    if not file_obj:
        return "Erro: Por favor, faca o upload de um arquivo de audio ou video.", "Nenhum arquivo fornecido."

    # Resolve temp file path
    file_path = file_obj.name if hasattr(file_obj, "name") else file_obj
    
    os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)

    # Base command assembly
    cmd = [
        sys.executable, "transcribe.py",
        file_path,
        "--model", model,
        "--device", device,
        "--compute_type", compute_type,
        "--batch_size", str(int(batch_size)),
        "--output_dir", TRANSCRIPTIONS_DIR
    ]

    if speaker_profile and speaker_profile != "Nenhum":
        cmd += ["--speaker-profile", speaker_profile]

    if language and language != "Auto":
        cmd += ["--language", language]

    if not diarize:
        cmd += ["--no-diarization"]
    else:
        if num_speakers and num_speakers > 0:
            cmd += ["--num_speakers", str(int(num_speakers))]
        if min_speakers and min_speakers > 0:
            cmd += ["--min_speakers", str(int(min_speakers))]
        if max_speakers and max_speakers > 0:
            cmd += ["--max_speakers", str(int(max_speakers))]

    # Setup environment
    env = os.environ.copy()
    if os.getenv("HF_HOME"):
        env["HF_HOME"] = os.getenv("HF_HOME")

    # Spawn process and capture standard outputs
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        env=env
    )

    log_accumulator = f"Comando executado:\n{' '.join(cmd)}\n\n"
    yield log_accumulator, "A iniciar processo de transcricao..."

    # Stream outputs line by line
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            log_accumulator += line
            yield log_accumulator, "A transcrever... Verifique o log em tempo real."

    # Finish process
    rc = process.poll()
    if rc != 0:
        log_accumulator += f"\n[!] O processo terminou com erro (codigo {rc})."
        yield log_accumulator, f"Falha na transcricao (codigo {rc})."
        return

    # Find transcription outputs
    filename_no_ext = os.path.splitext(os.path.basename(file_path))[0]
    output_folder = os.path.join(TRANSCRIPTIONS_DIR, filename_no_ext)
    
    output_files_info = ""
    if os.path.exists(output_folder):
        files = os.listdir(output_folder)
        if files:
            output_files_info = f"Transcricao concluida! Pasta de saida: '{output_folder}'\n\nArquivos gerados:\n"
            for f in files:
                output_files_info += f" - {f} ({os.path.abspath(os.path.join(output_folder, f))})\n"
            
            # Show text preview
            txt_file = os.path.join(output_folder, f"{filename_no_ext}.txt")
            if os.path.exists(txt_file):
                try:
                    with open(txt_file, "r", encoding="utf-8") as tf:
                        preview = tf.read(1500)
                        if len(preview) >= 1500:
                            preview += "\n... (exibindo apenas os primeiros 1500 caracteres)"
                        output_files_info += f"\n\n--- PRÉVIA DA TRANSCRIÇÃO (txt) ---\n{preview}"
                except Exception as e:
                    output_files_info += f"\n\n(Nao foi possivel ler a previa: {e})"
        else:
            output_files_info = "O processo terminou, mas nenhum arquivo foi encontrado na pasta de saida."
    else:
        output_files_info = f"Processo concluido, mas a pasta de saida '{output_folder}' nao existe."

    yield log_accumulator, output_files_info

def generate_tts_ui(text, upload_file, engine, voice, format, preview, preview_chars, device, speed=1.0,
                    analyze_ptbr=False, normalize_ptbr=False):
    """
    Invokes synthesize.py in a subprocess to run the synthesis.
    This guarantees CLI alignment and prevents memory issues.
    """
    # 1. Resolve text input
    if upload_file:
        try:
            with open(upload_file.name, "r", encoding="utf-8") as f:
                input_text = f.read()
        except UnicodeDecodeError:
            with open(upload_file.name, "r", encoding="latin-1") as f:
                input_text = f.read()
    else:
        input_text = text

    input_text = input_text.strip()
    if not input_text:
        return None, "Erro: Escreva algum texto ou faca o upload de um arquivo .txt.", ""

    # PT-BR analysis (run in-process for speed, before synthesis)
    analysis_md = ""
    if analyze_ptbr:
        try:
            from src.tts.ptbr_text import analyze_ptbr_text
            analysis = analyze_ptbr_text(input_text)
            if analysis["has_issues"]:
                analysis_md = "**⚠️ Analise PT-BR — problemas encontrados:**\n\n" + "\n\n".join(
                    f"- {w}" for w in analysis["warnings"]
                )
            else:
                analysis_md = "✅ Analise PT-BR: nenhum problema detectado."
        except Exception as e:
            analysis_md = f"(Erro na analise PT-BR: {e})"

    # In preview mode, slice the string
    if preview:
        input_text = input_text[:int(preview_chars)]

    os.makedirs(SPEECH_DIR, exist_ok=True)
    import time
    suffix = "preview" if preview else "full"
    output_file = os.path.join(SPEECH_DIR, f"speech_{engine}_{suffix}_{int(time.time())}.{format}")

    # Write text input to a temporary .txt file to support long text safely
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_txt = os.path.join(TEMP_DIR, f"tts_input_{int(time.time())}_{os.getpid()}.txt")

    try:
        with open(temp_txt, "w", encoding="utf-8") as f:
            f.write(input_text)

        # Build command line using --input instead of passing raw --text in command args
        cmd = [
            sys.executable, "synthesize.py",
            "--input", temp_txt,
            "--engine", engine,
            "--voice", voice,
            "--output", output_file,
            "--format", format,
            "--device", device,
            "--speed", str(speed)
        ]

        if normalize_ptbr:
            cmd.append("--normalize-ptbr")

        # Spawn process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        log = f"Comando executado:\n{' '.join(cmd)}\n\n"
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                log += line

        rc = process.poll()
        if rc != 0:
            return None, f"Erro na sintese de audio (codigo {rc}):\n{log}", analysis_md

        if os.path.exists(output_file):
            return output_file, f"Audio sintetizado com sucesso!\nSalvo em: {os.path.abspath(output_file)}\n\nLog do processo:\n{log}", analysis_md
        else:
            return None, f"Erro: O processo terminou com sucesso, mas o arquivo de audio nao foi localizado.\nLog:\n{log}", analysis_md

    finally:
        # Clean up temporary file
        if os.path.exists(temp_txt):
            debug_mode = os.getenv("DEBUG") in ["1", "True", "true"]
            if not debug_mode:
                try:
                    os.remove(temp_txt)
                except Exception:
                    pass


def run_compare_voices_ui():
    """Launches compare-voices mode via subprocess and returns status text."""
    import time
    output_dir = os.path.join("outputs", "speech", "voice_compare")
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        sys.executable, "synthesize.py",
        "--compare-voices",
        "--output-dir", output_dir,
    ]
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            universal_newlines=True
        )
        log = ""
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                log += line
        rc = process.poll()
        abs_dir = os.path.abspath(output_dir)
        report_json = os.path.join(abs_dir, "compare_report.json")
        report_md = os.path.join(abs_dir, "compare_report.md")
        if rc == 0:
            result = f"✅ Comparativo concluido!\n\nPasta: {abs_dir}\n"
            if os.path.exists(report_md):
                result += f"Relatorio MD:   {report_md}\n"
            if os.path.exists(report_json):
                result += f"Relatorio JSON: {report_json}\n"
            result += f"\nLog:\n{log}"
        else:
            result = f"⚠️ Comparativo terminou com codigo {rc}.\nAlgumas vozes podem ter falhado.\n\nPasta: {abs_dir}\nLog:\n{log}"
        return result
    except Exception as e:
        return f"Erro ao executar comparativo: {e}"


def update_voice_info(engine, voice) -> str:
    """
    Returns a formatted Markdown card with the selected voice's metadata and local installation status.
    """
    if not voice:
        return "Nenhuma voz selecionada."
        
    try:
        engine_lower = engine.lower()
        
        # Piper custom ONNX files check
        if engine_lower == "piper" and (os.path.isabs(voice) or voice.endswith(".onnx")):
            filename = os.path.basename(voice)
            status = TTSRegistry.get_voice_status(engine_lower, voice)
            status_desc = "Instalado (Caminho customizado)" if status["installed_locally"] else "Nao encontrado (Caminho invalido)"
            status_emoji = "🟢" if status["installed_locally"] else "🔴"
            return f"""
### 🗣️ Voz Customizada: `{filename}`
- **Motor:** Piper (ONNX)
- **Caminho:** `{voice}`
- **Status:** {status_emoji} {status_desc}
- **Nota:** Check the selected voice/model license before commercial use.
"""

        from src.tts.registry import VOICE_MAPPING
        if engine_lower not in VOICE_MAPPING or voice not in VOICE_MAPPING[engine_lower]:
            return f"Voz '{voice}' nao encontrada no registry. Verifique a engine selecionada ou atualize a lista de vozes."

        info = VOICE_MAPPING[engine_lower][voice]
        status = TTSRegistry.get_voice_status(engine_lower, voice)
        
        status_emoji = "🟢" if status["installed_locally"] else "🟡"
        if not status["ready_to_use"] or "Falta espeak" in status["status_description"] or "nao instalado" in status["status_description"]:
            status_emoji = "🔴"
            
        md = f"""
### 🗣️ Detalhes da Voz: `{info['name']}`
- **Motor:** {engine.upper()} | **ID Interno:** `{info['id']}`
- **Idioma:** `{info['lang']}` | **Genero:** {info.get('gender', 'Desconhecido')}
- **Estilo:** *{info.get('style', 'Natural')}*
- **Status:** {status_emoji} **{status['status_description']}**
- **Origem da Voz:** `{info.get('source', 'unknown')}`
- **Aviso de Licenca:** {info.get('license_note', '')}
"""
        return md
    except Exception as e:
        return f"Voz '{voice}' nao encontrada no registry. Verifique a engine selecionada ou atualize a lista de vozes.\n(Erro: {e})"

def on_engine_change_with_card(engine):
    """
    Dynamically updates choices of the Voice dropdown and the voice info card.
    """
    from src.tts.registry import VOICE_MAPPING
    engine = engine.lower()
    choices = []
    default_val = ""
    if engine in VOICE_MAPPING:
        choices = list(VOICE_MAPPING[engine].keys())
        default_val = choices[0] if choices else ""
        
    dropdown_update = gr.update(choices=choices, value=default_val)
    card_update = update_voice_info(engine, default_val)
    return dropdown_update, card_update


import json
from src.core.presets import (
    list_tts_presets, get_tts_preset, create_tts_preset, delete_tts_preset, set_default_tts_preset,
    list_speaker_profiles, get_speaker_profile, create_speaker_profile, delete_speaker_profile
)
from src.core.history import list_jobs, get_job, clear_history

def apply_preset_to_fields(preset_name):
    """Query preset and return updates for all TTS UI components."""
    if not preset_name or preset_name == "Nenhum":
        return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        
    p = get_tts_preset(preset_name)
    if not p:
        return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        
    engine = p.get("engine", "kokoro")
    voice = p.get("voice", "pt_br_dora")
    fmt = p.get("output_format", "wav")
    speed = p.get("speed", 1.0)
    preview_chars = p.get("preview_chars", 300)
    
    from src.tts.registry import VOICE_MAPPING
    choices = list(VOICE_MAPPING.get(engine, {}).keys())
    card = update_voice_info(engine, voice)
    
    return (
        gr.update(value=engine),
        gr.update(choices=choices, value=voice),
        gr.update(value=fmt),
        gr.update(value=float(speed)),
        gr.update(value=int(preview_chars)),
        gr.update(value=card)
    )

def load_history_ui(job_type_filter):
    """Retrieve and format job history database rows for Gradio Dataframe."""
    api_filter = None if job_type_filter == "Todos" else job_type_filter.lower()
    jobs = list_jobs(limit=100, job_type=api_filter)
    
    data = []
    for j in jobs:
        created_time = j["created_at"].split(".")[0].replace("T", " ")
        data.append([
            str(j["id"]),
            j["job_type"].upper(),
            j["status"].upper(),
            created_time,
            j["input_name"] or j["input_path"] or "(Texto)",
            j["engine"] or j["model"] or "N/A",
            j["voice"] or j["language"] or "N/A",
            j["primary_output_path"] or "N/A"
        ])
    return data, jobs

def on_history_row_select(evt: gr.SelectData, jobs_list):
    """Load job details and output file path on table cell click."""
    row_idx = evt.index[0]
    if not jobs_list or row_idx >= len(jobs_list):
        return "Nenhum detalhe encontrado.", None
        
    job = jobs_list[row_idx]
    
    md = f"""### 📋 Detalhes do Job #{job['id']} ({job['job_type'].upper()})
- **Status:** `{job['status'].upper()}`
- **Criado em:** `{job['created_at'].split('.')[0].replace('T', ' ')}`
- **Concluido em:** `{job['completed_at'].split('.')[0].replace('T', ' ') if job['completed_at'] else 'N/A'}`
- **Dispositivo:** `{job['device'].upper() if job['device'] else 'N/A'}`
- **Duracao:** `{job['duration_seconds'] if job['duration_seconds'] is not None else 'N/A'} segundos`
- **Caminho de Entrada:** `{job['input_path'] or 'N/A'}`
- **Pasta de Saida:** `{job['output_dir'] or 'N/A'}`
- **Arquivo de Saida:** `{job['primary_output_path'] or 'N/A'}`
"""
    if job['text_snippet']:
        md += f"\n- **Texto/Snippet:** *{job['text_snippet']}*"
        
    if job['metadata_json']:
        try:
            meta = json.loads(job['metadata_json'])
            if "full_text" in meta:
                md += f"\n\n--- TEXTO COMPLETO ---\n{meta['full_text']}"
        except Exception:
            pass
            
    if job['error_message']:
        md += f"\n\n❌ **Erro:** `{job['error_message']}`"
        
    audio_path = None
    if job['job_type'] == 'tts' and job['primary_output_path'] and os.path.exists(job['primary_output_path']):
        audio_path = job['primary_output_path']
        
    return md, audio_path

def clear_history_ui(job_type_filter):
    """Delete selected job history database rows."""
    api_filter = None if job_type_filter == "Todos" else job_type_filter.lower()
    clear_history(job_type=api_filter)
    return load_history_ui(job_type_filter)

def create_preset_ui(name, engine, voice, fmt, speed, preview, chunk, lang):
    """Validate and create preset row, updating dropdown choices."""
    if not name or not name.strip():
        return "Erro: O nome do preset nao pode ser vazio.", gr.update(), gr.update()
        
    res = create_tts_preset(
        name=name.strip(),
        engine=engine,
        voice=voice,
        output_format=fmt,
        speed=speed,
        preview_chars=preview,
        chunk_chars=chunk,
        language=lang
    )
    if res is None:
        return f"Erro: Preset '{name}' ja existe ou houve uma falha de banco.", gr.update(), gr.update()
        
    presets = list_tts_presets()
    choices = [p["name"] for p in presets]
    dropdown_up = gr.update(choices=choices, value=name)
    main_dropdown_up = gr.update(choices=["Nenhum"] + choices, value=name)
    return f"Preset '{name}' criado com sucesso!", dropdown_up, main_dropdown_up

def delete_preset_ui(name):
    """Delete preset by name, updating dropdown choices."""
    if not name or name == "Nenhum":
        return "Erro: Selecione um preset valido.", gr.update(), gr.update()
    delete_tts_preset(name)
    presets = list_tts_presets()
    choices = [p["name"] for p in presets]
    val = choices[0] if choices else None
    dropdown_up = gr.update(choices=choices, value=val)
    main_dropdown_up = gr.update(choices=["Nenhum"] + choices, value="Nenhum")
    return f"Preset '{name}' excluido com sucesso.", dropdown_up, main_dropdown_up

def set_default_preset_ui(name):
    """Configure default preset choice."""
    if not name or name == "Nenhum":
        return "Erro: Selecione um preset valido."
    set_default_tts_preset(name)
    return f"Preset '{name}' definido como padrao com sucesso."

def create_profile_ui(name, mapping_json_str, notes):
    """Validate speaker profile mapping JSON and insert into SQLite DB."""
    if not name or not name.strip():
        return "Erro: O nome do perfil nao pode ser vazio.", gr.update(), gr.update()
    try:
        mapping = json.loads(mapping_json_str)
        if not isinstance(mapping, dict):
            return "Erro: O mapeamento de oradores deve ser um dicionario JSON.", gr.update(), gr.update()
    except Exception as e:
        return f"Erro: JSON de mapeamento invalido ({e})", gr.update(), gr.update()
        
    res = create_speaker_profile(name.strip(), mapping, notes)
    if res is None:
        return f"Erro: Perfil '{name}' ja existe ou houve uma falha de banco.", gr.update(), gr.update()
        
    profiles = list_speaker_profiles()
    choices = [p["name"] for p in profiles]
    dropdown_up = gr.update(choices=choices, value=name)
    main_dropdown_up = gr.update(choices=["Nenhum"] + choices, value=name)
    return f"Perfil '{name}' criado com sucesso!", dropdown_up, main_dropdown_up

def delete_profile_ui(name):
    """Delete speaker profile and update dropdown choices."""
    if not name or name == "Nenhum":
        return "Erro: Selecione um perfil valido.", gr.update(), gr.update()
    delete_speaker_profile(name)
    profiles = list_speaker_profiles()
    choices = [p["name"] for p in profiles]
    val = choices[0] if choices else None
    dropdown_up = gr.update(choices=choices, value=val)
    main_dropdown_up = gr.update(choices=["Nenhum"] + choices, value="Nenhum")
    return f"Perfil '{name}' excluido com sucesso.", dropdown_up, main_dropdown_up

def load_app_settings_ui():
    from src.core.presets import get_setting
    history_enabled = get_setting("history_enabled", "true").lower() == "true"
    save_full_text = get_setting("save_full_text_history", "false").lower() == "true"
    return history_enabled, save_full_text

def save_app_settings(history_enabled, save_full_text):
    from src.core.presets import set_setting
    set_setting("history_enabled", "true" if history_enabled else "false")
    set_setting("save_full_text_history", "true" if save_full_text else "false")
    return "Opcoes de historico salvas com sucesso!"

def on_engine_change_simple(engine):
    from src.tts.registry import VOICE_MAPPING
    engine = engine.lower()
    choices = []
    default_val = ""
    if engine in VOICE_MAPPING:
        choices = list(VOICE_MAPPING[engine].keys())
        default_val = choices[0] if choices else ""
    return gr.update(choices=choices, value=default_val)

def refresh_presets_and_profiles_ui():
    presets = list_tts_presets()
    preset_choices = [p["name"] for p in presets]
    preset_val = preset_choices[0] if preset_choices else None
    
    profiles = list_speaker_profiles()
    profile_choices = [p["name"] for p in profiles]
    profile_val = profile_choices[0] if profile_choices else None
    
    return (
        gr.update(choices=preset_choices, value=preset_val),
        gr.update(choices=profile_choices, value=profile_val)
    )

def refresh_stt_profiles_dropdown():
    profiles = list_speaker_profiles()
    choices = ["Nenhum"] + [p["name"] for p in profiles]
    return gr.update(choices=choices)

def refresh_tts_presets_dropdown():
    presets = list_tts_presets()
    choices = ["Nenhum"] + [p["name"] for p in presets]
    
    def_preset_name = "Nenhum"
    for p in presets:
        if p.get("is_default") == 1:
            def_preset_name = p["name"]
            break
            
    return gr.update(choices=choices, value=def_preset_name)

APP_CSS = """
    .gradio-container { max-width: 1100px; margin: 0 auto; font-family: 'Outfit', sans-serif; }
    .tabs { border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .tab-item { padding: 15px; }
    footer { display: none !important; }
"""

def build_app():
    # Load env configs
    from src.core.config import configure_hf_environment
    configure_hf_environment()

    # Premium dark theme and glassmorphism styling
    with gr.Blocks(title="Speech Studio - Local STT & TTS") as app:
        
        gr.HTML("""
        <div style="text-align: center; margin-bottom: 25px; margin-top: 15px;">
            <h1 style="color: #2b6cb0; margin-bottom: 5px; font-weight: 800; font-size: 2.3em;">🎙️ Speech Studio</h1>
            <p style="color: #4a5568; font-size: 1.1em; font-weight: 500;">Estudio Profissional Local de Transcricao (STT) e Sintese de Voz (TTS)</p>
        </div>
        """)

        with gr.Tabs():
            # Tab 1: Transcription (STT)
            with gr.TabItem("🎙️ Transcricao (STT)") as stt_tab:
                gr.Markdown("### Transcrever arquivos de audio ou video localmente com WhisperX e Pyannote")
                with gr.Row():
                    with gr.Column(scale=5):
                        file_input = gr.File(label="Upload de Arquivo (Audio/Video)", file_types=["audio", "video"])
                        
                        with gr.Row():
                            model_dropdown = gr.Dropdown(
                                choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"], 
                                value="small", 
                                label="Modelo Whisper"
                            )
                            lang_dropdown = gr.Dropdown(
                                choices=["Auto", "pt", "en", "es", "fr", "de", "it"], 
                                value="Auto", 
                                label="Idioma (Auto = detecao automatica)"
                            )
                        
                        with gr.Row():
                            device_dropdown = gr.Dropdown(
                                choices=["auto", "cuda", "cpu"], 
                                value="auto", 
                                label="Dispositivo"
                            )
                            compute_type_dropdown = gr.Dropdown(
                                choices=["int8", "float16", "float32"], 
                                value="int8", 
                                label="Precisao"
                            )
                            batch_size_slider = gr.Slider(
                                minimum=1, maximum=16, step=1, value=2, 
                                label="WhisperX Batch Size"
                            )
                        
                        gr.Markdown("#### Diarizacao (Identificacao de Locutores)")
                        with gr.Row():
                            diarize_checkbox = gr.Checkbox(value=True, label="Ativar Separacao de Vozes (Diarizacao)")
                            
                            profiles = list_speaker_profiles()
                            profile_choices = ["Nenhum"] + [p["name"] for p in profiles]
                            speaker_profile_dropdown = gr.Dropdown(
                                choices=profile_choices,
                                value="Nenhum",
                                label="Perfil de Oradores (Opcional)"
                            )
                        
                        with gr.Row():
                            num_speakers_input = gr.Number(value=0, label="Speakers Exato (0 = auto)", precision=0)
                            min_speakers_input = gr.Number(value=0, label="Speakers Minimo", precision=0)
                            max_speakers_input = gr.Number(value=0, label="Speakers Maximo", precision=0)
                            
                        transcribe_btn = gr.Button("Iniciar Transcricao", variant="primary", size="lg")
                        
                    with gr.Column(scale=6):
                        log_output = gr.Textbox(label="Logs de Execucao (Tempo Real)", lines=15, max_lines=20, interactive=False)
                        results_output = gr.Textbox(label="Visualizacao e Caminhos dos Arquivos de Saida", lines=10, interactive=False)

                # Click binding
                transcribe_btn.click(
                    fn=transcribe_audio_ui,
                    inputs=[
                        file_input, model_dropdown, lang_dropdown, device_dropdown,
                        compute_type_dropdown, batch_size_slider, diarize_checkbox,
                        num_speakers_input, min_speakers_input, max_speakers_input,
                        speaker_profile_dropdown
                    ],
                    outputs=[log_output, results_output]
                )

            # Tab 2: Text to Speech (TTS)
            with gr.TabItem("🗣️ Sintese de Voz (TTS)") as tts_tab:
                gr.Markdown("### Gerar fala realista a partir de texto usando Kokoro ou Piper")
                with gr.Row():
                    with gr.Column(scale=5):
                        text_input = gr.Textbox(
                            label="Texto para sintese", 
                            placeholder="Digite ou cole o roteiro aqui...", 
                            lines=8
                        )
                        file_upload = gr.File(label="Ou carregue um arquivo de texto (.txt)", file_types=[".txt"])
                        
                        with gr.Row():
                            presets_list = list_tts_presets()
                            preset_choices = ["Nenhum"] + [p["name"] for p in presets_list]
                            # Find default preset if exists
                            def_preset_name = "Nenhum"
                            for p in presets_list:
                                if p.get("is_default") == 1:
                                    def_preset_name = p["name"]
                                    break
                                    
                            preset_dropdown = gr.Dropdown(
                                choices=preset_choices,
                                value=def_preset_name,
                                label="Preset de Configuracao (TTS)"
                            )
                            apply_preset_btn = gr.Button("Aplicar Preset", variant="secondary")
                            
                        with gr.Row():
                            engine_dropdown = gr.Dropdown(
                                choices=["kokoro", "piper"], 
                                value="kokoro", 
                                label="Motor TTS"
                            )
                            
                            from src.tts.registry import VOICE_MAPPING
                            default_voices = list(VOICE_MAPPING["kokoro"].keys())
                            
                            voice_dropdown = gr.Dropdown(
                                choices=default_voices, 
                                value=default_voices[0] if default_voices else "", 
                                label="Voz / Modelo",
                                allow_custom_value=True
                            )
                        
                        # Show voice metadata dynamically below selections
                        voice_info_card = gr.Markdown(
                            value=update_voice_info("kokoro", default_voices[0] if default_voices else "")
                        )
                        
                        with gr.Row():
                            format_dropdown = gr.Dropdown(
                                choices=["wav", "mp3"], 
                                value="wav", 
                                label="Formato de Saida"
                            )
                            device_tts_dropdown = gr.Dropdown(
                                choices=["cuda", "cpu"], 
                                value="cuda" if torch.cuda.is_available() else "cpu", 
                                label="Dispositivo"
                            )
                            speed_slider = gr.Slider(
                                minimum=0.5, maximum=2.0, step=0.1, value=1.0, 
                                label="Velocidade da Fala"
                            )
                            preview_chars_slider = gr.Slider(
                                minimum=100, maximum=1000, step=50, value=300, 
                                label="Caracteres da Previa"
                            )
                        
                        with gr.Row():
                            analyze_ptbr_cb = gr.Checkbox(
                                label="Analisar texto PT-BR (detectar acentos ausentes)",
                                value=False
                            )
                            normalize_ptbr_cb = gr.Checkbox(
                                label="Aplicar normalizacao PT-BR simples (corrigir acentos basicos)",
                                value=False
                            )
                        ptbr_analysis_md = gr.Markdown("", label="Resultado da Analise PT-BR")

                        with gr.Row():
                            preview_btn = gr.Button("Gerar Previa (Rápido)", variant="secondary")
                            full_btn = gr.Button("Gerar Audio Completo", variant="primary")
                            
                    with gr.Column(scale=6):
                        audio_output = gr.Audio(label="Player de Audio Gerado", type="filepath")
                        status_output = gr.Textbox(label="Informacoes do Processamento", lines=10, interactive=False)
                        
                        gr.Markdown("⚠️ **Aviso de Ética e Licencamento:**\n"
                                    "Esta ferramenta e destinada apenas a fins legitimos e locais. "
                                    "Nao utilize para clonar vozes de terceiros sem autorizacao, criar deepfakes enganosos, "
                                    "imitar celebridades ou pessoas reais com fins de engano ou difamacao. "
                                    "Verifique a licenca de cada modelo/voz antes de utilizacao comercial.")

                # Events
                engine_dropdown.change(
                    fn=on_engine_change_with_card,
                    inputs=[engine_dropdown],
                    outputs=[voice_dropdown, voice_info_card]
                )
                
                voice_dropdown.change(
                    fn=update_voice_info,
                    inputs=[engine_dropdown, voice_dropdown],
                    outputs=[voice_info_card]
                )
                
                apply_preset_btn.click(
                    fn=apply_preset_to_fields,
                    inputs=[preset_dropdown],
                    outputs=[engine_dropdown, voice_dropdown, format_dropdown, speed_slider, preview_chars_slider, voice_info_card]
                )
                
                preview_btn.click(
                    fn=lambda text, f, eng, vc, fmt, dev, chars, speed, anlz, norm: generate_tts_ui(
                        text, f, eng, vc, fmt, True, chars, dev, speed, anlz, norm
                    ),
                    inputs=[text_input, file_upload, engine_dropdown, voice_dropdown, format_dropdown, device_tts_dropdown, preview_chars_slider, speed_slider, analyze_ptbr_cb, normalize_ptbr_cb],
                    outputs=[audio_output, status_output, ptbr_analysis_md]
                )

                full_btn.click(
                    fn=lambda text, f, eng, vc, fmt, dev, chars, speed, anlz, norm: generate_tts_ui(
                        text, f, eng, vc, fmt, False, chars, dev, speed, anlz, norm
                    ),
                    inputs=[text_input, file_upload, engine_dropdown, voice_dropdown, format_dropdown, device_tts_dropdown, preview_chars_slider, speed_slider, analyze_ptbr_cb, normalize_ptbr_cb],
                    outputs=[audio_output, status_output, ptbr_analysis_md]
                )

            # Tab 3: Historico
            with gr.TabItem("📜 Historico") as history_tab:
                gr.Markdown("### Historico de Jobs locais (STT e TTS)")
                with gr.Row():
                    filter_dropdown = gr.Dropdown(
                        choices=["Todos", "STT", "TTS"],
                        value="Todos",
                        label="Filtrar por Tipo"
                    )
                    refresh_hist_btn = gr.Button("🔄 Atualizar Historico", variant="secondary")
                    clear_hist_btn = gr.Button("🗑️ Limpar Historico", variant="stop")
                
                jobs_state = gr.State([])
                
                history_df = gr.Dataframe(
                    headers=["ID", "Tipo", "Status", "Data", "Entrada", "Motor/Modelo", "Voz/Idioma", "Caminho de Saida"],
                    datatype=["str", "str", "str", "str", "str", "str", "str", "str"],
                    interactive=False,
                    label="Lista de Execucoes Recentes (Clique em uma linha para ver detalhes)"
                )
                
                with gr.Row():
                    with gr.Column(scale=6):
                        job_details_md = gr.Markdown("*Selecione um job na tabela acima para ver os detalhes completos.*")
                    with gr.Column(scale=5):
                        hist_audio_player = gr.Audio(label="Player de Audio (Apenas para TTS)", type="filepath", interactive=False)

            # Tab 4: Presets e Perfis
            with gr.TabItem("🎛️ Presets e Perfis") as presets_tab:
                from src.tts.registry import VOICE_MAPPING
                preset_default_voices = list(VOICE_MAPPING.get("kokoro", {}).keys())
                
                with gr.Row():
                    # Column 1: Presets TTS
                    with gr.Column(scale=1):
                        gr.Markdown("### 🎛️ Gestao de Presets TTS")
                        preset_msg = gr.Markdown("")
                        preset_list_dropdown = gr.Dropdown(
                            choices=[p["name"] for p in list_tts_presets()],
                            label="Presets Disponiveis",
                            interactive=True
                        )
                        with gr.Row():
                            delete_preset_btn = gr.Button("🗑️ Excluir Preset", variant="stop")
                            set_default_preset_btn = gr.Button("⭐ Definir como Padrao", variant="primary")
                        
                        gr.Markdown("---")
                        gr.Markdown("#### Criar Novo Preset TTS")
                        new_preset_name = gr.Textbox(label="Nome do Preset", placeholder="ex: Minha Voz Kokoro")
                        with gr.Row():
                            new_preset_engine = gr.Dropdown(choices=["kokoro", "piper"], value="kokoro", label="Motor")
                            new_preset_voice = gr.Dropdown(choices=preset_default_voices, value=preset_default_voices[0] if preset_default_voices else "", label="Voz/ID")
                        with gr.Row():
                            new_preset_format = gr.Dropdown(choices=["wav", "mp3"], value="wav", label="Formato")
                            new_preset_speed = gr.Slider(minimum=0.5, maximum=2.0, step=0.1, value=1.0, label="Velocidade")
                        with gr.Row():
                            new_preset_preview = gr.Slider(minimum=100, maximum=1000, step=50, value=300, label="Caracteres Previa")
                            new_preset_chunk = gr.Slider(minimum=100, maximum=1000, step=50, value=400, label="Tamanho Chunk")
                        new_preset_lang = gr.Textbox(label="Idioma (Opcional)", placeholder="ex: pt-br", value="pt-br")
                        create_preset_btn = gr.Button("💾 Salvar Preset", variant="primary")
                        
                    # Column 2: Speaker Profiles STT
                    with gr.Column(scale=1):
                        gr.Markdown("### 👤 Perfis de Oradores (Diarizacao STT)")
                        profile_msg = gr.Markdown("")
                        profile_list_dropdown = gr.Dropdown(
                            choices=[p["name"] for p in list_speaker_profiles()],
                            label="Perfis Disponiveis",
                            interactive=True
                        )
                        delete_profile_btn = gr.Button("🗑️ Excluir Perfil", variant="stop")
                        
                        gr.Markdown("---")
                        gr.Markdown("#### Criar Novo Perfil de Oradores")
                        new_profile_name = gr.Textbox(label="Nome do Perfil", placeholder="ex: Reuniao Equipe")
                        new_profile_mapping = gr.Textbox(
                            label="Mapeamento de Speakers (JSON)", 
                            placeholder='{\n  "SPEAKER_00": "Gabriel",\n  "SPEAKER_01": "Ana"\n}',
                            lines=6
                        )
                        new_profile_notes = gr.Textbox(label="Notas / Descricao (Opcional)", placeholder="ex: Mapeamento padrao para reunioes")
                        create_profile_btn = gr.Button("💾 Salvar Perfil", variant="primary")

            # Tab 5: Models / Voices Status
            with gr.TabItem("📦 Modelos e Vozes") as models_tab:
                gr.Markdown("### Diagnosticos de Componentes e Status do Ambiente")
                status_html = gr.HTML(value=get_system_status_html())
                voices_status_html = gr.HTML(value=get_voices_status_html())
                refresh_btn = gr.Button("Atualizar Status", variant="secondary")

                gr.Markdown("---")
                gr.Markdown(
                    "### 🇧🇷 Comparativo de Vozes PT-BR\n"
                    "Gera um arquivo WAV com cada voz PT-BR registrada usando a mesma frase padrao. "
                    "As vozes que falharem serao listadas no relatorio sem interromper as demais."
                )
                compare_btn = gr.Button("🎙️ Gerar Comparativo PT-BR", variant="primary")
                compare_output = gr.Textbox(
                    label="Resultado do Comparativo",
                    lines=12,
                    interactive=False
                )

                def refresh_all_status():
                    return get_system_status_html(), get_voices_status_html()

                refresh_btn.click(
                    fn=refresh_all_status,
                    inputs=[],
                    outputs=[status_html, voices_status_html]
                )

                compare_btn.click(
                    fn=run_compare_voices_ui,
                    inputs=[],
                    outputs=[compare_output]
                )

            # Tab 6: Settings
            with gr.TabItem("⚙️ Configuracoes") as settings_tab:
                gr.Markdown("### Opcoes do Historico e Privacidade")
                
                with gr.Row():
                    history_enabled_cb = gr.Checkbox(label="Ativar Historico de Execucoes", value=True)
                    save_full_text_cb = gr.Checkbox(label="Salvar Texto Completo no Historico (STT/TTS)", value=False)
                
                save_settings_btn = gr.Button("💾 Salvar Opcoes de Historico", variant="primary")
                settings_msg = gr.Markdown("")
                
                gr.Markdown("---")
                gr.Markdown("### Caminhos Globais do Sistema e Variaveis")
                settings_html = gr.HTML(value=get_settings_html())
                refresh_settings_btn = gr.Button("Atualizar Caminhos", variant="secondary")
                
                refresh_settings_btn.click(
                    fn=get_settings_html,
                    inputs=[],
                    outputs=[settings_html]
                )

        # Tab Events Wiring
        # STT Tab selection updates profiles dropdown
        stt_tab.select(
            fn=refresh_stt_profiles_dropdown,
            inputs=[],
            outputs=[speaker_profile_dropdown]
        )
        
        # TTS Tab selection updates presets dropdown
        tts_tab.select(
            fn=refresh_tts_presets_dropdown,
            inputs=[],
            outputs=[preset_dropdown]
        )
        
        # History Tab selection loads the dataframe
        history_tab.select(
            fn=load_history_ui,
            inputs=[filter_dropdown],
            outputs=[history_df, jobs_state]
        )
        
        # Refresh history button
        refresh_hist_btn.click(
            fn=load_history_ui,
            inputs=[filter_dropdown],
            outputs=[history_df, jobs_state]
        )
        
        # Clear history button
        clear_hist_btn.click(
            fn=clear_history_ui,
            inputs=[filter_dropdown],
            outputs=[history_df, jobs_state]
        )
        
        # Click on cell in history dataframe
        history_df.select(
            fn=on_history_row_select,
            inputs=[jobs_state],
            outputs=[job_details_md, hist_audio_player]
        )
        
        # Presets & Profiles Tab selection
        presets_tab.select(
            fn=refresh_presets_and_profiles_ui,
            inputs=[],
            outputs=[preset_list_dropdown, profile_list_dropdown]
        )
        
        # Preset Management
        new_preset_engine.change(
            fn=on_engine_change_simple,
            inputs=[new_preset_engine],
            outputs=[new_preset_voice]
        )
        
        create_preset_btn.click(
            fn=create_preset_ui,
            inputs=[
                new_preset_name, new_preset_engine, new_preset_voice,
                new_preset_format, new_preset_speed, new_preset_preview,
                new_preset_chunk, new_preset_lang
            ],
            outputs=[preset_msg, preset_list_dropdown, preset_dropdown]
        )
        
        delete_preset_btn.click(
            fn=delete_preset_ui,
            inputs=[preset_list_dropdown],
            outputs=[preset_msg, preset_list_dropdown, preset_dropdown]
        )
        
        set_default_preset_btn.click(
            fn=set_default_preset_ui,
            inputs=[preset_list_dropdown],
            outputs=[preset_msg]
        )
        
        # Profile Management
        create_profile_btn.click(
            fn=create_profile_ui,
            inputs=[new_profile_name, new_profile_mapping, new_profile_notes],
            outputs=[profile_msg, profile_list_dropdown, speaker_profile_dropdown]
        )
        
        delete_profile_btn.click(
            fn=delete_profile_ui,
            inputs=[profile_list_dropdown],
            outputs=[profile_msg, profile_list_dropdown, speaker_profile_dropdown]
        )
        
        # Settings Tab selection
        settings_tab.select(
            fn=load_app_settings_ui,
            inputs=[],
            outputs=[history_enabled_cb, save_full_text_cb]
        )
        
        # Save settings button
        save_settings_btn.click(
            fn=save_app_settings,
            inputs=[history_enabled_cb, save_full_text_cb],
            outputs=[settings_msg]
        )
                
    return app
