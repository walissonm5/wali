#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PCAPCracker Pro - Ferramenta de Auditoria WPA/WPA2 com Suporte a IA (Groq & Ollama)"""
import os, re, sqlite3, subprocess, hashlib, json, time, configparser, requests
from datetime import datetime
from pathlib import Path
from colorama import Fore, Style, init
from tqdm import tqdm
from html import escape
from groq import Groq

init(autoreset=True)

# Configurações
class Cfg:
    PCAP="pcap"; HASH="hash"; WL="wordlist"; RULES="rules"
    LOG="logs"; DB="pcapcracker.db"; MAX_ATT=2
    def __init__(self):
        self.POT=f"{self.HASH}/pot.pot"
        self.HTML=f"{self.LOG}/html"; self.JSON=f"{self.LOG}/json"
        for d in [self.PCAP, self.HASH, self.WL, self.RULES, self.LOG, self.HTML, self.JSON]:
            try:
                os.makedirs(d, exist_ok=True)
                if not os.access(d, os.W_OK):
                    raise PermissionError(f"Sem permissão para escrever em: {d}")
            except Exception as e:
                print(f"{Fore.RED}[✗] Erro ao criar diretório {d}: {e}{Style.RESET_ALL}")
                exit(1)

cfg=Cfg()

# Template HTML
HTML_TPL="""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{title}</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
min-height:100vh;padding:20px}}
.container{{max-width:1200px;margin:0 auto;background:rgba(255,255,255,0.98);
border-radius:20px;box-shadow:0 25px 80px rgba(0,0,0,0.4);overflow:hidden}}
.header{{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);
color:#fff;padding:40px;text-align:center;position:relative}}
.header::after{{content:'';position:absolute;bottom:0;left:0;right:0;
height:4px;background:linear-gradient(90deg,#00f260,#0575e6,#00f260)}}
.header h1{{font-size:2.5em;margin-bottom:10px;text-shadow:2px 2px 4px rgba(0,0,0,0.3)}}
.header .subtitle{{font-size:1.1em;opacity:0.9;color:#00f260}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));
gap:20px;padding:30px;background:#f8f9fa}}
.stat-card{{background:#fff;padding:25px;border-radius:15px;
box-shadow:0 5px 15px rgba(0,0,0,0.1);border-left:5px solid;
transition:transform 0.3s}}
.stat-card:hover{{transform:translateY(-5px)}}
.stat-card.success{{border-color:#00f260}}
.stat-card.info{{border-color:#0575e6}}
.stat-card.warning{{border-color:#ffd32a}}
.stat-label{{font-size:0.9em;color:#6c757d;text-transform:uppercase;
letter-spacing:1px;margin-bottom:10px}}
.stat-value{{font-size:2.5em;font-weight:bold;color:#1a1a2e}}
.content{{padding:40px}}
.section{{margin-bottom:40px}}
.section-title{{font-size:1.8em;color:#1a1a2e;margin-bottom:20px;
padding-bottom:15px;border-bottom:3px solid #00f260;display:flex;
align-items:center;gap:10px}}
.section-title::before{{content:'🔐';font-size:1.2em}}
.network-card{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
padding:30px;border-radius:15px;margin:20px 0;box-shadow:0 10px 30px rgba(0,0,0,0.2);
color:#fff}}
.network-name{{font-size:2em;font-weight:bold;margin-bottom:20px;
text-shadow:2px 2px 4px rgba(0,0,0,0.3);word-break:break-all}}
.detail{{background:rgba(255,255,255,0.2);padding:15px;border-radius:10px;
margin:10px 0;backdrop-filter:blur(10px)}}
.detail-label{{font-weight:600;opacity:0.9;margin-right:10px}}
.detail-value{{font-family:monospace;font-size:1.1em}}
.password-box{{background:linear-gradient(135deg,#00f260 0%,#0575e6 100%);
padding:35px;border-radius:15px;text-align:center;margin:30px 0;
box-shadow:0 15px 40px rgba(0,0,0,0.3);animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.02)}}}}
.password-label{{font-size:1.2em;opacity:0.9;margin-bottom:15px;color:#fff}}
.password{{font-size:2.5em;font-weight:bold;font-family:monospace;
letter-spacing:3px;color:#fff;text-shadow:2px 2px 8px rgba(0,0,0,0.3);
word-break:break-all}}
.info-table{{width:100%;border-collapse:separate;border-spacing:0 10px}}
.info-table tr{{background:#fff;box-shadow:0 2px 8px rgba(0,0,0,0.1)}}
.info-table td{{padding:15px;border:none}}
.info-table td:first-child{{font-weight:600;color:#667eea;width:30%;
border-radius:10px 0 0 10px}}
.info-table td:last-child{{border-radius:0 10px 10px 0;font-family:monospace}}
.badge{{display:inline-block;padding:8px 16px;border-radius:20px;
font-size:0.85em;font-weight:600}}
.badge.success{{background:#d4edda;color:#155724}}
.badge.danger{{background:#f8d7da;color:#721c24}}
.badge.info{{background:#d1ecf1;color:#0c5460}}
.footer{{background:#1a1a2e;color:#fff;padding:20px;text-align:center;
font-size:0.9em}}
</style></head><body><div class="container">{content}<div class="footer">
Gerado por PCAPCracker Pro • {timestamp}</div></div></body></html>"""

# Banco de Dados
class DB:
    def __init__(self,p):
        self.p=p; self.init()
    def init(self):
        c=sqlite3.connect(self.p)
        c.execute("""CREATE TABLE IF NOT EXISTS res(id INTEGER PRIMARY KEY,
        ssid TEXT,bssid TEXT,pwd TEXT,pcap TEXT,ts TEXT,wl TEXT,status TEXT,
        hmz TEXT,wmz TEXT,method TEXT)""")
        try:
            c.execute("ALTER TABLE res ADD COLUMN method TEXT")
        except sqlite3.OperationalError:
            pass
        c.execute("""CREATE TABLE IF NOT EXISTS att(id INTEGER PRIMARY KEY,
        hmz TEXT,wmz TEXT,type TEXT,ts TEXT,cnt INT DEFAULT 1,
        UNIQUE(hmz,wmz,type))""")
        # Nova tabela para estatísticas de senhas
        c.execute("""CREATE TABLE IF NOT EXISTS pwd_stats(id INTEGER PRIMARY KEY,
        pwd TEXT UNIQUE, count INTEGER DEFAULT 1, last_seen TEXT)""")
        c.commit(); c.close()
    def save(self,ss,bs,pw,pc,wl,st,hm,wm,mt):
        c=sqlite3.connect(self.p)
        try:
            c.execute("""INSERT INTO res (ssid,bssid,pwd,pcap,ts,wl,status,hmz,wmz,method)
                        VALUES (?,?,?,?,?,?,?,?,?,?)""",
                     (ss,bs,pw,pc,datetime.now().isoformat(),wl,st,hm,wm,mt))
            # Atualizar estatísticas de senhas
            c.execute("""INSERT INTO pwd_stats (pwd, count, last_seen) VALUES (?, 1, ?)
                        ON CONFLICT(pwd) DO UPDATE SET count=count+1, last_seen=?""",
                     (pw, datetime.now().isoformat(), datetime.now().isoformat()))
            c.commit()
        except sqlite3.Error as e:
            L.e(f"Erro ao salvar no banco de dados: {e}")
        finally:
            c.close()
    def reg(self,hm,wm,tp):
        c=sqlite3.connect(self.p)
        try:
            c.execute("""INSERT INTO att VALUES(NULL,?,?,?,?,1)
            ON CONFLICT(hmz,wmz,type) DO UPDATE SET cnt=cnt+1""",
            (hm,wm,tp,datetime.now().isoformat()))
            c.commit()
        except sqlite3.Error as e:
            L.e(f"Erro ao registrar tentativa: {e}")
        finally:
            c.close()
    def chk(self,hm,wm,tp,mx):
        c=sqlite3.connect(self.p)
        try:
            r=c.execute("SELECT cnt FROM att WHERE hmz=? AND wmz=? AND type=?",
                       (hm,wm,tp)).fetchone()
            return r and r[0]>=mx
        except sqlite3.Error as e:
            L.e(f"Erro ao verificar tentativa: {e}")
            return False
        finally:
            c.close()
    def all(self):
        c=sqlite3.connect(self.p)
        try:
            r=c.execute(
                "SELECT ssid,bssid,pwd,status,ts,method,wl FROM res ORDER BY ts DESC"
            ).fetchall()
            return r
        except sqlite3.Error as e:
            L.e(f"Erro ao recuperar resultados: {e}")
            return []
        finally:
            c.close()

    def wordlist_stats(self):
        c = sqlite3.connect(self.p)
        try:
            rows = c.execute(
                """SELECT wl, ssid, MAX(ts) as last_used
                   FROM res
                   WHERE status LIKE '%OK%' OR status LIKE '%CRACK%'
                   GROUP BY wl, ssid
                   ORDER BY wl"""
            ).fetchall()
        except sqlite3.Error as e:
            L.e(f"Erro ao recuperar estatísticas de wordlists: {e}")
            return []
        finally:
            c.close()

        stats = {}
        for wl, ssid, ts in rows:
            name = Path(wl).name if wl else "desconhecida"
            if name not in stats:
                stats[name] = {"name": name, "cracks": 0, "last_used": ts or "", "ssids": []}
            stats[name]["cracks"] += 1
            if ssid and ssid not in stats[name]["ssids"]:
                stats[name]["ssids"].append(ssid)
            if ts and ts > stats[name]["last_used"]:
                stats[name]["last_used"] = ts

        return sorted(stats.values(), key=lambda x: x["cracks"], reverse=True)

    def get_pwd_ranking(self, limit=10):
        c = sqlite3.connect(self.p)
        try:
            return c.execute("SELECT pwd, count, last_seen FROM pwd_stats ORDER BY count DESC LIMIT ?", (limit,)).fetchall()
        except sqlite3.Error as e:
            L.e(f"Erro ao recuperar ranking de senhas: {e}")
            return []
        finally:
            c.close()

# Utilitários
def fhash(f):
    if not os.path.isfile(f): return None
    h=hashlib.md5()
    with open(f,'rb') as x: h.update(x.read())
    return h.hexdigest()

def run(cmd,cap=False):
    try:
        if cap: return subprocess.run(cmd,capture_output=True,text=True)
        return subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except Exception as e:
        L.e(f"Erro ao executar comando {cmd}: {e}")
        return None

def valid(f): return os.path.isfile(f) and os.path.getsize(f)>0

# Alerta Sonoro
def play_sound():
    print("\a", end="", flush=True)
    try:
        import platform
        sys_name = platform.system()
        wav = _gen_wav()
        if sys_name == "Linux":
            for player in [["paplay"], ["aplay"], ["ffplay","-nodisp","-autoexit"]]:
                try:
                    subprocess.run(player + [wav], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, timeout=4)
                    break
                except FileNotFoundError:
                    continue
        elif sys_name == "Darwin":
            subprocess.run(["afplay", wav], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=4)
        elif sys_name == "Windows":
            import winsound
            for freq in [600, 900, 1200]:
                winsound.Beep(freq, 200)
    except Exception:
        pass

def _gen_wav(path="/tmp/pcapcracker_alert.wav"):
    import struct, math, wave
    if os.path.exists(path):
        return path
    sr = 44100
    notes = [(784,0.12),(784,0.12),(784,0.12),(659,0.35),(0,0.05),(784,0.12),(659,0.35)]
    samples = []
    for freq, dur in notes:
        n = int(sr * dur)
        for i in range(n):
            if freq == 0:
                samples.append(0)
            else:
                env = min(i/max(int(sr*0.01),1), 1.0, (n-i)/max(int(sr*0.02),1))
                v = int(32767 * env * math.sin(2 * math.pi * freq * i / sr))
                samples.append(v)
    try:
        with wave.open(path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(struct.pack('<' + 'h' * len(samples), *samples))
    except Exception:
        pass
    return path

# ── Logger ────────────────────────────────────────────────
class L:
    G  = '\033[38;5;22m'; LG = '\033[38;5;46m'; RS = Style.RESET_ALL
    R  = Fore.RED; Y = Fore.YELLOW; C = Fore.CYAN; M = Fore.MAGENTA
    
    @staticmethod
    def s(m): print(f"  {L.G}[{L.LG}✓{L.G}]{L.RS} {m}")
    @staticmethod
    def e(m): print(f"  {L.R}[✗] {m}")
    @staticmethod
    def w(m): print(f"  {L.Y}[!] {m}")
    @staticmethod
    def i(m): print(f"  {L.G}[{L.LG}i{L.G}]{L.RS} {m}")
    @staticmethod
    def p(m): print(f"  {L.G}[{L.LG}*{L.G}]{L.RS} {m}")
    
    @staticmethod
    def box(title, lines):
        if isinstance(lines, str): lines = lines.split('\n')
        width = max(len(re.sub(r'\033\[[0-9;]*m', '', l)) for l in lines + [title]) + 6
        print(f"\n  {L.G}┌{'─'*(width-2)}┐{L.RS}")
        print(f"  {L.G}│{L.RS}  {L.LG}{title.upper()}{' '*(width-len(title)-5)}{L.G}│{L.RS}")
        print(f"  {L.G}├{'─'*(width-2)}┤{L.RS}")
        for l in lines:
            clean = re.sub(r'\033\[[0-9;]*m', '', l)
            print(f"  {L.G}│{L.RS}  {l}{' '*(width-len(clean)-5)}{L.G}│{L.RS}")
        print(f"  {L.G}└{'─'*(width-2)}┘{L.RS}")

    @staticmethod
    def success_box(ssid, bssid, pwd):
        play_sound()
        lines = [
            f"{Fore.WHITE}SSID:{L.RS}   {Fore.CYAN}{ssid}{L.RS}",
            f"{Fore.WHITE}BSSID:{L.RS}  {Fore.MAGENTA}{bssid}{L.RS}",
            f"{Fore.WHITE}SENHA:{L.RS}  {Fore.GREEN}{pwd}{L.RS}"
        ]
        L.box("SUCESSO: REDE QUEBRADA", lines)

# ── Extrator ───────────────────────────────────────────────
class Ext:
    @staticmethod
    def extract(p):
        if not valid(p): return None
        nm=Path(p).stem; hf=f"{cfg.HASH}/{nm}.22000"
        if valid(hf): return hf
        L.p(f"Extraindo hashes de: {Path(p).name}")
        
        # Tentar converter .scap via tshark se necessário
        if p.lower().endswith('.scap'):
            tmp=f"/tmp/{nm}.pcap"
            run(["tshark","-F","pcap","-r",p,"-w",tmp])
            p=tmp
            
        run(["hcxpcapngtool","-o",hf,p])
        if valid(hf):
            L.s(f"Hashes salvos: {Path(hf).name}")
            gen_html({"ssid":Ext.parse(hf)[0],"bssid":Ext.parse(hf)[1],
                     "pcap":Path(p).name,"hash":Path(hf).name,"method":"hcxpcapngtool"})
            return hf
        L.e(f"Falha na extração: {Path(p).name}")
        return None

    @staticmethod
    def parse(hf):
        if not valid(hf): return "DESCONHECIDO","DESCONHECIDO",None
        with open(hf,'r') as f:
            ln=f.readline()
            if not ln: return "DESCONHECIDO","DESCONHECIDO",None
            pts=ln.split("*")
            if len(pts)<5: return "DESCONHECIDO","DESCONHECIDO",None
            try:
                bs=pts[3].upper()
                ss_hex=pts[5]
                ss=bytes.fromhex(ss_hex).decode('utf-8','ignore')
                return ss if ss else "OCULTO", ":".join(bs[i:i+2] for i in range(0,12,2)), pts[4]
            except:
                return "DESCONHECIDO","DESCONHECIDO",None

# ── AI Support (Groq & Ollama) ─────────────────────────────
class AI:
    def __init__(self):
        config = configparser.ConfigParser()
        try:
            config.read('config.ini')
            self.provider = config.get('AI', 'PROVIDER', fallback='groq').lower()
            self.model = config.get('AI', 'MODEL', fallback='llama-3.3-70b-versatile')
            self.api_key = config.get('AI', 'GROQ_API_KEY', fallback=os.getenv("GROQ_API_KEY"))
            self.ollama_url = config.get('AI', 'OLLAMA_URL', fallback='http://localhost:11434/api/generate')
        except Exception:
            self.provider = 'groq'
            self.model = 'llama-3.3-70b-versatile'
            self.api_key = os.getenv("GROQ_API_KEY")
            self.ollama_url = 'http://localhost:11434/api/generate'
        
        self.client = None
        if self.provider == 'groq' and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except:
                self.client = None

    def ask(self, prompt):
        if self.provider == 'ollama':
            try:
                payload = {"model": self.model, "prompt": prompt, "stream": False}
                r = requests.post(self.ollama_url, json=payload, timeout=30)
                if r.status_code == 200:
                    return r.json().get('response', 'Sem resposta do Ollama.')
                return f"Erro Ollama: Status {r.status_code}"
            except Exception as e:
                return f"Erro ao conectar ao Ollama: {e}"
        else:
            if not self.client: return "Erro: Groq não configurado."
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"Erro Groq: {e}"

    def analyze_ssid(self, ssid):
        prompt = f"""Analise o SSID de rede Wi-Fi '{ssid}' e sugira estratégias de ataque de dicionário.
        Identifique se o nome sugere um provedor específico (ex: VIVO, CLARO), modelo de roteador, 
        ou se parece ser um nome personalizado que pode conter padrões como datas, nomes próprios ou locais.
        Retorne uma análise curta em PORTUGUÊS e 3 sugestões de padrões de senha."""
        return self.ask(prompt)

    def suggest_wordlists(self, ssid):
        prompt = f"""Com base no SSID '{ssid}', sugira quais tipos de wordlists seriam mais eficazes.
        Exemplo: Se for 'VIVO-XXXX', sugira wordlists de padrões de operadoras. Se for 'Joao_2023', sugira wordlists de nomes e datas.
        Retorne uma lista curta de 3 tipos de wordlists em PORTUGUÊS."""
        return self.ask(prompt)

    def suggest_next_steps(self, results):
        if not results: return "Nenhum resultado para analisar."
        summary = "\n".join([f"SSID: {r[0]}, BSSID: {r[1]}, Status: {r[3]}" for r in results[:10]])
        prompt = f"""Com base nos seguintes resultados de tentativas de crack:
        {summary}
        Sugira os próximos passos em PORTUGUÊS. Recomende wordlists ou regras do hashcat."""
        return self.ask(prompt)

# ── Gerador de HTML de Resultados ──────────────────────────
def gen_results_html(db):
    rows = db.all()
    wl_stats = db.wordlist_stats()
    pwd_ranking = db.get_pwd_ranking(15)
    total = len(rows)
    path = f"{cfg.LOG}/results.html"
    
    seen = set(); unique = []
    for r in rows:
        key = (r[0], r[1], r[2])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    
    cards = ""
    for r in unique:
        ssid, bssid, pwd, status, ts, method, wl = r
        cards += f"""
        <div class="network-card">
            <div class="network-header">
                <div class="led"></div>
                <div class="ssid-name">{escape(ssid)}</div>
                <div class="tag">{escape(status)}</div>
            </div>
            <div class="card-body">
                <div class="field"><span class="lbl">BSSID</span><span class="val mono">{escape(bssid)}</span></div>
                <div class="field"><span class="lbl">MÉTODO</span><span class="val">{escape(method)}</span></div>
                <div class="field"><span class="lbl">WORDLIST</span><span class="val">{escape(Path(wl).name if wl else '-')}</span></div>
                <div class="field"><span class="lbl">DATA</span><span class="val mono">{ts[:19]}</span></div>
            </div>
            <div class="pwd-reveal">
                <div class="pwd-label">// SENHA DESCOBERTA</div>
                <div class="pwd-value">{escape(pwd)}</div>
            </div>
        </div>"""

    wl_rows = ""
    max_cracks = max(s['cracks'] for s in wl_stats) if wl_stats else 1
    for i, s in enumerate(wl_stats):
        rank_cls = f"rank-{i}" if i < 3 else "rank-other"
        pct = (s['cracks'] / max_cracks) * 100
        ssids_html = "".join([f'<span class="ssid-tag">{escape(x)}</span>' for x in s['ssids'][:3]])
        if len(s['ssids']) > 3: ssids_html += f'<span class="more-tag">+{len(s['ssids'])-3}</span>'
        
        wl_rows += f"""
        <div class="wl-row {rank_cls}" style="--delay: {i*0.1}s">
            <div class="wl-rank">{i+1}</div>
            <div class="wl-info">
                <div class="wl-name">{escape(s['name'])}</div>
                <div class="wl-ssids">{ssids_html}</div>
                <div class="wl-last">Último uso: {s['last_used'][:16]}</div>
            </div>
            <div class="wl-bar-wrap">
                <div class="wl-bar" style="--pct: {pct}%" data-pct="{pct}%"></div>
            </div>
            <div class="wl-count">{s['cracks']}<span class="wl-unit">quebras</span></div>
        </div>"""

    pwd_rows = ""
    if pwd_ranking:
        max_count = max(p[1] for p in pwd_ranking)
        for p in pwd_ranking:
            pct = (p[1] / max_count) * 100
            pwd_rows += f"""
            <div class="wl-row rank-other">
                <div class="wl-info">
                    <div class="wl-name" style="font-family:'Orbitron';color:var(--cyan)">{escape(p[0])}</div>
                    <div class="wl-last">Última vez vista: {p[2][:16]}</div>
                </div>
                <div class="wl-bar-wrap">
                    <div class="wl-bar" style="--pct: {pct}%; background:var(--cyan)"></div>
                </div>
                <div class="wl-count" style="color:var(--cyan)">{p[1]}<span class="wl-unit">vezes</span></div>
            </div>"""

    wl_section = f"""
    <div class="wl-section">
        <div class="section-hdr">desempenho de wordlists</div>
        <div class="wl-list">{wl_rows}</div>
    </div>""" if wl_rows else ""

    pwd_section = f"""
    <div class="wl-section">
        <div class="section-hdr">catálogo de senhas mais comuns</div>
        <div class="wl-list">{pwd_rows}</div>
    </div>""" if pwd_rows else ""

    empty_msg = '<div class="empty">// NENHUMA SENHA QUEBRADA AINDA</div>' if not unique else ""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>PCAPCracker Pro - Resultados</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
:root{{--bg:#050505;--panel:#0a0a0a;--green:#00ff41;--dkgreen:#003b00;--cyan:#00f6ff;--gold:#ffd700;--silver:#c0c0c0;--bronze:#cd7f32}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:#888;font-family:'Share Tech Mono',monospace;overflow-x:hidden}}
#matrix{{position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;opacity:0.15}}
.wrapper{{max-width:1000px;margin:0 auto;padding:40px 20px;position:relative;z-index:1}}
.site-header{{text-align:center;margin-bottom:60px;padding:40px;border:1px solid #111;background:rgba(0,0,0,0.8);backdrop-filter:blur(10px)}}
.lock-span{{font-size:3em;display:block;margin-bottom:10px;filter:drop-shadow(0 0 10px var(--green))}}
.lock-span.open{{display:none}}
.site-title{{font-family:'Orbitron',sans-serif;font-size:2.5em;color:#fff;letter-spacing:.3em;text-transform:uppercase;margin-bottom:10px}}
.site-sub{{color:var(--green);letter-spacing:.5em;font-size:.8em}}
.blink{{animation:blink 1s step-end infinite}}
@keyframes blink{{50%{{opacity:0}}}}
.stats-bar{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:40px}}
.stat{{background:var(--panel);padding:20px;border:1px solid #181818;text-align:center}}
.stat-lbl{{font-size:.7em;color:#444;text-transform:uppercase;letter-spacing:.2em;margin-bottom:5px}}
.stat-num{{font-family:'Orbitron',sans-serif;font-size:2em;color:#fff}}
.section-hdr{{font-size:.8em;color:var(--green);letter-spacing:.4em;text-transform:uppercase;margin-bottom:20px;display:flex;align-items:center;gap:15px}}
.section-hdr::after{{content:'';flex:1;height:1px;background:linear-gradient(90deg,var(--dkgreen),transparent)}}
.network-card{{background:var(--panel);border:1px solid #181818;margin-bottom:30px;transition:all .3s}}
.network-card:hover{{border-color:var(--dkgreen);box-shadow:0 0 30px rgba(0,255,65,0.05)}}
.network-header{{padding:15px 20px;background:#0d0d0d;display:flex;align-items:center;gap:15px;border-bottom:1px solid #151515}}
.led{{width:10px;height:10px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);animation:pulse .9s ease-in-out infinite alternate}}
@keyframes pulse{{from{{opacity:.4}}to{{opacity:1}}}}
.ssid-name{{flex:1;font-size:1.1em;color:#eee;letter-spacing:.05em;word-break:break-all}}
.tag{{font-size:.7em;padding:3px 10px;border:1px solid var(--dkgreen);color:var(--dkgreen);letter-spacing:.1em}}
.card-body{{padding:18px 20px;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}}
.field{{display:flex;flex-direction:column;gap:3px}}
.lbl{{font-size:.65em;color:#444;letter-spacing:.2em}}
.val{{font-size:.9em;color:#aaa}}
.mono{{font-family:'Share Tech Mono',monospace}}
.ok{{color:var(--green);text-shadow:0 0 8px var(--green)}}
.pwd-reveal{{padding:20px;background:#080808;border-top:1px solid #1a1a1a;text-align:center}}
.pwd-label{{font-size:.7em;color:var(--dkgreen);letter-spacing:.25em;margin-bottom:10px}}
.pwd-value{{font-size:1.8em;color:var(--cyan);font-family:'Orbitron',sans-serif;letter-spacing:.12em;word-break:break-all;text-shadow:0 0 20px var(--cyan),0 0 40px rgba(0,246,255,.4)}}
.empty{{color:#333;text-align:center;padding:60px;letter-spacing:.2em}}
.wl-section{{margin:50px 0}}
.wl-list{{display:flex;flex-direction:column;gap:14px}}
.wl-row{{display:grid;grid-template-columns:48px 1fr 220px 80px;align-items:center;gap:16px;background:var(--panel);border:1px solid #181818;padding:16px 20px;position:relative;overflow:hidden;animation:fadeSlide .5s ease calc(var(--delay)) both;transition:border-color .3s,box-shadow .3s}}
.wl-row:hover{{border-color:rgba(0,255,65,.3);box-shadow:0 0 20px rgba(0,255,65,.06),inset 0 0 40px rgba(0,255,65,.02)}}
.wl-row.rank-0{{border-left:3px solid var(--gold)}}
.wl-row.rank-1{{border-left:3px solid var(--silver)}}
.wl-row.rank-2{{border-left:3px solid var(--bronze)}}
.wl-rank{{font-size:1.6em;text-align:center;line-height:1}}
.wl-info{{min-width:0}}
.wl-name{{font-size:.95em;color:#ddd;letter-spacing:.04em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.wl-ssids{{display:flex;flex-wrap:wrap;gap:5px;margin-top:7px}}
.ssid-tag{{font-size:.65em;padding:2px 8px;background:#111;border:1px solid #222;color:#888;border-radius:3px}}
.wl-bar-wrap{{height:8px;background:#111;border-radius:4px;overflow:hidden;position:relative}}
.wl-bar{{height:100%;width:0;background:linear-gradient(90deg,var(--dkgreen),var(--green));box-shadow:0 0 10px rgba(0,255,65,.5);border-radius:4px;transition:width 1.2s cubic-bezier(.22,1,.36,1)}}
.wl-count{{font-family:'Orbitron',sans-serif;font-size:1.3em;color:var(--green);text-shadow:0 0 12px var(--green);text-align:right}}
.site-footer{{text-align:center;padding:30px;font-size:.7em;color:#222;border-top:1px solid #111;margin-top:40px;letter-spacing:.15em}}
</style></head>
<body>
<canvas id="matrix"></canvas>
<div class="wrapper">
  <header class="site-header">
    <div style="position:relative;display:inline-block;margin-bottom:12px">
      <span class="lock-span">🔒</span>
      <span class="lock-span open" style="position:absolute;left:0">🔓</span>
    </div>
    <div class="site-title">cyberwalisson</div>
    <div class="site-sub">[ WPA/WPA2 &nbsp;·&nbsp; RESULTADOS &nbsp;·&nbsp; <span class="blink">■</span> AO VIVO ]</div>
  </header>
  <div class="stats-bar">
    <div class="stat"><div class="stat-lbl">// senhas quebradas</div><div class="stat-num">{total:03d}</div></div>
    <div class="stat"><div class="stat-lbl">// wordlists ativas</div><div class="stat-num">{len(wl_stats):03d}</div></div>
    <div class="stat"><div class="stat-lbl">// última atualização</div><div class="stat-num" style="font-size:1em;padding-top:8px">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div></div>
  </div>
  {wl_section}
  {pwd_section}
  <div class="section-hdr" style="margin-top:40px">redes alvo</div>
  {cards}{empty_msg}
  <footer class="site-footer">cyberwalisson :: pcapcracker pro &nbsp;|&nbsp; {datetime.now().strftime("%Y")} &nbsp;|&nbsp; <span style="color:var(--green)">[ USO APENAS PARA TESTES AUTORIZADOS ]</span></footer>
</div>
<script>
const c=document.getElementById('matrix'),ctx=c.getContext('2d');
function resize(){{c.width=window.innerWidth;c.height=window.innerHeight}}
resize();window.addEventListener('resize',resize);
const cols=Math.floor(c.width/16);const drops=Array(cols).fill(1);
const chars='アイウエオカキクケコ0123456789ABCDEF<>[]{{}}01';
function draw(){{ctx.fillStyle='rgba(0,0,0,0.05)';ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='#00ff41';ctx.font='14px monospace';drops.forEach((y,i)=>{{ctx.fillText(chars[Math.floor(Math.random()*chars.length)],i*16,y*16);if(y*16>c.height&&Math.random()>0.975)drops[i]=0;drops[i]++;}});}}
setInterval(draw,50);
(function(){{const observer=new IntersectionObserver((entries)=>{{entries.forEach(e=>{{if(e.isIntersecting){{const bar=e.target.querySelector('.wl-bar');if(bar){{const pct=bar.getAttribute('data-pct');bar.style.width=pct;}}observer.unobserve(e.target);}}}}}},{{threshold:0.1}});document.querySelectorAll('.wl-row').forEach(r=>observer.observe(r));}})();
</script>
</body></html>"""

    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        L.s(f"results.html atualizado ({total} senha(s)): {path}")
        return path
    except Exception as e:
        L.e(f"Erro ao salvar results.html: {e}")
        return None

def gen_html(data, tp="extract"):
    ts=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fname=f"extracao_{data['ssid'][:20]}_{ts}.html"
    content=f"""<div class="header">
<h1>📦 EXTRAÇÃO DE HASH</h1>
<div class="subtitle">Captura de Handshake de Rede</div></div>
<div class="stats">
<div class="stat-card success"><div class="stat-label">Extraído</div>
<div class="stat-value">✓</div></div>
<div class="stat-card info"><div class="stat-label">Formato</div>
<div class="stat-value" style="font-size:1.5em">22000</div></div></div>
<div class="content">
<div class="section"><h2 class="section-title">Informações da Rede</h2>
<div class="network-card">
<div class="network-name">{escape(data['ssid'])}</div>
<div class="detail"><span class="detail-label">BSSID:</span>
<span class="detail-value">{escape(data['bssid'])}</span></div>
<div class="detail"><span class="detail-label">Método:</span>
<span class="detail-value">{data['method']}</span></div></div></div>
<div class="section"><h2 class="section-title">Arquivos</h2>
<table class="info-table"><tr><td>Fonte PCAP</td><td>{escape(data['pcap'])}</td></tr>
<tr><td>Arquivo Hash</td><td>{escape(data['hash'])}</td></tr>
</table></div></div>"""

    path=f"{cfg.HTML}/{fname}"
    L.p(f"Gerando HTML: {path}")
    try:
        with open(path,'w',encoding='utf-8') as f:
            f.write(HTML_TPL.format(title=fname.replace('.html',''),content=content,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        L.s(f"HTML salvo: {path}")
        return path
    except Exception as e:
        L.e(f"Erro ao salvar HTML {path}: {e}")
        return None

# ── Logger JSON ────────────────────────────────────────────
def log_json(db_or_data, tp="crack"):
    if tp == "crack":
        path = f"{cfg.JSON}/resultados.json"
        rows = db_or_data.all()
        wl_stats = db_or_data.wordlist_stats()
        pwd_ranking = db_or_data.get_pwd_ranking(50)

        seen = set(); unique = []
        for r in rows:
            key = (r[0], r[1], r[2])
            if key not in seen:
                seen.add(key)
                unique.append({
                    "ssid": r[0], "bssid": r[1], "senha": r[2],
                    "status": r[3], "data": r[4],
                    "metodo": r[5], "wordlist": r[6]
                })
        payload = {
            "gerado_em": datetime.now().isoformat(),
            "total": len(unique),
            "estatisticas_wordlist": wl_stats,
            "ranking_senhas": pwd_ranking,
            "resultados": unique
        }
        L.p(f"Atualizando resultados.json ({len(unique)} senha(s))")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=4, ensure_ascii=False)
        except Exception as e:
            L.e(f"Erro ao salvar JSON: {e}")

# ── SSID Map ───────────────────────────────────────────────
def build_ssid_map():
    ssid_map = {}
    if not os.path.exists(cfg.HASH): return {}
    hfiles = [f for f in os.listdir(cfg.HASH)
              if f.endswith('.22000') and valid(f"{cfg.HASH}/{f}")]
    for hf in hfiles:
        path = f"{cfg.HASH}/{hf}"
        ss, bs, _ = Ext.parse(path)
        key = ss if ss != "UNKNOWN" else Path(hf).stem
        if key not in ssid_map:
            ssid_map[key] = []
        ssid_map[key].append(path)
    return ssid_map

def select_ssid(ssid_map):
    if not ssid_map:
        L.e("nenhum hash disponível — verifique a pasta pcap/"); return None, None
    G = '\033[38;5;22m'; LG = '\033[38;5;46m'; RS = '\033[0m'
    ssids = list(ssid_map.keys())
    print(f"\n  {G}// alvos disponíveis{RS}\n  {G}{'─'*46}{RS}")
    for i, s in enumerate(ssids):
        n = len(ssid_map[s])
        print(f"  {G}[{LG}{i:02d}{G}]{RS}  {LG}{s}{RS}  {G}// {n} hash{'es' if n>1 else ''}{RS}")
    print(f"  {G}{'─'*46}{RS}")
    try:
        idx = int(input(f"\n  {G}[{LG}>{G}]{RS} selecione o ID do alvo: ").strip())
        ssid = ssids[idx]
        L.i(f"alvo bloqueado :: {LG}{ssid}{RS}")
        return ssid, ssid_map[ssid]
    except (ValueError, IndexError):
        L.e("seleção inválida"); return None, None

def select_wordlist():
    wls = [f for f in os.listdir(cfg.WL) if valid(f"{cfg.WL}/{f}")]
    if not wls:
        L.e("nenhuma wordlist encontrada na pasta wordlist/"); return None
    G = '\033[38;5;22m'; LG = '\033[38;5;46m'; RS = '\033[0m'
    print(f"\n  {G}// wordlists disponíveis\n  {'─'*46}{RS}")
    for i, w in enumerate(wls):
        sz = os.path.getsize(f"{cfg.WL}/{w}")
        sz_lbl = f"{sz//1024}K" if sz < 1024*1024 else f"{sz//1024//1024}M"
        print(f"  {G}[{LG}{i:02d}{G}]{RS}  {w}  {G}// {sz_lbl}{RS}")
    print(f"  {G}{'─'*46}{RS}")
    try:
        idx = int(input(f"\n  {G}[{LG}>{G}]{RS} selecione o ID da wordlist: ").strip())
        L.i(f"wordlist carregada :: {LG}{wls[idx]}{RS}")
        return f"{cfg.WL}/{wls[idx]}"
    except (ValueError, IndexError):
        L.e("seleção inválida"); return None

# ── Atacante ───────────────────────────────────────────────
class Att:
    def __init__(self,db): self.db=db
    def hc(self,hf,wl,rules=None):
        hm=fhash(hf); wm=fhash(wl)
        if self.db.chk(hm,wm,"hc",cfg.MAX_ATT):
            L.w(f"Ignorando (máx tentativas): {Path(hf).name}")
            return None
        cmd=["hashcat","-m","22000","-a","0",hf,wl,"--potfile-path",cfg.POT,
             "--opencl-device-types","1","--force","--quiet"]
        if rules: cmd+=["-r",rules]
        L.p(f"Hashcat: {Path(hf).name} + {Path(wl).name}")
        run(cmd); self.db.reg(hm,wm,"hc")
        pwd=self._chk(hf)
        if pwd:
            ss,bs,_=Ext.parse(hf)
            L.success_box(ss,bs,pwd)
            self.db.save(ss,bs,pwd,Path(hf).name,Path(wl).name,"OK-HC",hm,wm,"hashcat")
            gen_results_html(self.db)
            log_json(self.db, 'crack')
        else:
            L.w("Não encontrada")
        return pwd
    def _chk(self,hf):
        r=run(["hashcat","-m","22000","--show",hf,"--potfile-path",cfg.POT],cap=True)
        if r and r.stdout:
            for ln in r.stdout.splitlines():
                pts=ln.split(":")
                if len(pts)>=2: return pts[-1].strip()
        return None

# ── CLI ────────────────────────────────────────────────────
class CLI:
    def __init__(self):
        self.db=DB(cfg.DB); self.ai=AI()
        self.att=Att(self.db)
        self.ssid_map = {}

    def banner(self):
        G  = '\033[38;5;22m'; LG = '\033[38;5;46m'
        RS = Style.RESET_ALL;  Y  = Fore.YELLOW
        mask = f"""
{G}  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░{L.RS}
{G}  ░  {LG} ██████╗██╗   ██╗██████╗ ███████╗██████╗{G}           ░{L.RS}
{G}  ░  {LG}██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗{G}          ░{L.RS}
{G}  ░  {LG}██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝{G}          ░{L.RS}
{G}  ░  {LG}██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗{G}          ░{L.RS}
{G}  ░  {LG}╚██████╗   ██║   ██████╔╝███████╗██║  ██║{G}          ░{L.RS}
{G}  ░  {LG} ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝{G}          ░{L.RS}
{G}  ░                                                       ░{L.RS}
{G}  ░  {Y}     w a l i s s o n  //  WPA/WPA2  //  v2.3 IA  {G}░{L.RS}
{G}  ░  {LG}  Nós somos Anonymous. Nós somos Legião.         {G}░{L.RS}
{G}  ░  {LG}  Nós não perdoamos. Nós não esquecemos.         {G}░{L.RS}
{G}  ░  {LG}  Esperem por nós.                               {G}░{L.RS}
{G}  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░{L.RS}"""
        print(mask)

    def menu(self):
        n   = len(self.ssid_map)
        G   = '\033[38;5;22m'; LG  = '\033[38;5;46m'
        RS  = Style.RESET_ALL;  Y   = Fore.YELLOW
        bar = f"{G}  {'─'*50}{L.RS}"
        print(f"\n{bar}")
        print(f"{G}  // {LG}MENU DE OPERAÇÕES{L.RS}")
        print(f"{bar}")
        print(f"  {G}[{LG}1{G}]{L.RS}  alvo SSID  +  wordlist única")
        print(f"  {G}[{LG}2{G}]{L.RS}  alvo SSID  +  todas wordlists")
        print(f"  {G}[{LG}3{G}]{L.RS}  TODOS os alvos  +  todas wordlists   {G}// TOTALMENTE AUTO{L.RS}")
        print(f"  {G}[{LG}4{G}]{L.RS}  mostrar senhas quebradas")
        print(f"  {G}[{LG}5{G}]{L.RS}  exportar CSV")
        print(f"  {G}[{LG}6{G}]{L.RS}  {Y}Análise IA (Estratégia SSID){L.RS}")
        print(f"  {G}[{LG}7{G}]{L.RS}  {Y}Sugestões IA (Wordlists Ideais){L.RS}")
        print(f"  {G}[{LG}8{G}]{L.RS}  {Y}Ranking de Senhas Mais Usadas{L.RS}")
        print(f"  {G}[{LG}0{G}]{L.RS}  desconectar")
        print(f"{bar}")
        print(f"  {G}alvos_em_memoria {LG}::{L.RS} {Y}{n}{L.RS}   "
              f"{G}sessão {LG}::{L.RS} {Y}{datetime.now().strftime('%H:%M:%S')}{L.RS}")
        print(f"{bar}\n")

    def auto_extract(self):
        G  = '\033[38;5;22m'; LG = '\033[38;5;46m'; RS = Style.RESET_ALL
        bar = f"{G}  {'─'*50}{L.RS}"
        print(f"\n{bar}")
        print(f"{G}  // {LG}ESCANEANDO DIRETÓRIO PCAP{L.RS}")
        print(f"{bar}")
        if not os.path.exists(cfg.PCAP): os.makedirs(cfg.PCAP)
        pcaps = [f for f in os.listdir(cfg.PCAP)
                 if f.lower().endswith(('.pcap', '.pcapng', '.cap', '.scap'))]
        if not pcaps:
            L.w("nenhum arquivo pcap encontrado em pcap/")
        else:
            L.i(f"{len(pcaps)} arquivo(s) detectado(s) — iniciando extração de hashes")
            for p in tqdm(pcaps, desc="  extraindo", unit="pcap",
                          bar_format="  {l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]"):
                Ext.extract(f"{cfg.PCAP}/{p}")
        self.ssid_map = build_ssid_map()
        if self.ssid_map:
            print(f"\n{bar}")
            print(f"{G}  // {LG}ALVOS IDENTIFICADOS{L.RS}")
            print(f"{bar}")
            for ssid, paths in self.ssid_map.items():
                n = len(paths)
                print(f"  {G}[+]{L.RS} {LG}{ssid}{L.RS}  {G}// {n} hash{'es' if n>1 else ''}{L.RS}")
            print(f"{bar}")
        else:
            L.w("nenhum hash disponível após a extração")
        print()

    def attack_ssid_wl(self):
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{'ATAQUE: SSID + WORDLIST'.center(50)}")
        print(f"{'='*50}{Style.RESET_ALL}\n")
        ssid, hashes = select_ssid(self.ssid_map)
        if not ssid: return
        wl = select_wordlist()
        if not wl: return
        L.i(f"Alvo: {Fore.CYAN}{ssid}{Style.RESET_ALL} | WL: {Fore.YELLOW}{Path(wl).name}{Style.RESET_ALL}")
        cracked = False
        for hf in hashes:
            if self.att.hc(hf, wl): cracked = True
        if cracked: self.show()

    def attack_ssid_all_wl(self):
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{'ATAQUE: SSID + TODAS WORDLISTS'.center(50)}")
        print(f"{'='*50}{Style.RESET_ALL}\n")
        ssid, hashes = select_ssid(self.ssid_map)
        if not ssid: return
        wls = [f"{cfg.WL}/{f}" for f in os.listdir(cfg.WL) if valid(f"{cfg.WL}/{f}")]
        if not wls: L.e("Sem wordlists na pasta wordlist/"); return
        L.i(f"Alvo: {Fore.CYAN}{ssid}{Style.RESET_ALL} | "
            f"{Fore.YELLOW}{len(wls)} wordlist(s){Style.RESET_ALL}")
        cracked = False
        for hf in hashes:
            for wl in tqdm(wls, desc=f"WL → {Path(hf).name}", unit="w"):
                if self.att.hc(hf, wl): cracked = True
        if cracked: self.show()
        L.s("operação concluída")

    def attack_all_ssid_all_wl(self):
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{'ATAQUE: TODOS SSIDs + TODAS WORDLISTS'.center(50)}")
        print(f"{'='*50}{Style.RESET_ALL}\n")
        if not self.ssid_map:
            L.e("Nenhum hash disponível. Verifique a pasta pcap/."); return
        wls = [f"{cfg.WL}/{f}" for f in os.listdir(cfg.WL) if valid(f"{cfg.WL}/{f}")]
        if not wls: L.e("Sem wordlists na pasta wordlist/"); return
        total_ssids = len(self.ssid_map)
        L.i(f"SSIDs: {Fore.CYAN}{total_ssids}{Style.RESET_ALL} | "
            f"Wordlists: {Fore.YELLOW}{len(wls)}{Style.RESET_ALL}")
        cracked = False
        for idx, (ssid, hashes) in enumerate(self.ssid_map.items(), 1):
            print(f"\n{Fore.CYAN}[{idx}/{total_ssids}]{Style.RESET_ALL} "
                  f"Alvo: {Fore.CYAN}{ssid}{Style.RESET_ALL}")
            for hf in hashes:
                for wl in tqdm(wls, desc=f"  WL → {Path(hf).name}", unit="w"):
                    if self.att.hc(hf, wl): cracked = True
        if cracked: self.show()
        L.s("operação concluída")

    def show(self):
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{'SENHAS QUEBRADAS'.center(50)}")
        print(f"{'='*50}{Style.RESET_ALL}\n")
        rs = self.db.all()
        if not rs: L.w("Nenhuma senha encontrada"); return
        print(f"{Fore.GREEN}Total: {len(rs)} senha(s){Style.RESET_ALL}\n")
        for r in rs:
            ss, bs, pw = r[0], r[1], r[2]
            lines = [
                f"{Fore.WHITE}SSID:{Style.RESET_ALL}   {Fore.CYAN}{ss[:40]}{Style.RESET_ALL}",
                f"{Fore.WHITE}BSSID:{Style.RESET_ALL}  {Fore.MAGENTA}{bs}{Style.RESET_ALL}",
                f"{Fore.WHITE}SENHA:{Style.RESET_ALL}  {Fore.GREEN}{pw}{Style.RESET_ALL}"
            ]
            L.box(f"{Fore.GREEN}✓ SENHA QUEBRADA{Style.RESET_ALL}", lines)

    def csv(self):
        rs=self.db.all()
        if not rs: L.w("Sem dados"); return
        out="export.csv"
        try:
            with open(out,"w") as f:
                f.write("ssid,bssid,password,status,timestamp,method,wordlist\n")
                for r in rs: f.write(",".join(str(x or "") for x in r)+"\n")
            L.s(f"CSV gerado: {out}")
        except Exception as e:
            L.e(f"Erro ao salvar CSV {out}: {e}")

    def ai_ssid_analysis(self):
        ssid, _ = select_ssid(self.ssid_map)
        if not ssid: return
        L.p(f"Analisando SSID '{ssid}' com IA ({self.ai.provider})...")
        analysis = self.ai.analyze_ssid(ssid)
        L.box("ANÁLISE ESTRATÉGICA IA", analysis.split('\n'))

    def ai_wordlist_suggestion(self):
        ssid, _ = select_ssid(self.ssid_map)
        if not ssid: return
        L.p(f"Consultando IA ({self.ai.provider}) para sugestão de wordlists para '{ssid}'...")
        suggestion = self.ai.suggest_wordlists(ssid)
        L.box("WORDLISTS SUGERIDAS PELA IA", suggestion.split('\n'))

    def show_pwd_ranking(self):
        ranking = self.db.get_pwd_ranking(15)
        if not ranking: L.w("Sem estatísticas de senhas ainda."); return
        lines = [f"{Fore.CYAN}{p[0]:<20}{L.RS} | {Fore.YELLOW}{p[1]} vezes{L.RS}" for p in ranking]
        L.box("RANKING DE SENHAS MAIS COMUNS", lines)

    def run(self):
        self.banner()
        self.auto_extract()
        while True:
            self.menu()
            op=input(f"\n{Fore.YELLOW}► Opção: {Style.RESET_ALL}").strip()
            if op=="1":   self.attack_ssid_wl()
            elif op=="2": self.attack_ssid_all_wl()
            elif op=="3": self.attack_all_ssid_all_wl()
            elif op=="4": self.show()
            elif op=="5": self.csv()
            elif op=="6": self.ai_ssid_analysis()
            elif op=="7": self.ai_wordlist_suggestion()
            elif op=="8": self.show_pwd_ranking()
            elif op=="0": print(f"{Fore.GREEN}Até logo!{Style.RESET_ALL}"); break
            else: L.e("Opção inválida")

if __name__=="__main__":
    cli=CLI()
    cli.run()
