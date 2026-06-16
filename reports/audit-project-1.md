# Audit Report — Project 1: code-smells-project

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask==3.1.1, flask-cors==5.0.1, sqlite3 (stdlib)
Domain:        E-commerce — produtos (products), usuários (users),
               pedidos (orders), relatórios de vendas (sales reports)
Architecture:  Partial MVC — 4 flat files at root, no directory separation.
               models.py mixes data access with business logic across 4 domains;
               controllers.py handles HTTP + partial validation; database.py
               is a global singleton with DDL + seed data embedded.
Source files:  5 files analyzed (~780 lines of code)
               app.py          (88 lines)  — routes + 2 admin endpoints
               controllers.py  (292 lines) — HTTP handlers
               models.py       (314 lines) — DB queries + business logic
               database.py     (86 lines)  — connection + DDL + seed data
               requirements.txt (2 lines)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   5 analyzed | ~780 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] C1 — SQL Injection
File: models.py:28, 47-50, 57-62, 66-68, 92, 109-110, 126-130, 140, 148-153, 155-166, 174, 188-189, 192-193, 220-221, 224-225, 279-281, 289-295
Description: Every single SQL statement in models.py is built by string concatenation,
  never by parameterized queries. Affected functions and representative lines:
  - `get_produto_por_id` (line 28): `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))`
  - `criar_produto` (lines 47-50): `"INSERT INTO produtos ... VALUES ('" + nome + "', '" + descricao + "', " + str(preco) + ...)`
  - `atualizar_produto` (lines 57-62): `"UPDATE produtos SET nome = '" + nome + "', descricao = '" + descricao + "' ..."`
  - `deletar_produto` (line 68): `"DELETE FROM produtos WHERE id = " + str(id)`
  - `get_usuario_por_id` (line 92): `"SELECT * FROM usuarios WHERE id = " + str(id)`
  - `login_usuario` (lines 109-110): `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`
  - `criar_usuario` (lines 126-130): `"INSERT INTO usuarios ... VALUES ('" + nome + "', '" + email + "', '" + senha + "' ...)"`
  - `criar_pedido` (lines 140, 148-166): multiple concatenated SELECT/INSERT/UPDATE in loop
  - `get_pedidos_usuario` (lines 174, 188-189, 192-193): three nested cursor queries by string concat
  - `get_todos_pedidos` (lines 220-225): same nested pattern
  - `atualizar_status_pedido` (lines 279-281): `"UPDATE pedidos SET status = '" + novo_status + "' WHERE id = " + str(pedido_id)`
  - `buscar_produtos` (lines 289-295): dynamic query built with `query += " AND (nome LIKE '%" + termo + "%' ...)"`
Impact: Any user input (URL params, JSON body, query strings) can inject arbitrary SQL.
  `login_usuario` is trivially bypassed with `' OR '1'='1`. `buscar_produtos` allows
  full data exfiltration. `criar_produto` with a crafted `nome` can DROP tables.
Recommendation: Replace all concatenated queries with parameterized queries using
  `?` placeholders — e.g., `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`.

---

### [CRITICAL] C2 — Hardcoded Credentials
File: app.py:7, database.py:75-83
Description: Two hardcoded credential sites:
  1. `app.py` line 7: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` — Flask
     secret key is a string literal in source, committed to git.
  2. `database.py` lines 75-83: seed data inserts plaintext admin credentials directly:
     `("Admin", "admin@loja.com", "admin123", "admin")`,
     `("João Silva", "joao@email.com", "123456", "cliente")`,
     `("Maria Santos", "maria@email.com", "senha123", "cliente")`
Impact: SECRET_KEY exposure breaks Flask session security. Plaintext seed passwords
  in version history mean they are permanently compromised — even after rotation.
Recommendation: Load `SECRET_KEY` from environment variable via `os.environ.get("SECRET_KEY")`.
  Remove hardcoded passwords from seed data; use hashed passwords or a separate seed script.

---

### [CRITICAL] C3 — Unauthenticated Dangerous Endpoints
File: app.py:47-57, app.py:59-78
Description: Two admin endpoints with zero authentication:
  1. `POST /admin/reset-db` (lines 47-57): executes `DELETE FROM itens_pedido`,
     `DELETE FROM pedidos`, `DELETE FROM produtos`, `DELETE FROM usuarios` with no auth check whatsoever.
  2. `POST /admin/query` (lines 59-78): takes a `"sql"` field from the request JSON
     and passes it directly to `cursor.execute(query)`. Any HTTP client can run
     arbitrary SQL — `DROP TABLE`, `UPDATE usuarios SET tipo='admin'`, anything.
Impact: Any unauthenticated caller can wipe the entire database or exfiltrate/manipulate
  all data. This is a remote code execution vector via SQLite extension loading.
Recommendation: Either remove these endpoints entirely or protect them with a strong
  admin authentication decorator. The `/admin/query` endpoint should be deleted — there
  is no legitimate production use case for a public arbitrary-SQL endpoint.

---

### [CRITICAL] C4 — God File (Multi-Domain Model Module)
File: models.py:1-314
Description: `models.py` is a 314-line flat module covering four unrelated business
  domains with 15 functions: produto queries (`get_todos_produtos`, `get_produto_por_id`,
  `criar_produto`, `atualizar_produto`, `deletar_produto`, `buscar_produtos`), usuario
  queries (`get_todos_usuarios`, `get_usuario_por_id`, `login_usuario`, `criar_usuario`),
  pedido queries (`criar_pedido`, `get_pedidos_usuario`, `get_todos_pedidos`,
  `atualizar_status_pedido`), and report generation (`relatorio_vendas`). Beyond data
  access, it also contains business logic: stock management, order total calculation,
  and discount tier computation — violating single responsibility at every level.
Impact: Any change to the product domain risks breaking order logic. The file cannot
  be tested, deployed, or replaced by domain. New developers have no clear mental model
  of what belongs where.
Recommendation: Split into domain-scoped modules: `models/produto.py`,
  `models/usuario.py`, `models/pedido.py`; move business rules to a `services/` layer.

---

### [HIGH] H1 — Weak Cryptography / Broken Authentication
File: models.py:109-120, models.py:122-131, database.py:75-83
Description: Passwords are stored and compared as plaintext throughout:
  - `criar_usuario` (lines 122-131) inserts `senha` directly — no hashing applied.
  - `login_usuario` (lines 109-120) authenticates by plain string match in SQL.
  - Seed data in `database.py` (lines 75-83) confirms plaintext storage: `"admin123"`, `"123456"`, `"senha123"`.
  - Login endpoint issues no JWT or session token — no authenticated session exists.
Impact: A single DB read gives all user passwords in plaintext.
Recommendation: Hash passwords with `werkzeug.security.generate_password_hash`
  on creation; verify with `check_password_hash` on login. Issue a JWT on successful login.

---

### [HIGH] H2 — Sensitive Data Exposed in Responses and Logs
File: controllers.py:276-292, models.py:79-87, models.py:93-103
Description: Three sensitive data leaks:
  1. `health_check` (controllers.py lines 276-292) returns in its JSON response:
     `"secret_key": "minha-chave-super-secreta-123"`, `"db_path": "loja.db"`, `"debug": True`.
  2. `get_todos_usuarios` (models.py lines 79-87) includes `"senha": row["senha"]`
     in every returned user object, sending plaintext passwords to any caller of `GET /usuarios`.
  3. `get_usuario_por_id` (models.py lines 93-103) also returns `"senha": row["senha"]`.
Impact: SECRET_KEY exposure breaks session signing. Password exposure means any call to
  `/usuarios` dumps all plaintext credentials to the caller.
Recommendation: Remove `senha` from all user serializers. Remove `secret_key`, `db_path`,
  and `debug` from the health endpoint response.

---

### [HIGH] H3 — N+1 Query Problem
File: models.py:171-200, models.py:203-232
Description: Both `get_pedidos_usuario` and `get_todos_pedidos` implement a three-level
  nested query pattern using three separate cursors per call:
  - Outer loop: SELECT pedidos → N rows
  - Per pedido: SELECT itens_pedido → N×M queries
  - Per item: SELECT nome FROM produtos → N×M×K queries
  For 10 orders with 3 items each: 1 + 10 + 30 = 41 queries.
  For 100 orders with 5 items each: 1 + 100 + 500 = 601 queries.
Impact: Response time grows O(N×M) with data volume. Timeouts and DB lock contention at scale.
Recommendation: Replace with a single JOIN query across pedidos, itens_pedido, and produtos,
  then aggregate results in Python.

---

### [HIGH] H4 — Missing Cascade / Orphaned Data on Delete
File: models.py:65-70, database.py:14-54
Description: `deletar_produto` executes only `DELETE FROM produtos WHERE id = ?` with no
  deletion of related `itens_pedido` records. No `ON DELETE` constraint defined in schema.
  The defensive `prod["nome"] if prod else "Desconhecido"` in `get_pedidos_usuario` proves
  this bug is known and worked around rather than fixed.
Impact: Data integrity violations, historical order records become corrupted.
Recommendation: Add `ON DELETE RESTRICT` (prevent deletion of products in orders)
  or handle cascading deletion explicitly in a transaction.

---

### [HIGH] H5 — Business Logic in Wrong Layer
File: models.py:133-169, models.py:235-273, controllers.py:208-210, controllers.py:247-250
Description: Business rules scattered across model and controller layers:
  1. `criar_pedido` in models.py (lines 133-169): stock checks, total calculation, stock decrement.
  2. `relatorio_vendas` in models.py (lines 235-273): discount tier logic with magic constants.
  3. `criar_pedido` in controllers.py (lines 208-210): inline notification simulation via print.
  4. `atualizar_status_pedido` in controllers.py (lines 247-250): business notifications inline.
Impact: Logic can't be tested in isolation or reused across contexts.
Recommendation: Extract `services/pedido_service.py` and `services/relatorio_service.py`.

---

### [MEDIUM] M1 — Code Duplication (DRY Violation)
File: controllers.py:28-55, controllers.py:64-96, models.py:12-21, models.py:30-40, models.py:302-310
Description: Identical validation blocks in `criar_produto` and `atualizar_produto` (8 lines
  copy-pasted). The produto row-to-dict mapping is repeated in 3 separate functions.
Impact: New field on `produtos` table must be added in 3 mapper sites and 2 validation blocks.
Recommendation: Extract `_validate_produto_payload(dados)` and `_row_to_produto(row)` helpers.

---

### [MEDIUM] M2 — Missing Input Validation
File: controllers.py:146-165, controllers.py:237-254, models.py:133-169
Description: No email format validation in `criar_usuario`. `atualizar_status_pedido` calls
  `dados.get("status")` without null-checking `dados` first. `criar_pedido` never validates
  that `usuario_id` references an existing user.
Impact: Invalid emails persisted. NULL-body requests return 500 instead of 400. Ghost user references.
Recommendation: Add email regex, None guard for request body, and user existence check.

---

### [MEDIUM] M3 — Mutable Global State
File: database.py:4, database.py:7-10
Description: Module-level `db_connection = None` mutated by `get_db()` via `global` statement.
  Single `sqlite3.Connection` shared across all concurrent requests without locking.
Impact: Race conditions under concurrent load; `check_same_thread=False` suppresses the guard
  but not the actual race condition.
Recommendation: Use Flask's `g` object for per-request connections or SQLAlchemy with pooling.

---

### [MEDIUM] M4 — Inadequate Error Handling
File: controllers.py:10-12, controllers.py:60-62, models.py:133-169
Description: All catch blocks return `str(e)` directly to clients, leaking internal DB error
  messages. `criar_pedido` performs multiple INSERTs/UPDATEs with no transaction rollback on
  failure. `atualizar_status_pedido` may receive None body without protection.
Impact: Internal schema information exposed. Partial order creation on failure leaves corrupt data.
Recommendation: Return generic error messages; wrap mutations in explicit transactions with rollback.

---

### [LOW] L1 — Deprecated APIs
None found.

---

### [LOW] L2 — Debug Mode in Production
File: app.py:8, app.py:88, controllers.py:289
Description: `DEBUG = True` hardcoded in app config and `app.run()`. Also returned in the
  `/health` JSON response advertising debug status publicly.
Impact: Werkzeug interactive debugger provides a Python REPL on unhandled exceptions.
Recommendation: `app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "0") == "1"`.

---

### [LOW] L3 — Print Instead of Logger
File: controllers.py:8, 11, 57, 106, 161, 179-182, 208-210, 219, 247-250; app.py:56, 82-86
Description: 15+ `print()` statements used as logging throughout. No `import logging` anywhere.
Impact: No log levels, no timestamps, no structured output, no alerting integration.
Recommendation: Replace with `import logging; logger = logging.getLogger(__name__)`.

---

### [LOW] L4 — Magic Values
File: models.py:256-262
Description: Discount tier logic uses four magic numeric constants with no named variables:
  `if faturamento > 10000`, `elif faturamento > 5000`, `elif faturamento > 1000`,
  with multipliers `0.1`, `0.05`, `0.02`. Business meaning is entirely implicit.
Impact: Discount thresholds cannot be configured without reading implementation code.
Recommendation: Define named constants: `DISCOUNT_TIER_HIGH = 10000`, `DISCOUNT_RATE_HIGH = 0.10`.

================================
Total: 16 findings
CRITICAL: 4 | HIGH: 5 | MEDIUM: 4 | LOW: 3
================================
