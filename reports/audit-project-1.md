# Architecture Audit Report

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~784 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 3 | LOW: 3
Total findings: 14

## Findings
(sorted by severity: CRITICAL → HIGH → MEDIUM → LOW)

### [CRITICAL] SQL Injection via String Concatenation (AP-01)
File: models.py:28, 48-50, 57-63, 68, 92, 109-111, 127-130,
      140, 148-151, 155-167, 174, 188, 192, 220, 224, 280-282, 289-296
Description: Every SQL query in models.py is built via string concatenation
  with user-supplied or externally-controlled values. Affects all CRUD
  operations for produtos, usuarios, and pedidos — including the login query.
Code snippet:
  # models.py:28
  cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))

  # models.py:48-50
  cursor.execute(
      "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES ('" +
      nome + "', '" + descricao + "', " + str(preco) + ", " + str(estoque) + ", '" + categoria + "')"
  )

  # models.py:109-111 (login — authentication bypass)
  cursor.execute(
      "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
  )

  # models.py:289-296
  query = "SELECT * FROM produtos WHERE 1=1"
  if termo:
      query += " AND (nome LIKE '%" + termo + "%' OR descricao LIKE '%" + termo + "%')"
  if categoria:
      query += " AND categoria = '" + categoria + "'"
Impact: An attacker can bypass authentication (' OR '1'='1), dump the
  entire database, delete all records, or execute arbitrary SQL through
  any of these endpoints.
Recommendation: Replace all string-concatenated queries with parameterized
  queries using ? placeholders: cursor.execute("SELECT * FROM produtos
  WHERE id = ?", (id,))

### [CRITICAL] Hardcoded Credentials / Secrets (AP-02)
File: app.py:7 | database.py:75-83
Description: The Flask SECRET_KEY is hardcoded as a literal string in
  app.py. Seed data in database.py stores plaintext passwords for admin
  and client accounts directly in source code.
Code snippet:
  # app.py:7
  app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"

  # database.py:75-78
  usuarios = [
      ("Admin", "admin@loja.com", "admin123", "admin"),
      ("João Silva", "joao@email.com", "123456", "cliente"),
      ("Maria Santos", "maria@email.com", "senha123", "cliente"),
  ]
Impact: Any developer with repo access knows the SECRET_KEY and all
  seed account passwords. These are committed to git history.
Recommendation: Move SECRET_KEY to a .env file loaded via os.environ.
  Extract to src/config/settings.py. Seed passwords should use hashed values.

### [CRITICAL] Unauthenticated Dangerous Admin Endpoints (AP-03)
File: app.py:47-78
Description: Two admin endpoints are exposed with no authentication:
  /admin/reset-db wipes all tables, and /admin/query executes arbitrary
  SQL submitted by anyone via a POST body.
Code snippet:
  # app.py:59-76
  @app.route("/admin/query", methods=["POST"])
  def executar_query():
      dados = request.get_json()
      query = dados.get("sql", "")
      ...
      cursor.execute(query)   # executes any SQL from request body

  # app.py:47-57
  @app.route("/admin/reset-db", methods=["POST"])
  def reset_database():
      cursor.execute("DELETE FROM itens_pedido")
      ...
Impact: Any unauthenticated HTTP client can permanently wipe the entire
  database or execute arbitrary SQL (DROP TABLE, exfiltrate data, etc.).
Recommendation: Remove /admin/query entirely. Gate /admin/reset-db behind
  DEBUG mode + authentication. Move to src/routes/admin_routes.py.

### [CRITICAL] Plaintext Password Storage (AP-04)
File: models.py:122-131 | database.py:75-83
Description: Passwords are stored and retrieved as plaintext strings.
  No hashing applied in criar_usuario(). login_usuario() compares raw
  string passwords.
Code snippet:
  # models.py:122-131
  def criar_usuario(nome, email, senha, tipo="cliente"):
      cursor.execute(
          "INSERT INTO usuarios (nome, email, senha, tipo) VALUES ('" +
          nome + "', '" + email + "', '" + senha + "', '" + tipo + "')"
      )
Impact: A database breach exposes every user's actual password in plaintext.
Recommendation: Use werkzeug.security (generate_password_hash /
  check_password_hash) already bundled with Flask.

### [HIGH] Business Logic in Wrong Layer (AP-05)
File: models.py:256-272 | controllers.py:208-210, 247-251
Description: Discount/pricing business rules live inside the data-access
  layer (models.py). Notification logic (email, SMS, push) is triggered
  from controller functions via print() stubs.
Code snippet:
  # models.py:256-272 — discount rules embedded in a model function
  desconto = 0
  if faturamento > 10000:
      desconto = faturamento * 0.1
  elif faturamento > 5000:
      desconto = faturamento * 0.05
  elif faturamento > 1000:
      desconto = faturamento * 0.02

  # controllers.py:208-210 — notification side-effects in controller
  print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]) + " criado...")
  print("ENVIANDO SMS: Seu pedido foi recebido!")
  print("ENVIANDO PUSH: Novo pedido recebido pelo sistema")
Impact: Business rules cannot be unit-tested independently. Changing
  discount tiers requires editing a DB-access file.
Recommendation: Extract discount logic to src/services/relatorio_service.py.
  Extract notifications to src/services/notification_service.py.

### [HIGH] God File (AP-06)
File: controllers.py (293 lines) | models.py (315 lines)
Description: controllers.py handles all domains — produtos, usuarios,
  pedidos, relatorios, health — in a single flat file. models.py mixes
  data access for all four tables plus discount calculation logic.
Code snippet:
  # controllers.py — 15 functions across 3 unrelated domains
  def listar_produtos(): ...      # line 5
  def listar_usuarios(): ...      # line 128
  def criar_pedido(): ...         # line 188
  def relatorio_vendas(): ...     # line 257
Impact: Adding a new domain requires editing shared files. Merge
  conflicts are frequent. No clear ownership of each domain.
Recommendation: Split into src/controllers/produto_controller.py,
  src/controllers/usuario_controller.py, src/controllers/pedido_controller.py.

### [HIGH] N+1 Query Problem (AP-07)
File: models.py:186-200 | models.py:219-232
Description: Both get_pedidos_usuario() and get_todos_pedidos() fetch
  all pedidos, then for EACH pedido run a separate query for its itens,
  then for EACH item run another query for the product name.
Code snippet:
  # models.py:186-198
  cursor2 = db.cursor()
  cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
  itens = cursor2.fetchall()
  for item in itens:
      cursor3 = db.cursor()
      cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
Impact: 10 orders with 3 items each = 41 queries. 100 orders = 401+ queries.
Recommendation: Replace with a single JOIN query across pedidos,
  itens_pedido, and produtos.

### [HIGH] Sensitive Data Exposed via API / Logs (AP-08)
File: controllers.py:276-291 | models.py:79-86, 92-102
Description: The /health endpoint returns SECRET_KEY and db_path in
  the JSON response. get_todos_usuarios() and get_usuario_por_id()
  include the plaintext senha field in every response.
Code snippet:
  # controllers.py:288-289
  "secret_key": "minha-chave-super-secreta-123",
  "db_path": "loja.db",

  # models.py:84
  "senha": row["senha"],   # plaintext password returned to caller
Impact: Any client calling GET /health receives the app secret key.
  GET /usuarios leaks all user passwords to the frontend.
Recommendation: Remove secret_key and db_path from health response.
  Never include password fields in model serialization.

### [MEDIUM] Duplicate Code / Missing DRY (AP-09)
File: controllers.py:29-36 and controllers.py:73-79 | models.py:171-233
Description: Product field validation (nome, preco, estoque required +
  range checks) is copy-pasted between criar_produto and atualizar_produto.
  The N+1 loop body in get_pedidos_usuario and get_todos_pedidos is
  nearly identical (~30 lines duplicated).
Code snippet:
  # controllers.py:30-36 (and again at lines 73-79)
  if "nome" not in dados:
      return jsonify({"erro": "Nome é obrigatório"}), 400
  if "preco" not in dados:
      return jsonify({"erro": "Preço é obrigatório"}), 400
  if "estoque" not in dados:
      return jsonify({"erro": "Estoque é obrigatório"}), 400
Impact: Bug in validation must be fixed in two places.
Recommendation: Extract to a _validar_payload_produto(dados) helper.

### [MEDIUM] Global Mutable State (AP-10)
File: database.py:4-10
Description: A single global db_connection is reused across all requests.
  With check_same_thread=False, this bypasses SQLite's thread safety.
Code snippet:
  db_connection = None
  def get_db():
      global db_connection
      if db_connection is None:
          db_connection = sqlite3.connect(db_path, check_same_thread=False)
Impact: Under concurrent requests the shared connection can produce
  corrupted results or "database is locked" errors.
Recommendation: Use Flask's g object with teardown_appcontext for
  per-request connections.

### [MEDIUM] Fake / Simulated External Services (AP-12)
File: controllers.py:208-210, 247-251
Description: Email, SMS, and push notification delivery is simulated
  entirely by print() statements. No actual integration exists.
Code snippet:
  print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]) + " criado para usuario " + str(usuario_id))
  print("ENVIANDO SMS: Seu pedido foi recebido!")
  print("ENVIANDO PUSH: Novo pedido recebido pelo sistema")
Impact: Production deployments silently drop all notifications.
Recommendation: Extract to src/services/notification_service.py with
  a real interface stub (explicit TODO comments, not disguised as working code).

### [LOW] Magic Numbers / Magic Strings (AP-13)
File: models.py:257-261
Description: Discount tier thresholds (10000, 5000, 1000) and rates
  (0.1, 0.05, 0.02) are unexplained literals.
Code snippet:
  if faturamento > 10000:
      desconto = faturamento * 0.1
  elif faturamento > 5000:
      desconto = faturamento * 0.05
Impact: Intent is unclear; business rule changes require searching all occurrences.
Recommendation: Define as named constants in src/services/relatorio_service.py.

### [LOW] Unused Import (AP-15)
File: models.py:2
Description: import sqlite3 is present but never used directly.
Code snippet:
  import sqlite3
Recommendation: Remove the unused import.

### [LOW] Routes via app.add_url_rule() Instead of Blueprints (DEP-03)
File: app.py:11-30
Description: All 14 routes are registered via app.add_url_rule() in the
  entry point instead of Flask Blueprints.
Code snippet:
  app.add_url_rule("/produtos", "listar_produtos", controllers.listar_produtos, methods=["GET"])
  # ... 13 more lines
Recommendation: Create per-domain Blueprints in src/routes/ and register
  via app.register_blueprint().

================================
Total: 14 findings
Estimated refactoring effort: High
================================
```
