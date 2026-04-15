# 🛡️ PCAPCracker Pro (AI Edition)

Ferramenta avançada para auditoria de redes WPA/WPA2-PSK com integração de Inteligência Artificial para análise estratégica.

## 🚀 Novidades: Suporte a IA
Esta versão agora inclui suporte nativo a modelos de linguagem (LLM) para auxiliar no processo de pentest:

- **🔍 Análise Inteligente de SSID**: A IA analisa o nome da rede (SSID) para identificar padrões de provedores, modelos de roteadores ou nomes personalizados, sugerindo as melhores wordlists e estratégias de ataque.
- **💡 Sugestões de Próximos Passos**: Com base no histórico de tentativas de crack, a IA recomenda novas abordagens, como o uso de regras específicas do Hashcat ou wordlists temáticas.

## 🛠️ Requisitos
- Python 3.x
- Hashcat
- hcxtools
- OpenAI API Key (configurada via variável de ambiente `OPENAI_API_KEY`)

## 📖 Como usar
1. Coloque seus arquivos `.pcap` na pasta `pcap/`.
2. Adicione suas wordlists na pasta `wordlist/`.
3. Execute a ferramenta:
   ```bash
   python3 pcapcracker_pro.py
   ```
4. Use as opções **6** e **7** do menu para suporte de IA.

## ⚖️ Aviso Legal
Esta ferramenta foi desenvolvida apenas para fins educacionais e testes de penetração autorizados. O uso contra redes sem permissão explícita é ilegal.
