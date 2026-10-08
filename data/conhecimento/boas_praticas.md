# Boas Práticas de Desenvolvimento

## Git e commits
- Faça commits pequenos e com um propósito só. Mensagem no imperativo e objetiva: `feat: adiciona filtro por data`.
- Convenção *Conventional Commits*: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
- Fluxo com branches: crie uma branch por tarefa (`git switch -c feat/filtro-data`), abra um Pull Request e faça merge após a revisão.
- Desfazer com segurança: `git restore arquivo` descarta mudanças locais; `git revert <commit>` cria um commit que desfaz outro sem reescrever o histórico.
- Nunca faça commit de segredos. Se acontecer, **revogue a chave imediatamente**: apagar o arquivo não remove a chave do histórico.

## Code review
- Revise primeiro o comportamento (o código faz o que a tarefa pede?), depois a legibilidade e só então o estilo.
- Comentários de revisão devem ser específicos e sugerir uma alternativa.
- PRs pequenos (até ~400 linhas) são revisados com mais qualidade e rapidez.

## Depuração (debugging)
1. Reproduza o erro de forma consistente.
2. Leia a mensagem de erro e o *stack trace* inteiro: a primeira linha do **seu** código costuma apontar a causa.
3. Isole: reduza o caso até o menor exemplo que ainda falha.
4. Formule uma hipótese, teste e mude **uma** coisa por vez.
5. Depois de corrigir, escreva um teste que teria pegado o bug.

## Testes
- Pirâmide de testes: muitos testes de unidade (rápidos), alguns de integração e poucos de ponta a ponta (E2E).
- Teste comportamento, não implementação. Bons testes seguem o padrão *Arrange, Act, Assert*.
- Ferramentas por linguagem: Python → pytest; Node.js → `node --test`, Jest ou Vitest; PHP → PHPUnit ou Pest; C# → xUnit, NUnit ou MSTest.

## Organização de tarefas de desenvolvimento
- Quebre tarefas grandes em entregas de até 1 dia de trabalho.
- Uma issue boa tem: contexto (por quê), critério de aceite (como saber que acabou) e links relevantes.
- Prioridade no Linear: 1 = Urgente, 2 = Alta, 3 = Média, 4 = Baixa (0 = sem prioridade).
- Estados típicos de um quadro Kanban (Trello): "A fazer" → "Fazendo" → "Em revisão" → "Feito". Limite o trabalho em andamento.
