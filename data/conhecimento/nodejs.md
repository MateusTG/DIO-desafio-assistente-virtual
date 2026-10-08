# Node.js

## Projeto e gerenciamento de pacotes
- Inicie um projeto com `npm init -y`, que cria o `package.json`.
- Instale dependências com `npm install express`; para ferramentas só de desenvolvimento, use `npm install -D nodemon`.
- `package-lock.json` trava as versões exatas e **deve** ser versionado. `node_modules/` **não** deve.
- Em CI, prefira `npm ci`: instala exatamente o que está no lock e é mais rápido.
- Scripts ficam em `"scripts"` no `package.json` e rodam com `npm run nome`, por exemplo `"dev": "nodemon src/index.js"`.

## Módulos: CommonJS x ES Modules
- CommonJS (padrão histórico): `const fs = require("fs");` e `module.exports = { ... }`.
- ES Modules: `import fs from "node:fs";` e `export function ...`. Ative com `"type": "module"` no `package.json` ou com a extensão `.mjs`.
- Em ES Modules, `__dirname` não existe. Use `import.meta.dirname` (Node 20.11+) ou derive de `import.meta.url`.
- Prefira o prefixo `node:` para módulos nativos (`node:fs`, `node:path`) para deixar claro que não são pacotes do npm.

## Event loop e código assíncrono
- O Node executa JavaScript em **uma** thread principal, com um event loop que agenda callbacks de I/O.
- Operações de I/O (rede, disco) não bloqueiam; cálculos pesados **bloqueiam** todo o servidor. Para CPU intensiva, use `worker_threads`.
- Use as versões com Promise das APIs: `import { readFile } from "node:fs/promises";` e `await readFile(caminho, "utf8")`.
- Evite as versões `*Sync` (ex.: `readFileSync`) dentro de rotas de servidor.
- `fetch` é nativo a partir do Node 18.

## Express: API básica
```js
import express from "express";
const app = express();
app.use(express.json()); // lê corpo JSON

app.get("/tarefas/:id", async (req, res, next) => {
  try {
    const tarefa = await buscarTarefa(req.params.id);
    if (!tarefa) return res.status(404).json({ erro: "não encontrada" });
    res.json(tarefa);
  } catch (err) {
    next(err); // envia para o middleware de erro
  }
});

app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ erro: "erro interno" });
});

app.listen(3000);
```
- Middlewares rodam em ordem; chame `next()` para seguir adiante.
- Valide entradas (ex.: com as bibliotecas `zod` ou `joi`) antes de usar.

## Variáveis de ambiente e configuração
- Leia com `process.env.NOME`. Para carregar um arquivo `.env`, use o pacote `dotenv` ou a flag `node --env-file=.env` (Node 20.6+).
- Nunca versione o `.env`; versione um `.env.example` sem valores secretos.

## Erros comuns
- `UnhandledPromiseRejection`: faltou `await` ou `.catch()` em uma Promise que falhou.
- `EADDRINUSE`: a porta já está em uso; encerre o outro processo ou troque a porta.
- `ERR_REQUIRE_ESM`: tentativa de usar `require` em um pacote que é só ES Module; use `import`.
- `Cannot find module`: dependência não instalada (`npm install`) ou caminho relativo errado.

## Testes
- O Node 18+ tem um executor de testes nativo: `node --test`, com `import test from "node:test"` e `import assert from "node:assert"`.
- Alternativas populares: Jest e Vitest.
