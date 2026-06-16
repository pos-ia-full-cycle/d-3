# Refactoring Playbook

These are concrete transformation patterns for Phase 3. For each anti-pattern found in the audit, apply the matching playbook entry. Each entry has a BEFORE (broken code) and AFTER (corrected code).

---

## P1 — Fix SQL Injection: Use Parameterized Queries

**Applies to:** Anti-pattern C1

### BEFORE (Python — string concatenation)
```python
# UNSAFE: user input directly in query string
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("SELECT * FROM users WHERE email = '" + email + "' AND senha = '" + senha + "'")
cursor.execute("INSERT INTO produtos (nome, preco) VALUES ('" + nome + "', " + str(preco) + ")")
query = "SELECT * FROM produtos WHERE nome LIKE '%" + termo + "%'"
cursor.execute(query)
```

### AFTER (Python — parameterized with `?`)
```python
# SAFE: user input passed as separate tuple
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("SELECT * FROM users WHERE email = ? AND senha = ?", (email, senha))
cursor.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome, preco))
cursor.execute("SELECT * FROM produtos WHERE nome LIKE ?", (f"%{termo}%",))
```

### BEFORE (Node.js — string concatenation)
```javascript
db.run("DELETE FROM users WHERE id = " + id)
db.get("SELECT * FROM courses WHERE id = " + cid + " AND active = 1")
```

### AFTER (Node.js — parameterized with `?`)
```javascript
db.run("DELETE FROM users WHERE id = ?", [id])
db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [cid])
```

---

## P2 — Fix Hardcoded Credentials: Use Environment Variables

**Applies to:** Anti-pattern C2

### BEFORE (Python)
```python
# app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True

# notification_service.py
self.email_password = 'senha123'
self.email_user = 'taskmanager@gmail.com'
```

### AFTER (Python)
```python
# config/settings.py
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-in-prod")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    EMAIL_USER = os.environ.get("EMAIL_USER")
    EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
    PAYMENT_GATEWAY_KEY = os.environ.get("PAYMENT_GATEWAY_KEY")
```

```
# .env (not committed to git — add to .gitignore)
SECRET_KEY=a-real-random-secret-key
EMAIL_USER=app@example.com
EMAIL_PASSWORD=real-password-from-vault
```

### BEFORE (Node.js)
```javascript
// utils.js
const config = {
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
};
```

### AFTER (Node.js)
```javascript
// config/index.js
require('dotenv').config();

const config = {
    dbPass: process.env.DB_PASS,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    port: parseInt(process.env.PORT) || 3000,
};

module.exports = config;
```

---

## P3 — Fix God Class: Split into MVC Layers

**Applies to:** Anti-pattern C4

### BEFORE (Node.js — God Class)
```javascript
class AppManager {
    constructor() { this.db = new sqlite3.Database(':memory:'); }
    initDb() { /* creates tables, seeds data */ }
    setupRoutes(app) {
        app.post('/api/checkout', (req, res) => {
            // 50 lines: validates input, queries DB, processes payment,
            // creates enrollment, logs audit, sends response
        });
        app.get('/api/admin/financial-report', (req, res) => {
            // 40 lines: nested callbacks, N+1 queries, builds report
        });
    }
}
```

### AFTER (Node.js — split into layers)
```javascript
// models/CourseModel.js
class CourseModel {
    static async findById(db, id) {
        return new Promise((resolve, reject) => {
            db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [id], (err, row) => {
                if (err) reject(err); else resolve(row);
            });
        });
    }
}

// services/CheckoutService.js
class CheckoutService {
    static async processCheckout(db, { userId, courseId, cardNumber }) {
        const course = await CourseModel.findById(db, courseId);
        if (!course) throw new Error("Curso não encontrado");
        const status = cardNumber.startsWith("4") ? "PAID" : "DENIED";
        if (status === "DENIED") throw new Error("Pagamento recusado");
        const enrollmentId = await EnrollmentModel.create(db, userId, courseId);
        await PaymentModel.create(db, enrollmentId, course.price, status);
        return { enrollmentId };
    }
}

// controllers/checkoutController.js
async function checkout(req, res) {
    try {
        const result = await CheckoutService.processCheckout(db, req.body);
        res.status(200).json({ msg: "Sucesso", ...result });
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
}

// routes/checkoutRoutes.js
const router = express.Router();
router.post('/checkout', checkoutController.checkout);
module.exports = router;
```

---

## P4 — Fix Weak Cryptography: Use bcrypt

**Applies to:** Anti-pattern H1

### BEFORE (Python — MD5)
```python
import hashlib

def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()  # BROKEN

def check_password(self, pwd):
    return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

### AFTER (Python — werkzeug/bcrypt)
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

### BEFORE (Node.js — fake crypto)
```javascript
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

### AFTER (Node.js — bcrypt)
```javascript
const bcrypt = require('bcrypt');

async function hashPassword(pwd) {
    return bcrypt.hash(pwd, 12);
}

async function verifyPassword(pwd, hash) {
    return bcrypt.compare(pwd, hash);
}
```

---

## P5 — Fix N+1 Query: Use JOIN or Eager Loading

**Applies to:** Anti-pattern H3

### BEFORE (Python — N+1 with nested cursors)
```python
def get_pedidos_usuario(usuario_id):
    cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
    rows = cursor.fetchall()
    for row in rows:
        cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (row["id"],))
        for item in cursor2.fetchall():
            cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))
            # O(N*M) queries for N orders with M items each
```

### AFTER (Python — single JOIN query)
```python
def get_pedidos_com_itens(usuario_id):
    cursor.execute("""
        SELECT p.id, p.status, p.total, p.criado_em,
               ip.produto_id, ip.quantidade, ip.preco_unitario,
               pr.nome as produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
        WHERE p.usuario_id = ?
        ORDER BY p.id
    """, (usuario_id,))
    rows = cursor.fetchall()
    # Group in Python — 1 query total
    pedidos = {}
    for row in rows:
        pid = row["id"]
        if pid not in pedidos:
            pedidos[pid] = {"id": pid, "status": row["status"], "total": row["total"], "itens": []}
        if row["produto_id"]:
            pedidos[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"]
            })
    return list(pedidos.values())
```

### AFTER (SQLAlchemy ORM — eager loading)
```python
from sqlalchemy.orm import joinedload

tasks = Task.query.options(
    joinedload(Task.user),
    joinedload(Task.category)
).all()
# Single query with JOINs — no N+1
```

---

## P6 — Extract Business Logic to Service Layer

**Applies to:** Anti-pattern H5

### BEFORE (business logic in model)
```python
# models.py — discount calculation should not be here
def relatorio_vendas():
    cursor.execute("SELECT SUM(total) FROM pedidos")
    faturamento = cursor.fetchone()[0] or 0
    # Complex business rule inside a data layer function
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02
    else:
        desconto = 0
    return {"faturamento_bruto": faturamento, "desconto": desconto}
```

### AFTER (model fetches data, service applies rules)
```python
# models/order_model.py — data only
class OrderModel:
    @staticmethod
    def get_total_revenue():
        cursor.execute("SELECT SUM(total) FROM pedidos")
        return cursor.fetchone()[0] or 0

# services/report_service.py — business rules
DISCOUNT_TIERS = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]

class ReportService:
    @staticmethod
    def calculate_sales_report():
        faturamento = OrderModel.get_total_revenue()
        desconto = next(
            (faturamento * rate for threshold, rate in DISCOUNT_TIERS if faturamento > threshold),
            0
        )
        return {
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
        }
```

---

## P7 — Fix Code Duplication: Extract to Utility/Service

**Applies to:** Anti-pattern M1

### BEFORE (overdue logic duplicated in 4 places)
```python
# Copied verbatim in get_tasks(), get_task(), get_user_tasks(), task_stats()
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
        else:
            task_data['overdue'] = False
    else:
        task_data['overdue'] = False
else:
    task_data['overdue'] = False
```

### AFTER (single function, used everywhere)
```python
# models/task.py or utils/task_utils.py
def is_task_overdue(task) -> bool:
    if not task.due_date:
        return False
    if task.status in ('done', 'cancelled'):
        return False
    return task.due_date < datetime.now(timezone.utc).replace(tzinfo=None)

# Used in all routes:
task_data['overdue'] = is_task_overdue(t)
```

---

## P8 — Fix Deprecated APIs: Use Modern Equivalents

**Applies to:** Anti-pattern L1

### BEFORE (Python — deprecated datetime)
```python
from datetime import datetime

created_at = db.Column(db.DateTime, default=datetime.utcnow)  # deprecated in Python 3.12
task.due_date < datetime.utcnow()  # deprecated
```

### AFTER (Python — timezone-aware)
```python
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

created_at = db.Column(db.DateTime, default=utcnow)
task.due_date < utcnow()
```

### BEFORE (SQLAlchemy — deprecated Query.get)
```python
user = User.query.get(user_id)       # deprecated in SQLAlchemy 2.0
task = Task.query.get(task_id)
```

### AFTER (SQLAlchemy 2.0 compatible)
```python
user = db.session.get(User, user_id)  # correct API
task = db.session.get(Task, task_id)
```

### BEFORE (Node.js — deprecated Buffer constructor)
```javascript
let buf = new Buffer(data);  // deprecated
```

### AFTER (Node.js)
```javascript
let buf = Buffer.from(data);  // correct
```

---

## P9 — Centralize Error Handling

**Applies to:** Anti-pattern M4

### BEFORE (error handling scattered, internals leaked)
```python
except Exception as e:
    return jsonify({"erro": str(e)}), 500  # leaks internal stack traces
```

```python
except:  # bare except — catches SystemExit, KeyboardInterrupt too
    db.session.rollback()
    return jsonify({'error': 'Erro ao atualizar'}), 500
```

### AFTER (Python Flask — centralized handler)
```python
# middlewares/error_handler.py
import logging

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"erro": "Recurso não encontrado"}), 404

    @app.errorhandler(ValueError)
    def validation_error(e):
        return jsonify({"erro": str(e)}), 400

    @app.errorhandler(Exception)
    def internal_error(e):
        logger.exception("Unhandled exception")
        return jsonify({"erro": "Erro interno do servidor"}), 500

# In route handlers — only catch specific, expected errors:
try:
    result = OrderService.create_order(usuario_id, itens)
except ValueError as e:
    return jsonify({"erro": str(e)}), 400
# Let unexpected errors bubble up to the centralized handler
```

---

## P10 — Remove Sensitive Data from API Responses

**Applies to:** Anti-pattern H2

### BEFORE (password and secret key returned in responses)
```python
# user.to_dict() returns password hash
def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'password': self.password,  # NEVER return this
        'role': self.role,
    }

# health endpoint exposes config
return jsonify({
    "secret_key": "minha-chave-super-secreta-123",  # NEVER return this
    "db_path": "loja.db",
    "debug": True,
})
```

### AFTER (safe serialization)
```python
def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        # 'password' omitted
        'role': self.role,
        'active': self.active,
        'created_at': str(self.created_at),
    }

# health endpoint — infrastructure info only, no secrets
return jsonify({
    "status": "ok",
    "database": "connected",
    "version": "1.0.0",
})
```
