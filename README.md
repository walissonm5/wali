# 🛡️ PCAPCracker Pro (Groq Edition)

Ferramenta avançada para auditoria de redes WPA/WPA2-PSK com integração de Inteligência Artificial **GRATUITA** via GroqCloud.

## 🚀 Novidades: Suporte a GroqCloud (Grátis)
Esta versão utiliza a API do GroqCloud, permitindo o uso de modelos de linguagem de ponta sem custos:

- **🔍 Análise Inteligente de SSID**: A IA analisa o nome da rede (SSID) para identificar padrões de provedores ou modelos de roteadores.
- **💡 Sugestões de Próximos Passos**: Com base no histórico de tentativas de crack, a IA recomenda novas abordagens, como wordlists ou regras do Hashcat.

## 🛠️ Requisitos
- Python 3.x
- `python3-venv` (para ambientes virtuais)
- Hashcat, hcxtools, tshark
- **Groq API Key**: Obtenha gratuitamente em [console.groq.com/keys](https://console.groq.com/keys)

## ⚙️ Instalação e Configuração (Automática)

Para configurar o ambiente, incluindo o ambiente virtual Python e a API da Groq, execute o script `setup.sh`:

```bash
chmod +x setup.sh
./setup.sh
```

O script irá:
1. Instalar as dependências do sistema (hashcat, hcxdumptool, tshark).
2. Criar e configurar um ambiente virtual Python (`.venv`).
3. Instalar as bibliotecas Python necessárias (`groq`, `colorama`, `tqdm`).
4. Solicitar sua **GROQ_API_KEY**.
5. Permitir que você escolha o modelo da Groq (ex: `llama-3.3-70b-versatile`).
6. Criar a estrutura de diretórios necessária.
7. Gerar o arquivo `config.ini` com suas configurações.

## ✅ Teste da Configuração da IA

Para verificar se a integração com a GroqCloud está funcionando corretamente, execute o comando de teste:

```bash
./run.sh test
```

## 📖 Como usar
1. Coloque seus arquivos `.pcap` na pasta `pcap/`.
2. Adicione suas wordlists na pasta `wordlist/`.
3. Execute a ferramenta usando o script `run.sh`:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
4. Use as opções **6** e **7** do menu para suporte de IA.

## ⚖️ Aviso Legal
Esta ferramenta foi desenvolvida apenas para fins educacionais e testes de penetração autorizados. O uso contra redes sem permissão explícita é ilegal.
