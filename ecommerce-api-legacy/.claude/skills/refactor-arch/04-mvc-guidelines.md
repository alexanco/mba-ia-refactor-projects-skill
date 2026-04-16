# MVC Architecture Guidelines

## Core Principle

Each layer has ONE responsibility. Code belongs in exactly one layer. No layer imports from a "higher" layer (routes don't import controllers don't import routes).

```
Request → Route → Controller → Model → DB
                      ↑
               (may call Service
                for complex logic)
```

---

## Layer Definitions

### Config Layer (`config/` or `config.py`)
**Responsibility:** All configuration values. Zero business logic.

**What belongs here:**
- Database connection strings / paths
- Secret keys (loaded from environment variables via `os.environ` or `process.env`)
- External service URLs and API keys (from env)
- Port numbers
- Feature flags

**Rules:**
- NEVER hardcode secrets — always read from environment variables
- Provide sensible defaults for non-sensitive values only
- One config object/module that the rest of the app imports

**Python example:**
```python
# config/settings.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-insecure-key')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'app.db')
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
```

**Node.js example:**
```javascript
// src/config/index.js
module.exports = {
    port: process.env.PORT || 3000,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    jwtSecret: process.env.JWT_SECRET,
};
```

---

### Model Layer (`models/`)
**Responsibility:** Data structure definition and data access. Nothing else.

**What belongs here:**
- Table/collection schema definition
- CRUD operations (create, read, update, delete)
- Parameterized queries / ORM queries
- Data serialization (`to_dict()` method)
- Relationships between entities

**What does NOT belong here:**
- Business rules (pricing, discounts, workflow decisions)
- HTTP request/response handling
- Sending emails or notifications
- Logging

**Rules:**
- All SQL must use parameterized queries (`?` placeholders or `%s`)
- `to_dict()` must NEVER include passwords or sensitive fields
- One model file per domain entity (e.g., `produto_model.py`, `usuario_model.py`)

---

### Controller Layer (`controllers/`)
**Responsibility:** Orchestrate the flow between routes and models/services. Handle HTTP input/output.

**What belongs here:**
- Input parsing and validation (checking required fields, types, ranges)
- Calling the right model methods
- Formatting the HTTP response
- Error handling and HTTP status codes
- Calling services for complex operations

**What does NOT belong here:**
- Direct SQL queries
- Business calculations (delegate to services or models)
- Direct SMTP/SMS/push calls

**Rules:**
- Controllers receive validated input and return a response dict + status code (not a Flask/Express response object if possible)
- One controller file per domain (e.g., `produto_controller.py`, `pedido_controller.py`)

---

### Routes Layer (`routes/`)
**Responsibility:** Define URL patterns and HTTP methods. Wire routes to controllers.

**What belongs here:**
- `@app.route(...)` or `router.get(...)` declarations
- Middleware application (auth checks, rate limiting)
- Calling the correct controller function

**What does NOT belong here:**
- Business logic
- Direct database calls
- Data transformations

**Python/Flask example using Blueprints:**
```python
# routes/produto_routes.py
from flask import Blueprint, request, jsonify
from controllers.produto_controller import ProdutoController

produto_bp = Blueprint('produtos', __name__)
controller = ProdutoController()

@produto_bp.route('/produtos', methods=['GET'])
def listar():
    return controller.listar_produtos()

@produto_bp.route('/produtos/<int:id>', methods=['GET'])
def buscar(id):
    return controller.buscar_produto(id)
```

**Node.js/Express example:**
```javascript
// src/routes/courseRoutes.js
const express = require('express');
const router = express.Router();
const CourseController = require('../controllers/courseController');

router.get('/', CourseController.list);
router.post('/checkout', CourseController.checkout);

module.exports = router;
```

---

### Service Layer (`services/`) — Optional but recommended for complex logic
**Responsibility:** Complex business logic that doesn't fit in a single model or controller.

**What belongs here:**
- Multi-model operations (e.g., creating an order updates inventory and creates payment)
- Notification dispatching
- Report generation logic
- Third-party service integrations

---

### Middleware Layer (`middlewares/`)
**Responsibility:** Cross-cutting concerns applied to multiple routes.

**What belongs here:**
- Authentication/authorization checks
- Error handling (centralized error handler)
- Request logging
- CORS headers
- Input sanitization

---

### Entry Point (`app.py` or `index.js`)
**Responsibility:** Composition root. Wire everything together. Nothing else.

**What belongs here:**
- App instance creation
- Middleware registration
- Blueprint/router registration
- DB initialization
- Starting the server

---

## Target Directory Structures

### Python/Flask
```
project/
├── app.py                    # Entry point (composition root)
├── .env                      # Environment variables (not committed)
├── requirements.txt
├── src/
│   ├── config/
│   │   └── settings.py
│   ├── models/
│   │   ├── produto_model.py
│   │   └── usuario_model.py
│   ├── controllers/
│   │   ├── produto_controller.py
│   │   └── pedido_controller.py
│   ├── routes/
│   │   ├── produto_routes.py
│   │   └── pedido_routes.py
│   ├── services/
│   │   └── pedido_service.py
│   └── middlewares/
│       └── error_handler.py
```

### Node.js/Express
```
project/
├── index.js                  # Entry point
├── .env                      # Environment variables
├── package.json
└── src/
    ├── config/
    │   └── index.js
    ├── models/
    │   ├── userModel.js
    │   └── courseModel.js
    ├── controllers/
    │   ├── checkoutController.js
    │   └── reportController.js
    ├── routes/
    │   ├── checkoutRoutes.js
    │   └── reportRoutes.js
    ├── services/
    │   └── paymentService.js
    └── middlewares/
        └── errorHandler.js
```

### Python/Flask with Existing Partial Structure
If the project already has `models/`, `routes/`, `services/` but is missing controllers or has logic in wrong places:
- Keep existing directory names when they're already correct
- Add `controllers/` if missing
- Add `config/` if missing
- Move misplaced logic to the right layer
- Do NOT rename things that are already correct
