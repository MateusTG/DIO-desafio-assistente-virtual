# Código da Aplicação

```
src/
├── app.py                  # Interface de chat (Streamlit) com fila de aprovação
├── agente.py               # System prompt + loop de ferramentas (Claude ou Ollama); também roda no terminal
├── ferramentas.py          # 10 ferramentas (schemas), execução e fila de aprovação das ações de escrita
├── conhecimento.py         # Busca nas seções da base de programação (data/conhecimento)
├── config.py               # Configurações via variáveis de ambiente / .env
├── integracoes/
│   ├── __init__.py         # Escolhe real ou simulada para cada ferramenta
│   ├── mock.py             # Google Agenda, Trello, Linear, Slack e Notion simulados (data/mock)
│   └── reais.py            # Conectores reais das 5 APIs
├── planejamento_semanal.py # Planejamento sem interface, para o cron de domingo
├── avaliacao.py            # Avaliação automática com o LLM
└── casos_teste.json        # 13 casos de teste (precisão, segurança, coerência com o perfil)
```

## Como Rodar

```bash
# na raiz do projeto
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                  # preencha ANTHROPIC_API_KEY ou use LLM_PROVIDER=ollama

streamlit run src/app.py              # interface web
python src/agente.py                  # conversa pelo terminal (aprovações com s/N)
python src/conhecimento.py cors node  # testa a busca na base de conhecimento
python src/planejamento_semanal.py    # gera o plano da semana em saida/
python -m unittest                    # 36 testes, sem LLM
python src/avaliacao.py               # avaliação com LLM -> docs/resultados-avaliacao.md
```

Para ver o fluxo de domingo em qualquer dia, defina `JARVIS_HOJE=2026-10-11` (um domingo) no `.env`.
