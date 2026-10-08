# Desenvolvimento Web (HTML, CSS, JavaScript, HTTP)

## HTML semântico e acessibilidade
- Use tags com significado: `header`, `nav`, `main`, `section`, `article`, `aside`, `footer`. Elas ajudam leitores de tela e SEO.
- Toda imagem informativa precisa de `alt` descritivo; imagens decorativas usam `alt=""`.
- Todo campo de formulário precisa de um `label` associado (`<label for="email">` + `<input id="email">`).
- Use `button` para ações e `a` para navegação. Não use `div` clicável.
- Declare o idioma da página: `<html lang="pt-BR">`, e inclua `<meta name="viewport" content="width=device-width, initial-scale=1">` para funcionar bem no celular.

## CSS: layout com Flexbox e Grid
- Flexbox organiza itens em uma dimensão (linha **ou** coluna): `display: flex; justify-content: space-between; align-items: center; gap: 1rem;`.
- Grid organiza em duas dimensões: `display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;` cria colunas responsivas sem media query.
- Prefira unidades relativas (`rem`, `%`, `vw`) e `max-width` em vez de larguras fixas.
- `box-sizing: border-box` faz o `padding` e a `border` contarem dentro da largura declarada.
- Variáveis CSS: declare em `:root { --cor-primaria: #0a84ff; }` e use com `var(--cor-primaria)`.

## JavaScript moderno (ES6+)
- Use `const` por padrão e `let` quando precisar reatribuir. Evite `var` (escopo de função e hoisting confuso).
- Compare com `===` e `!==` (sem conversão de tipo). `==` converte tipos e gera surpresas como `0 == ""` ser `true`.
- Desestruturação: `const { nome, idade } = usuario;` e `const [primeiro, ...resto] = lista;`.
- Encadeamento opcional e coalescência nula: `usuario?.endereco?.cidade ?? "não informado"`.
- Métodos de array: `map` (transforma), `filter` (filtra), `reduce` (acumula), `find` (primeiro que casa), `some`/`every` (testes).
- Módulos: `export function soma() {}` e `import { soma } from "./util.js";`.

## Assincronismo: Promises e async/await
- `async`/`await` deixa código assíncrono com cara de síncrono. Sempre trate erros com `try/catch`.
- Para executar requisições independentes em paralelo, use `await Promise.all([a(), b()])` em vez de vários `await` em sequência.
- `Promise.allSettled` espera todas, mesmo as que falham, e informa o status de cada uma.
- Exemplo com `fetch`:
  ```js
  async function buscarUsuario(id) {
    const resp = await fetch(`/api/usuarios/${id}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  }
  ```
- Atenção: `fetch` **não** rejeita a Promise em erros HTTP (404, 500). É preciso checar `resp.ok`.

## HTTP e APIs REST
- Métodos: `GET` (ler), `POST` (criar), `PUT` (substituir), `PATCH` (atualizar parte), `DELETE` (remover).
- Códigos de status: 2xx sucesso (200 OK, 201 Created, 204 No Content); 3xx redirecionamento; 4xx erro do cliente (400 Bad Request, 401 não autenticado, 403 sem permissão, 404 não encontrado, 422 dados inválidos, 429 limite de requisições); 5xx erro do servidor.
- `GET`, `PUT` e `DELETE` devem ser idempotentes: repetir a chamada não muda o resultado.
- Nomeie recursos no plural e com substantivos: `/usuarios/42/pedidos`, não `/getPedidosDoUsuario`.

## CORS
- CORS é uma proteção do **navegador**: uma página só lê respostas de outra origem (domínio, porta ou protocolo diferente) se o servidor permitir com o cabeçalho `Access-Control-Allow-Origin`.
- O erro de CORS se resolve **no servidor** (liberando a origem), não no front-end.
- Requisições com métodos ou cabeçalhos especiais disparam um *preflight* `OPTIONS` antes da chamada real.
- Evite `Access-Control-Allow-Origin: *` em APIs que usam cookies ou autenticação.

## Segurança web essencial
- **XSS**: nunca insira texto do usuário com `innerHTML`. Use `textContent` ou o escape do framework.
- **SQL Injection**: use consultas parametrizadas, nunca concatene strings com dados do usuário.
- **CSRF**: proteja formulários que alteram dados com token CSRF ou cookies `SameSite`.
- Guarde segredos (chaves de API, senhas) em variáveis de ambiente, nunca no código nem no repositório.
- Senhas devem ser armazenadas com hash lento e com salt (bcrypt, Argon2), nunca em texto puro nem com MD5/SHA1.
