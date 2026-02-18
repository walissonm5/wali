import requests
import time
import socket
import random
from stem import Signal
from stem.control import Controller
from fake_useragent import UserAgent

class ProxyManager:
    def __init__(self, proxy_file="config/proxies.txt"):
        self.ua = UserAgent()
        self.proxies = self._load_proxies(proxy_file)
        self.tor_proxy = "socks5h://127.0.0.1:9050"
        self.use_tor = self._check_tor()
        
    def _load_proxies(self, path):
        try:
            with open(path, "r") as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                return lines
        except:
            return []

    def _check_tor(self):
        try:
            s = socket.create_connection(("127.0.0.1", 9050), timeout=2)
            s.close()
            return True
        except:
            return False

    def get_random_proxy(self):
        """Retorna um proxy aleatório do pool ou Tor como fallback."""
        if self.proxies:
            p = random.choice(self.proxies)
            return {"http": p, "https": p}
        if self.use_tor:
            return {"http": self.tor_proxy, "https": self.tor_proxy}
        return None

    def get_external_ip(self, proxies=None):
        """Testa o IP externo atual."""
        urls = ["https://api.ipify.org", "https://ifconfig.me/ip", "https://icanhazip.com"]
        for url in urls:
            try:
                r = requests.get(url, proxies=proxies, timeout=5)
                if r.status_code == 200:
                    return r.text.strip()
            except:
                continue
        return "Desconhecido"

    def renew_ip(self):
        """Força a troca de IP via Tor ou rotação de pool."""
        if self.use_tor:
            try:
                with Controller.from_port(port=9051) as controller:
                    controller.authenticate()
                    controller.signal(Signal.NEWNYM)
                time.sleep(2) # Espera o circuito estabilizar
                return True
            except Exception as e:
                print(f"[!] Erro ao renovar Tor: {e}")
        return False

    def is_banned(self, response):
        """Detecta se fomos banidos/rate-limited."""
        ban_indicators = [403, 429, 503]
        if response.status_code in ban_indicators:
            return True
        # Algumas APIs retornam 200 mas com mensagem de erro
        text = response.text.lower()
        if "too many requests" in text or "captcha" in text or "blocked" in text:
            return True
        return False

    def get_headers(self):
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def smart_request(self, url, method="GET", retries=3, **kwargs):
        """Executa uma requisição com retry inteligente e troca de IP."""
        for attempt in range(retries):
            proxies = self.get_random_proxy()
            headers = self.get_headers()
            
            try:
                r = requests.request(method, url, proxies=proxies, headers=headers, timeout=10, **kwargs)
                if not self.is_banned(r):
                    return r
                
                print(f"[!] Ban detectado em {url}. Trocando IP (Tentativa {attempt+1}/{retries})...")
                self.renew_ip()
                time.sleep(random.uniform(2, 5))
            except Exception as e:
                print(f"[!] Erro na requisição: {e}. Retentando...")
                self.renew_ip()
                
        return None
