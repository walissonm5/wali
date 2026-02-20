"""
Proxy Manager - Gerenciador de proxies e rede resiliente
Com tratamento gracioso de dependências faltantes
"""

import requests
import time
import socket
import random
import sys

# Importações opcionais com fallback
try:
    from stem import Signal
    from stem.control import Controller
    TOR_AVAILABLE = True
except ImportError:
    TOR_AVAILABLE = False
    print("[*] Stem não disponível - Tor desativado")

try:
    from fake_useragent import UserAgent
    ua_available = True
except ImportError:
    ua_available = False
    print("[*] fake-useragent não disponível - usando User-Agents padrão")

class ProxyManager:
    """Gerenciador de proxies com suporte a Tor e fallback automático"""
    
    def __init__(self, proxy_file="config/proxies.txt"):
        """Inicializa o gerenciador de proxies"""
        self.ua = None
        if ua_available:
            try:
                self.ua = UserAgent()
            except:
                pass
        
        self.proxies = self._load_proxies(proxy_file)
        self.tor_proxy = "socks5h://127.0.0.1:9050"
        self.use_tor = self._check_tor()
        self.current_proxy_idx = 0
        
        if self.use_tor:
            print("[✓] Tor detectado e disponível")
        elif self.proxies:
            print(f"[✓] {len(self.proxies)} proxy(ies) carregado(s)")
        else:
            print("[*] Usando conexão direta (sem proxies)")
    
    def _load_proxies(self, path):
        """Carrega proxies do arquivo de configuração"""
        try:
            with open(path, "r") as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                return lines
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"[!] Erro ao carregar proxies: {e}")
            return []
    
    def _check_tor(self):
        """Verifica se Tor está disponível"""
        if not TOR_AVAILABLE:
            return False
        
        try:
            s = socket.create_connection(("127.0.0.1", 9050), timeout=2)
            s.close()
            return True
        except:
            return False
    
    def get_random_proxy(self):
        """Retorna um proxy aleatório do pool ou Tor como fallback"""
        if self.proxies:
            p = random.choice(self.proxies)
            return {"http": p, "https": p}
        
        if self.use_tor:
            return {"http": self.tor_proxy, "https": self.tor_proxy}
        
        return None
    
    def get_next_proxy(self):
        """Retorna o próximo proxy da lista em sequência"""
        if not self.proxies:
            if self.use_tor:
                return {"http": self.tor_proxy, "https": self.tor_proxy}
            return None
        
        proxy = self.proxies[self.current_proxy_idx]
        self.current_proxy_idx = (self.current_proxy_idx + 1) % len(self.proxies)
        return {"http": proxy, "https": proxy}
    
    def get_external_ip(self, proxies=None):
        """Testa o IP externo atual"""
        urls = [
            "https://api.ipify.org",
            "https://ifconfig.me/ip",
            "https://icanhazip.com"
        ]
        
        for url in urls:
            try:
                r = requests.get(url, proxies=proxies, timeout=5)
                if r.status_code == 200:
                    return r.text.strip()
            except:
                continue
        
        return "Desconhecido"
    
    def renew_ip(self):
        """Força a troca de IP via Tor ou rotação de pool"""
        if self.use_tor and TOR_AVAILABLE:
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
    
    def is_banned(self, response):
        """Detecta se fomos banidos/rate-limited"""
        ban_indicators = [403, 429, 503]
        
        if response.status_code in ban_indicators:
            return True
        
        text = response.text.lower()
        ban_keywords = ["too many requests", "captcha", "blocked", "access denied", "forbidden"]
        
        for keyword in ban_keywords:
            if keyword in text:
                return True
        
        return False
    
    def get_headers(self):
        """Retorna headers com User-Agent aleatório ou padrão"""
        if self.ua:
            try:
                user_agent = self.ua.random
            except:
                user_agent = self._get_default_user_agent()
        else:
            user_agent = self._get_default_user_agent()
        
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    def _get_default_user_agent(self):
        """Retorna um User-Agent padrão"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        ]
        return random.choice(user_agents)
    
    def smart_request(self, url, method="GET", retries=3, **kwargs):
        """Executa uma requisição com retry inteligente e troca de IP"""
        for attempt in range(retries):
            try:
                proxies = self.get_next_proxy()
                headers = self.get_headers()
                
                r = requests.request(
                    method, url,
                    proxies=proxies,
                    headers=headers,
                    timeout=10,
                    **kwargs
                )
                
                if not self.is_banned(r):
                    return r
                
                print(f"[!] Ban detectado em {url}. Trocando IP (Tentativa {attempt+1}/{retries})...")
                self.renew_ip()
                time.sleep(random.uniform(2, 5))
            
            except Exception as e:
                print(f"[!] Erro na requisição: {e}. Retentando...")
                self.renew_ip()
                time.sleep(random.uniform(1, 3))
        
        print(f"[!] Falha após {retries} tentativas para {url}")
        return None


# Teste rápido
if __name__ == "__main__":
    print("[*] Testando ProxyManager...")
    pm = ProxyManager()
    
    print(f"[*] Proxies carregados: {len(pm.proxies)}")
    print(f"[*] Tor disponível: {pm.use_tor}")
    
    # Testar IP externo
    proxy = pm.get_next_proxy()
    ip = pm.get_external_ip(proxy)
    print(f"[✓] IP Externo: {ip}")
    
    print("[✓] ProxyManager funcionando!")
