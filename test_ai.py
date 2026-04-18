#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, configparser, requests
from groq import Groq
from colorama import Fore, Style, init

init(autoreset=True)

def test_ai():
    print(f"\n{Fore.CYAN}=== Teste de Configuração de IA ==={Style.RESET_ALL}\n")
    
    config = configparser.ConfigParser()
    if not os.path.exists('config.ini'):
        print(f"{Fore.RED}[✗] Arquivo config.ini não encontrado. Execute o ./setup.sh primeiro.{Style.RESET_ALL}")
        return

    config.read('config.ini')
    provider = config.get('AI', 'PROVIDER', fallback='groq').lower()
    model = config.get('AI', 'MODEL', fallback='llama-3.3-70b-versatile')
    
    print(f"{Fore.YELLOW}[i] Provedor: {provider.upper()}")
    print(f"{Fore.YELLOW}[i] Modelo: {model}")

    if provider == 'ollama':
        url = config.get('AI', 'OLLAMA_URL', fallback='http://localhost:11434/api/generate')
        print(f"{Fore.YELLOW}[i] URL Ollama: {url}")
        try:
            payload = {"model": model, "prompt": "Olá, responda apenas 'OK'", "stream": False}
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200:
                print(f"{Fore.GREEN}[✓] Conexão com Ollama estabelecida com sucesso!{Style.RESET_ALL}")
                print(f"{Fore.WHITE}Resposta: {r.json().get('response')}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}[✗] Erro no Ollama: Status {r.status_code}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[✗] Falha ao conectar ao Ollama: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[!] Certifique-se de que o Ollama está rodando e o modelo '{model}' foi baixado.{Style.RESET_ALL}")
    
    else:
        api_key = config.get('AI', 'GROQ_API_KEY', fallback='')
        if not api_key:
            print(f"{Fore.RED}[✗] GROQ_API_KEY não encontrada no config.ini{Style.RESET_ALL}")
            return
            
        try:
            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": "Olá, responda apenas 'OK'"}],
                model=model,
            )
            print(f"{Fore.GREEN}[✓] Conexão com GroqCloud estabelecida com sucesso!{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Resposta: {chat_completion.choices[0].message.content}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[✗] Falha na API da Groq: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    test_ai()
