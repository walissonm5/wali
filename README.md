# 🛡️ PCAPCracker Pro (AI Edition)

Ferramenta avançada para auditoria de redes WPA/WPA2-PSK com integração de Inteligência Artificial para análise estratégica.

## 🚀 Novidades: Suporte a IA
Esta versão agora inclui suporte nativo a modelos de linguagem (LLM) para auxiliar no processo de pentest:

- **🔍 Análise Inteligente de SSID**: A IA analisa o nome da rede (SSID) para identificar padrões de provedores, modelos de roteadores ou nomes personalizados, sugerindo as melhores wordlists e estratégias de ataque.
- **💡 Sugestões de Próximos Passos**: Com base no histórico de tentativas de crack, a IA recomenda novas abordagens, como o uso de regras específicas do Hashcat ou wordlists temáticas.

## 🛠️ Requisitos
- Python 3.x
- `python3-venv` (para ambientes virtuais)
- Hashcat
- hcxtools
- OpenAI API Key (configurada via variável de ambiente `OPENAI_API_KEY`)

## ⚙️ Instalação e Configuração (Automática)

Para configurar o ambiente, incluindo um ambiente virtual Python e todas as dependências, execute o script `setup.sh`:

```bash
chmod +x setup.sh
./setup.sh
```

O script irá:
1. Instalar as dependências do sistema (python3-venv, hashcat, hcxdumptool, hcxpcapngtool, tshark).
2. Criar e ativar um ambiente virtual Python (`.venv`).
3. Instalar as bibliotecas Python necessárias (openai, colorama, tqdm) dentro do ambiente virtual.
4. Solicitar sua `OPENAI_API_KEY`.
5. Permitir que você escolha o modelo de IA a ser utilizado (`gpt-4.1-mini`, `gemini-2.5-flash`, etc.).
6. Criar a estrutura de diretórios (`pcap/`, `wordlist/`, `hash/`, `rules/`, `logs/`).
7. Gerar o arquivo `config.ini` com o modelo de IA selecionado.

**Observação**: O script `setup.sh` agora inclui `set -e` e `set -x` para depuração. Isso significa que ele será mais "barulhento" no terminal, mostrando cada comando executado e parando em caso de erro. Isso é útil para identificar problemas.

## ✅ Teste da Configuração da IA

Para verificar se a integração com a IA está funcionando corretamente, execute o script `test_ai.py` através do `run.sh`:

```bash
./run.sh python3 test_ai.py
```

Este script verificará se a `OPENAI_API_KEY` está configurada e se o modelo de IA selecionado em `config.ini` consegue se comunicar com a API da OpenAI.

## 📖 Como usar
1. Coloque seus arquivos `.pcap` na pasta `pcap/`.
2. Adicione suas wordlists na pasta `wordlist/`.
3. Execute a ferramenta usando o script `run.sh` (ele ativará automaticamente o ambiente virtual):
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
4. Use as opções **6** e **7** do menu para suporte de IA.

## ⚖️ Aviso Legal
Esta ferramenta foi desenvolvida apenas para fins educacionais e testes de penetração autorizados. O uso contra redes sem permissão explícita é ilegal.
