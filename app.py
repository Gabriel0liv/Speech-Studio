import argparse
import sys
import os

# Ensure package root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description="Inicia o Speech Studio (Gradio App).")
    parser.add_argument("--port", type=int, default=7860, help="Porta para rodar o Gradio (padrao: 7860)")
    parser.add_argument("--server-name", type=str, default="127.0.0.1", help="Nome do servidor (ex: 0.0.0.0 para acesso externo, padrao: 127.0.0.1)")
    parser.add_argument("--share", action="store_true", help="Cria um link publico do Gradio")
    parser.add_argument("--healthcheck", action="store_true", help="Executa o diagnostico do sistema e encerra")
    
    args = parser.parse_args()
    
    if args.healthcheck:
        from src.core.healthcheck import run_healthcheck
        success = run_healthcheck()
        sys.exit(0 if success else 1)
        
    try:
        from src.ui.gradio_app import build_app, APP_CSS
    except ImportError as e:
        print(f"[!] Erro ao importar a aplicacao: {e}")
        print("    Por favor, execute './install_tts.ps1' para instalar as dependencias de Gradio e TTS.")
        sys.exit(1)
    
    print("[*] A carregar o Speech Studio local...")
    try:
        app = build_app()
        print(f"[*] A iniciar o servidor Gradio em http://{args.server_name}:{args.port} ...")
        app.launch(
            server_name=args.server_name,
            server_port=args.port,
            share=args.share,
            css=APP_CSS
        )
    except Exception as e:
        print(f"\n[!] Erro fatal ao iniciar o aplicativo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
