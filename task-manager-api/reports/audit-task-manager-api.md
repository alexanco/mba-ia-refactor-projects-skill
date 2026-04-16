# Architecture Audit Report

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 + SQLAlchemy 3.1.1
Files:   10 analyzed | ~620 lines of code

## Summary
CRITICAL: 2 | HIGH: 3 | MEDIUM: 4 | LOW: 3
Total findings: 12

## Findings

### [CRITICAL] Hardcoded Credentials / Secrets (AP-02)
File: app.py:13
Description: Flask SECRET_KEY is a literal string committed to source control.
Code snippet:
  app.config['SECRET_KEY'] = 'super-secret-key-123'
Impact: Any developer or CI runner with repo access has the signing key for
all sessions/tokens.
Recommendation: Move to os.environ / python-dotenv: SECRET_KEY = os.getenv('SECRET_KEY')

---

### [CRITICAL] Hardcoded Credentials / Secrets (AP-02)
File: services/notification_service.py:8-10
Description: SMTP username and password are literals inside the class constructor.
Code snippet:
  self.email_user = 'taskmanager@gmail.com'
  self.email_password = 'senha123'
Impact: SMTP credentials leaked in version control; rotation requires a code
change and redeploy.
Recommendation: Read from environment variables via os.getenv('SMTP_USER') /
os.getenv('SMTP_PASSWORD').

---

### [CRITICAL] Weak / Broken Cryptography (AP-04)
File: models/user.py:29,32 | routes/user_routes.py:210
Description: Passwords hashed with MD5 (not a password hashing algorithm)
and the login route returned a fake JWT token.
Code snippet:
  self.password = hashlib.md5(pwd.encode()).hexdigest()
  'token': 'fake-jwt-token-' + str(user.id)
Impact: MD5 hashes are reversible in seconds with rainbow tables; the fake
token allows any client to impersonate any user by guessing the pattern.
Recommendation: Replace hashlib.md5 with werkzeug.security
generate_password_hash / check_password_hash (bcrypt). Remove fake token.

---

### [HIGH] Business Logic in Wrong Layer — MVC Violation (AP-05)
File: routes/task_routes.py:88-154
Description: Input validation, overdue computation, and DB session management
are all inside the route handler instead of a controller layer.
Code snippet:
  if len(title) < 3:
      return jsonify({'error': 'Título muito curto'}), 400
  if status not in ['pending', 'in_progress', 'done', 'cancelled']:
      ...
  task.updated_at = datetime.utcnow()
  db.session.add(task); db.session.commit()
Impact: Business rules cannot be unit-tested without an HTTP client.
Recommendation: Extract into controllers/task_controller.py.

---

### [HIGH] N+1 Query Problem (AP-07)
File: routes/task_routes.py:41-57
Description: get_tasks() issues one separate query per task to retrieve the
user name and one more for the category name.
Code snippet:
  for t in tasks:
      user = User.query.get(t.user_id)   # query inside loop
      cat = Category.query.get(t.category_id)  # query inside loop
Impact: With N tasks the endpoint executes up to 2N+1 SQL queries.
Recommendation: Use SQLAlchemy joinedload so user and category are fetched
in one additional query, not N.

---

### [HIGH] N+1 Query Problem (AP-07)
File: routes/report_routes.py:53-68
Description: summary_report() loads every user and then queries all tasks
per user inside the loop.
Code snippet:
  users = User.query.all()
  for u in users:
      user_tasks = Task.query.filter_by(user_id=u.id).all()
Impact: With M users the endpoint executes M+1 queries for the productivity
section alone.
Recommendation: Replace with a single GROUP BY query.

---

### [HIGH] Sensitive Data Exposed via API (AP-08)
File: models/user.py:16-26
Description: to_dict() serializes the password hash and returns it in every
API response.
Code snippet:
  return {
      ...
      'password': self.password,
      ...
  }
Impact: Every API consumer receives the password hash.
Recommendation: Remove 'password' from to_dict().

---

### [MEDIUM] Duplicate Code / Missing DRY (AP-09)
File: routes/task_routes.py:30-39, 71-81, 170-181 |
      routes/user_routes.py:171-181 |
      routes/report_routes.py:33-43 |
      models/task.py:51-60
Description: The "is task overdue?" logic is copy-pasted in at least 6 locations.
Code snippet:
  if t.due_date:
      if t.due_date < datetime.utcnow():
          if t.status != 'done' and t.status != 'cancelled':
              task_data['overdue'] = True
Impact: A business-rule change must be applied in 6+ places.
Recommendation: Consolidate into Task.is_overdue() model method.

---

### [MEDIUM] SQLAlchemy Deprecated Query.get() (DEP-01)
File: routes/task_routes.py:67,117,122,159 | routes/user_routes.py:29,94,155 |
      routes/report_routes.py:105
Description: Model.query.get(id) is deprecated in SQLAlchemy 2.x.
Code snippet:
  task = Task.query.get(task_id)
Impact: Deprecation warnings now; will raise in a future release.
Recommendation: Replace with db.session.get(Task, task_id).

---

### [MEDIUM] Fake / Simulated External Service (AP-12)
File: services/notification_service.py:1-49
Description: In-memory notifications list wiped on restart; notifications
not persisted.
Code snippet:
  self.notifications = []   # wiped on restart
Impact: Notification history invisible across restarts.
Recommendation: Persist notifications to DB or document clearly as stub.

---

### [MEDIUM] datetime.utcnow() Deprecated (DEP-04)
File: models/task.py:15-16, models/user.py:14, routes/task_routes.py:31,
      routes/user_routes.py:172, routes/report_routes.py:35, utils/helpers.py:38
Description: datetime.utcnow() is deprecated in Python 3.12.
Code snippet:
  created_at = db.Column(db.DateTime, default=datetime.utcnow)
Impact: DeprecationWarning on every call.
Recommendation: Replace with datetime.now(timezone.utc).

---

### [LOW] Unused Imports (AP-15)
File: routes/task_routes.py:7, app.py:7, routes/user_routes.py:6
Description: Multiple files import standard-library modules never used.
Code snippet:
  import json, os, sys, time   # none used in task_routes.py
Impact: Cognitive overhead.
Recommendation: Remove unused imports.

---

### [LOW] Bare Except Clauses (AP-16)
File: routes/task_routes.py:62,138 | routes/user_routes.py:131,149 |
      routes/report_routes.py:188 | utils/helpers.py:47-50
Description: Bare except: silently swallows all exceptions.
Code snippet:
  except:
      return jsonify({'error': 'Erro interno'}), 500
Impact: Real errors invisible; impossible to debug.
Recommendation: Replace with except Exception as e: and log the error.

---

### [LOW] Magic Numbers / Strings (AP-13)
File: routes/task_routes.py:96-100, routes/user_routes.py:64
Description: Validation limits (3, 200, 4) are inline literals; constants
defined in utils/helpers.py are never imported.
Code snippet:
  if len(title) < 3:
  if len(title) > 200:
Impact: Changing a limit requires editing multiple route files.
Recommendation: Import constants from utils/helpers.py.

================================
Total: 12 findings
Estimated refactoring effort: High
================================
```
