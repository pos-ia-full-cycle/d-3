================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 + SQLAlchemy (via Flask-SQLAlchemy 3.1.1)
Files:   17 analyzed | ~969 lines of code

## Summary
CRITICAL: 2 | HIGH: 5 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] C2 — Hardcoded Credentials
File: app.py:13, services/notification_service.py:9-10
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` is a literal
  string committed to version control. Additionally, services/notification_service.py
  lines 9-10 hardcode SMTP credentials:
    `self.email_user = 'taskmanager@gmail.com'`
    `self.email_password = 'senha123'`
  Neither reads from environment variables.
Impact: Credentials committed to git are permanently exposed in history.
  The secret key is used for session/token signing — anyone with repo access
  can forge sessions. The SMTP password leaks a real Gmail account.
Recommendation: Load all secrets via `os.environ.get()` or `python-dotenv`.
  python-dotenv is already listed in requirements.txt — create a `.env` file
  and use `app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')` pattern.

### [CRITICAL] C3 — Unauthenticated Destructive Endpoints
File: routes/user_routes.py:134-151, routes/task_routes.py:225-238, routes/report_routes.py:211-222
Description: The DELETE endpoints for `/users/<id>`, `/tasks/<id>`, and
  `/categories/<id>` have zero authentication checks. `/login` at
  routes/user_routes.py:185 returns `'token': 'fake-jwt-token-' + str(user.id)`
  which is never validated by any middleware or decorator in any route.
  The `role` field on User exists (models/user.py:12) but is never enforced.
Impact: Any unauthenticated HTTP client can delete any user, task, or category.
  An attacker can also enumerate valid user IDs (1, 2, 3...) from the fake
  token to target specific accounts.
Recommendation: Implement real JWT authentication (e.g., `flask-jwt-extended`),
  add an `@require_auth` decorator, and apply it to all write endpoints.

### [HIGH] H1 — Weak Cryptography / Broken Auth
File: models/user.py:29, models/user.py:32, routes/user_routes.py:210
Description: Passwords are hashed using MD5:
  `self.password = hashlib.md5(pwd.encode()).hexdigest()` (line 29)
  `return self.password == hashlib.md5(pwd.encode()).hexdigest()` (line 32)
  Login at routes/user_routes.py:210 returns a predictable fake token:
  `'token': 'fake-jwt-token-' + str(user.id)` — trivially guessable for any
  known user ID. Seed passwords are also weak: '1234', 'abcd', 'pass' (seed.py:19-34).
Impact: MD5 hashes are broken in seconds with modern rainbow tables. The token
  scheme makes session hijacking trivial — token for user 1 is always
  'fake-jwt-token-1'.
Recommendation: Replace MD5 with `bcrypt` or `werkzeug.security.generate_password_hash`.
  Replace fake tokens with real JWT (`flask-jwt-extended`).

### [HIGH] H2 — Sensitive Data Exposed in API Responses
File: models/user.py:18-25, routes/user_routes.py:33-34, routes/user_routes.py:207-210
Description: `User.to_dict()` includes `'password': self.password` (line 22),
  which returns the MD5 hash. This is then exposed via:
  - `GET /users/<id>` → `user.to_dict()` at user_routes.py:33
  - `POST /login` → `user.to_dict()` inside the response at user_routes.py:208
  Every user fetch leaks the password hash to any API consumer.
Impact: Even though MD5 is weak, exposing hashes gives attackers a direct
  cracking target. Combined with H1 (MD5), hashes are crackable instantly.
Recommendation: Remove `'password'` key from `User.to_dict()`. Add a separate
  `to_public_dict()` method that excludes the password field.

### [HIGH] H3 — N+1 Query Problem
File: routes/task_routes.py:41-57, routes/report_routes.py:53-68, routes/user_routes.py:22
Description: Three separate N+1 patterns:
  1. `get_tasks()` (task_routes.py:41-57): For each task in the loop, fires
     `User.query.get(t.user_id)` (line 42) AND `Category.query.get(t.category_id)`
     (line 51) — 2N extra queries for N tasks.
  2. `summary_report()` (report_routes.py:53-68): For each user in the loop,
     fires `Task.query.filter_by(user_id=u.id).all()` (line 56).
  3. `get_users()` (user_routes.py:22): `len(u.tasks)` triggers lazy-load of
     all tasks for every user in the list.
Impact: With 100 tasks, `GET /tasks` fires 201+ queries. Performance degrades
  linearly with data size; the report endpoint is worse.
Recommendation: Use SQLAlchemy eager loading: add `joinedload` or `subqueryload`
  on the `Task.user` and `Task.category` relationships, and use aggregate
  queries (`func.count`) instead of loading full collections.

### [HIGH] H4 — Missing Cascade / Orphaned Data on Category Delete
File: routes/report_routes.py:211-222, models/task.py:14
Description: `delete_category()` (report_routes.py:211-222) calls
  `db.session.delete(cat)` without handling related tasks. The FK column
  `category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)`
  (task.py:14) has no `ondelete='SET NULL'` or `ondelete='CASCADE'` defined.
  SQLite silently ignores FK constraints by default, so the delete succeeds
  but leaves tasks with dangling `category_id` values pointing to deleted rows.
Impact: Tasks retain stale `category_id` references, causing misleading data
  and potential errors if FK enforcement is enabled (e.g., in PostgreSQL).
Recommendation: Add `ondelete='SET NULL'` to the FK definition and set
  `nullable=True` cascade behavior, OR add explicit nullification:
  `Task.query.filter_by(category_id=cat_id).update({'category_id': None})`
  before deleting the category.

### [HIGH] H5 — Business Logic in Wrong Layer (Fat Routes)
File: routes/task_routes.py:13-60, routes/report_routes.py:13-100, routes/report_routes.py:103-155
Description: Three large route functions contain complex business logic:
  1. `get_tasks()` (task_routes.py:13-60): Manually rebuilds the task dict
     (duplicating `Task.to_dict()`), runs overdue calculation inline, and
     fires N+1 queries — 48 lines of logic in a route handler.
  2. `summary_report()` (report_routes.py:13-100): Runs 10+ separate DB
     queries, an overdue detection loop, and a user productivity aggregation
     loop — 88 lines of report business logic in a route.
  3. `user_report()` (report_routes.py:103-155): Aggregates task statistics
     with a manual for-loop across statuses, priority counts, and overdue check.
  Additionally, category CRUD operations (`/categories`) are placed inside
  `report_routes.py` (lines 157-223) rather than in a dedicated routes file.
  `utils/helpers.py` defines `process_task_data()` (line 57) which is never
  called — routes reimplement the same validation inline.
Impact: Report logic cannot be tested without an HTTP request; the category
  routes are semantically misplaced; changing business rules requires editing
  multiple route files.
Recommendation: Extract report logic to a `ReportService`, task validation
  to a `TaskService`, and move category routes to `routes/category_routes.py`.

### [MEDIUM] M1 — Code Duplication (DRY Violation)
File: routes/task_routes.py:30-39, routes/task_routes.py:71-80,
      routes/task_routes.py:284-287, routes/user_routes.py:171-180,
      routes/report_routes.py:33-37, routes/report_routes.py:132-135
Description: The overdue detection block is copy-pasted 6 times across 3 files:
  ```
  if t.due_date:
      if t.due_date < datetime.utcnow():
          if t.status != 'done' and t.status != 'cancelled':
  ```
  `Task.is_overdue()` already exists at models/task.py:50 but is never called.

  Additional duplications:
  - Title length validation (3-200 chars) duplicated in `create_task()` lines
    96-100 and `update_task()` lines 167-170.
  - Status enum check duplicated in `create_task()` line 110 and `update_task()`
    line 177.
  - Email regex `r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'` duplicated at
    user_routes.py:61 and user_routes.py:106; `validate_email()` exists in
    utils/helpers.py:19 but is never imported.
Impact: Any fix (e.g., adding a new terminal status) must be applied in 6+
  places; current inconsistencies are already present (user_tasks doesn't
  include category_name but tasks endpoint does).
Recommendation: Replace all overdue blocks with `task.is_overdue()`. Replace
  duplicate validations with the existing helpers in utils/helpers.py.

### [MEDIUM] M2 — Missing Input Validation / Sanitization
File: routes/report_routes.py:196-208, routes/report_routes.py:167-188,
      utils/helpers.py:52-55
Description: Three gaps:
  1. `update_category()` (report_routes.py:196) does not check if `data` is
     None before accessing `data['name']`, `data['description']`, `data['color']`
     — unlike all other PUT handlers which check `if not data`.
  2. `create_category()` (report_routes.py:178) and `update_category()` accept
     any string for `color`, but `is_valid_color()` exists at utils/helpers.py:52
     and is never called.
  3. Password minimum length is only 4 characters (user_routes.py:64, line 115)
     — industry standard is 8+.
Impact: Malformed JSON to `PUT /categories/<id>` causes an unhandled 500 error.
  Invalid hex colors are stored without validation.
Recommendation: Add the `if not data` guard to `update_category()`, call
  `is_valid_color()` on color inputs, and raise the password minimum to 8.

### [MEDIUM] M4 — Inadequate Error Handling (Bare except)
File: routes/task_routes.py:62, routes/task_routes.py:138, routes/task_routes.py:222,
      routes/task_routes.py:236, routes/user_routes.py:131, routes/user_routes.py:150,
      routes/report_routes.py:184-188, routes/report_routes.py:205-208,
      routes/report_routes.py:218-222, utils/helpers.py:47-50
Description: 10 bare `except:` or `except Exception` clauses that swallow all
  errors silently. Example from task_routes.py:62:
  ```python
  except:
      return jsonify({'error': 'Erro interno'}), 500
  ```
  The actual exception is lost. utils/helpers.py:47-50 uses bare `except:` in
  `parse_date()`, masking invalid date format errors.
  `get_tasks()` (task_routes.py:62) wraps the entire function in a try/except
  including the DB queries, hiding connection errors.
Impact: Root causes are invisible in logs; DB connection failures and data
  integrity errors are indistinguishable. No rollback is triggered in the
  `update_user` bare except (user_routes.py:131).
Recommendation: Catch specific exceptions (`ValueError`, `IntegrityError`,
  `SQLAlchemyError`), log the error with `logging.exception()`, and never
  swallow exceptions silently.

### [LOW] L1 — Deprecated APIs
File: models/user.py:14, models/task.py:15-16, models/category.py:11,
      routes/task_routes.py:31,42,51,67,117,122,159,188,215,285,
      routes/user_routes.py:29,94,155, routes/report_routes.py:105,193,213
Description: Two categories of deprecated APIs:
  1. `datetime.utcnow()` — deprecated since Python 3.12 and used in model
     column defaults (`default=datetime.utcnow` in user.py:14, task.py:15-16,
     category.py:11) and called directly in 8+ route functions.
  2. `Model.query.get(id)` — deprecated in SQLAlchemy 2.0, used 10+ times
     across all route files (e.g., `Task.query.get(task_id)` at task_routes.py:67,
     `User.query.get(user_id)` at user_routes.py:29, etc.).
Impact: Deprecation warnings in logs; both APIs will be removed in future
  minor/major versions causing breaking changes.
Recommendation: Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`.
  Replace `Model.query.get(id)` with `db.session.get(Model, id)`.

### [LOW] L2 — Debug Mode Hardcoded
File: app.py:34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` — `debug=True`
  is a literal, not read from an environment variable.
Impact: If this code runs in production, Werkzeug's interactive debugger is
  exposed on `0.0.0.0`, allowing arbitrary Python code execution in-browser
  when an exception occurs.
Recommendation: `app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')`

### [LOW] L3 — print() Instead of Logger
File: routes/task_routes.py:149,153,219,233, routes/user_routes.py:83,89,147,
      services/notification_service.py:21,24, utils/helpers.py:38-41
Description: 10 `print()` calls used for operational logging across route and
  service files. Examples: `print(f"Task criada: {task.id} - {task.title}")`,
  `print(f"ERRO: {str(e)}")`. `utils/helpers.py` even defines `log_action()`
  using `print()` internally (lines 36-41). No `import logging` or
  `logging.getLogger(__name__)` exists in any source file.
Impact: No log levels (DEBUG/INFO/WARNING/ERROR), no timestamps, no structured
  output — makes production debugging impossible and prevents log routing.
Recommendation: Add `import logging; logger = logging.getLogger(__name__)` to
  each module and replace all `print()` calls with `logger.info()` / `logger.error()`.

================================
Total: 13 findings
================================
