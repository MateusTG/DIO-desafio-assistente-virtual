# Integrações Reais (opcional)

Por padrão, o Jarvis roda em **modo demo** (`JARVIS_MODO=demo`), com todas as ferramentas simuladas por `data/mock/`. Para conectar as suas contas de verdade, defina `JARVIS_MODO=real` no `.env` e configure as ferramentas que quiser. **As que ficarem sem credenciais continuam simuladas.** A barra lateral mostra o modo de cada uma.

> [!WARNING]
> Os conectores reais (`src/integracoes/reais.py`) têm testes com respostas HTTP simuladas, mas ainda **não foram testados com contas reais**. Comece com um calendário e um quadro de teste.

> [!CAUTION]
> Tokens dão acesso às suas contas. Guarde-os só no `.env` (que está no `.gitignore`) e **nunca** os cole no chat nem faça commit deles.

---

## Google Agenda (eventos e alertas)

1. No [Google Cloud Console](https://console.cloud.google.com/), crie um projeto e ative a **Google Calendar API**.
2. Configure a **tela de consentimento OAuth** (tipo "Externo", com você como usuário de teste).
3. Em **Credenciais → Criar credenciais → ID do cliente OAuth → App para computador**, baixe o JSON e salve como `credentials.json` na raiz do projeto.
4. Na primeira execução, o navegador abre para autorizar. O token fica salvo em `token.json`.

Escopo usado: `calendar.events` (ler e criar eventos). Os eventos criados recebem um alerta **popup** com os minutos definidos (padrão do perfil: 15).

| Variável | Padrão |
|---|---|
| `GOOGLE_CREDENCIAIS` | `credentials.json` |
| `GOOGLE_TOKEN` | `token.json` |
| `GOOGLE_CALENDAR_ID` | `primary` (o seu calendário principal) |

## Trello

1. Acesse [trello.com/power-ups/admin](https://trello.com/power-ups/admin), crie um Power-Up e gere uma **API key**. Na mesma página, gere um **token**.
2. O ID do quadro aparece ao abrir `https://trello.com/b/<ID>/...` ou ao acrescentar `.json` ao final da URL do quadro.

`TRELLO_KEY`, `TRELLO_TOKEN`, `TRELLO_BOARD_ID`

## Slack

1. Em [api.slack.com/apps](https://api.slack.com/apps), crie um app e adicione os escopos de bot `channels:history` e `chat:write`.
2. Instale o app no workspace e copie o **Bot User OAuth Token** (`xoxb-...`).
3. Convide o bot para o canal (`/invite @seu-bot`) e copie o ID do canal (clique no nome do canal → "Sobre").

`SLACK_BOT_TOKEN`, `SLACK_CANAL_ID`. O Jarvis lê as mensagens recentes **desse canal** e envia mensagens em qualquer canal em que o bot esteja.

## Linear

1. Nas configurações da sua conta no Linear, na seção de API, crie uma **Personal API key**.
2. Para descobrir o ID do time (`LINEAR_TEAM_ID`), que só é necessário para criar issues:
   ```bash
   curl -s https://api.linear.app/graphql -H "Authorization: $LINEAR_API_KEY" \
     -H "Content-Type: application/json" -d '{"query":"{ teams { nodes { id name } } }"}'
   ```

`LINEAR_API_KEY`, `LINEAR_TEAM_ID`. O Jarvis lista as issues **atribuídas a você** que não estão concluídas.

## Notion

1. Em [notion.so/my-integrations](https://www.notion.so/my-integrations), crie uma integração interna e copie o token.
2. Nas páginas que o Jarvis pode ler, use **⋯ → Conexões → adicionar a integração**.
3. Para criar páginas, escolha uma página "pai" (ex.: "Planos semanais"), conecte a integração e copie o ID (os 32 caracteres no fim da URL).

`NOTION_TOKEN`, `NOTION_PAGINA_PAI_ID`

---

## Planejamento automático aos domingos

Para o Jarvis montar a semana sozinho todo domingo às 19h (Linux/macOS), use `crontab -e`:

```cron
0 19 * * 0  cd /caminho/do/projeto && .venv/bin/python src/planejamento_semanal.py
```

O plano é salvo em `saida/plano_semana_AAAA-MM-DD.md`, e os eventos ficam **propostos, mas não criados**. Se preferir criar os blocos e alertas automaticamente, adicione `--aprovar-tudo`. No Windows, use o Agendador de Tarefas com o mesmo comando.
