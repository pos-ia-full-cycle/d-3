# MVC Architecture Guidelines

These are the target architecture rules for Phase 3. Adapt the structure to the detected stack — the layer names and file extensions change, but the responsibilities never do.

---

## Core Principle: Separation of Responsibilities

Each layer has exactly one job. A function belongs in exactly one layer. When in doubt, ask: "What would change if I switched from SQLite to PostgreSQL?" (→ only Models should change). "What would change if I added a CLI interface?" (→ only Routes/Views should change).

---

## Target MVC Structure

### Python/Flask

```
src/
├── config/
│   └── settings.py          # All config, reads from env vars
├── models/
│   └── <entity>_model.py    # DB schema + data access methods only
├── controllers/
│   └── <entity>_controller.py  # HTTP orchestration + response formatting
├── routes/
│   └── <entity>_routes.py   # Blueprint definitions + URL mapping only
├── services/
│   └── <entity>_service.py  # Complex business logic (optional layer)
├── middlewares/
│   └── error_handler.py     # Centralized error handling
└── app.py                   # Composition root — wires everything together
```

### Node.js/Express

```
src/
├── config/
│   └── index.js             # All config, reads from process.env
├── models/
│   └── <Entity>.js          # DB schema + query methods only
├── controllers/
│   └── <entity>Controller.js  # Business orchestration + response
├── routes/
│   └── <entity>Routes.js    # Express Router + URL mapping only
├── services/
│   └── <entity>Service.js   # Business logic (optional)
├── middlewares/
│   └── errorHandler.js      # Centralized error handling
└── app.js                   # Express app setup + route mounting
```

---

## Layer Responsibilities

### Config Layer
**Allowed:**
- Reading environment variables: `os.environ.get("SECRET_KEY")` or `process.env.SECRET_KEY`
- Providing defaults for development: `os.environ.get("DEBUG", "false").lower() == "true"`
- Exporting a single config object consumed by all other layers

**Forbidden:**
- Hardcoded credentials or secrets
- Business logic
- Direct DB access

**Example (Python):**
```python
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    PAYMENT_GATEWAY_KEY = os.environ.get("PAYMENT_GATEWAY_KEY")
```

---

### Models Layer
**Allowed:**
- ORM model class definitions (columns, relationships)
- Data access methods: `find_by_id`, `find_all`, `create`, `update`, `delete`
- Parameterized SQL queries
- Schema validation at the data level (nullable, unique constraints)
- `to_dict()` serialization method (without sensitive fields)

**Forbidden:**
- Business rules (e.g., "apply 10% discount if revenue > 10000")
- HTTP request/response objects
- Sending emails, pushing notifications
- Calling other models (use services for cross-model logic)
- Hardcoded SQL with string concatenation

**Example (Python):**
```python
class UserModel:
    @staticmethod
    def find_by_email(email):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cursor.fetchone()

    @staticmethod
    def create(name, email, password_hash):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        db.commit()
        return cursor.lastrowid
```

---

### Controllers Layer
**Allowed:**
- Calling model or service methods
- Formatting HTTP responses (status codes, JSON structure)
- Orchestrating the flow for a use case (validate → process → respond)
- Calling notification services (not implementing them)
- Input validation and sanitization at the HTTP boundary

**Forbidden:**
- Raw SQL queries
- Complex business calculations (discount logic, report aggregation)
- Direct DB connections
- Sending emails or SMS directly

**Example (Python):**
```python
def login(email, senha):
    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    usuario = UserModel.find_by_email(email)
    if not usuario or not AuthService.verify_password(senha, usuario["password"]):
        return jsonify({"erro": "Credenciais inválidas"}), 401

    token = AuthService.generate_token(usuario["id"])
    return jsonify({"token": token, "usuario": {"id": usuario["id"], "nome": usuario["nome"]}}), 200
```

---

### Routes / Views Layer
**Allowed:**
- URL pattern registration
- HTTP method binding (GET, POST, PUT, DELETE)
- Delegating immediately to a controller
- Blueprint/Router creation and configuration

**Forbidden:**
- Any business logic
- Direct DB access
- Data transformation or formatting

**Example (Python Flask):**
```python
from flask import Blueprint, request
from controllers.user_controller import UserController

user_bp = Blueprint("users", __name__, url_prefix="/usuarios")

@user_bp.route("", methods=["GET"])
def listar():
    return UserController.listar_todos()

@user_bp.route("/<int:id>", methods=["GET"])
def buscar(id):
    return UserController.buscar_por_id(id)

@user_bp.route("", methods=["POST"])
def criar():
    return UserController.criar(request.get_json())
```

---

### Services Layer (optional but recommended for complex logic)
**Use when:**
- Business logic spans multiple models
- A use case requires multiple steps (validate → transform → persist → notify)
- Logic needs to be reused across multiple controllers

**Example (Python):**
```python
class OrderService:
    @staticmethod
    def create_order(user_id, items):
        # Validates stock for all items before creating anything
        for item in items:
            product = ProductModel.find_by_id(item["produto_id"])
            if not product:
                raise ValueError(f"Produto {item['produto_id']} não encontrado")
            if product["estoque"] < item["quantidade"]:
                raise ValueError(f"Estoque insuficiente para {product['nome']}")

        total = sum(
            ProductModel.find_by_id(i["produto_id"])["preco"] * i["quantidade"]
            for i in items
        )
        order_id = OrderModel.create(user_id, total)
        for item in items:
            OrderItemModel.create(order_id, item["produto_id"], item["quantidade"])
            ProductModel.decrement_stock(item["produto_id"], item["quantidade"])

        NotificationService.notify_new_order(user_id, order_id)
        return {"pedido_id": order_id, "total": total}
```

---

### Middlewares Layer
**Responsibilities:**
- Centralized error handling (catch all unhandled exceptions, return consistent error format)
- Authentication/authorization checks
- Request logging
- CORS configuration

**Example (Python Flask):**
```python
def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Internal error: {e}")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
```

---

### App Entry Point (app.py / app.js)
**Responsibilities:**
- Create the app instance
- Load configuration
- Initialize the database connection
- Register blueprints/routers
- Register middleware
- Start the server

**Must NOT contain:**
- Route handlers
- Business logic
- DB queries
