================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Node.js/Express
Files:   3 analyzed | ~181 lines of code

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 4 | LOW: 3
Total findings: 13

## Findings

### [CRITICAL] Hardcoded Credentials / Secrets (AP-02)
File: src/utils.js:2-6
Description: Database password, live payment gateway key, and SMTP user are
  all hardcoded as string literals in a committed source file.
Code snippet:
  dbUser: "admin_master",
  dbPass: "senha_super_secreta_prod_123",
  paymentGatewayKey: "pk_live_1234567890abcdef",
  smtpUser: "no-reply@fullcycle.com.br",
Impact: Any developer or attacker with repo access obtains the live payment
  gateway key and database credentials immediately.
Recommendation: Extract all secrets to environment variables via a .env file.
  Replace config object with process.env reads (PT-02).

### [CRITICAL] Weak / Broken Cryptography (AP-04)
File: src/utils.js:17-23 | src/AppManager.js:18 | src/AppManager.js:68
Description: Passwords are (1) stored as the plaintext literal '123' in the
  seed user, and (2) "hashed" via badCrypto(), which is a loop concatenating
  base64-encoded characters — not a cryptographic hash. The result is a
  10-character deterministic string trivially reversible.
Code snippet:
  function badCrypto(pwd) {
      let hash = "";
      for(let i = 0; i < 10000; i++) {
          hash += Buffer.from(pwd).toString('base64').substring(0, 2);
      }
      return hash.substring(0, 10);
  }
  // AppManager.js:18 — seed data
  "INSERT INTO users ... VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')"
Impact: All user passwords can be recovered in milliseconds. The seed account
  has the literal password '123' persisted to the database.
Recommendation: Replace badCrypto() with bcryptjs (PT-04). Re-seed with a
  properly hashed password.

### [CRITICAL] Sensitive Data Exposed via Logs (AP-08)
File: src/AppManager.js:45
Description: Card number (cc) and the live payment gateway key are both
  printed to stdout on every checkout request.
Code snippet:
  console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
Impact: PCI-DSS violation. Card numbers appear in server logs, accessible to
  anyone with log access. Combined with AP-02, the gateway key is also leaked.
Recommendation: Remove this log entirely. Never log card numbers or API keys.

### [HIGH] God Class (AP-06)
File: src/AppManager.js:1-141
Description: AppManager is a single class that handles DB schema creation,
  seed data insertion, HTTP route registration, user creation, payment
  processing, enrollment creation, audit logging, and financial report
  generation. No concern is separated.
Code snippet:
  class AppManager {
      constructor() { this.db = new sqlite3.Database(':memory:'); }
      initDb() { /* creates 5 tables + seeds data */ }
      setupRoutes(app) {
          app.post('/api/checkout', ...);
          app.get('/api/admin/financial-report', ...);
          app.delete('/api/users/:id', ...);
      }
  }
Impact: Impossible to test any single concern in isolation. Any change risks
  breaking unrelated features. No reuse possible.
Recommendation: Split into models/, controllers/, routes/, services/ per
  MVC guidelines (PT-06 + PT-08).

### [HIGH] N+1 Query Problem (AP-07)
File: src/AppManager.js:88-128
Description: The financial report iterates over every course, then for each
  course iterates over every enrollment, and inside that loop fires two
  additional queries — one for the user and one for the payment. With C courses
  and E average enrollments, this produces 1 + C + C*E*2 queries.
Code snippet:
  courses.forEach(c => {
      this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
          enrollments.forEach(enr => {
              this.db.get("SELECT name, email FROM users WHERE id = ?", [enr.user_id], (err, user) => {
                  this.db.get("SELECT amount, status FROM payments WHERE enrollment_id = ?", [enr.id], ...
              });
          });
      });
  });
Impact: With 100 courses and 50 enrollments each → 10,001 queries per report
  request. Severe performance degradation in production.
Recommendation: Replace with a single JOIN query across enrollments, users,
  and payments (PT-03).

### [HIGH] Business Logic in Wrong Layer (AP-05)
File: src/AppManager.js:43-75
Description: Payment processing, user creation, enrollment creation, and
  audit logging are all performed inline inside the route handler. The fake
  payment gateway (cc.startsWith("4")) is business logic embedded in the
  HTTP layer.
Code snippet:
  let status = cc.startsWith("4") ? "PAID" : "DENIED";
  // ... db.run INSERT enrollments, payments, audit_logs all nested here
Impact: Business rules cannot be tested independently. Payment logic is
  coupled to Express request/response objects.
Recommendation: Extract PaymentService, EnrollmentService; move logic to
  controllers and services layers (PT-06).

### [MEDIUM] Fake / Simulated External Services (AP-12)
File: src/AppManager.js:46
Description: Payment validation is faked as cc.startsWith("4") (checks if
  card starts with "4", mimicking Visa). No real payment gateway is called.
Code snippet:
  let status = cc.startsWith("4") ? "PAID" : "DENIED";
Impact: Feature appears functional in development but no real payment
  processing occurs. Hidden assumption about Visa card prefix.
Recommendation: Extract to a PaymentService stub with a clear TODO comment
  or integration point for a real gateway.

### [MEDIUM] Missing Input Validation at Boundaries (AP-11)
File: src/AppManager.js:35
Description: Only presence of usr, eml, cid, cc is checked. No validation
  that c_id is a positive integer, that card number has valid format, that
  email is a valid email, or that pwd meets minimum requirements.
Code snippet:
  if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");
Impact: Invalid data (negative course IDs, malformed emails) passes through
  to the database causing silent corruption.
Recommendation: Add field-level validation in the controller layer before
  passing to models/services.

### [MEDIUM] Global Mutable State (AP-10)
File: src/utils.js:9-10
Description: globalCache and totalRevenue are module-level mutable variables
  exported and mutated from request handlers across the app's lifetime.
Code snippet:
  let globalCache = {};
  let totalRevenue = 0;
Impact: Under concurrent requests, cache entries are overwritten
  unpredictably. totalRevenue is never updated yet exported, suggesting
  broken accounting logic.
Recommendation: Remove globalCache; use request-scoped state or a proper
  caching layer. Remove the dead totalRevenue variable.

### [MEDIUM] sqlite3 Callback API (DEP-02)
File: src/AppManager.js — throughout (lines 37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 132)
Description: All database operations use the sqlite3 callback API, resulting
  in 5-level callback pyramids (callback hell) that are hard to read, test,
  and maintain.
Code snippet:
  this.db.get("SELECT * FROM courses ...", [cid], (err, course) => {
      this.db.get("SELECT id FROM users ...", [e], (err, user) => {
          this.db.run("INSERT INTO enrollments ...", [...], function(err) {
              // 2 more levels deep
          });
      });
  });
Recommendation: Replace sqlite3 with better-sqlite3 (synchronous) or wrap
  in Promise utilities. Use async/await (PT-08).

### [LOW] Poor Naming / Cryptic Variables (AP-14)
File: src/AppManager.js:29-34
Description: All checkout request fields use single-letter or abbreviated
  names: u, e, p, cid, cc — with no documentation of what they represent.
Code snippet:
  let u = req.body.usr;
  let e = req.body.eml;
  let p = req.body.pwd;
  let cid = req.body.c_id;
  let cc = req.body.card;
Impact: Code intent is opaque. cc (card number) is especially dangerous as
  it is also logged (see AP-08).
Recommendation: Rename to name, email, password, courseId, cardNumber.

### [LOW] Unused Import (AP-15)
File: src/AppManager.js:2
Description: totalRevenue is destructured from utils but never used inside
  AppManager.js.
Code snippet:
  const { config, logAndCache, badCrypto, totalRevenue } = require('./utils');
Impact: Dead import, increases cognitive load.
Recommendation: Remove totalRevenue from the destructured import.

### [LOW] Magic Strings (AP-13)
File: src/AppManager.js:46 | src/AppManager.js:108
Description: The string "PAID" and the card prefix check "4" are magic
  literals with no named constant explaining their domain meaning.
Code snippet:
  let status = cc.startsWith("4") ? "PAID" : "DENIED";
  if (payment && payment.status === 'PAID') {
Impact: Change requires finding all occurrences. "4" as Visa prefix is
  completely undocumented.
Recommendation: Define PAYMENT_STATUS constants (PAID, DENIED) in the
  config or a constants file.

================================
Total: 13 findings
Estimated refactoring effort: High
================================
