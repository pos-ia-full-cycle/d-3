# Architecture Audit Report

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.18.2
Files:   3 analyzed | ~179 lines of code

## Summary
CRITICAL: 3 | HIGH: 5 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] C2 — Hardcoded Credentials
File: src/utils.js:1-7
Description: The `config` object hardcodes four production secrets as literals:
  `dbUser: "admin_master"` (line 2),
  `dbPass: "senha_super_secreta_prod_123"` (line 3),
  `paymentGatewayKey: "pk_live_1234567890abcdef"` (line 4),
  `smtpUser: "no-reply@fullcycle.com.br"` (line 5).
  The live payment gateway key `pk_live_1234567890abcdef` is also exported and
  referenced in `AppManager.js:45` where it is printed to stdout.
Impact: Any developer with git access or log access holds live credentials. The payment
  gateway key can be used to process fraudulent transactions. Rotating the key requires
  a code change and redeployment.
Recommendation: Move all secrets to environment variables and read them via `process.env`.
  Use a `.env` file + `dotenv` for local development; never commit credentials.

### [CRITICAL] C3 — Unauthenticated Dangerous Endpoints
File: src/AppManager.js:80-129, 131-137
Description: Both `/api/admin/financial-report` (GET, line 80) and `/api/users/:id`
  (DELETE, line 131) have zero authentication or authorization guards. Any anonymous
  HTTP client can retrieve the full revenue report or delete any user by ID.
  The DELETE handler even acknowledges its own damage in the response string:
  `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` (line 135).
Impact: Anyone on the internet can enumerate all users and revenue data, or
  mass-delete users with a simple loop over sequential IDs.
Recommendation: Add authentication middleware (JWT or session) to all `/api/admin/*`
  routes and require an admin role check before executing destructive operations.

### [CRITICAL] C4 — God Class
File: src/AppManager.js:1-141
Description: The single `AppManager` class concentrates seven unrelated responsibilities:
  (1) database connection (`constructor`, line 7),
  (2) schema creation and seed data (`initDb`, lines 10-23),
  (3) HTTP route registration (`setupRoutes`, line 25),
  (4) checkout flow with payment processing (lines 28-78),
  (5) financial report generation (lines 80-129),
  (6) user deletion (lines 131-137),
  (7) audit logging (line 57).
  The method `setupRoutes` alone is 113 lines of mixed DB queries, business logic,
  and HTTP response handling.
Impact: Impossible to unit test any single responsibility in isolation. Any change
  to the checkout flow risks breaking the report. Zero reusability of business logic.
Recommendation: Decompose into Model, Service, and Controller layers per MVC:
  UserModel, CourseModel, EnrollmentModel, PaymentModel for data access;
  CheckoutService, ReportService for business logic; route files for HTTP wiring.

### [HIGH] H1 — Weak Cryptography / Broken Auth
File: src/utils.js:17-23, src/AppManager.js:18, 68
Description: The `badCrypto` function (utils.js:17-23) implements a homemade "hash"
  by base64-encoding the password in a loop 10,000 times and taking the first 10 chars:
  `Buffer.from(pwd).toString('base64').substring(0,2)` repeated to produce a 10-char string.
  This is trivially reversible — there are only a handful of possible outputs per short password.
  The seed user has password stored in plaintext: `'123'` (AppManager.js:18).
  The checkout flow creates new users with `badCrypto(p || "123456")` (line 68), defaulting
  to the literal `"123456"` if no password is provided. Furthermore, returning users are
  enrolled without any password verification — only email lookup (lines 40-74).
Impact: All stored passwords can be reversed instantly. Any attacker knowing a user's
  email can enroll in courses with no password check.
Recommendation: Use `bcrypt` (`bcryptjs` package) with a minimum cost factor of 12 for
  password hashing. Add password verification on returning-user login flow.

### [HIGH] H2 — Sensitive Data Exposed in Logs
File: src/AppManager.js:45
Description: The checkout handler logs the raw credit card number and the live payment
  gateway API key to stdout in a single `console.log`:
  `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`
  where `cc` is the raw card number from `req.body.card` and `config.paymentGatewayKey`
  is `"pk_live_1234567890abcdef"`.
Impact: Every checkout attempt writes full card data and the live API key to process
  stdout and any downstream log aggregator (CloudWatch, Datadog, Splunk).
  This is a PCI-DSS violation.
Recommendation: Remove this log line entirely. Never log card data. If payment events
  must be logged, log only the last 4 digits of the card and mask the API key.

### [HIGH] H3 — N+1 Query Problem
File: src/AppManager.js:83-128
Description: The `/api/admin/financial-report` handler executes cascading nested queries
  for every row returned by its parent query:
  1. `SELECT * FROM courses` (line 83) — 1 query
  2. For each course: `SELECT * FROM enrollments WHERE course_id = ?` (line 92) — N queries
  3. For each enrollment: `SELECT name, email FROM users WHERE id = ?` (line 104) — N queries
  4. For each enrollment: `SELECT amount, status FROM payments WHERE enrollment_id = ?` (line 106) — N queries
  With 2 courses and 1 enrollment each, this is already 7 queries. With 100 courses
  averaging 50 students, this becomes 10,001 queries per report request.
Impact: Report response time degrades as O(courses × enrollments). Under load, this
  can saturate the DB connection and time out.
Recommendation: Rewrite using a single JOIN query:
  `SELECT c.title, u.name, p.amount, p.status FROM courses c
   LEFT JOIN enrollments e ON e.course_id = c.id
   LEFT JOIN users u ON u.id = e.user_id
   LEFT JOIN payments p ON p.enrollment_id = e.id`
  Then aggregate in JavaScript.

### [HIGH] H4 — Missing Cascade / Orphaned Data
File: src/AppManager.js:12-16, 131-137
Description: The `CREATE TABLE` statements (lines 12-16) define no `FOREIGN KEY` constraints
  and no `ON DELETE CASCADE` clauses. The DELETE handler at line 132-136 deletes a user
  with `DELETE FROM users WHERE id = ?` but leaves all related `enrollments` and `payments`
  rows intact. The response message itself documents the bug:
  `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` (line 135).
Impact: Deleted users leave ghost enrollment and payment records referencing a non-existent
  `user_id`. Reports count ghost revenue; re-used IDs cause data collisions.
Recommendation: Add `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE`
  to enrollments, and cascade from enrollments to payments. Enable foreign keys in SQLite
  with `PRAGMA foreign_keys = ON`. Wrap multi-table deletes in a transaction.

### [HIGH] H5 — Business Logic in Wrong Layer
File: src/AppManager.js:28-138
Description: All business logic lives inside anonymous route callback functions inside
  `setupRoutes`. The checkout flow (lines 28-78) performs: user lookup, user creation,
  payment gateway call, enrollment insert, payment insert, and audit log insert — all
  directly in the route handler. The `processPaymentAndEnroll` inner function (line 43)
  is declared inside the request callback, making it untestable and unreachable from
  anywhere else.
Impact: Payment and enrollment logic cannot be unit tested, cannot be reused by
  other endpoints, and cannot be replaced (e.g., swapping payment gateway) without
  modifying the HTTP handler.
Recommendation: Extract `CheckoutService.process(userId, courseId, card)` and
  `ReportService.getFinancialReport()` as standalone service classes. Controllers
  should only call services and send HTTP responses.

### [MEDIUM] M2 — Missing Input Validation
File: src/AppManager.js:35
Description: The checkout handler validates only presence of fields:
  `if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request")`
  There is no validation of: email format for `e`, integer type for `cid`, card number
  format/length for `cc`, or maximum length for name `u`. A request with
  `{ "c_id": "1 OR 1=1", "card": "x", "usr": "", "eml": "not-an-email" }` passes
  the guard (since all fields are truthy) and reaches the DB layer.
Impact: Invalid or malformed data enters the database.
Recommendation: Add a validation layer using `express-validator` or `joi`. Validate
  email format, `cid` as positive integer, card as numeric string of 13-19 digits,
  and name as non-empty string with max length.

### [MEDIUM] M3 — Mutable Global State
File: src/utils.js:9-10
Description: Two module-level mutable variables are exported and shared across all
  request handlers: `let globalCache = {}` (line 9) and `let totalRevenue = 0` (line 10).
  `globalCache` is written by `logAndCache` on every checkout (AppManager.js:59)
  with key `last_checkout_${userId}`. `totalRevenue` is exported but never updated anywhere.
Impact: Concurrent writes to `globalCache` via async DB callbacks have no synchronization.
  `totalRevenue` is dead state that misleads future developers.
Recommendation: Remove `totalRevenue` (dead variable). Replace `globalCache` with
  a proper cache abstraction. Do not export raw mutable state.

### [MEDIUM] M4 — Inadequate Error Handling
File: src/AppManager.js:50-57
Description: The checkout flow performs three sequential DB writes (INSERT enrollments,
  INSERT payments, INSERT audit_logs) with no wrapping transaction. If `INSERT INTO payments`
  fails (line 54), the enrollment row at line 50 remains committed — orphaned enrollment
  with no payment. Audit_log INSERT errors at line 57 are silently ignored
  (`(err) => {` with no error check). The financial report silently swallows
  errors on user and payment lookups at lines 104-106.
Impact: A failed payment leaves a phantom enrollment. Unchecked errors in the report
  handler silently omit data without alerting operators.
Recommendation: Wrap the checkout sequence in a SQLite transaction (`BEGIN`/`COMMIT`/`ROLLBACK`).
  Check and propagate all DB errors. Use centralized error-handling middleware.

### [LOW] L3 — Print Instead of Logger
File: src/app.js:13, src/AppManager.js:45, src/utils.js:13
Description: The project uses `console.log` as its only logging mechanism in three locations:
  `console.log(\`Frankenstein LMS rodando na porta ${config.port}...\`)` (app.js:13),
  `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` (AppManager.js:45),
  `console.log(\`[LOG] Salvando no cache: ${key}\`)` (utils.js:13).
  No structured logger is present.
Impact: No log levels, no timestamps, no JSON output for log aggregators.
Recommendation: Replace with `winston` or `pino`. Configure log level via `LOG_LEVEL`
  environment variable.

### [LOW] L4 — Poor Naming / Magic Values
File: src/AppManager.js:29-34, 46
Description: The checkout handler uses five single-letter or cryptic variable names:
  `u` (user name, line 29), `e` (email, line 30), `p` (password, line 31),
  `cid` (course ID, line 32), `cc` (credit card, line 33).
  Line 46 uses the magic value `cc.startsWith("4")` to determine if payment is approved,
  with no named constant or comment explaining the Visa-prefix simulation rule.
Impact: Code is unreadable without decoding intent. Hidden business rule blocks future changes.
Recommendation: Rename to descriptive names (`userName`, `email`, `password`,
  `courseId`, `cardNumber`). Extract `const APPROVED_CARD_PREFIX = "4"` as a named constant.

================================
Total: 13 findings
================================
```
