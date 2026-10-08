# Base de Conhecimento

O Jarvis usa três tipos de conhecimento:

1. **Base de programação e produtividade** (curada, em Markdown), consultada pela ferramenta `consultar_base_conhecimento`;
2. **Perfil do usuário**, que vai no system prompt;
3. **Dados das ferramentas** (agenda, Trello, Linear, Slack, Notion), consultados ao vivo pelas ferramentas. Na demonstração, vêm de dados simulados.

## Dados Utilizados

| Arquivo | Formato | Utilização no Agente |
|---------|---------|---------------------|
| `conhecimento/web.md` | Markdown | HTML semântico, CSS (Flexbox/Grid), JavaScript moderno, async/await, HTTP/REST, CORS, segurança web |
| `conhecimento/python.md` | Markdown | venv, PEP 8, estruturas de dados, erros, `requests`, asyncio, pytest, frameworks |
| `conhecimento/nodejs.md` | Markdown | npm, CommonJS × ESM, event loop, Express, `.env`, erros comuns, testes |
| `conhecimento/php.md` | Markdown | Composer, recursos do PHP 8, arrays, PDO, segurança, Laravel/Symfony |
| `conhecimento/csharp.md` | Markdown | CLI do .NET, records, pattern matching, nullable, LINQ, async/await, ASP.NET Core |
| `conhecimento/boas_praticas.md` | Markdown | Git, code review, depuração, testes, organização de tarefas (prioridades do Linear) |
| `conhecimento/produtividade.md` | Markdown | **Ritual de planejamento de domingo**, regras de blocos de foco, alertas no Google Agenda |
| `perfil_usuario.json` | JSON | Nome, stack, expediente, período de foco, almoço, restrições e lembrete padrão |
| `mock/agenda.json` | JSON | Eventos da semana (dailies, reuniões, academia, aula) |
| `mock/trello.json` | JSON | Quadro "Projetos Pessoais" com listas e cartões |
| `mock/linear.json` | JSON | Issues do time ENG com prioridade, estimativa e prazo |
| `mock/slack.json` | JSON | Mensagens com pedidos e prazos |
| `mock/notion.json` | JSON | Páginas (notas da sprint, onboarding, ideias de estudo) |

---

## Adaptações nos Dados

- **Substituí os dados financeiros do repositório base** por dados do novo caso de uso: um desenvolvedor e as ferramentas que ele usa.
- **A base de programação foi escrita em Markdown, dividida em seções `##`.** Cada seção é um trecho pesquisável e vira a fonte citada (`arquivo.md > seção`).
- **Incluí armadilhas comuns de propósito**, como "`fetch` não rejeita em 404", "não existe `array_flatten` no PHP" e "evite `.Result` em C# async". São exatamente os pontos em que um LLM tende a alucinar.
- **As datas dos dados simulados são relativas** (`dia_semana: 0` = segunda). Elas são convertidas para a semana de referência, que é a semana atual ou a próxima, se hoje for domingo. Assim, a demonstração nunca fica desatualizada.
- **Os dados simulados têm conexões entre si para o agente descobrir:** a Carla pede no Slack para priorizar a ENG-142, que é urgente e vence na terça; a Bruna pede a revisão da ENG-150 até quinta; o Rafael quer a exportação CSV (ENG-138) na demo de quarta.

---

## Estratégia de Integração

### Como os dados são carregados?

| Fonte | Quando | Como |
|---|---|---|
| Base de programação | Início da sessão | `conhecimento.py` divide os `.md` em seções e indexa as palavras (sem acentos, sem *stopwords*, com peso maior para termos raros). |
| Perfil | Início da sessão | Vai inteiro no system prompt, junto com a data/hora atual e a semana de referência. |
| Agenda e ferramentas | A cada pergunta | Por **ferramentas** chamadas pelo LLM. No modo `demo`, vêm de `data/mock`; no modo `real`, das APIs. |

### Como os dados são usados no prompt?

- **Perfil e data atual → system prompt.** São pequenos e sempre relevantes: sem a data, o modelo não sabe o que é "amanhã"; sem o perfil, não respeita os horários de foco.
- **Base de programação → recuperada sob demanda (RAG simples).** O prompt manda chamar `consultar_base_conhecimento` antes de responder dúvidas técnicas. A ferramenta devolve as 3 seções mais relevantes, cada uma com a linha `FONTE:`.
- **Agenda, tarefas e mensagens → consultadas ao vivo.** Esses dados mudam o tempo todo, então nunca ficam no prompt. O modelo precisa consultá-los, o que evita respostas desatualizadas.

---

## Exemplo de Contexto Montado

Resultado real da ferramenta para a consulta `"erro de cors no node"`:

```
FONTE: web.md > CORS
[Desenvolvimento Web (HTML, CSS, JavaScript, HTTP)]
- CORS é uma proteção do **navegador**: uma página só lê respostas de outra origem (domínio, porta ou
  protocolo diferente) se o servidor permitir com o cabeçalho `Access-Control-Allow-Origin`.
- O erro de CORS se resolve **no servidor** (liberando a origem), não no front-end.
...
---
FONTE: nodejs.md > Módulos: CommonJS x ES Modules
...
```

Resultado real de `listar_tarefas(fonte="linear")` numa demonstração com data de domingo, 11/10/2026:

```json
{"linear": [
 {"id": "ENG-142", "titulo": "Corrigir erro de CORS na API de relatórios (Node.js)", "estado": "Todo",
  "prioridade": 1, "estimativa_horas": 3, "prazo": "2026-10-13 (terça)"},
 {"id": "ENG-138", "titulo": "Endpoint de exportação CSV no serviço Python (FastAPI)", "estado": "In Progress",
  "prioridade": 2, "estimativa_horas": 6, "prazo": "2026-10-14 (quarta)"},
 ...
]}
```

Trecho do contexto fixo no system prompt:

```
## Contexto atual
- Agora: domingo, 2026-10-11 19:00 (America/Sao_Paulo)
- Semana de referência: 2026-10-12 (segunda) a 2026-10-18 (domingo)
- Integrações: Google Agenda: simulado, Trello: simulado, Linear: simulado, Slack: simulado, Notion: simulado

## Perfil do usuário (fonte: perfil_usuario.json)
{ "nome": "Alex Souza", "stack_principal": ["Python", "Node.js"],
  "periodo_de_foco": {"inicio": "09:00", "fim": "12:00"}, "lembrete_padrao_minutos": 15, ... }
```
