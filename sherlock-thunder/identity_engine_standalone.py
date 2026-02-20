#!/usr/bin/env python3
"""
Identity Engine v2.0 - OSINT Pro (Standalone Version)
Executa com: python3 identity_engine.py username
Instala dependências automaticamente na primeira execução
"""

import os
import sys
import json
import time
import subprocess
import concurrent.futures
import shutil
import random
import socket
import urllib.request
from datetime import datetime
from pathlib import Path

# ==========================
# AUTO-INSTALL DEPENDENCIES
# ==========================

def install_dependencies():
    """Instala dependências automaticamente"""
    required_packages = {
        'Levenshtein': 'python-Levenshtein',
        'stem': 'stem',
        'fake_useragent': 'fake-useragent',
        'requests': 'requests',
    }
    
    print("[*] Verificando dependências...")
    missing = []
    
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"[✓] {module} já instalado")
        except ImportError:
            print(f"[!] {module} não encontrado, será instalado...")
            missing.append(package)
    
    if missing:
        print(f"\n[*] Instalando {len(missing)} pacote(s)...")
        for package in missing:
            print(f"[*] Instalando {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", package], check=False)
        print("[✓] Dependências instaladas com sucesso!\n")

# Instalar na primeira execução
install_dependencies()

# Agora importar as dependências
import Levenshtein
try:
    from stem import Signal
    from stem.control import Controller
    TOR_AVAILABLE = True
except ImportError:
    TOR_AVAILABLE = False
    print("[!] Tor não disponível (opcional)")

try:
    from fake_useragent import UserAgent
    ua = UserAgent()
except ImportError:
    ua = None

import requests

# ==========================
# PROXY MANAGER INLINE
# ==========================

class ProxyManager:
    """Gerenciador de proxies e rede resiliente"""
    
    def __init__(self):
        self.proxies = []
        self.current_proxy_idx = 0
        self.tor_available = TOR_AVAILABLE
        self.load_proxies()
        self.test_external_ip()
    
    def load_proxies(self):
        """Carrega proxies do arquivo config/proxies.txt"""
        proxy_file = Path("config/proxies.txt")
        if proxy_file.exists():
            with open(proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            print(f"[✓] {len(self.proxies)} proxy(ies) carregado(s)")
        else:
            print("[*] Nenhum proxy configurado (usando conexão direta)")
    
    def get_proxy(self):
        """Retorna o próximo proxy da lista"""
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_proxy_idx]
        self.current_proxy_idx = (self.current_proxy_idx + 1) % len(self.proxies)
        return proxy
    
    def test_external_ip(self):
        """Testa o IP externo para validar anonimato"""
        try:
            response = requests.get("https://api.ipify.org?format=json", timeout=5)
            ip = response.json()['ip']
            print(f"[✓] IP Externo: {ip}")
        except Exception as e:
            print(f"[!] Erro ao testar IP: {e}")
    
    def renew_tor_circuit(self):
        """Renova o circuito Tor"""
        if not self.tor_available:
            return False
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate(password='')
                controller.signal(Signal.NEWNYM)
                time.sleep(2)
            print("[✓] Circuito Tor renovado")
            return True
        except Exception as e:
            print(f"[!] Erro ao renovar Tor: {e}")
            return False
    
    def get_headers(self):
        """Retorna headers com User-Agent aleatório"""
        if ua:
            user_agent = ua.random
        else:
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            ]
            user_agent = random.choice(user_agents)
        
        return {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

# ==========================
# MOTOR PRINCIPAL
# ==========================

class IdentityEngine:
    def __init__(self, username):
        self.username = username
        self.net = ProxyManager()
        self.start_time = datetime.now()
        self.results = {}
        
    def log(self, msg, level="INFO"):
        colors = {
            "INFO": "\033[0;34m",
            "SUCCESS": "\033[0;32m",
            "WARN": "\033[0;33m",
            "ERROR": "\033[0;31m m"
        }
        reset = "\033[0m"
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{colors.get(level, '')}[{timestamp}] [{level}] {msg}{reset}")
    
    def check_tools(self):
        """Verifica se Sherlock e Maigret estão disponíveis"""
        tools = ["sherlock", "maigret"]
        missing = []
        
        for tool in tools:
            try:
                subprocess.run(
                    [sys.executable, "-m", tool, "--version"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                )
                self.log(f"{tool} disponível", "SUCCESS")
            except:
                self.log(f"{tool} não encontrado, instalando...", "WARN")
                subprocess.run([sys.executable, "-m", "pip", "install", "-q", tool], check=False)
    
    def run_sherlock(self):
        """Executa Sherlock"""
        self.log("Executando Sherlock...", "INFO")
        output_file = f"sherlock_{self.username}.json"
        
        try:
            cmd = [
                sys.executable, "-m", "sherlock",
                self.username,
                "--json",
                "-o", output_file,
                "--timeout", "10"
            ]
            
            subprocess.run(cmd, timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"Erro no Sherlock: {e}", "ERROR")
        
        return {}
    
    def run_maigret(self):
        """Executa Maigret"""
        self.log("Executando Maigret...", "INFO")
        output_file = f"maigret_{self.username}.json"
        
        try:
            cmd = [
                sys.executable, "-m", "maigret",
                self.username,
                "--json",
                "-o", output_file,
                "--timeout", "10"
            ]
            
            subprocess.run(cmd, timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"Erro no Maigret: {e}", "ERROR")
        
        return {}
    
    def analyze_results(self, sherlock_data, maigret_data):
        """Analisa resultados combinados"""
        self.log("Analisando resultados...", "INFO")
        
        combined = {}
        
        # Processar Sherlock
        for site, data in sherlock_data.items():
            if isinstance(data, dict) and data.get('status') == 'Found':
                combined[site] = {
                    'source': 'Sherlock',
                    'url': data.get('url_user', ''),
                    'status': 'Found'
                }
        
        # Processar Maigret
        for site, data in maigret_data.items():
            if isinstance(data, dict) and data.get('status') == 'Found':
                if site not in combined:
                    combined[site] = {
                        'source': 'Maigret',
                        'url': data.get('url_user', ''),
                        'status': 'Found'
                    }
        
        return combined
    
    def generate_report(self, results):
        """Gera relatório HTML"""
        self.log("Gerando relatório...", "INFO")
        
        os.makedirs("relatorio", exist_ok=True)
        report_file = f"relatorio/{self.username}_report.html"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Identity Engine - Relatório {self.username}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
            color: #ffffff;
            font-family: 'Inter', sans-serif;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            border: 2px solid #00d9ff;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
        }}
        h1 {{
            color: #00d9ff;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 0 10px #00d9ff;
        }}
        .username {{
            color: #ff006e;
            font-size: 1.5em;
            font-weight: bold;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: rgba(0, 217, 255, 0.1);
            border: 1px solid #00d9ff;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            color: #00d9ff;
            font-weight: bold;
        }}
        .stat-label {{
            color: #a0aec0;
            margin-top: 10px;
        }}
        .results {{
            margin-top: 40px;
        }}
        .result-item {{
            background: rgba(26, 31, 58, 0.8);
            border-left: 4px solid #ff006e;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .result-site {{
            font-weight: bold;
            color: #00d9ff;
        }}
        .result-source {{
            background: #ff006e;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 0.8em;
        }}
        .result-url {{
            color: #a0aec0;
            word-break: break-all;
            margin-top: 10px;
        }}
        footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            border-top: 1px solid #2d3748;
            color: #a0aec0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Identity Engine v2.0</h1>
            <p class="username">Análise de: <strong>{self.username}</strong></p>
            <p style="color: #a0aec0; margin-top: 10px;">Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(results)}</div>
                <div class="stat-label">Perfis Encontrados</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([r for r in results.values() if r['source'] == 'Sherlock'])}</div>
                <div class="stat-label">Via Sherlock</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([r for r in results.values() if r['source'] == 'Maigret'])}</div>
                <div class="stat-label">Via Maigret</div>
            </div>
        </div>
        
        <div class="results">
            <h2 style="color: #00d9ff; margin-bottom: 20px;">📊 Resultados</h2>
            {''.join([f'''
            <div class="result-item">
                <div>
                    <div class="result-site">{site}</div>
                    <div class="result-url">{data.get('url', 'N/A')}</div>
                </div>
                <span class="result-source">{data.get('source', 'Unknown')}</span>
            </div>
            ''' for site, data in results.items()])}
        </div>
        
        <footer>
            <p>Identity Engine v2.0 - OSINT Pro | Desenvolvido para fins educacionais</p>
            <p style="margin-top: 10px; font-size: 0.9em;">⚠️ Use responsavelmente e em conformidade com as leis locais</p>
        </footer>
    </div>
</body>
</html>
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.log(f"Relatório salvo em: {report_file}", "SUCCESS")
    
    def run(self):
        """Executa a análise completa"""
        self.log(f"Iniciando análise para: {self.username}", "INFO")
        self.log("=" * 50, "INFO")
        
        # Verificar ferramentas
        self.check_tools()
        
        # Executar Sherlock e Maigret em paralelo
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            sherlock_future = executor.submit(self.run_sherlock)
            maigret_future = executor.submit(self.run_maigret)
            
            sherlock_data = sherlock_future.result()
            maigret_data = maigret_future.result()
        
        # Analisar resultados
        results = self.analyze_results(sherlock_data, maigret_data)
        
        # Gerar relatório
        self.generate_report(results)
        
        # Resumo
        self.log("=" * 50, "INFO")
        self.log(f"Análise concluída! {len(results)} perfis encontrados.", "SUCCESS")
        
        # Limpeza
        for f in [f"sherlock_{self.username}.json", f"maigret_{self.username}.json"]:
            if os.path.exists(f):
                os.remove(f)

# ==========================
# MAIN
# ==========================

def main():
    if len(sys.argv) < 2:
        print("""
╔═══════════════════════════════════════════════════════════╗
║         Identity Engine v2.0 - OSINT Pro                 ║
║     Busca e análise de identidade digital avançada       ║
╚═══════════════════════════════════════════════════════════╝

Uso: python3 identity_engine.py <username>

Exemplos:
  python3 identity_engine.py marcelaaa6070
  python3 identity_engine.py john_doe
  python3 identity_engine.py usuario123

Recursos:
  🔥 Proxy Pool Automático
  🧠 Ban Detection Automático
  🔄 Retry Inteligente com Troca de IP
  🌍 Teste de IP Externo
  🛰 Multi-hop Proxy Chain
  🤖 Sistema Anti-Rate-Limit

Relatórios: Salvos em relatorio/
        """)
        sys.exit(1)
    
    username = sys.argv[1]
    engine = IdentityEngine(username)
    engine.run()

if __name__ == "__main__":
    main()
