#!/usr/bin/env python3

import os
import sys
import json
import time
import socket
import subprocess
import concurrent.futures
import shutil
from datetime import datetime

import requests
import Levenshtein

# ==========================
# CONFIG
# ==========================

REPORT_DIR = "relatorio"
os.makedirs(REPORT_DIR, exist_ok=True)

TOR_SOCKS = "socks5h://127.0.0.1:9050"
TOR_CONTROL_PORT = 9051

CLUSTER_THRESHOLD = 0.80


# ==========================
# NETWORK ENGINE
# ==========================

def is_tor_running():
    try:
        s = socket.create_connection(("127.0.0.1", 9050), timeout=3)
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False
    except Exception:
        return False


def renew_tor_circuit():
    try:
        with socket.create_connection(("127.0.0.1", TOR_CONTROL_PORT), timeout=5) as s:
            s.send(b'AUTHENTICATE\r\n')
            s.recv(1024)
            s.send(b'SIGNAL NEWNYM\r\n')
            s.recv(1024)
            s.send(b'QUIT\r\n')
        print("[+] Circuito Tor renovado.")
        return True
    except Exception as e:
        print(f"[!] Falha ao renovar circuito Tor: {e}")
        return False


def build_proxy_dict(proxy_url):
    if not proxy_url:
        return None
    return {
        "http": proxy_url,
        "https": proxy_url
    }


def get_working_proxy(user_proxy=None):
    if user_proxy:
        print(f"[*] Usando proxy manual: {user_proxy}")
        return build_proxy_dict(user_proxy)

    if is_tor_running():
        print("[*] Tor detectado em 127.0.0.1:9050.")
        return build_proxy_dict(TOR_SOCKS)

    print("[!] Nenhum proxy detectado. Usando conexão direta.")
    return None


# ==========================
# EXECUÇÃO SHERLOCK / MAIGRET
# ==========================

def check_tool_availability(tool_name):
    """Verifica se a ferramenta está instalada no sistema."""
    return shutil.which(tool_name) is not None


def run_sherlock(username, proxy_url=None):
    if not check_tool_availability("sherlock"):
        print("[!] Sherlock não encontrado no PATH. Pulando...")
        return None
        
    output_file = f"{username}_sherlock.json"
    cmd = ["sherlock", username, "--json", output_file]

    if proxy_url:
        cmd.extend(["--proxy", proxy_url])

    print(f"[*] Iniciando Sherlock para {username}...")
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
        return output_file
    except subprocess.TimeoutExpired:
        print(f"[!] Sherlock excedeu o tempo limite para {username}.")
    except Exception as e:
        print(f"[!] Erro ao executar Sherlock: {e}")
    return None


def run_maigret(username, proxy_url=None):
    # Correção: Verificar se o maigret está disponível ou tentar via python3 -m maigret
    tool_cmd = "maigret"
    if not check_tool_availability(tool_cmd):
        # Tenta verificar se está instalado como módulo python
        try:
            subprocess.run([sys.executable, "-m", "maigret", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            tool_cmd = [sys.executable, "-m", "maigret"]
        except:
            print("[!] Maigret não encontrado (nem no PATH nem como módulo python). Pulando...")
            return None
    else:
        tool_cmd = [tool_cmd]

    output_file = f"{username}_maigret.json"
    # Nota: Maigret usa --json para especificar o nome do arquivo de saída
    cmd = tool_cmd + [username, "--json", output_file]

    if proxy_url:
        cmd.extend(["--proxy", proxy_url])

    print(f"[*] Iniciando Maigret para {username}...")
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
        return output_file
    except subprocess.TimeoutExpired:
        print(f"[!] Maigret excedeu o tempo limite para {username}.")
    except Exception as e:
        print(f"[!] Erro ao executar Maigret: {e}")
    return None


# ==========================
# PARSER
# ==========================

def parse_json_file(file_path):
    if not file_path or not os.path.exists(file_path):
        return []
        
    found = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

            # Sherlock JSON format (dependendo da versão pode variar)
            if isinstance(data, dict):
                # Se for o formato de resultados do Sherlock
                if "profiles" in data:
                    for site in data["profiles"]:
                        found.append(data["profiles"][site].get("username", username))
                else:
                    found.extend(data.keys())
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        if "username" in item:
                            found.append(item["username"])
                        elif "site" in item:
                            found.append(username) # Fallback
    except Exception as e:
        print(f"[!] Erro ao processar {file_path}: {e}")
        pass

    return list(set(found))


# ==========================
# LEVENSHTEIN
# ==========================

def calculate_similarity(a, b):
    if not a or not b:
        return 0
    return Levenshtein.ratio(a.lower(), b.lower())


# ==========================
# GITHUB AGE (USANDO PROXY)
# ==========================

def get_github_creation_date(username, proxies):
    try:
        url = f"https://api.github.com/users/{username}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, proxies=proxies, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json().get("created_at")
    except Exception:
        pass
    return None


def calculate_account_age(date_str):
    try:
        creation = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d")
        days = (datetime.utcnow() - creation).days

        if days < 30:
            return "MUITO_RECENTE (Suspeito)", 30
        elif days < 180:
            return "RECENTE", 15
        elif days < 365:
            return "MODERADA", 5
        else:
            return "ANTIGA (Confiável)", 0
    except Exception:
        return "DESCONHECIDA", 0


# ==========================
# ANALYSIS
# ==========================

def analyze(target_username, found_users, proxies):
    score = 0
    penalty_total = 0
    detailed = []

    if not found_users:
        return 0, []

    for user in found_users:
        ratio = calculate_similarity(target_username, user)

        if ratio >= 0.95:
            score += 35
            level = "EXATA/QUASE EXATA"
        elif ratio >= 0.85:
            score += 25
            level = "ALTA"
        elif ratio >= 0.70:
            score += 15
            level = "MÉDIA"
        else:
            level = "BAIXA"

        creation_date = get_github_creation_date(user, proxies)

        if creation_date:
            age_level, penalty = calculate_account_age(creation_date)
            penalty_total += penalty
        else:
            age_level = "N/A"

        detailed.append((user, round(ratio * 100), level, age_level))

    # Normalização básica do score
    final_score = max(min(score - penalty_total, 100), 0)

    return final_score, detailed


# ==========================
# HTML
# ==========================

def generate_html(username, score, detailed):
    file_path = f"{REPORT_DIR}/{username}_report.html"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if score >= 80:
        color = "#00ff99"
        conclusion = "Perfil altamente consistente. Baixo risco de ser fake."
    elif score >= 50:
        color = "#ffaa00"
        conclusion = "Perfil com consistência moderada. Requer verificação manual."
    else:
        color = "#ff4444"
        conclusion = "Perfil com baixa consistência ou muito recente. Alto risco de ser fake."

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <title>Relatório OSINT - {username}</title>
            <style>
                body {{ background:#111; color:#eee; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding:40px; line-height: 1.6; }}
                .container {{ max-width: 800px; margin: auto; background: #1e1e1e; padding: 20px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
                h1 {{ color: #00d4ff; border-bottom: 2px solid #333; padding-bottom: 10px; }}
                .score-container {{ background:#333; border-radius:20px; width:100%; height: 35px; overflow:hidden; margin: 20px 0; border: 1px solid #444; }}
                .score-bar {{ background:{color}; height:100%; text-align:center; line-height: 35px; font-weight: bold; color: #000; transition: width 1s ease-in-out; }}
                .conclusion {{ font-size: 1.2em; font-weight: bold; color: {color}; background: rgba(0,0,0,0.2); padding: 10px; border-left: 5px solid {color}; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #333; }}
                th {{ background: #252525; color: #00d4ff; }}
                tr:hover {{ background: #2a2a2a; }}
                .footer {{ margin-top: 30px; font-size: 0.8em; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Relatório de Identidade OSINT</h1>
                <p><strong>Alvo:</strong> {username} | <strong>Data:</strong> {timestamp}</p>

                <div class="score-container">
                    <div class="score-bar" style="width:{score}%;">{score}%</div>
                </div>

                <div class="conclusion">
                    {conclusion}
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Username Encontrado</th>
                            <th>Similaridade</th>
                            <th>Nível</th>
                            <th>Idade (GitHub)</th>
                        </tr>
                    </thead>
                    <tbody>
        """)

        for user, sim, level, age in detailed:
            f.write(f"""
                        <tr>
                            <td>{user}</td>
                            <td>{sim}%</td>
                            <td>{level}</td>
                            <td>{age}</td>
                        </tr>
            """)

        f.write("""
                    </tbody>
                </table>
                <div class="footer">
                    Gerado por Identity Engine v2.0 - Sherlock & Maigret Integration
                </div>
            </div>
        </body>
        </html>
        """)

    print(f"[+] Relatório detalhado salvo em: {file_path}")


# ==========================
# MAIN
# ==========================

def main():
    if len(sys.argv) < 2:
        print("\n[!] Erro: Nome de usuário não fornecido.")
        print("Uso:")
        print("  python3 identity_engine.py <username>")
        print("  python3 identity_engine.py <username> <proxy_url>")
        print("\nExemplos:")
        print("  python3 identity_engine.py marcelaaa6070")
        print("  python3 identity_engine.py marcelaaa6070 socks5://127.0.0.1:9050\n")
        sys.exit(1)

    global username
    username = sys.argv[1]
    user_proxy = sys.argv[2] if len(sys.argv) >= 3 else None

    print(f"\n[*] Iniciando busca para: {username}")
    
    proxies = get_working_proxy(user_proxy)

    if is_tor_running():
        renew_tor_circuit()

    print("[*] Executando ferramentas de busca (Sherlock + Maigret)...")

    # Usando caminhos absolutos ou relativos para os arquivos temporários
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_s = executor.submit(run_sherlock, username, user_proxy)
        future_m = executor.submit(run_maigret, username, user_proxy)

        # Aguarda resultados com tratamento de exceção
        try:
            sherlock_file = future_s.result()
        except Exception as e:
            print(f"[!] Falha na thread do Sherlock: {e}")
            sherlock_file = None

        try:
            maigret_file = future_m.result()
        except Exception as e:
            print(f"[!] Falha na thread do Maigret: {e}")
            maigret_file = None

    found = []
    if sherlock_file:
        found += parse_json_file(sherlock_file)
        if os.path.exists(sherlock_file): os.remove(sherlock_file) # Limpeza
        
    if maigret_file:
        found += parse_json_file(maigret_file)
        if os.path.exists(maigret_file): os.remove(maigret_file) # Limpeza

    found = list(set(found))

    if not found:
        print("[!] Nenhum perfil adicional foi encontrado pelas ferramentas.")
        # Adiciona o próprio username para análise básica se nada for encontrado
        found = [username]

    print(f"[+] Total de {len(found)} variantes de perfis para análise.")

    print("[*] Analisando consistência e metadados...")
    score, detailed = analyze(username, found, proxies)

    print(f"[+] Score de Confiança: {score}%")

    generate_html(username, score, detailed)

    print(f"\n[✓] Processo concluído com sucesso para {username}.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Operação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Erro crítico: {e}")
        sys.exit(1)
