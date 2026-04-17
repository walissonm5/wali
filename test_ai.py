import os
import configparser
from groq import Groq
from colorama import Fore, Style, init

init(autoreset=True)

def log_info(message): print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} {message}")
def log_warn(message): print(f"{Fore.YELLOW}[AVISO]{Style.RESET_ALL} {message}")
def log_error(message): print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} {message}")

def test_groq_configuration():
    log_info("Iniciando teste de configuração da GroqCloud...")

    # 1. Ler config.ini
    config = configparser.ConfigParser()
    config_file_path = 'config.ini'
    
    if not os.path.exists(config_file_path):
        log_error("Arquivo config.ini não encontrado. Execute ./setup.sh primeiro.")
        return False
        
    try:
        config.read(config_file_path)
        api_key = config.get('AI', 'GROQ_API_KEY', fallback=None)
        ai_model = config.get('AI', 'MODEL', fallback='llama-3.3-70b-versatile')
    except Exception as e:
        log_error(f"Erro ao ler config.ini: {e}")
        return False

    if not api_key:
        log_error("GROQ_API_KEY não encontrada no config.ini.")
        return False
        
    log_info(f"Modelo selecionado: {ai_model}")

    # 2. Tentar fazer uma chamada simples à API da Groq
    try:
        client = Groq(api_key=api_key)
        log_info(f"Tentando chamar a API da Groq com o modelo: {ai_model}...")
        
        completion = client.chat.completions.create(
            model=ai_model,
            messages=[{"role": "user", "content": "Responda apenas com a palavra 'CONECTADO'."}],
            max_tokens=5
        )
        
        response_text = completion.choices[0].message.content.strip().upper()
        if "CONECTADO" in response_text:
            log_info(f"Conexão com a GroqCloud bem-sucedida! Resposta: '{response_text}'")
            return True
        else:
            log_error(f"A IA respondeu, mas a resposta não foi a esperada. Resposta: '{response_text}'")
            return False
            
    except Exception as e:
        log_error(f"Falha ao conectar ou obter resposta da GroqCloud. Erro: {e}")
        log_error("Verifique sua GROQ_API_KEY no config.ini e sua conexão com a internet.")
        return False

if __name__ == "__main__":
    if test_groq_configuration():
        log_info("Teste de IA (GroqCloud) concluído com SUCESSO!")
    else:
        log_error("Teste de IA (GroqCloud) concluído com FALHA.")
