# Anti-Patterns Catalog

Use this catalog in Phase 2 to scan the project for each anti-pattern. For every match found, record the exact file and line number.

Severity scale:
- **CRITICAL**: Security breach or complete architectural failure
- **HIGH**: Serious MVC/SOLID violation that prevents maintainability or testability
- **MEDIUM**: Duplication, performance issue, or misplaced responsibility
- **LOW**: Readability, naming, or minor quality issue

---

## CRITICAL Anti-Patterns

### C1 — SQL Injection
**Detection signals:**
- String concatenation in SQL queries: `"SELECT * FROM t WHERE id = " + str(id)`
- f-string in SQL: `f"SELECT * FROM users WHERE email = '{email}'"`
- Template formatting: `"INSERT INTO t VALUES ('%s')" % value` (with `%` not `?`)
- User input directly embedded in query strings

**Python pattern to look for:**
```python
cursor.execute("SELECT ... WHERE col = " + variable)
cursor.execute("INSERT INTO ... VALUES ('" + nome + "', ...)")
query += " AND nome LIKE '%" + termo + "%'"
```

**Node.js pattern to look for:**
```js
db.run("DELETE FROM users WHERE id = " + id)  # parameterized would use ?
```

**Impact:** Attacker can read/modify/delete any data, bypass authentication, execute OS commands.

---

### C2 — Hardcoded Credentials
**Detection signals:**
- `SECRET_KEY = "some-literal-string"` in app config
- `password = "literal"` or `pass = "literal"` in source code
- `API_KEY = "pk_live_..."` or `paymentGatewayKey: "pk_live_..."` in config objects
- SMTP/email passwords: `email_password = 'senha123'`
- Database passwords: `dbPass: "senha_super_secreta_prod_123"`
- Connection strings with embedded credentials

**Impact:** Credentials committed to git are permanently exposed. Live API keys can be used maliciously.

---

### C3 — Unauthenticated Dangerous Endpoint
**Detection signals:**
- Route that executes arbitrary SQL sent by client: `cursor.execute(dados.get("sql"))`
- Route that resets/deletes all data without auth check: `DELETE FROM table` in open route
- Admin routes with no authentication middleware or token check
- Route handler with no `@require_auth` or `if not token` guard

**Impact:** Anyone with network access can destroy data or execute arbitrary code.

---

### C4 — God Class / God File
**Detection signals:**
- Single class with 5+ unrelated responsibilities: `initDb`, `setupRoutes`, `processPayment`, `generateReport`, `sendEmail`
- Single file > 300 lines mixing: route definitions + DB queries + business logic + data formatting
- One module covering multiple business domains (users + products + orders + reports all in one file)

**Impact:** Impossible to test in isolation, any change risks breaking everything, zero reusability.

---

## HIGH Anti-Patterns

### H1 — Weak Cryptography / Broken Auth
**Detection signals:**
- `import hashlib` followed by `hashlib.md5(pwd.encode()).hexdigest()` for password hashing
- Custom "crypto" functions using base64, XOR, or simple string manipulation
- Passwords stored as plaintext in DB seed data: `("admin", "admin@x.com", "admin123", "admin")`
- Login by comparing plaintext: `WHERE email = ? AND senha = ?` with unhashed input
- Fake token generation: `'token': 'fake-jwt-token-' + str(user.id)`

**Impact:** Passwords cracked instantly with rainbow tables. Sessions hijackable.

---

### H2 — Sensitive Data Exposed in Logs or Responses
**Detection signals:**
- Credit card number logged: `console.log(\`Processando cartão ${cc}...\`)`
- API key logged: `console.log(\`chave ${config.paymentGatewayKey}\`)`
- Password hash returned in API response: `to_dict()` includes `'password': self.password`
- Secret key exposed via endpoint: `"secret_key": "minha-chave-super-secreta-123"` in JSON response
- PII (emails, CPFs) in unprotected log output

**Impact:** Sensitive data leaked to log aggregators, monitoring systems, or API consumers.

---

### H3 — N+1 Query Problem
**Detection signals:**
- SQL query inside a `for` loop that iterates over rows from a previous query
- Pattern: `cursor.execute("SELECT * FROM parent")` then `for row in rows: cursor.execute("SELECT * FROM child WHERE parent_id = " + str(row["id"]))`
- ORM lazy loading in loop: `for task in tasks: user = User.query.get(task.user_id)`
- Nested callbacks each firing a new DB query (Node.js callback hell pattern)

**Impact:** Performance degrades O(N) with data size. 100 orders = 300+ queries.

---

### H4 — Missing Cascade / Orphaned Data
**Detection signals:**
- DELETE on a parent entity without deleting or nullifying child records
- No `ON DELETE CASCADE` in foreign key definitions
- Code comment acknowledging the bug: "matrículas e pagamentos ficaram sujos"
- No transaction wrapping multi-step delete operations

**Impact:** Data integrity violations, foreign key constraint errors, ghost records.

---

### H5 — Business Logic in Wrong Layer (Massive Controller or Fat Model)
**Detection signals:**
- Complex discount calculation inside a `models.py` function (not in service or controller)
- Payment processing logic inside a route handler function
- Financial report generation (multiple queries + transformations) directly in a model
- Notification sending (email, SMS, push) triggered directly inside a controller function

**Impact:** Logic can't be reused, tested in isolation, or replaced without touching HTTP layer.

---

## MEDIUM Anti-Patterns

### M1 — Code Duplication (DRY Violation)
**Detection signals:**
- Identical overdue calculation block copied into 3+ route functions
- Same validation logic (title length, status enum check) duplicated across create and update handlers
- Same SQL query fragment repeated in multiple functions without extraction
- Helper function exists but isn't used — routes reimplement the same logic

**Impact:** Bug fix must be applied in N places. Inconsistencies accumulate over time.

---

### M2 — Missing Input Validation / Sanitization
**Detection signals:**
- Route accepts user input and passes it directly to model/DB with no type or range check
- No validation of enum values (status, role, category) before persistence
- Missing required-field checks for POST endpoints
- No email format validation before insert

**Impact:** Bad data enters the database, causing downstream errors or security issues.

---

### M3 — Mutable Global State
**Detection signals:**
- Module-level mutable variables: `let globalCache = {}`, `let totalRevenue = 0`
- Global DB connection: `db_connection = None` at module level
- State modified across requests without synchronization

**Impact:** Race conditions in concurrent requests, unpredictable behavior, hard-to-reproduce bugs.

---

### M4 — Inadequate Error Handling
**Detection signals:**
- Bare `except:` or `except Exception` catching everything and swallowing the error
- Error details from internal exceptions returned directly to the client: `return jsonify({"erro": str(e)})`
- No rollback on failed DB transaction
- No `try/catch` around external service calls (SMTP, payment gateway)

**Impact:** Leaks internal stack traces to clients, masks root causes, leaves DB in inconsistent state.

---

## LOW Anti-Patterns

### L1 — Deprecated APIs
**Detection signals (Python):**
- `datetime.utcnow()` — deprecated since Python 3.12; use `datetime.now(timezone.utc)`
- `Query.get(id)` / `Model.query.get(id)` — deprecated in SQLAlchemy 2.0; use `db.session.get(Model, id)`
- `flask.escape()` — removed in Flask 2.x; use `markupsafe.escape()`
- `@app.before_first_request` — deprecated in Flask 2.3+; use `with app.app_context()`

**Detection signals (Node.js):**
- `require('crypto').createCipher()` — deprecated; use `createCipheriv()`
- `new Buffer()` — deprecated; use `Buffer.from()` or `Buffer.alloc()`
- `util.isArray()` — deprecated; use `Array.isArray()`

**Impact:** Deprecation warnings in logs, future breaking changes, security gaps in old crypto APIs.

---

### L2 — Debug Mode in Production
**Detection signals:**
- `app.config["DEBUG"] = True` hardcoded (not from env var)
- `app.run(debug=True)` as default, not conditional on environment
- `"debug": True` returned in a public API health endpoint response

**Impact:** Exposes stack traces to users, enables Werkzeug debugger (Python code execution in browser).

---

### L3 — Print Instead of Logger
**Detection signals:**
- `print("Listando " + str(len(produtos)) + " produtos")` in route handlers
- `print("ERRO: " + str(e))` instead of `logging.error()`
- `console.log(...)` as only logging mechanism in production Node.js code
- No `import logging` or `logger = logging.getLogger(__name__)` anywhere in project

**Impact:** No log levels, no timestamps, no structured output, no ability to control verbosity per environment.

---

### L4 — Poor Naming / Magic Values
**Detection signals:**
- Single-letter or cryptic variable names: `u`, `e`, `p`, `cid`, `cc` in route handlers
- Magic numbers without named constants: `if faturamento > 10000` with no named constant
- Generic function names: `process()`, `handle()`, `doStuff()`
- Boolean flags instead of enums: `active = 1` / `active = 0` without named constants

**Impact:** Code is unreadable, intent is unclear, maintenance requires reading implementation, not interface.
