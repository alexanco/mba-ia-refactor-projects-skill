# ecommerce-api-legacy

LMS API com fluxo de checkout em Node.js/Express refatorada para arquitetura MVC como parte do desafio `refactor-arch`.

## Arquitetura

```
ecommerce-api-legacy/
├── src/
│   ├── app.js                      # Entry point — composição da aplicação
│   ├── config/
│   │   ├── index.js                # Toda configuração via variáveis de ambiente
│   │   └── database.js             # Inicialização e conexão SQLite
│   ├── models/
│   │   ├── userModel.js
│   │   ├── courseModel.js
│   │   ├── enrollmentModel.js
│   │   ├── paymentModel.js
│   │   └── auditLogModel.js
│   ├── controllers/
│   │   ├── checkoutController.js
│   │   ├── userController.js
│   │   └── reportController.js
│   ├── routes/
│   │   ├── checkoutRoutes.js       # POST /api/checkout
│   │   ├── userRoutes.js           # DELETE /api/users/:id
│   │   └── reportRoutes.js         # GET /api/admin/financial-report, /api/courses
│   ├── services/
│   │   ├── paymentService.js       # Lógica de processamento de pagamento
│   │   ├── enrollmentService.js    # Criação de matrícula + auditoria
│   │   └── reportService.js        # Geração do relatório financeiro com JOIN
│   └── middlewares/
│       └── errorHandler.js         # Handler de erro centralizado
├── data/
│   └── lms.db                      # Banco SQLite persistido
├── .env.example
├── package.json
└── reports/
    └── audit-ecommerce-api-legacy.md
```

## Como rodar

**1. Instale as dependências:**

```bash
npm install
```

**2. Configure as variáveis de ambiente:**

```bash
cp .env.example .env
# Edite .env — defina PAYMENT_GATEWAY_KEY para integração real
```

**3. Suba a API:**

```bash
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite (`data/lms.db`) é criado automaticamente no boot com cursos e um usuário seed.

## Variáveis de ambiente

| Variável               | Padrão      | Descrição                                   |
|------------------------|-------------|---------------------------------------------|
| `PORT`                 | `3000`      | Porta da aplicação                          |
| `DB_PATH`              | `:memory:`  | Caminho do SQLite (use `data/lms.db` para persistir) |
| `PAYMENT_GATEWAY_KEY`  | —           | Chave do gateway de pagamento               |

## Endpoints

### Checkout

| Método | Rota              | Descrição                                              |
|--------|-------------------|--------------------------------------------------------|
| POST   | `/api/checkout`   | Processa matrícula: valida pagamento, cria usuário se necessário, registra matrícula e pagamento |

**Body:**
```json
{
  "usr": "Nome Completo",
  "eml": "email@exemplo.com",
  "pwd": "senha",
  "c_id": 1,
  "card": "4111111111111111"
}
```

### Cursos

| Método | Rota           | Descrição              |
|--------|----------------|------------------------|
| GET    | `/api/courses` | Lista todos os cursos  |

### Usuários

| Método | Rota                 | Descrição           |
|--------|----------------------|---------------------|
| DELETE | `/api/users/:id`     | Remove um usuário   |

### Relatórios

| Método | Rota                          | Descrição                                         |
|--------|-------------------------------|---------------------------------------------------|
| GET    | `/api/admin/financial-report` | Relatório financeiro com receita por curso via JOIN único |

## Melhorias aplicadas (refactor-arch)

- **Segurança:** `badCrypto()` substituído por `bcryptjs.hash()`; credenciais de gateway, banco e SMTP movidas para variáveis de ambiente; `console.log(cardNumber, gatewayKey)` removido
- **Arquitetura MVC:** `AppManager` (141 linhas, 8 responsabilidades) decomposto em `models/`, `controllers/`, `routes/` e `services/` por domínio
- **Performance:** N+1 queries no relatório financeiro (até 10.001 queries) substituídas por JOIN único em `reportService.js`
- **Qualidade:** callback hell de 5 níveis substituído por `async/await` com `better-sqlite3`; lógica de pagamento extraída para `paymentService.js`; lógica de matrícula extraída para `enrollmentService.js`; error handler centralizado

O relatório completo de auditoria está em [`reports/audit-ecommerce-api-legacy.md`](reports/audit-ecommerce-api-legacy.md).
