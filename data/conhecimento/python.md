# Python

## Ambiente virtual e dependências
- Crie um ambiente isolado por projeto: `python -m venv .venv`.
- Ative: `source .venv/bin/activate` (Linux/macOS) ou `.venv\Scripts\activate` (Windows).
- Instale e registre dependências: `pip install requests` e `pip freeze > requirements.txt`; para reinstalar, use `pip install -r requirements.txt`.
- Não versione a pasta `.venv/`; adicione-a ao `.gitignore`.

## Boas práticas e estilo (PEP 8)
- Nomes: `snake_case` para funções e variáveis, `PascalCase` para classes, `MAIUSCULAS` para constantes.
- Indentação de 4 espaços. Formatadores como `black` ou `ruff format` padronizam o estilo automaticamente.
- Use f-strings para formatar texto: `f"Olá, {nome}!"`.
- Use `pathlib.Path` para caminhos de arquivo em vez de concatenar strings.
- Abra arquivos com `with open(caminho, encoding="utf-8") as f:`, que fecha o arquivo automaticamente.
- Type hints documentam a intenção: `def soma(a: int, b: int) -> int:`. Eles não são verificados em tempo de execução; use `mypy` ou `pyright` para checar.

## Estruturas de dados
- `list` é ordenada e mutável; `tuple` é ordenada e imutável; `set` não tem duplicatas e faz busca rápida; `dict` mapeia chave → valor.
- List comprehension: `quadrados = [x * x for x in numeros if x > 0]`.
- `dict.get(chave, padrao)` evita `KeyError` quando a chave pode não existir.
- `collections.Counter` conta ocorrências; `collections.defaultdict` cria valores padrão automaticamente.
- `dataclasses.dataclass` gera `__init__`, `__repr__` e `__eq__` para classes que guardam dados.

## Tratamento de erros
- Capture exceções específicas: `except FileNotFoundError:`, e não um `except:` genérico que esconde bugs.
- Use `raise ValueError("mensagem clara")` para sinalizar entrada inválida.
- `finally` sempre executa; prefira `with` (gerenciadores de contexto) para liberar recursos.
- Armadilha clássica: argumento padrão mutável. `def f(itens=[])` reaproveita a mesma lista entre chamadas. Use `def f(itens=None): itens = itens or []`.

## Requisições HTTP
- A biblioteca `requests` é a mais usada (`pip install requests`):
  ```python
  import requests
  resp = requests.get("https://api.exemplo.com/itens", timeout=10)
  resp.raise_for_status()  # lança exceção para 4xx/5xx
  dados = resp.json()
  ```
- Sempre defina `timeout`: sem ele, a requisição pode esperar para sempre.
- Para código assíncrono, use `httpx` (`httpx.AsyncClient`) ou `aiohttp`.

## Assincronismo (asyncio)
- `async def` cria uma corrotina; `await` espera outra corrotina; `asyncio.run(main())` inicia o programa.
- `asyncio.gather(a(), b())` executa corrotinas em paralelo.
- asyncio ajuda em tarefas de I/O (rede, disco). Para tarefas pesadas de CPU, use `multiprocessing` ou `concurrent.futures.ProcessPoolExecutor`.

## Testes com pytest
- Instale com `pip install pytest`; arquivos `test_*.py` e funções `test_*` são descobertos automaticamente.
- Use `assert` simples: `assert soma(2, 3) == 5`.
- Para testar exceções: `with pytest.raises(ValueError): funcao_invalida()`.
- *Fixtures* (`@pytest.fixture`) preparam dados reutilizáveis entre testes.
- A biblioteca padrão também tem o `unittest`: `python -m unittest discover tests`.

## Frameworks web
- **Flask**: micro-framework simples, bom para APIs pequenas e protótipos.
- **FastAPI**: APIs modernas com type hints, validação automática via Pydantic e documentação OpenAPI em `/docs`.
- **Django**: framework completo com ORM, admin, autenticação e migrações, bom para aplicações grandes.
- Streamlit e Gradio criam interfaces web de dados e IA rapidamente, só com Python.
