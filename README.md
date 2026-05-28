# Pipeline Local de Transcrição e Diarização de Voz (Audio-to-Text)

Este projeto implementa um pipeline completo em Python para transcrição de áudio e vídeo local, com identificação precisa de "quem falou quando" (Speaker Diarization). 

O pipeline baseia-se em **modelos de IA locais** para garantir privacidade, velocidade e zero custos com APIs externas.

---

## 🛠️ Stack Tecnológica

- **Python 3.10+**
- **FFmpeg** (para extração, conversão e normalização de áudio/vídeo)
- **WhisperX** (baseado no `faster-whisper` e CTranslate2 para transcrição acelerada com alinhamento de palavras)
- **pyannote.audio** (para separação de vozes/diarização via Hugging Face)
- **PyTorch + CUDA 12.6** (para aceleração por GPU de forma nativa)

---

## 📋 Pré-requisitos

1. **Python 3.10.11** instalado no sistema.
2. **FFmpeg** instalado e adicionado ao PATH do Windows.
   - Para verificar se está pronto, abra um terminal e rode: `ffmpeg -version`
3. **GPU NVIDIA (Recomendado):** O script foi otimizado para placas com pouca VRAM (como a RTX 3050 de 4GB), mas também possui fallback automático para execução em CPU.

---

## 🚀 Instalação e Configuração

Fornecemos scripts do PowerShell para automatizar a criação do ambiente virtual (`.venv`) e instalação de todas as dependências complexas (incluindo o PyTorch com suporte a CUDA).

### Opção A: Instalação com Aceleração por GPU (Recomendado)
Abra o PowerShell na pasta do projeto e execute:
```powershell
powershell -ExecutionPolicy Bypass -File .\install_gpu.ps1
```
*Este script instalará o PyTorch 2.8.0 com CUDA 12.6, instalará as dependências do `requirements.txt`, compilará o WhisperX diretamente do GitHub e validará se a sua GPU foi reconhecida com sucesso.*

### Opção B: Instalação para rodar apenas em CPU
Se o seu computador não possuir placa de vídeo NVIDIA dedicada:
```powershell
powershell -ExecutionPolicy Bypass -File .\install_cpu.ps1
```

---

## 🔑 Configuração do Hugging Face (Obrigatório para Diarização)

Para identificar diferentes interlocutores (ex: `SPEAKER_00`, `SPEAKER_01`), o modelo Pyannote exige aceitação dos termos de licença e uso de um token de acesso.

1. Crie uma conta ou faça login no [Hugging Face](https://huggingface.co/).
2. Aceite as condições de uso dos seguintes modelos de IA (clique nos links e clique em **Accept** ou **Agree to share info**):
   - [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)
   - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) (opcional, caso queira usar a versão 3.1 diretamente)
   - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0) (opcional, dependência direta de modelos pyannote)
3. Crie um token de acesso **Read** em [hf.co/settings/tokens](https://huggingface.co/settings/tokens).
4. Copie o arquivo `.env.example` para um novo arquivo chamado `.env` na raiz do projeto:
   ```bash
   cp .env.example .env
   ```
5. Insira o seu token copiado no `.env`:
   ```env
   HF_TOKEN=hf_seu_token_aqui
   ```

---

## 💻 Como Utilizar

### 🚀 Modo Fácil: Assistente de Console (Recomendado)

Você não precisa decorar nenhum comando ou parâmetro complexo para rodar a transcrição. Fornecemos um assistente interativo em português para ajudá-lo de forma visual:

1. **Abra o assistente (Duplo Clique):**
   - Dê um duplo clique no arquivo **`transcrever.bat`** na pasta do projeto.
   - Isso abrirá uma janela preta de terminal com um menu de opções numerado.
2. **Escolha o modo de transcrição:**
   - **Opção 1:** Modo Completo (Modelo Medium + CUDA + VAD Sensível) -> **Recomendado para uso geral** (entrevistas, podcasts, gameplays, vídeos). Evita falas cortadas e detecta a quantidade de vozes de forma automática.
   - **Opção 2:** Modo Rápido (Modelo Small) -> Muito mais rápido para testes ou arquivos curtos.
   - **Opção 3:** Apenas Texto -> Transcreve tudo em texto corrido sem separar as vozes (não necessita de Token do Hugging Face).
   - **Opção 4:** Configuração Personalizada -> Permite escolher cada parâmetro (como modelo, idioma, etc.) com explicações simples passo a passo de cada um.
3. **Arraste e solte o arquivo de áudio/vídeo:**
   - Quando o console solicitar o arquivo, basta pegar o arquivo de áudio ou vídeo no seu computador, **arrastar e soltar diretamente dentro da janela preta** e apertar `Enter`.
   - O pipeline começará a rodar sozinho com as configurações ideais.

---

### ⚡ Modo Super Rápido (Arrastar e Soltar no Ícone)

Se você já quer transcrever um vídeo usando o modo recomendado (Modo Completo):
1. No Windows Explorer, **arraste o arquivo de vídeo ou áudio diretamente para cima do ícone do arquivo `transcrever.bat`**.
2. O terminal se abrirá sozinho e iniciará a transcrição imediata com todas as configurações recomendadas, sem fazer nenhuma pergunta.

---

### 🛠️ Modo Avançado (Linha de Comando)

Sempre ative o ambiente virtual antes de executar o script manualmente no terminal:
```powershell
.venv\Scripts\Activate.ps1
```

### 1. Transcrição Básica (Sem Diarização/Vozes)
Caso queira apenas transcrever rapidamente sem separar as vozes (não necessita de token do Hugging Face):
```bash
python transcribe.py inputs/video.mp4 --no-diarization
```

### 2. Transcrição Completa com Diarização (Vozes Separadas)
Se o token estiver configurado no `.env`, o script fará automaticamente a separação das vozes:
```bash
python transcribe.py inputs/video.mp4
```

### 3. Melhorando a Precisão da Transcrição e Evitando Out of Memory (OOM)

O modelo padrão (`small`) oferece boa velocidade e precisão geral, mas pode cometer pequenos erros gramaticais em português (como trocar plural/singular) ou errar nomes próprios incomuns. Para resolver isso:

#### A. Usar um Modelo Maior (Melhor Qualidade)
Em placas de 4GB VRAM (como a RTX 3050), você pode usar o modelo `medium` ou até `large-v3` **desde que utilize precisão `int8`** (que reduz drasticamente o uso de VRAM) e mantenha o `batch_size` baixo (1 ou 2):
```bash
# Alta precisão com modelo medium
python transcribe.py inputs/conversa.mp3 --model medium --compute_type int8 --batch_size 1

# Precisão máxima com modelo large-v3
python transcribe.py inputs/conversa.mp3 --model large-v3 --compute_type int8 --batch_size 1
```

#### B. Usar Contexto Inicial (`--initial-prompt`)
Se a transcrição errar nomes específicos ou termos técnicos recorrentes (ex: escrever "Alice" em vez de "Ares", ou "destina" em vez de "destinos"), você pode dar dicas ao Whisper:
```bash
python transcribe.py inputs/conversa.mp3 --model medium --compute_type int8 --initial-prompt "Olá Ravi, aqui é o Ares. Nossos destinos..."
```
*O prompt inicial serve para guiar o estilo, pontuação e grafia correta de nomes e termos logo no início da transcrição.*

#### C. Evitando Falas Cortadas ou Omitidas (Ajuste de Sensibilidade do VAD)
O WhisperX utiliza um modelo de VAD (Detecção de Atividade de Voz) para segmentar o áudio e ignorar trechos de silêncio antes de transcrever. Se o seu áudio tiver falas muito sussurradas, rápidas ou de baixo volume, o detector de silêncio pode cortar e ignorar diálogos inteiros.

Para evitar que diálogos sejam omitidos, você pode reduzir os limiares de início (`--vad-onset`) e fim (`--vad-offset`) de fala, tornando o detector muito mais sensível:
```bash
# VAD altamente sensível (captura falas sussurradas/silenciosas sem cortar partes do diálogo)
python transcribe.py inputs/EntrevistaDaimonax.mp4 --device cuda --model medium --compute_type int8 --batch_size 1 --num_speakers 2 --language pt --vad-onset 0.1 --vad-offset 0.1
```
- `--vad-onset` (padrão `0.500`): Limiar para iniciar a fala. Valores baixos (ex: `0.1`) são muito mais sensíveis e capturam sons de voz mais baixos de imediato.
- `--vad-offset` (padrão `0.363`): Limiar para encerrar a fala. Valores baixos (ex: `0.1`) fazem o VAD esperar mais antes de decidir que a fala terminou, evitando cortar o fim de frases.
- `--chunk-size` (padrão `30`): Tamanho dos blocos de áudio (em segundos) que são divididos pelo VAD para análise.


### 4. Definindo a Quantidade de Locutores
Fornecer dicas de interlocutores aumenta drasticamente a precisão da diarização:
```bash
# Caso saiba exatamente a quantidade de pessoas
python transcribe.py inputs/reuniao.mp3 --num_speakers 2

# Caso tenha uma estimativa
python transcribe.py inputs/podcast.wav --min_speakers 2 --max_speakers 4
```

### 5. Substituindo SPEAKER_00 por Nomes Reais (Speaker Mapping)
Você pode criar um arquivo JSON simples contendo o mapa de speakers para substituir as tags genéricas por nomes reais:
Crie um arquivo `speakers.json`:
```json
{
  "SPEAKER_00": "Gabriell",
  "SPEAKER_01": "João"
}
```
E rode o script passando este mapeamento:
```bash
python transcribe.py inputs/conversa.mp4 --speaker-map speakers.json
```

### 6. Processando uma Pasta Inteira
Para transcrever múltiplos arquivos de uma só vez, aponte para um diretório:
```bash
# Transcreve todos os arquivos da pasta inputs/
python transcribe.py inputs/

# Transcreve recursivamente em todas as subpastas
python transcribe.py inputs/ --recursive
```

---

## 📁 Arquivos Gerados na Saída (`outputs/`)

Para cada arquivo processado (ex: `aula.mp4`), o pipeline gera:
1. **`aula.txt`**: Transcrição formatada como roteiro de diálogo com timestamps simples (ex: `[00:00:12] Gabriell: Olá...`).
2. **`aula.json`**: Estrutura de dados completa retornada pelos modelos, contendo timestamps por palavra e dados brutos.
3. **`aula.srt`**: Legenda padrão compatível com a maioria dos players (VLC, YouTube, etc.).
4. **`aula.vtt`**: Legenda em formato WebVTT.

### 📐 Regras de Legenda Implementadas
As legendas geradas seguem diretrizes profissionais de legibilidade:
- Máximo de **2 linhas** por bloco.
- Máximo de **42 caracteres** por linha (quebras automáticas inteligentes).
- Duração mínima de **1,0 segundo** e máxima de **6,0 segundos**.
- Quebra automática de legenda sempre que houver **mudança de locutor**.

---

## ⚙️ Parâmetros Disponíveis (CLI)

| Parâmetro | Padrão | Descrição |
| :--- | :--- | :--- |
| `input_path` | *(Obrigatório)* | Caminho do arquivo ou pasta a transcrever. |
| `--model` | `small` | Tamanho do modelo Whisper (`tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`). |
| `--language` | `None` | Código do idioma (ex: `pt`, `en`, `es`). Auto-detetado se omitido. |
| `--initial-prompt` | `None` | Texto inicial para dar contexto e vocabulário ao Whisper (ex: nomes próprios, termos técnicos). |
| `--compute_type` | `int8` | Tipo de computação/precisão (`int8`, `float16`, `float32`). |
| `--batch_size` | `2` | Tamanho do lote para execução. |
| `--num_speakers` | `None` | Número exato de interlocutores. |
| `--min_speakers` | `None` | Número mínimo de interlocutores. |
| `--max_speakers` | `None` | Número máximo de interlocutores. |
| `--output_dir` | `outputs` | Pasta onde as exportações serão salvas. |
| `--formats` | `txt json srt vtt` | Formatos de exportação (separados por espaço). |
| `--no-diarization` | `False` | Pula a etapa de diarização. |
| `--keep-wav` | `False` | Mantém o arquivo WAV mono 16kHz temporário. |
| `--device` | `auto` | Dispositivo de hardware (`auto`, `cuda`, `cpu`). |
| `--hf-token` | `None` | Token do Hugging Face (sobrescreve o `.env`). |
| `--diarize-model` | `pyannote/...-1` | Modelo do Hugging Face usado para diarização. |
| `--speaker-map` | `None` | Caminho do JSON contendo o mapeamento de speakers. |
| `--recursive` | `False` | Busca arquivos de forma recursiva nas pastas. |
| `--chunk-size` | `30` | Tamanho do chunk para processamento do VAD em segundos. |
| `--vad-onset` | `0.500` | Limiar de início de fala para o VAD (menor = mais sensível). |
| `--vad-offset` | `0.363` | Limiar de fim de fala para o VAD (menor = mais sensível). |
| `--offline` | `False` | Ativa o modo offline do Hugging Face Hub (usa apenas cache local). |
| `--cache-dir` | `None` | Caminho do diretório de cache do Hugging Face (sobrescreve HF_HOME). |

---

## Hugging Face Cache and Offline Mode

O Hugging Face é necessário exclusivamente para autenticar e descarregar os modelos de diarização (separação de vozes) do `pyannote`. Toda a transcrição e processamento ocorrem **100% localmente** na sua máquina.

Para otimizar o uso do cache e evitar downloads repetitivos (mesmo se você apagar ou recriar o ambiente virtual `.venv`), você pode configurar um cache permanente fora do diretório do projeto.

### 1. Definindo Cache Permanente via `.env`

Defina a variável `HF_HOME` no seu arquivo `.env` apontando para uma pasta permanente (use barras `/` no Windows para evitar conflitos de escape):

```env
HF_HOME=D:/huggingface_cache
```

Isso fará com que todos os modelos baixados fiquem salvos em `D:/huggingface_cache/hub`.

### 2. Modo Offline (`--offline` ou `HF_HUB_OFFLINE=1`)

Depois de executar a transcrição pela primeira vez e descarregar os modelos necessários no cache, você pode rodar o pipeline de forma totalmente offline. Isso impede chamadas desnecessárias de verificação ao Hugging Face Hub e acelera a inicialização:

**Primeira execução (Online - para baixar os modelos no cache):**
```powershell
.venv\Scripts\python transcribe.py inputs/dialogo_teste.mp3 --language pt --model small --compute_type int8 --batch_size 2 --device cuda --cache-dir D:/huggingface_cache
```

**Execuções subsequentes (Offline - sem acesso à rede):**
```powershell
.venv\Scripts\python transcribe.py inputs/video.mp4 --language pt --model small --compute_type int8 --batch_size 2 --device cuda --cache-dir D:/huggingface_cache --offline
```

*Nota: Se você tentar rodar no modo offline (`--offline`) sem ter baixado o modelo previamente na pasta de cache configurada, o script exibirá um erro claro explicando a situação em vez de quebrar com um traceback.*

---

## 🎙️ Fase 2: Speech Studio (Interface Gradio & Síntese de Voz - TTS)

A Fase 2 expande este projeto para um estúdio de áudio profissional local completo, adicionando uma interface web interativa baseada em **Gradio** e suporte à síntese de voz (Text-to-Speech) com os motores **Kokoro** (alto desempenho e naturalidade) e **Piper** (síntese extremamente rápida).

### 🚀 Novas Funcionalidades

1. **Interface Gráfica Baseada em Gradio (`app.py`):**
   - **Tab de Transcrição (STT):** Faça upload de arquivos, configure o modelo Whisper, Batch Size, precisão e parâmetros de diarização. O pipeline é executado em um subprocesso isolado para liberar completamente a VRAM da GPU ao finalizar, evitando falhas de memória (OOM).
   - **Tab de Síntese de Voz (TTS):** Escreva roteiros, selecione vozes, configure a velocidade e o formato de saída (WAV/MP3). Inclui um fluxo de **Prévia Rápida** (default: primeiros 300 caracteres) para testar a entonação antes de gerar o áudio completo.
   - **Tab de Modelos e Vozes:** Veja o status detalhado da GPU (CUDA), FFmpeg, eSpeak NG, Kokoro e Piper.
   - **Tab de Configurações:** Verifique as variáveis de ambiente (`HF_HOME`, `HF_HUB_OFFLINE`) e o status do token Hugging Face de forma segura (nunca revelando o token).

2. **CLI de Síntese de Voz (`synthesize.py`):**
   - Permite sintetizar textos via linha de comando com suporte a quebra inteligente de sentenças (chunks de até 400 caracteres) e conversão para MP3 via FFmpeg.

---

### 📦 Instalação do Módulo de TTS e App

1. **Instalar dependências adicionais:**
   Abra o PowerShell na pasta do projeto e execute:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install_tts.ps1
   ```
   *Este script instalará os pacotes do `requirements-tts.txt` (Gradio, Kokoro, onnxruntime e Piper) e verificará a presença do eSpeak NG.*

2. **Instalar eSpeak NG (Obrigatório para TTS):**
   Tanto o Kokoro quanto o Piper utilizam o `espeak-ng` para conversão de texto em fonemas no Windows:
   - Baixe o instalador `.msi` da [página de lançamentos do espeak-ng](https://github.com/espeak-ng/espeak-ng/releases).
   - Execute o instalador (ex: `espeak-ng-1.52.0-x64.msi`).
   - Se o instalador não adicionar o diretório automaticamente ao PATH, o script do Speech Studio tentará localizá-lo em caminhos comuns (`C:\Program Files\eSpeak NG` ou `C:\Program Files (x86)\eSpeak NG`) automaticamente.

---

### 💻 Como Usar a Síntese de Voz (CLI)

Use o script `synthesize.py` para gerar áudios a partir de textos:

#### 1. Síntese Básica com Kokoro (Voz Padrão Dora - PT-BR)
```bash
python synthesize.py --text "Olá, isto é um teste do Speech Studio com o motor Kokoro." --engine kokoro --output outputs/speech/teste_kokoro.wav
```

#### 2. Síntese com Piper (Voz Lula - PT-BR)
*O motor Piper baixará automaticamente os arquivos do modelo (`.onnx` e `.onnx.json`) do Hugging Face na primeira execução, salvando-os na pasta `voices/`.*
```bash
python synthesize.py --text "Olá, este é um teste utilizando o Piper localmente." --engine piper --voice pt_br_lula --output outputs/speech/teste_piper.wav
```

#### 3. Síntese a partir de arquivo de texto (.txt) com Prévia (Preview)
```bash
python synthesize.py --input roteiro.txt --engine kokoro --preview --preview-chars 300 --output outputs/speech/previa_roteiro.wav
```

#### 4. Exportar diretamente em MP3
```bash
python synthesize.py --text "Texto exportado em MP3." --engine kokoro --format mp3 --output outputs/speech/saida.mp3
```

---

### 🖥️ Iniciando a Interface Web (Gradio)

Abra o PowerShell no projeto e execute:
```powershell
powershell -ExecutionPolicy Bypass -File .\launch_app.ps1
```
Ou execute diretamente:
```bash
python app.py
```
Isso iniciará um servidor web local em `http://127.0.0.1:7860`. Abra este endereço no navegador para utilizar o Speech Studio de forma visual.

---

### ⚠️ AVISO DE ÉTICA E SEGURANÇA

This tool is intended for local speech transcription and local text-to-speech generation. Do not use it to impersonate real people, clone voices without permission, scam, defame, or mislead others. Only use voice cloning or speaker-like synthesis with your own voice or with explicit consent. For commercial use, verify the license of each model and voice.

---

## 🔍 Resolução de Problemas & Diagnósticos (Troubleshooting / Healthcheck)

Para facilitar a identificação e resolução de problemas comuns na configuração do ambiente, o Speech Studio inclui ferramentas de diagnóstico integradas.

### 1. Diagnóstico do Sistema via Linha de Comando (Healthcheck)

Você pode verificar a saúde das dependências, caminhos, GPU e variáveis de ambiente executando o comando `--healthcheck` em qualquer um dos pontos de entrada:

```bash
# Executa diagnosticos pelo launcher do app
python app.py --healthcheck

# Ou pelo utilitario de sintese de voz
python synthesize.py --healthcheck
```

Este comando verifica rapidamente:
* Versão do Python e diretório raiz do projeto.
* Instalação de pacotes críticos (PyTorch, WhisperX, Gradio, Kokoro, Piper).
* Disponibilidade de GPU/CUDA.
* Presença do executável **FFmpeg** no PATH.
* Instalação e configuração do **eSpeak NG**.
* Status e existência das pastas de cache e saída.
* Segurança do token do Hugging Face (mostra se está configurado sem expor o token).

> [!NOTE]
> O comando de healthcheck roda instantaneamente sem inicializar modelos neurais pesados na GPU e sem fazer downloads de pesos.

---

### 2. Resolvendo Problemas com eSpeak NG no Windows
Se o healthcheck ou a síntese (Kokoro/Piper) indicar falta do **eSpeak NG**, os modelos falharão em converter texto em fonemas.

**Como Resolver:**
1. Baixe o instalador oficial do eSpeak NG para Windows `.msi` a partir do repositório oficial [espeak-ng/espeak-ng Releases](https://github.com/espeak-ng/espeak-ng/releases) (ex: `espeak-ng-X.XX-x64.msi`).
2. Instale-o no caminho padrão (`C:\Program Files\eSpeak NG`).
3. O aplicativo tentará localizar o eSpeak automaticamente na pasta de instalação. Se mesmo assim não for detectado, adicione a variável de ambiente:
   * **Nome:** `PHONEMIZER_ESPEAK_PATH`
   * **Valor:** `C:\Program Files\eSpeak NG` (ou a pasta onde instalou)

---

### 3. Resolvendo Falhas de FFmpeg (Conversões de Áudio)
O FFmpeg é necessário para segmentar arquivos de áudio longos na transcrição (STT) e para converter arquivos WAV gerados em MP3 na síntese de voz (TTS).

**Como Resolver:**
1. Baixe os binários estáticos do FFmpeg para Windows (como de [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)).
2. Extraia os arquivos para uma pasta permanente (ex: `C:\ffmpeg`).
3. Adicione o caminho do diretório `bin` (ex: `C:\ffmpeg\bin`) à variável de ambiente `PATH` do sistema.
4. Reinicie o terminal e valide executando `ffmpeg -version`.

---

### 4. Otimização de VRAM e Erros de Out-Of-Memory (OOM)
Se você estiver utilizando uma GPU com pouca VRAM (ex: 4GB como a RTX 3050 Laptop), processar transcrições longas com diarização pode estourar a memória.

**Ações Recomendadas:**
* **Diminua o tamanho do lote (batch size):** Use `--batch_size 4` ou `--batch_size 2` na chamada do CLI `transcribe.py`.
* **Use precisão reduzida:** O WhisperX por padrão utiliza `float16` em CUDA, o que é ótimo para economia de VRAM. Garanta que `--compute_type float16` esteja sendo usado (padrão em GPU).
* **Forçar CPU para TTS:** Se quiser economizar VRAM durante a geração de áudio ou estiver tendo conflitos, você pode rodar a síntese em CPU selecionando "cpu" na interface ou passando `--device cpu` no `synthesize.py`. Os motores Kokoro e Piper rodam de forma muito eficiente em CPU.

---

### 5. Configuração Segura de Cache e Tokens
Para rodar a diarização (pyannote), é obrigatório possuir um token do Hugging Face e aceitar os termos do modelo no site do Hugging Face.

* **Onde colocar o token:** Salve-o no arquivo `.env` na raiz do projeto como `HF_TOKEN=seu_token_aqui`. Nunca comite ou envie o arquivo `.env` para o Git (ele já está no `.gitignore`).
* **Proteção de Segredos:** O healthcheck nunca imprime ou registra o valor real do seu token, mostrando apenas `Found (Masked)`.
* **Modo Offline:** Se precisar trabalhar totalmente offline após ter baixado os modelos uma vez, defina `HF_HUB_OFFLINE=1` e defina um caminho permanente para o cache na variável `HF_HOME` do arquivo `.env`.

---

## 🎛️ Presets, Perfis e Histórico Local (Phase 3)

O Speech Studio agora conta com um banco de dados local SQLite (`data/speech_studio.db`) para guardar o histórico de execuções, presets de configuração de voz (TTS) e perfis de mapeamento de interlocutores (STT/Diarização).

### 1. Histórico Local de Execuções (Jobs)

Todas as transcrições (STT) e sínteses de voz (TTS) executadas via CLI ou interface são salvas na tabela de histórico por padrão.
* **Segurança e Privacidade:** O texto completo não é guardado no banco por padrão. Armazena-se apenas um pequeno fragmento (snippet) de até 300 caracteres.
* **Salvar Texto Completo:** Caso queira armazenar o conteúdo na íntegra nos metadados JSON do banco, passe o argumento `--save-full-text` no CLI ou ative a opção "Salvar Texto Completo no Histórico" na aba **⚙️ Configurações** da interface.
* **Desativar Histórico:** Use o argumento `--no-history` no CLI ou desmarque "Ativar Histórico de Execuções" na interface.
* **Precedência:** A flag `--no-history` ou a desativação nas configurações globais cancelará a gravação.

### 2. Presets de Parâmetros (TTS)

Evite redigitar parâmetros complexos de velocidade, motor, voz e caracteres de prévia a cada síntese de áudio.
* **Ordem de Precedência:** Parâmetro CLI explícito > Preset configurado > Valores padrões da aplicação.
* **Utilização via CLI:**
  ```bash
  python synthesize.py --text "Olá, usando configurações personalizadas." --preset "Narrador Kokoro Alex"
  ```
* **Utilização via UI:** Selecione o preset desejado na aba de síntese de voz e clique em **Aplicar Preset** para preencher instantaneamente todos os controles deslizantes, caixas de seleção e tabelas de voz correspondentes.
* **Gestão de Presets:** Na aba **🎛️ Presets e Perfis**, é possível criar novos presets com velocidades customizadas, excluir presets existentes ou definir um deles como o padrão global a ser carregado ao iniciar o estúdio.

### 3. Perfis de Interlocutores (Speaker Profiles)

Ao invés de passar arquivos `.json` de mapeamento de locutores externos via CLI, salve-os localmente como perfis reutilizáveis.
* **Mapeamento JSON:** Cada perfil contém uma estrutura de chaves e valores mapeando o locutor detectado ao seu respectivo nome (ex: `{"SPEAKER_00": "Gabriel", "SPEAKER_01": "Dra. Ana"}`).
* **Utilização via CLI:**
  ```bash
  python transcribe.py inputs/reuniao.wav --speaker-profile "Entrevista Podcast"
  ```
* **Sobrescrita/Mesclagem:** Se você passar simultaneamente o argumento `--speaker-profile` e um arquivo `--speaker-map`, as chaves fornecidas no arquivo de mapeamento CLI explícito terão prioridade máxima e serão mescladas sobre as chaves do perfil de banco.
* **Gestão de Perfis:** Crie e gerencie perfis na aba **🎛️ Presets e Perfis**. Os perfis salvos ficarão disponíveis para seleção instantânea tanto no console launcher wizard quanto no dropdown da aba de transcrição do Gradio.

## Phase 4: Modern React Frontend + FastAPI Bridge

O `app.py` com Gradio continua disponível como interface legada/local. A interface moderna agora vive no frontend React gerado pelo Lovable, vendorizado em `frontend/`, e a comunicação com o backend Python existente passa por uma bridge FastAPI em `api/`.

### Como instalar as dependências da API

```powershell
pip install -r requirements-api.txt
```

### Como executar a API

```powershell
.\run_api.ps1
```

### Como executar o frontend React

```powershell
.\run_frontend.ps1
```

### Como executar ambos

```powershell
.\run_studio.ps1
```

### URLs

- API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- React Frontend: [http://127.0.0.1:8080](http://127.0.0.1:8080)
- Gradio Legacy: [http://127.0.0.1:7860](http://127.0.0.1:7860)

### Notas operacionais

- O frontend Lovable permanece como fonte de verdade visual. As alterações desta fase são apenas de integração.
- Quando a API estiver offline, as páginas conectadas usam fallback para `mockData.ts` sem quebrar a interface.
- Áudios e transcrições gerados são servidos apenas por diretórios whitelisted:
  - `outputs/speech`
  - `outputs/transcriptions`
  - `outputs/speech/voice_compare`
- A rota de ficheiros bloqueia path traversal, `.env`, bases SQLite, caches, modelos e ficheiros arbitrários.
- O heavy-job lock da API é local e em memória. Ele é suficiente para esta fase de uso local, mas não é uma fila persistente.


