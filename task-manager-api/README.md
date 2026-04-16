# task-manager-api

API de Task Manager em Python/Flask refatorada para arquitetura MVC completa como parte do desafio `refactor-arch`.

## Arquitetura

```
task-manager-api/
├── app.py                          # Entry point — composição da aplicação
├── database.py                     # Instância do SQLAlchemy
├── seed.py                         # Popula o banco com dados de exemplo
├── .env.example                    # Template de variáveis de ambiente
├── requirements.txt
├── config/
│   └── settings.py                 # Toda configuração via variáveis de ambiente
├── controllers/
│   ├── task_controller.py          # CRUD + busca + stats de tasks
│   ├── user_controller.py          # CRUD + login de usuários
│   ├── category_controller.py      # CRUD de categorias
│   └── report_controller.py        # Relatórios com GROUP BY
├── models/
│   ├── task.py                     # Entidade Task + is_overdue()
│   ├── user.py                     # Entidade User + bcrypt
│   └── category.py                 # Entidade Category
├── routes/
│   ├── task_routes.py              # Blueprint /tasks (delega ao controller)
│   ├── user_routes.py              # Blueprint /users + /login
│   └── report_routes.py            # Blueprint /reports + /categories
├── services/
│   └── notification_service.py     # Envio de e-mail via SMTP (env vars)
├── middlewares/
│   └── error_handler.py            # Handlers centralizados 400/404/405/500
├── utils/
│   └── helpers.py                  # Constantes e funções utilitárias
└── reports/
    └── audit-task-manager-api.md
```

## Como rodar

**1. Crie um ambiente virtual e instale as dependências:**

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Configure as variáveis de ambiente:**

```bash
cp .env.example .env
# Edite .env — defina SECRET_KEY em produção
```

**3. Popule o banco e suba a API:**

```bash
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`.

## Variáveis de ambiente

| Variável        | Padrão                  | Descrição                        |
|-----------------|-------------------------|----------------------------------|
| `SECRET_KEY`    | `dev-only-insecure-key` | Chave secreta do Flask           |
| `DATABASE_URL`  | `sqlite:///tasks.db`    | URI do banco de dados            |
| `FLASK_DEBUG`   | `false`                 | Ativa o modo debug               |
| `SMTP_HOST`     | `smtp.gmail.com`        | Host do servidor SMTP            |
| `SMTP_PORT`     | `587`                   | Porta SMTP                       |
| `SMTP_USER`     | —                       | Usuário SMTP (e-mail remetente)  |
| `SMTP_PASSWORD` | —                       | Senha do servidor SMTP           |

## Endpoints

### Tasks

| Método | Rota                | Descrição                                       |
|--------|---------------------|-------------------------------------------------|
| GET    | `/tasks`            | Lista todas as tasks (com user_name e category_name via joinedload) |
| GET    | `/tasks/<id>`       | Retorna uma task                                |
| POST   | `/tasks`            | Cria uma task                                   |
| PUT    | `/tasks/<id>`       | Atualiza uma task                               |
| DELETE | `/tasks/<id>`       | Remove uma task                                 |
| GET    | `/tasks/search`     | Busca por `q`, `status`, `priority`, `user_id`  |
| GET    | `/tasks/stats`      | Contagens por status + taxa de conclusão        |

### Usuários

| Método | Rota                    | Descrição                       |
|--------|-------------------------|---------------------------------|
| GET    | `/users`                | Lista todos os usuários         |
| GET    | `/users/<id>`           | Retorna usuário com suas tasks  |
| POST   | `/users`                | Cria um usuário                 |
| PUT    | `/users/<id>`           | Atualiza um usuário             |
| DELETE | `/users/<id>`           | Remove usuário e suas tasks     |
| GET    | `/users/<id>/tasks`     | Tasks de um usuário             |
| POST   | `/login`                | Autenticação                    |

### Categorias

| Método | Rota                    | Descrição                       |
|--------|-------------------------|---------------------------------|
| GET    | `/categories`           | Lista categorias com task_count |
| POST   | `/categories`           | Cria uma categoria              |
| PUT    | `/categories/<id>`      | Atualiza uma categoria          |
| DELETE | `/categories/<id>`      | Remove uma categoria            |

### Relatórios

| Método | Rota                    | Descrição                                           |
|--------|-------------------------|-----------------------------------------------------|
| GET    | `/reports/summary`      | Visão geral: status, prioridade, overdue, produtividade por usuário (GROUP BY) |
| GET    | `/reports/user/<id>`    | Relatório individual de um usuário                  |

### Utilitários

| Método | Rota      | Descrição          |
|--------|-----------|--------------------|
| GET    | `/`       | Informações da API |
| GET    | `/health` | Health check       |

## Melhorias aplicadas (refactor-arch)

- **Segurança:** `hashlib.md5` substituído por `werkzeug generate_password_hash` (bcrypt); fake JWT token removido; credenciais SMTP movidas para variáveis de ambiente; campo `password` removido de todas as respostas da API
- **Arquitetura MVC:** lógica de negócio, validação e acesso a banco extraídos das rotas para controllers dedicados; rotas reduzidas a declarações puras
- **Performance:** N+1 em `GET /tasks` eliminado via `joinedload(Task.user, Task.category)`; N+1 no relatório de produtividade substituído por `GROUP BY` com `sqlalchemy.case`
- **Qualidade:** lógica de overdue centralizada em `Task.is_overdue()` (era duplicada em 6 lugares); `datetime.utcnow()` substituído por `datetime.now(timezone.utc)`; `Model.query.get()` substituído por `db.session.get()`; error handlers centralizados em `middlewares/error_handler.py`

O relatório completo de auditoria está em [`reports/audit-task-manager-api.md`](reports/audit-task-manager-api.md).
