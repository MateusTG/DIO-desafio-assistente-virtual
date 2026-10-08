# C# e .NET

## CLI do .NET
- Criar projetos: `dotnet new console -n MeuApp`, `dotnet new webapi -n MinhaApi`, `dotnet new xunit -n MeusTestes`.
- Rodar e testar: `dotnet run`, `dotnet build`, `dotnet test`.
- Pacotes NuGet: `dotnet add package Newtonsoft.Json` (ou use o `System.Text.Json`, que já vem embutido).
- `dotnet watch` recompila e reinicia a aplicação ao salvar arquivos.

## Recursos da linguagem
- `var` infere o tipo em tempo de compilação; a variável continua fortemente tipada.
- Propriedades automáticas: `public string Nome { get; set; }`; com `init`, só podem ser definidas na criação.
- `record` (C# 9) cria tipos imutáveis com igualdade por valor: `public record Pessoa(string Nome, int Idade);`.
- Interpolação de strings: `$"Olá, {nome}!"`.
- Pattern matching: `if (obj is string texto) { ... }` e expressões `switch`:
  `var faixa = idade switch { < 18 => "menor", < 60 => "adulto", _ => "idoso" };`.
- Nullable reference types (C# 8): com `<Nullable>enable</Nullable>`, `string?` indica que o valor pode ser nulo e o compilador avisa sobre possíveis `NullReferenceException`.
- Operadores de nulo: `?.` (acesso condicional), `??` (valor padrão) e `??=` (atribui se nulo).

## LINQ
- Consultas sobre coleções: `var ativos = usuarios.Where(u => u.Ativo).OrderBy(u => u.Nome).Select(u => u.Email).ToList();`.
- `First()` lança exceção se não houver elemento; `FirstOrDefault()` retorna `null` ou o valor padrão.
- LINQ é avaliado de forma preguiçosa (*deferred execution*): a consulta só roda quando é enumerada (`ToList`, `foreach`, `Count`...).

## async/await
- Métodos assíncronos retornam `Task` ou `Task<T>` e, por convenção, terminam com `Async`: `public async Task<Usuario> BuscarAsync(int id)`.
- Evite `.Result` e `.Wait()` em código assíncrono: podem causar deadlock. Use `await` em toda a cadeia.
- Evite `async void`, exceto em handlers de eventos; exceções nesses métodos não podem ser capturadas por quem chama.
- `await Task.WhenAll(t1, t2)` executa tarefas em paralelo.
- Use `HttpClient` via `IHttpClientFactory` (injeção de dependência) em vez de criar um `new HttpClient()` por requisição, o que pode esgotar sockets.

## ASP.NET Core
- Minimal API:
  ```csharp
  var builder = WebApplication.CreateBuilder(args);
  var app = builder.Build();
  app.MapGet("/tarefas/{id:int}", (int id) => Results.Ok(new { id }));
  app.Run();
  ```
- Injeção de dependência: registre serviços em `builder.Services` com `AddSingleton`, `AddScoped` (um por requisição) ou `AddTransient` (um por uso).
- Configuração em `appsettings.json` e variáveis de ambiente. Segredos de desenvolvimento ficam no `dotnet user-secrets`.
- Entity Framework Core é o ORM oficial: `dotnet ef migrations add Inicial` e `dotnet ef database update` (requer a ferramenta `dotnet-ef`).

## Erros comuns
- `NullReferenceException`: acesso a membro de objeto nulo. Ative nullable reference types e use `?.`/`??`.
- `InvalidOperationException: Sequence contains no elements`: `First()` ou `Single()` em coleção vazia; use `FirstOrDefault()`.
- `CS0103: The name 'x' does not exist in the current context`: variável fora do escopo ou `using` faltando.
