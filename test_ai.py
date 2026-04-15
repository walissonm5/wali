import os
import configparser
from openai import OpenAI
from colorama import Fore, Style, init

init(autoreset=True)

def log_info(message): print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} {message}")
def log_warn(message): print(f"{Fore.YELLOW}[WARN]{Style.RESET_ALL} {message}")
def log_error(message): print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")

def test_ai_configuration():
    log_info("Iniciando teste de configuração da IA...")

    # 1. Verificar OPENAI_API_KEY
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        log_error("Variável de ambiente OPENAI_API_KEY não encontrada. Por favor, defina-a antes de executar o script.")
        return False
    log_info("OPENAI_API_KEY encontrada.")

    # 2. Ler o modelo de IA de config.ini
    config = configparser.ConfigParser()
    config_file_path = 'config.ini'
    ai_model = 'gpt-4.1-mini' # Default fallback

    if os.path.exists(config_file_path):
        try:
            config.read(config_file_path)
            ai_model = config.get('AI', 'MODEL', fallback=ai_model)
            log_info(f"Modelo de IA lido de config.ini: {ai_model}")
        except Exception as e:
            log_warn(f"Não foi possível ler config.ini ou seção [AI] ausente. Usando modelo padrão: {ai_model}. Erro: {e}")
    else:
        log_warn(f"Arquivo config.ini não encontrado. Usando modelo padrão: {ai_model}.")
    
    # 3. Tentar fazer uma chamada simples à API da OpenAI
    try:
        client = OpenAI(api_key=api_key)
        log_info(f"Tentando chamar a API da OpenAI com o modelo: {ai_model}...")
        
        response = client.chat.completions.create(
            model=ai_model,
            messages=[{"role": "user", "content": "Teste de conexão com a IA. Responda com 'OK'."}],
            max_tokens=5
        )
        
        if response.choices and response.choices[0].message.content.strip().upper() == "OK":
            log_info(f"Conexão com a IA ({ai_model}) bem-sucedida! Resposta: '{response.choices[0].message.content.strip()}'")
            return True
        else:
            log_error(f"A IA ({ai_model}) respondeu, mas a resposta não foi a esperada. Resposta: '{response.choices[0].message.content.strip()}'")
            return False
            
    except Exception as e:
        log_error(f"Falha ao conectar ou obter resposta da IA ({ai_model}). Erro: {e}")
        log_error("Verifique sua OPENAI_API_KEY, o nome do modelo de IA em config.ini e sua conexão com a internet.")
        return False

if __name__ == "__main__":
    if test_ai_configuration():
        log_info("Teste de IA concluído com SUCESSO!")
    else:
        log_error("Teste de IA concluído com FALHA.")
