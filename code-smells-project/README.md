# code-smells-project

API de E-commerce em Python/Flask refatorada para arquitetura MVC como parte do desafio `refactor-arch`.

## Arquitetura

```
code-smells-project/
├── app.py                          # Entry point — composição da aplicação
├── .env.example                    # Template de variáveis de ambiente
├── requirements.txt
├── src/
│   ├── config/
│   │   └── settings.py             # Toda configuração via variáveis de ambiente
│   ├── models/
│   │   ├── database.py             # Conexão e inicialização do SQLite
│   │   ├── produto_model.py
│   │   ├── usuario_model.py
│   │   └── pedido_model.py
│   ├── controllers/
│   │   ├── produto_controller.py
│   │   ├── usuario_controller.py
│   │   ├── pedido_controller.py
│   │   └── system_controller.py
│   ├── routes/
│   │   ├── produto_routes.py       # Blueprint /produtos
│   │   ├── usuario_routes.py       # Blueprint /usuarios
│   │   ├── pedido_routes.py        # Blueprint /pedidos
│   │   ├── admin_routes.py         # Blueprint /admin (somente DEBUG)
│   │   └── system_routes.py        # Blueprint / e /health
│   ├── services/
│   │   ├── notification_service.py
│   │   └── relatorio_service.py    # Lógica de desconto e relatórios
│   └── middlewares/
│       └── error_handler.py        # Handlers centralizados 400/404/500
└── reports/
    └── audit-code-smells-project.md
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
# Edite .env — defina ao menos SECRET_KEY em produção
```

**3. Suba a API:**

```bash
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot com produtos, usuários e categorias de exemplo.

## Variáveis de ambiente

| Variável        | Padrão                               | Descrição                        |
|-----------------|--------------------------------------|----------------------------------|
| `SECRET_KEY`    | `dev-only-change-in-production`      | Chave secreta do Flask           |
| `DATABASE_PATH` | `loja.db`                            | Caminho do arquivo SQLite        |
| `FLASK_DEBUG`   | `false`                              | Ativa o modo debug               |

## Endpoints

### Produtos

| Método | Rota                   | Descrição                              |
|--------|------------------------|----------------------------------------|
| GET    | `/produtos`            | Lista todos os produtos                |
| GET    | `/produtos/<id>`       | Retorna um produto                     |
| POST   | `/produtos`            | Cria um produto                        |
| PUT    | `/produtos/<id>`       | Atualiza um produto                    |
| DELETE | `/produtos/<id>`       | Remove um produto                      |
| GET    | `/produtos/buscar`     | Busca por `q` (nome/descrição) e `categoria` |

### Usuários

| Método | Rota                   | Descrição                              |
|--------|------------------------|----------------------------------------|
| GET    | `/usuarios`            | Lista todos os usuários                |
| GET    | `/usuarios/<id>`       | Retorna um usuário                     |
| POST   | `/usuarios`            | Cria um usuário                        |
| PUT    | `/usuarios/<id>`       | Atualiza um usuário                    |
| DELETE | `/usuarios/<id>`       | Remove um usuário                      |
| POST   | `/login`               | Autenticação                           |

### Pedidos

| Método | Rota                          | Descrição                        |
|--------|-------------------------------|----------------------------------|
| GET    | `/pedidos`                    | Lista todos os pedidos           |
| GET    | `/pedidos/<id>`               | Retorna um pedido                |
| POST   | `/pedidos`                    | Cria um pedido                   |
| GET    | `/pedidos/usuario/<user_id>`  | Pedidos de um usuário            |
| GET    | `/relatorio/vendas`           | Relatório de vendas com desconto |

### Utilitários

| Método | Rota              | Descrição                                  |
|--------|-------------------|--------------------------------------------|
| GET    | `/`               | Informações da API                         |
| GET    | `/health`         | Health check                               |
| POST   | `/admin/reset-db` | Reset do banco (somente `FLASK_DEBUG=true`)|

## Melhorias aplicadas (refactor-arch)

- **Segurança:** SQL injection eliminado — todas as queries usam placeholders `?`; senhas migradas de plaintext para `werkzeug generate_password_hash`; credenciais movidas para variáveis de ambiente; `/admin/query` removido; `/admin/reset-db` bloqueado fora do modo debug
- **Arquitetura MVC:** god files (`controllers.py` 293 linhas, `models.py` 315 linhas) decompostos em módulos por domínio dentro de `src/`; rotas migradas de `app.add_url_rule()` para Blueprints
- **Performance:** N+1 queries nos pedidos substituídas por JOIN único em `pedido_model.py`
- **Qualidade:** lógica de desconto extraída para `relatorio_service.py`; conexão SQLite por requisição via `flask.g`; error handlers centralizados; senha removida das respostas da API

O relatório completo de auditoria está em [`reports/audit-code-smells-project.md`](reports/audit-code-smells-project.md).
