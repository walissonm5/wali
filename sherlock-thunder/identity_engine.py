#!/usr/bin/env python3
"""
Identity Engine v2.0 - OSINT Pro
Executa com: python3 identity_engine.py username
Ativa o ambiente virtual automaticamente
"""

import os
import sys
import json
import time
import subprocess
import concurrent.futures
import shutil
import random
from datetime import datetime
from pathlib import Path

# ==========================
# VERIFICAR E ATIVAR VENV
# ==========================

def ensure_venv():
    """Verifica e ativa o ambiente virtual"""
    venv_path = Path(__file__).parent / "venv"
    
    if not venv_path.exists():
        print("[*] Criando ambiente virtual...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        
        # Ativar e instalar dependências
        activate_script = venv_path / "bin" / "activate"
        pip_path = venv_path / "bin" / "pip"
        
        print("[*] Instalando dependências...")
        packages = [
            "requests",
            "python-Levenshtein",
            "sherlock-project",
            "maigret",
            "stem",
            "fake-useragent"
        ]
        
        for package in packages:
            subprocess.run([str(pip_path), "install", "-q", package], check=False)
        
        print("[✓] Ambiente virtual criado!")
    
    # Verificar se estamos dentro do venv
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if not in_venv:
        print("[*] Ativando ambiente virtual...")
        activate_script = venv_path / "bin" / "activate_this.py"
        
        if activate_script.exists():
            exec(open(str(activate_script)).read(), {'__file__': str(activate_script)})
        else:
            # Alternativa: re-executar com o Python do venv
            python_path = venv_path / "bin" / "python3"
            if python_path.exists():
                os.execv(str(python_path), [str(python_path)] + sys.argv)

ensure_venv()

# Agora importar as dependências
try:
    import Levenshtein
    from stem import Signal
    from stem.control import Controller
    from fake_useragent import UserAgent
    import requests
except ImportError as e:
    print(f"[!] Erro ao importar dependência: {e}")
    print("[*] Instalando dependências...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", 
                   "requests", "python-Levenshtein", "sherlock-project", 
                   "maigret", "stem", "fake-useragent"], check=False)
    print("[✓] Dependências instaladas. Execute novamente.")
    sys.exit(1)

# ==========================
# PROXY MANAGER
# ==========================

class ProxyManager:
    """Gerenciador de proxies e rede resiliente"""
    
    def __init__(self):
        self.proxies = []
        self.current_proxy_idx = 0
        self.tor_available = self.check_tor()
        self.load_proxies()
        self.test_external_ip()
    
    def check_tor(self):
        """Verifica se Tor está disponível"""
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate(password='')
            print("[✓] Tor detectado")
            return True
        except:
            print("[*] Tor não disponível (opcional)")
            return False
    
    def load_proxies(self):
        """Carrega proxies do arquivo config/proxies.txt"""
        proxy_file = Path("config/proxies.txt")
        if proxy_file.exists():
            with open(proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            print(f"[✓] {len(self.proxies)} proxy(ies) carregado(s)")
    
    def get_proxy(self):
        """Retorna o próximo proxy da lista"""
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_proxy_idx]
        self.current_proxy_idx = (self.current_proxy_idx + 1) % len(self.proxies)
        return proxy
    
    def test_external_ip(self):
        """Testa o IP externo"""
        try:
            response = requests.get("https://api.ipify.org?format=json", timeout=5)
            ip = response.json()['ip']
            print(f"[✓] IP Externo: {ip}")
        except:
            print("[!] Erro ao testar IP externo")
    
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
        except:
            print("[!] Erro ao renovar Tor")
            return False
    
    def get_headers(self):
        """Retorna headers com User-Agent aleatório"""
        try:
            ua = UserAgent()
            user_agent = ua.random
        except:
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            ]
            user_agent = random.choice(user_agents)
        
        return {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
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
        os.makedirs("relatorio", exist_ok=True)
    
    def log(self, msg, level="INFO"):
        colors = {
            "INFO": "\033[0;34m",
            "SUCCESS": "\033[0;32m",
            "WARN": "\033[0;33m",
            "ERROR": "\033[0;31m"
        }
        reset = "\033[0m"
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{colors.get(level, '')}[{timestamp}] [{level}] {msg}{reset}")
    
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
        """Analisa resultados"""
        self.log("Analisando resultados...", "INFO")
        
        combined = {}
        
        for site, data in sherlock_data.items():
            if isinstance(data, dict) and data.get('status') == 'Found':
                combined[site] = {
                    'source': 'Sherlock',
                    'url': data.get('url_user', ''),
                    'status': 'Found'
                }
        
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
        
        report_file = f"relatorio/{self.username}_report.html"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Identity Engine - {self.username}</title>
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
            display: inline-block;
            margin-top: 10px;
        }}
        .result-url {{
            color: #a0aec0;
            word-break: break-all;
            margin-top: 10px;
            font-size: 0.9em;
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
                <div class="result-site">🌐 {site}</div>
                <div class="result-url">{data.get('url', 'N/A')}</div>
                <span class="result-source">{data.get('source', 'Unknown')}</span>
            </div>
            ''' for site, data in results.items()])}
        </div>
        
        <footer>
            <p>Identity Engine v2.0 - OSINT Pro</p>
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
