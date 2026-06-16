# Project Analysis — Heuristics

Use these heuristics to detect the project's stack and architecture in Phase 1.

---

## Language Detection

| Signal | Language |
|---|---|
| `requirements.txt` or `*.py` files present | Python |
| `package.json` or `*.js`/`*.ts` files present | Node.js/JavaScript |
| `go.mod` present | Go |
| `pom.xml` or `build.gradle` present | Java/Kotlin |
| `Gemfile` present | Ruby |

If both Python and Node.js signals exist, check which has the entry point (`app.py` vs `app.js`/`index.js`/`server.js`).

---

## Framework Detection

### Python
Scan `requirements.txt` or `pyproject.toml`:
- `flask` or `Flask` → **Flask**
- `django` → **Django**
- `fastapi` → **FastAPI**
- `tornado` → **Tornado**

Also check imports in `.py` files: `from flask import`, `import django`, etc.

### Node.js
Scan `package.json` `dependencies`:
- `express` → **Express**
- `fastify` → **Fastify**
- `@nestjs/core` → **NestJS**
- `koa` → **Koa**
- `hapi` → **Hapi**

### Version Detection
- Python/Flask: look for `Flask==X.Y.Z` in requirements.txt
- Node.js: look for `"express": "^X.Y.Z"` in package.json

---

## Database Detection

| Import / Dependency | Database |
|---|---|
| `sqlite3`, `sqlite3.connect`, `Database(':memory:')` | SQLite |
| `flask_sqlalchemy`, `SQLAlchemy`, `from database import db` | SQLAlchemy ORM |
| `psycopg2`, `asyncpg` | PostgreSQL |
| `pymysql`, `mysql-connector` | MySQL |
| `mongoose`, `mongodb` | MongoDB |
| `sequelize` | Sequelize ORM (SQL) |
| `prisma` | Prisma ORM |
| `typeorm` | TypeORM |

Scan for `CREATE TABLE`, `db.Model`, `Schema(`, `model(` to identify entities/tables.

---

## Architecture Mapping

### Identify Existing Layers
Check for directories and file names:
- `models/` or `model.py` / `models.py` → has model layer
- `controllers/` or `controllers.py` → has controller layer
- `routes/` or `routes.py` → has routes layer
- `services/` or `services.py` → has service layer
- `views/` → has view layer (templates or route handlers)
- `middlewares/` or `middleware.js` → has middleware layer
- `config/` or `config.py` / `settings.py` → has config layer

### Architecture Patterns to Identify

**Monolith (everything in 1-2 files):**
- All routes, DB queries, business logic in one file (e.g., `app.py`)
- Signal: file > 200 lines with mixed concerns

**Partial MVC (some separation, but incomplete):**
- Has `models/` but routes contain business logic
- Has `routes/` but models do DB queries AND business rules
- Controllers directly access DB without models

**God Class:**
- Single class with `setupRoutes`, `initDb`, `processPayment`, `generateReport` all together
- Single file with 300+ lines covering multiple domains

**Flat structure (no directories):**
- All `.py` or `.js` files at root level
- No `src/` or domain-specific subdirectories

---

## Domain Identification

Read these signals to describe the business domain:
- Route paths: `/produtos`, `/pedidos`, `/usuarios` → E-commerce
- Route paths: `/tasks`, `/users`, `/categories` → Task Manager
- Route paths: `/courses`, `/enrollments`, `/checkout` → LMS/Education
- Model/class names in source files
- Any `README.md` present in the project root
- Database table names from CREATE TABLE or ORM models

---

## File Count

Count all source files (exclude: `node_modules/`, `.git/`, `__pycache__/`, `*.pyc`, `*.db`, `venv/`):
- List each file with its relative path
- Note approximate line count for large files (> 100 lines)
- Report total: "N files analyzed, ~M lines of code"
