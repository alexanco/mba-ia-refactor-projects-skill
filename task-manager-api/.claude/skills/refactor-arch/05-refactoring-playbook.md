# Refactoring Playbook

Each pattern includes a concrete before/after example. Apply the appropriate pattern for each finding from the audit.

---

## PT-01: Fix SQL Injection — Parameterized Queries

**Addresses:** AP-01 (SQL Injection)

**Before (Python):**
```python
# VULNERABLE: String concatenation
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("INSERT INTO usuarios (nome, email) VALUES ('" + nome + "', '" + email + "')")
query = "SELECT * FROM produtos WHERE nome LIKE '%" + termo + "%'"
```

**After (Python):**
```python
# SAFE: Parameterized queries with ? placeholders
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("INSERT INTO usuarios (nome, email) VALUES (?, ?)", (nome, email))
cursor.execute("SELECT * FROM produtos WHERE nome LIKE ?", (f'%{termo}%',))
```

**Before (Node.js):**
```javascript
// VULNERABLE
db.run("DELETE FROM users WHERE id = " + id);
db.get("SELECT * FROM courses WHERE id = " + cid);
```

**After (Node.js):**
```javascript
// SAFE: Parameterized with ? placeholders
db.run("DELETE FROM users WHERE id = ?", [id]);
db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [cid]);
```

---

## PT-02: Extract Config to Environment Variables

**Addresses:** AP-02 (Hardcoded Credentials)

**Before (Python):**
```python
# app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```

**After (Python):**
```python
# src/config/settings.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'app.db')

# app.py
from src.config.settings import Config
app.config.from_object(Config)
```

**Before (Node.js):**
```javascript
// utils.js
const config = {
    paymentGatewayKey: "pk_live_1234567890abcdef",
    dbPass: "senha_super_secreta_prod_123",
};
```

**After (Node.js):**
```javascript
// src/config/index.js
require('dotenv').config();

module.exports = {
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    port: process.env.PORT || 3000,
};
// Add PAYMENT_GATEWAY_KEY=... to .env file (not committed)
```

---

## PT-03: Remove N+1 Queries — Use JOINs or Eager Loading

**Addresses:** AP-07 (N+1 Query Problem)

**Before (Python — nested cursors in loop):**
```python
# N+1: fetches items then product for each item
cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
rows = cursor.fetchall()
for row in rows:
    cursor2 = db.cursor()
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (str(row["id"]),))
    itens = cursor2.fetchall()
    for item in itens:
        cursor3 = db.cursor()
        cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (str(item["produto_id"]),))
```

**After (Python — single JOIN query):**
```python
# Single query with JOIN
cursor.execute("""
    SELECT p.*, ip.produto_id, ip.quantidade, ip.preco_unitario, pr.nome as produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
    WHERE p.usuario_id = ?
""", (usuario_id,))
```

---

## PT-04: Fix Password Hashing

**Addresses:** AP-04 (Weak Cryptography), AP-02 (Plaintext passwords)

**Before (Python — MD5):**
```python
import hashlib
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()  # BROKEN
```

**After (Python — bcrypt or werkzeug):**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

**Before (Node.js — fake base64 "hash"):**
```javascript
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10); // NOT a hash
}
```

**After (Node.js — bcryptjs):**
```javascript
const bcrypt = require('bcryptjs');

async function hashPassword(pwd) {
    return bcrypt.hash(pwd, 12);
}

async function verifyPassword(pwd, hash) {
    return bcrypt.compare(pwd, hash);
}
```

---

## PT-05: Remove Sensitive Data from API Responses

**Addresses:** AP-08 (Sensitive Data Exposed)

**Before (Python — password in to_dict):**
```python
def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'password': self.password,  # NEVER expose this
        'role': self.role,
    }
```

**After (Python):**
```python
def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'role': self.role,
        'active': self.active,
        'created_at': str(self.created_at),
    }
```

**Before (Python — health check leaking secrets):**
```python
return jsonify({
    "status": "ok",
    "secret_key": "minha-chave-super-secreta-123",  # NEVER
    "db_path": "loja.db",
    "debug": True,
})
```

**After (Python):**
```python
return jsonify({
    "status": "ok",
    "database": "connected",
    "version": "1.0.0",
})
```

---

## PT-06: Replace God Class with Layered Structure

**Addresses:** AP-06 (God Class), AP-05 (Business Logic in Wrong Layer)

**Before (Node.js — AppManager does everything):**
```javascript
class AppManager {
    constructor() { this.db = new sqlite3.Database(':memory:'); }
    
    initDb() { /* creates tables AND seeds data */ }
    
    setupRoutes(app) {
        app.post('/api/checkout', (req, res) => {
            // validates input + processes payment + creates user + creates enrollment
            // all in one deeply nested callback
        });
    }
}
```

**After (Node.js — separated layers):**
```javascript
// src/models/userModel.js
class UserModel {
    static async findByEmail(db, email) { ... }
    static async create(db, data) { ... }
}

// src/services/paymentService.js
class PaymentService {
    static processCard(cardNumber, amount) { ... }
}

// src/controllers/checkoutController.js
class CheckoutController {
    static async checkout(req, res) {
        const { usr, eml, pwd, c_id, card } = req.body;
        // validate → find/create user → process payment → enroll
        const course = await CourseModel.findById(db, c_id);
        const payment = await PaymentService.processCard(card, course.price);
        // ...
    }
}

// src/routes/checkoutRoutes.js
router.post('/api/checkout', CheckoutController.checkout);
```

---

## PT-07: Centralize Duplicate Logic with Helper/Service

**Addresses:** AP-09 (Duplicate Code)

**Before (Python — overdue check in 4 different places):**
```python
# In get_tasks, get_task, get_user_tasks, task_stats — all repeat this:
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

**After (Python — extracted to a helper or model method):**
```python
# In utils/task_helpers.py or on the Task model
def is_overdue(task):
    if not task.due_date:
        return False
    if task.status in ('done', 'cancelled'):
        return False
    return task.due_date < datetime.utcnow()

# Usage everywhere:
task_data['overdue'] = is_overdue(t)
```

---

## PT-08: Eliminate Callback Hell — Use Async/Await

**Addresses:** Deeply nested callbacks in Node.js (AP-06)

**Before (Node.js — 5-level callback pyramid):**
```javascript
db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
    db.get("SELECT id FROM users WHERE email = ?", [email], (err, user) => {
        db.run("INSERT INTO enrollments ...", [...], function(err) {
            db.run("INSERT INTO payments ...", [...], function(err) {
                db.run("INSERT INTO audit_logs ...", [...], (err) => {
                    res.json({ msg: "Sucesso" });
                });
            });
        });
    });
});
```

**After (Node.js — using better-sqlite3 synchronously):**
```javascript
const Database = require('better-sqlite3');
// or wrap existing sqlite3 in promises

async function checkout(courseId, userEmail, cardNumber) {
    const course = db.prepare('SELECT * FROM courses WHERE id = ? AND active = 1').get(courseId);
    if (!course) throw new Error('Course not found');
    
    let user = db.prepare('SELECT id FROM users WHERE email = ?').get(userEmail);
    if (!user) {
        const hash = await hashPassword(password);
        const result = db.prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)').run(name, email, hash);
        user = { id: result.lastInsertRowid };
    }
    
    const enrollment = db.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)').run(user.id, courseId);
    db.prepare('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)').run(enrollment.lastInsertRowid, course.price, 'PAID');
    
    return { enrollment_id: enrollment.lastInsertRowid };
}
```

---

## PT-09: Fix Deprecated SQLAlchemy Query.get()

**Addresses:** DEP-01

**Before:**
```python
task = Task.query.get(task_id)
user = User.query.get(user_id)
cat = Category.query.get(cat_id)
```

**After:**
```python
task = db.session.get(Task, task_id)
user = db.session.get(User, user_id)
cat = db.session.get(Category, cat_id)
```

---

## PT-10: Remove Dangerous Admin Endpoints

**Addresses:** AP-03 (Unauthenticated Dangerous Admin Endpoints)

**Before:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    dados = request.get_json()
    query = dados.get("sql", "")
    cursor.execute(query)  # Executes ANY SQL from request body
```

**After:**
- **Remove entirely** if there is no legitimate use case
- If needed for development only: add environment check + authentication:

```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    if not Config.DEBUG:
        return jsonify({"erro": "Endpoint não disponível em produção"}), 403
    # Add proper auth check here
    ...
```

---

## PT-11: Organize Flask Routes with Blueprints

**Addresses:** DEP-03 (app.add_url_rule for all routes)

**Before (app.py with all routes):**
```python
app.add_url_rule("/produtos", "listar_produtos", controllers.listar_produtos, methods=["GET"])
app.add_url_rule("/produtos/<int:id>", "buscar_produto", controllers.buscar_produto, methods=["GET"])
# ... 20 more lines of this
```

**After (using Blueprints):**
```python
# src/routes/produto_routes.py
from flask import Blueprint
from src.controllers.produto_controller import ProdutoController

produto_bp = Blueprint('produtos', __name__)

@produto_bp.route('/produtos', methods=['GET'])
def listar():
    return ProdutoController.listar()

@produto_bp.route('/produtos/<int:id>', methods=['GET'])
def buscar(id):
    return ProdutoController.buscar(id)

# app.py
from src.routes.produto_routes import produto_bp
app.register_blueprint(produto_bp)
```

---

## PT-12: Centralize Error Handling

**Addresses:** AP-16 (Bare Except), general error handling

**Before (Python — inconsistent error handling):**
```python
try:
    ...
except:  # catches everything including KeyboardInterrupt
    return jsonify({'error': 'Erro interno'}), 500
```

**After (Python — centralized error handler):**
```python
# src/middlewares/error_handler.py
from flask import jsonify

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"erro": str(e), "sucesso": False}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500

# app.py
from src.middlewares.error_handler import register_error_handlers
register_error_handlers(app)
```

**After (Node.js — Express error middleware):**
```javascript
// src/middlewares/errorHandler.js
function errorHandler(err, req, res, next) {
    console.error(err.stack);
    res.status(err.status || 500).json({
        error: err.message || 'Internal Server Error'
    });
}

module.exports = errorHandler;

// src/app.js (must be registered AFTER routes)
app.use(errorHandler);
```
