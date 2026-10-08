# PHP

## Composer e autoload
- Composer é o gerenciador de dependências: `composer init`, `composer require guzzlehttp/guzzle`.
- `composer.lock` deve ser versionado; `vendor/` não.
- Autoload PSR-4 no `composer.json`: `"autoload": { "psr-4": { "App\\": "src/" } }`. Depois rode `composer dump-autoload` e inclua `require __DIR__ . '/vendor/autoload.php';`.

## Recursos do PHP 8
- Tipos de retorno e de parâmetro: `function soma(int $a, int $b): int`.
- Ative tipagem estrita no topo do arquivo: `declare(strict_types=1);`.
- `match` é uma alternativa mais segura ao `switch`: compara com `===` e retorna valor:
  `$texto = match($status) { 200 => 'ok', 404 => 'não encontrado', default => 'erro' };`
- Operador nullsafe: `$cidade = $usuario?->endereco?->cidade;`.
- Argumentos nomeados: `str_pad(string: $s, length: 10, pad_type: STR_PAD_LEFT);`.
- Promoção de propriedades no construtor:
  `public function __construct(private string $nome, private int $idade) {}`.
- PHP 8.1 trouxe `enum` e propriedades `readonly`.

## Arrays e funções úteis
- `array_map`, `array_filter` e `array_reduce` para transformar, filtrar e acumular.
- Para "achatar" um array de arrays, use `array_merge(...$listas)`. **Não existe** função nativa `array_flatten` no PHP.
- `in_array($valor, $lista, true)`: o terceiro argumento `true` ativa a comparação estrita.
- `json_encode($dados)` e `json_decode($json, true)` (o `true` retorna array associativo em vez de objeto).
- `??` (coalescência nula): `$pagina = $_GET['pagina'] ?? 1;`.

## Banco de dados com PDO (seguro)
```php
$pdo = new PDO('mysql:host=localhost;dbname=app;charset=utf8mb4', $usuario, $senha, [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
]);
$stmt = $pdo->prepare('SELECT * FROM usuarios WHERE email = :email');
$stmt->execute(['email' => $email]);
$usuario = $stmt->fetch(PDO::FETCH_ASSOC);
```
- Sempre use *prepared statements*; nunca concatene variáveis na SQL.
- As antigas funções `mysql_*` foram removidas no PHP 7. Use PDO ou `mysqli`.

## Segurança
- Senhas: `password_hash($senha, PASSWORD_DEFAULT)` para gravar e `password_verify($senha, $hash)` para conferir. Nunca use `md5`.
- Escape saída HTML com `htmlspecialchars($texto, ENT_QUOTES, 'UTF-8')` para evitar XSS.
- Não exiba erros em produção: `display_errors=Off` e registre em log.

## Frameworks e ferramentas
- **Laravel**: framework completo (Eloquent ORM, migrations, filas, Blade). Comandos via `php artisan`.
- **Symfony**: componentes robustos e reutilizáveis (muitos são usados pelo próprio Laravel).
- Servidor embutido para desenvolvimento: `php -S localhost:8000 -t public`.
- Testes com PHPUnit: `composer require --dev phpunit/phpunit` e `vendor/bin/phpunit`.
- Padrão de estilo: PSR-12 (hoje PER Coding Style). Ferramentas: PHP-CS-Fixer, PHP_CodeSniffer, PHPStan (análise estática).
