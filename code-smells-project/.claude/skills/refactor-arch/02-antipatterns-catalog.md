# Anti-Patterns Catalog

Each anti-pattern includes: severity, detection signals (exact code patterns to look for), and impact description.

---

## CRITICAL Severity

### AP-01: SQL Injection via String Concatenation
**Severity:** CRITICAL  
**Detection signals:**
- Python: `cursor.execute("SELECT * FROM ... WHERE id = " + str(id))`
- Python: `cursor.execute("INSERT INTO ... VALUES ('" + nome + "', ...)")`
- Python: `query += " AND nome LIKE '%" + termo + "%'"`
- Node.js: `db.run("DELETE FROM users WHERE id = " + id)`
- Any SQL string built with `+` concatenation using user-supplied data

**Impact:** Attacker can read/modify/delete any data, bypass authentication, execute system commands.

**What to look for:** Any `cursor.execute()`, `db.run()`, or `db.query()` call where the SQL string is built with string concatenation (`+`) rather than parameterized placeholders (`?` or `%s`).

---

### AP-02: Hardcoded Credentials / Secrets
**Severity:** CRITICAL  
**Detection signals:**
- `SECRET_KEY = "some-literal-string-123"`
- `password = "senha123"` in source code
- `paymentGatewayKey = "pk_live_..."` in source code
- `dbPass = "prod_password"` in source code
- Any API key, token, password, or secret stored as a string literal in code
- Credentials inserted into seed data functions

**Impact:** Credentials leaked in version control, accessible to anyone with repo access.

---

### AP-03: Unauthenticated Dangerous Admin Endpoints
**Severity:** CRITICAL  
**Detection signals:**
- Route accepting arbitrary SQL: `cursor.execute(query)` where query comes from `request.get_json()`
- `/admin/query` or similar endpoint that executes user-supplied SQL
- Admin reset endpoint (`/admin/reset-db`) with no authentication check
- Any endpoint performing destructive operations without verifying caller identity

**Impact:** Any user can wipe the database or execute arbitrary SQL.

---

### AP-04: Weak / Broken Cryptography
**Severity:** CRITICAL  
**Detection signals:**
- Python: `hashlib.md5(pwd.encode()).hexdigest()` for password hashing
- Node.js: custom crypto function using base64 encoding as "hashing"
- `sha1` for passwords
- Storing passwords in plaintext
- Fake tokens: `'fake-jwt-token-' + str(user.id)`

**Impact:** Passwords can be cracked instantly (MD5/SHA1 rainbow tables). Fake tokens allow impersonation.

---

## HIGH Severity

### AP-05: Business Logic in Wrong Layer (MVC Violation)
**Severity:** HIGH  
**Detection signals:**
- Discount/pricing calculations inside a model file that also does DB queries
- Notification sending (email, SMS, push) inside a controller or model
- Complex data transformations inside route handlers
- Financial report generation mixed with route handling code
- Multiple `if/elif` status business rules inside a controller instead of a service

**Impact:** Impossible to test business rules in isolation, any change risks breaking unrelated features.

---

### AP-06: God Class / God File
**Severity:** HIGH  
**Detection signals:**
- Single class with >200 lines handling multiple domains (DB init + routes + payments + logging)
- Single file with >300 lines containing unrelated functions (user management + product management + order management + reports)
- Class methods doing HTTP handling, SQL queries, AND business rules in the same method

**Impact:** Impossible to test, understand, or extend. Changes cascade unpredictably.

---

### AP-07: N+1 Query Problem
**Severity:** HIGH  
**Detection signals:**
- Python: `for row in rows: cursor.execute("SELECT ... WHERE id = " + str(row["id"]))`
- Python: nested cursor queries inside loops (`cursor2`, `cursor3` inside a `for` loop)
- Node.js: `enrollments.forEach(enr => { this.db.get(...user..., () => { this.db.get(...payment..., ...) }) })`
- Any SELECT inside a loop that fetches related data row-by-row

**Impact:** 1000 records = 1001+ database queries. Severe performance degradation at scale.

---

### AP-08: Sensitive Data Exposed via API or Logs
**Severity:** HIGH  
**Detection signals:**
- `to_dict()` method that includes `password` field in the returned dict
- Health check endpoint returning `secret_key` or `db_path`
- `console.log(cardNumber)` or `print("Processing card " + cc)`
- API response containing password hash
- Log statements printing sensitive user data

**Impact:** Passwords/secrets leaked to clients or in server logs.

---

## MEDIUM Severity

### AP-09: Duplicate Code / Missing DRY
**Severity:** MEDIUM  
**Detection signals:**
- Same overdue-checking logic block (e.g., `if t.due_date < datetime.utcnow() and t.status != 'done'`) copy-pasted in 3+ functions
- Same validation logic repeated across multiple route handlers
- Same response format code duplicated in multiple places

**Impact:** Bug fix must be applied in multiple places. Risk of inconsistency.

---

### AP-10: Global Mutable State
**Severity:** MEDIUM  
**Detection signals:**
- `let globalCache = {}` at module level, mutated from request handlers
- `global db_connection = None` used as a singleton without thread safety
- Module-level variables that accumulate state across requests

**Impact:** Unpredictable behavior under concurrent requests, memory leaks, hard to test.

---

### AP-11: Missing Input Validation at Boundaries
**Severity:** MEDIUM  
**Detection signals:**
- Route handler accepting `request.get_json()` without checking if fields exist
- No validation of status enum values before DB insert
- No check for negative numbers, empty strings, or None for required fields
- Accepting user_id from request body without verifying the user exists

**Impact:** Invalid data enters the database, causing downstream errors or data corruption.

---

### AP-12: Fake / Simulated External Services
**Severity:** MEDIUM  
**Detection signals:**
- `print("ENVIANDO EMAIL: ...")` instead of actual email sending
- `print("ENVIANDO SMS: ...")` substituting for SMS API calls
- Notification service that never actually sends notifications
- Payment processing that checks `card.startsWith("4")` as "validation"

**Impact:** Functionality appears to work in development but doesn't in production. Hidden assumptions.

---

## LOW Severity

### AP-13: Magic Numbers / Magic Strings
**Severity:** LOW  
**Detection signals:**
- `if faturamento > 10000: desconto = faturamento * 0.1` — unnamed thresholds
- `if priority < 1 or priority > 5` — unnamed range constants
- Status strings like `'pendente'`, `'aprovado'` scattered throughout code without constants
- Port numbers, timeout values as literals

**Impact:** Unclear intent, change requires finding all occurrences.

---

### AP-14: Poor Naming / Cryptic Variables
**Severity:** LOW  
**Detection signals:**
- Single-letter variables: `let u = req.body.usr`, `let e = req.body.eml`, `let cc = req.body.card`
- Abbreviated names without context: `enrId`, `enrPending`, `cid`
- Inconsistent naming: snake_case mixed with camelCase in the same file

**Impact:** Code is hard to read and maintain.

---

### AP-15: Unused Imports
**Severity:** LOW  
**Detection signals:**
- `import json, os, sys, time` at top of file where none of these are used
- `import sqlite3` in a file that only uses the db module
- Node.js: `const { config, logAndCache, badCrypto, totalRevenue } = require('./utils')` where `totalRevenue` is never used

**Impact:** Increases cognitive load, may indicate dead code paths.

---

### AP-16: Bare Except Clauses
**Severity:** LOW  
**Detection signals:**
- Python: `except:` without specifying the exception type
- Python: `except Exception:` without logging or re-raising
- Swallowing exceptions silently: `except: pass`
- Node.js: `.catch()` that does nothing

**Impact:** Hides bugs, makes debugging impossible.

---

## Deprecated APIs

### DEP-01: SQLAlchemy Deprecated Query.get()
**Stack:** Python + SQLAlchemy  
**Severity:** MEDIUM  
**Detection:** `Model.query.get(id)` — deprecated in SQLAlchemy 2.x  
**Replacement:** `db.session.get(Model, id)`

### DEP-02: sqlite3 Callback API
**Stack:** Node.js + sqlite3  
**Severity:** MEDIUM  
**Detection:** `db.run(sql, params, function(err) {...})`, `db.all(sql, params, (err, rows) => {...})`  
**Replacement:** Use `better-sqlite3` (synchronous) or `sqlite3` with Promise wrappers

### DEP-03: Flask app.add_url_rule() for all routes
**Stack:** Python + Flask  
**Severity:** LOW  
**Detection:** All routes defined via `app.add_url_rule()` in the entry point instead of Blueprints  
**Replacement:** Use Flask Blueprints for route organization (`Blueprint`, `app.register_blueprint()`)

### DEP-04: datetime.utcnow() (Python 3.12+)
**Stack:** Python  
**Severity:** LOW  
**Detection:** `datetime.utcnow()`  
**Replacement:** `datetime.now(timezone.utc)`
