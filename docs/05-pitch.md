# Pitch (3 minutos)

> [!TIP]
> Você pode usar alguns slides pra apoiar no seu Pitch e mostrar sua solução na prática.

## Roteiro Sugerido

### 1. O Problema (30 seg)
> Qual dor do cliente você resolve?

"Segunda-feira, 9 da manhã. O Alex, desenvolvedor, abre o Google Agenda, depois o Trello, o Linear, o Slack e o Notion, tentando descobrir o que é prioridade. Só no Slack, ele vê que a issue urgente vence amanhã. Quem trabalha com tecnologia perde horas por semana trocando de contexto entre ferramentas, e a semana começa sem plano."

### 2. A Solução (1 min)
> Como seu agente resolve esse problema?

"Esse é o Jarvis, um assistente pessoal inspirado no do Homem de Ferro. Ele conversa com você e com as suas ferramentas.

Todo domingo, ele cruza agenda, tarefas e mensagens e monta a semana: prioriza o que vence antes, reserva blocos de foco no horário em que você rende mais e propõe os eventos com alertas no Google Agenda. Durante a semana, responde 'o que vence hoje?', cria cartões e issues e tira dúvidas de Python, Node.js, PHP, C# e web, sempre citando a fonte.

E ele nunca age sozinho: toda ação de escrita espera o seu 'aprovar'. Essa garantia está no código, não só no prompt."

### 3. Demonstração (1 min)
> Mostre o agente funcionando (pode ser gravação de tela)

Gravação de tela de `streamlit run src/app.py` com `JARVIS_HOJE` num domingo:
1. Barra lateral: aviso "É domingo, dia de planejar a semana". Clique em **📅 Planejar minha semana**.
2. O Jarvis consulta agenda, Linear, Trello e Slack (os passos aparecem na tela) e mostra a tabela da semana. Ele percebe que a ENG-142 é urgente e que a Carla pediu prioridade.
3. Os blocos aparecem em **"Aguardando sua aprovação"**. Clique em **Aprovar todas** e pergunte "o que tenho na segunda?". Os blocos já estão lá.
4. Pergunte **"Como resolvo um erro de CORS no Node?"**. Ele responde com a fonte e liga a resposta à ENG-142.
5. Pergunte **"Uso array_flatten no PHP, certo?"**. Ele corrige: a função não existe.
6. (5 seg) Terminal com `python -m unittest` (36 testes passando) e `python src/avaliacao.py`.

### 4. Diferencial e Impacto (30 seg)
> Por que essa solução é inovadora e qual é o impacto dela na sociedade?

"A maioria dos assistentes de IA ou só conversa ou age sem pedir permissão. O Jarvis faz as duas coisas com responsabilidade: consulta dados reais em vez de inventar, cita fontes e mantém a pessoa no controle de cada ação. Ele funciona com Claude ou com um modelo local e gratuito via Ollama, o que deixa a ferramenta acessível para quem está começando. Menos tempo organizando trabalho significa mais tempo para aprender, criar e descansar."

---

## Checklist do Pitch

- [ ] Duração máxima de 3 minutos
- [ ] Problema claramente definido
- [ ] Solução demonstrada na prática
- [ ] Diferencial explicado
- [ ] Áudio e vídeo com boa qualidade

---

## Link do Vídeo

> Cole aqui o link do seu pitch (YouTube, Loom, Google Drive, etc.)

[Link do vídeo]
