# ⚡ Identity Engine v2.0 - OSINT Pro

Este projeto é uma engine avançada de OSINT para busca e análise de identidade digital, integrando **Sherlock** e **Maigret** com uma camada de rede resiliente.

## 🔥 Novas Funcionalidades

-   **🧠 Ban Detection Automático**: Identifica bloqueios (403, 429) e reage instantaneamente.
-   **🔄 Proxy Pool & Rotação**: Suporta lista de proxies customizados e fallback para Tor.
-   **🛡 Anti-Rate-Limit**: Delays inteligentes e User-Agents aleatórios.
-   **🚀 Auto-Setup**: Script que configura ambiente virtual e dependências sozinho.
-   **🛰 Multi-hop ready**: Estrutura preparada para encadeamento de proxies.

## 🛠 Como Instalar

Basta executar o script de setup automático:

```bash
chmod +x setup.sh
./setup.sh
```

## 🚀 Como Usar

1. Ative o ambiente virtual:
   ```bash
   source venv/bin/activate
   ```

2. Execute a busca:
   ```bash
   python3 identity_engine.py <username>
   ```

3. (Opcional) Adicione seus próprios proxies em `config/proxies.txt`.

## 📂 Estrutura do Projeto

- `identity_engine.py`: Motor principal e lógica de análise.
- `proxy_manager.py`: Cérebro da rede (rotação, anti-ban, renovação de IP).
- `setup.sh`: Instalador automático.
- `config/`: Configurações de proxy e rede.
- `relatorio/`: Onde os resultados HTML são salvos.

---
*Desenvolvido para fins educacionais e de pesquisa em segurança.*
