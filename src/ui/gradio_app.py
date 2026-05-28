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
    return "🔴 Nao encontrado", "O eSpeak NG e necessario para transcricao de fonemas. Instale-o via instalador Windows (.msi)."

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

def transcribe_audio_ui(file_obj, model, language, device, compute_type, batch_size, diarize, num_speakers, min_speakers, max_speakers):
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

def generate_tts_ui(text, upload_file, engine, voice, format, preview, preview_chars, device):
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
        return None, "Erro: Escreva algum texto ou faca o upload de um arquivo .txt."

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
            "--device", device
        ]

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
            return None, f"Erro na sintese de audio (codigo {rc}):\n{log}"
            
        if os.path.exists(output_file):
            return output_file, f"Audio sintetizado com sucesso!\nSalvo em: {os.path.abspath(output_file)}\n\nLog do processo:\n{log}"
        else:
            return None, f"Erro: O processo terminou com sucesso, mas o arquivo de audio nao foi localizado.\nLog:\n{log}"
            
    finally:
        # Clean up temporary file
        if os.path.exists(temp_txt):
            debug_mode = os.getenv("DEBUG") in ["1", "True", "true"]
            if not debug_mode:
                try:
                    os.remove(temp_txt)
                except Exception:
                    pass

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
            with gr.TabItem("🎙️ Transcricao (STT)"):
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
                        diarize_checkbox = gr.Checkbox(value=True, label="Ativar Separacao de Vozes (Diarizacao)")
                        
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
                        num_speakers_input, min_speakers_input, max_speakers_input
                    ],
                    outputs=[log_output, results_output]
                )

            # Tab 2: Text to Speech (TTS)
            with gr.TabItem("🗣️ Sintese de Voz (TTS)"):
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
                            preview_chars_slider = gr.Slider(
                                minimum=100, maximum=1000, step=50, value=300, 
                                label="Caracteres da Previa"
                            )
                        
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
                
                preview_btn.click(
                    fn=lambda text, f, eng, vc, fmt, dev, chars: generate_tts_ui(
                        text, f, eng, vc, fmt, True, chars, dev
                    ),
                    inputs=[text_input, file_upload, engine_dropdown, voice_dropdown, format_dropdown, device_tts_dropdown, preview_chars_slider],
                    outputs=[audio_output, status_output]
                )
                
                full_btn.click(
                    fn=lambda text, f, eng, vc, fmt, dev, chars: generate_tts_ui(
                        text, f, eng, vc, fmt, False, chars, dev
                    ),
                    inputs=[text_input, file_upload, engine_dropdown, voice_dropdown, format_dropdown, device_tts_dropdown, preview_chars_slider],
                    outputs=[audio_output, status_output]
                )

            # Tab 3: Models / Voices Status
            with gr.TabItem("📦 Modelos e Vozes"):
                gr.Markdown("### Diagnosticos de Componentes e Status do Ambiente")
                status_html = gr.HTML(value=get_system_status_html())
                voices_status_html = gr.HTML(value=get_voices_status_html())
                refresh_btn = gr.Button("Atualizar Status", variant="secondary")
                
                def refresh_all_status():
                    return get_system_status_html(), get_voices_status_html()
                
                refresh_btn.click(
                    fn=refresh_all_status,
                    inputs=[],
                    outputs=[status_html, voices_status_html]
                )

            # Tab 4: Settings
            with gr.TabItem("⚙️ Configuracoes"):
                gr.Markdown("### Caminhos Globais do Sistema e Variaveis")
                settings_html = gr.HTML(value=get_settings_html())
                refresh_settings_btn = gr.Button("Atualizar Configuracoes", variant="secondary")
                
                refresh_settings_btn.click(
                    fn=get_settings_html,
                    inputs=[],
                    outputs=[settings_html]
                )
                
    return app
