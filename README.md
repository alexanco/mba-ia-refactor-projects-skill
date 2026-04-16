# Desafio — Refatoração Arquitetural Automatizada com Skill

> Documentação do processo de criação e execução da skill `refactor-arch` nos 3 projetos legados.

**Ferramenta:** Claude Code | **Skill:** `.claude/skills/refactor-arch/`

---

## A) Análise Manual

Análise realizada diretamente no código-fonte de cada projeto **antes de qualquer refatoração**, para entender os problemas que a skill precisaria detectar.

---

### Projeto 1 — `code-smells-project` (Python/Flask — E-commerce API)

| Severidade | Problema | Arquivo / Linha | Por que é relevante |
|---|---|---|---|
| CRITICAL | **SQL Injection generalizado** | `models.py:28,48,109,289` | Todas as queries usam concatenação de strings com dados do usuário. O login é vulnerável a bypass com `' OR '1'='1` — comprometimento total do banco em produção. |
| CRITICAL | **Credenciais hardcoded** | `app.py:7`, `database.py:75-83` | `SECRET_KEY` e senhas de usuários seed em plaintext commitados. Qualquer pessoa com acesso ao repositório tem as credenciais. |
| CRITICAL | **Admin endpoints sem autenticação** | `app.py:47-78` | `/admin/reset-db` apaga todas as tabelas e `/admin/query` executa SQL arbitrário via POST, sem nenhuma verificação de identidade. |
| CRITICAL | **Senhas em plaintext** | `models.py:122-131` | `criar_usuario()` insere a senha diretamente no banco sem hash. Um dump expõe todas as senhas reais. |
| HIGH | **God Files** | `controllers.py` (293 linhas), `models.py` (315 linhas) | Um único arquivo de controllers gerencia produtos, usuários, pedidos e relatórios. Qualquer mudança implica risco de quebrar domínios não relacionados. |
| HIGH | **N+1 Queries** | `models.py:186-200` | Para cada pedido: query para itens + query por produto de cada item. 10 pedidos com 3 itens = 41 queries. |
| HIGH | **Regras de negócio na camada errada** | `models.py:256-272` | Lógica de desconto (thresholds de faturamento) dentro da camada de dados. Impossível testar em isolamento. |
| MEDIUM | **Código duplicado** | `controllers.py:29-36,73-79` | Validação de campos de produto copiada entre `criar_produto` e `atualizar_produto`. Bug deve ser corrigido em 2 lugares. |
| MEDIUM | **Estado global mutável** | `database.py:4-10` | Conexão SQLite compartilhada com `check_same_thread=False`. Sob concorrência: dados corrompidos ou "database is locked". |
| LOW | **Rotas via `add_url_rule()`** | `app.py:11-30` | 14 rotas registradas manualmente no entry point em vez de Blueprints. Dificulta escala e organização. |

---

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express — LMS com checkout)

| Severidade | Problema | Arquivo / Linha | Por que é relevante |
|---|---|---|---|
| CRITICAL | **Credenciais hardcoded** | `src/utils.js:2-6` | Chave de gateway de pagamento live (`pk_live_...`), senha do banco e usuário SMTP em código-fonte. Comprometimento imediato em repo público. |
| CRITICAL | **Criptografia quebrada** | `src/utils.js:17-23`, `src/AppManager.js:18` | `badCrypto()` concatena prefixos base64 em loop — não é hash. Usuário seed tem senha `'123'` em plaintext no banco. |
| CRITICAL | **Dados sensíveis em logs** | `src/AppManager.js:45` | Número do cartão e chave do gateway são `console.log()`'d em toda requisição de checkout. Violação direta de PCI-DSS. |
| HIGH | **God Class** | `src/AppManager.js:1-141` | Uma classe única: schema, seed, rotas HTTP, pagamento, matrícula, auditoria e relatório financeiro. Zero separação de responsabilidades. |
| HIGH | **N+1 Queries no relatório** | `src/AppManager.js:88-128` | Para cada curso → para cada matrícula → 2 queries (usuário + pagamento). 100 cursos × 50 matrículas = 10.001 queries por requisição. |
| HIGH | **Lógica de negócio na rota** | `src/AppManager.js:43-75` | Validação de pagamento, criação de usuário, matrícula e auditoria inline no handler HTTP, acoplados ao `req/res`. |
| MEDIUM | **Callback hell** | `src/AppManager.js` (geral) | 5 níveis de callbacks aninhados no checkout. Impossível adicionar tratamento de erro ou testar. |
| MEDIUM | **Estado global mutável** | `src/utils.js:9-10` | `globalCache` e `totalRevenue` são variáveis de módulo mutadas de handlers concorrentes. |
| LOW | **Nomes crípticos** | `src/AppManager.js:29-34` | Variáveis `u`, `e`, `p`, `cid`, `cc` sem documentação. `cc` (número do cartão) aparece em log — o nome opaco mascara o risco. |

---

### Projeto 3 — `task-manager-api` (Python/Flask — Task Manager)

| Severidade | Problema | Arquivo / Linha | Por que é relevante |
|---|---|---|---|
| CRITICAL | **Credenciais hardcoded** | `app.py:13`, `services/notification_service.py:8-10` | `SECRET_KEY = 'super-secret-key-123'` e credenciais SMTP (`senha123`) em código-fonte commitado. |
| CRITICAL | **Criptografia fraca + token falso** | `models/user.py:29`, `routes/user_routes.py:210` | MD5 é reversível com rainbow tables em segundos. Token `'fake-jwt-token-1'` permite impersonation trivial por qualquer cliente. |
| HIGH | **Lógica de negócio nas rotas** | `routes/task_routes.py:88-154` | Validação, cálculo de overdue e commit de banco dentro dos handlers. Impossível testar sem HTTP client. |
| HIGH | **N+1 Queries em GET /tasks** | `routes/task_routes.py:41-57` | Uma query por tarefa para nome do usuário + uma por tarefa para nome da categoria. N tarefas = 2N+1 queries. |
| HIGH | **Senha exposta na API** | `models/user.py:16-26` | `to_dict()` inclui o campo `password` (hash MD5) em todas as respostas — usuários, login, criação. |
| MEDIUM | **Código duplicado** | 6 locais em `task_routes.py`, `user_routes.py`, `report_routes.py`, `models/task.py` | Lógica de verificação de overdue copiada em 6 lugares. Mudança de regra requer editar todos. |
| MEDIUM | **API SQLAlchemy deprecated** | 8 locais (routes/) | `Model.query.get(id)` deprecated no SQLAlchemy 2.x — usada em toda operação de busca por ID. |
| LOW | **Imports não utilizados** | `routes/task_routes.py:7`, `app.py:7` | `import json, os, sys, time` em arquivos que não os usam. Aumenta carga cognitiva. |

---

## B) Construção da Skill

### Estrutura dos arquivos de referência

A skill foi organizada em 5 arquivos Markdown, cada um cobrindo uma área de conhecimento obrigatória:

```
.claude/skills/refactor-arch/
├── SKILL.md                    ← Prompt principal com as 3 fases e regras de execução
├── 01-project-analysis.md      ← Heurísticas de detecção de linguagem, framework e arquitetura
├── 02-antipatterns-catalog.md  ← Catálogo de 16 anti-patterns + 4 deprecated APIs
├── 03-audit-report-template.md ← Template padronizado do relatório de auditoria
├── 04-mvc-guidelines.md        ← Definição das camadas MVC e estruturas-alvo por stack
└── 05-refactoring-playbook.md  ← 12 padrões de transformação com exemplos before/after
```

A separação em 5 arquivos foi intencional: cada arquivo tem escopo bem delimitado, evitando que o modelo misture heurísticas de análise com regras de refatoração na mesma leitura. O `SKILL.md` instrui explicitamente quais arquivos ler em cada fase.

### Anti-patterns incluídos no catálogo e por quê

| Severidade | IDs | Critério de inclusão |
|---|---|---|
| CRITICAL | AP-01 SQL Injection, AP-02 Credentials, AP-03 Admin Endpoints, AP-04 Weak Crypto | Presentes em pelo menos 2 dos 3 projetos; impacto de segurança direto e imediato |
| HIGH | AP-05 Business Logic Wrong Layer, AP-06 God Class, AP-07 N+1 Queries, AP-08 Sensitive Data | Violações do core MVC ou problemas de performance severa |
| MEDIUM | AP-09 Duplicate Code, AP-10 Global State, AP-11 Missing Validation, AP-12 Fake Services | Problemas de manutenção e confiabilidade que não bloqueiam mas acumulam dívida técnica |
| LOW | AP-13 Magic Numbers, AP-14 Poor Naming, AP-15 Unused Imports, AP-16 Bare Except | Qualidade de código — impacto em legibilidade e debugging |
| Deprecated | DEP-01 SQLAlchemy `Query.get()`, DEP-02 sqlite3 callbacks, DEP-03 Flask `add_url_rule`, DEP-04 `datetime.utcnow()` | APIs obsoletas detectáveis por padrão de código preciso |

O catálogo propositalmente evita "código ruim" genérico — cada entry tem **sinais de detecção exatos** (pattern de código a procurar), não descrições vagas.

### Como a skill é agnóstica de tecnologia

Três mecanismos garantem que funciona independente da stack:

1. **`01-project-analysis.md` com tabelas por linguagem:** sinais distintos para Python (`requirements.txt`, `from flask import`) e Node.js (`package.json`, `require('express')`), com detecção de framework e versão.

2. **`02-antipatterns-catalog.md` com variantes por linguagem:** cada anti-pattern lista exemplos de código em Python *e* JavaScript/Node.js, permitindo detecção correta em ambas as stacks.

3. **`04-mvc-guidelines.md` com estruturas-alvo por stack:** diretórios-alvo separados para Python/Flask e Node.js/Express, mais uma seção "Python/Flask with Existing Partial Structure" que instrui o modelo a não sobrescrever diretórios já corretos.

### Desafios encontrados e como foram resolvidos

| Desafio | Solução |
|---|---|
| Skill criava `src/` mesmo em projetos com diretórios raiz já existentes | Adicionada seção "Existing Partial Structure" no `04-mvc-guidelines.md` instruindo a preservar diretórios corretos |
| Números de linha imprecisos no relatório | Adicionada regra explícita em `03-audit-report-template.md`: "Code snippet must contain actual lines from the file (not paraphrased)" |
| N+1 fix no Node.js gerava callback hell mais profundo ao adicionar JOIN | Incluído PT-08 (Eliminate Callback Hell) como transformação separada no playbook, obrigando resolução conjunta |
| `datetime.utcnow()` — nova API gera incompatibilidade com timestamps naive no SQLite | Adotada abordagem `datetime.now(timezone.utc).replace(tzinfo=None)` que usa API moderna mas mantém naive timestamps para compatibilidade com banco existente |

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total | Esforço |
|---|---|---|---|---|---|---|---|
| `code-smells-project` | Python/Flask | 4 | 4 | 3 | 3 | **14** | High |
| `ecommerce-api-legacy` | Node.js/Express | 3 | 3 | 4 | 3 | **13** | High |
| `task-manager-api` | Python/Flask | 2 | 3 | 4 | 3 | **12** | High |
| **Total** | — | **9** | **10** | **11** | **9** | **39** | — |

Relatórios completos: [`reports/audit-project-1.md`](reports/audit-project-1.md) | [`reports/audit-project-2.md`](reports/audit-project-2.md) | [`reports/audit-project-3.md`](reports/audit-project-3.md)

---

### Comparação antes/depois da estrutura

#### Projeto 1 — `code-smells-project`

```
ANTES                           DEPOIS
────────────────────────────    ────────────────────────────────────────
app.py                          app.py  (entry point limpo)
controllers.py  (293 linhas)    src/
models.py       (315 linhas)    ├── config/settings.py
database.py                     ├── models/produto_model.py
                                │           usuario_model.py
                                ├── controllers/produto_controller.py
                                │             usuario_controller.py
                                │             pedido_controller.py
                                ├── routes/produto_routes.py (Blueprint)
                                │         pedido_routes.py
                                ├── services/notification_service.py
                                │           relatorio_service.py
                                └── middlewares/error_handler.py
```

| Antes | Depois |
|---|---|
| SQL via concatenação de strings | Queries parametrizadas com `?` |
| Senhas em plaintext no banco | `werkzeug.security generate_password_hash` |
| `/admin/query` executa SQL arbitrário | Endpoint removido |
| 14 rotas em `app.add_url_rule()` | Blueprints por domínio |
| Conexão SQLite global compartilhada | Conexão por requisição via `flask.g` |

#### Projeto 2 — `ecommerce-api-legacy`

```
ANTES                           DEPOIS
────────────────────────────    ────────────────────────────────────────
src/app.js                      index.js  (entry point)
src/AppManager.js (141 linhas)  src/
src/utils.js                    ├── config/index.js  (env vars)
                                ├── models/userModel.js
                                │         courseModel.js
                                ├── controllers/checkoutController.js
                                │             reportController.js
                                ├── routes/checkoutRoutes.js
                                │        reportRoutes.js
                                └── services/paymentService.js
```

| Antes | Depois |
|---|---|
| `badCrypto()` (base64 loop) | `bcryptjs.hash()` |
| Chave de gateway em `utils.js` | `process.env.PAYMENT_GATEWAY_KEY` |
| `console.log(cardNumber, key)` | Log removido |
| 5 níveis de callback aninhado | `async/await` com `better-sqlite3` |
| N+1: até 10.001 queries por relatório | JOIN único |

#### Projeto 3 — `task-manager-api`

```
ANTES                           DEPOIS
────────────────────────────    ────────────────────────────────────────
app.py                          app.py  (usa Config, registra middlewares)
database.py                     config/settings.py  (novo)
models/task.py                  controllers/task_controller.py  (novo)
models/user.py    ←MD5          controllers/user_controller.py  (novo)
models/category.py              controllers/category_controller.py (novo)
routes/task_routes.py  ←fat     controllers/report_controller.py (novo)
routes/user_routes.py  ←fat     middlewares/error_handler.py  (novo)
routes/report_routes.py ←fat    routes/*.py  (finos — só declarações)
services/notification_service.py models/user.py  ←bcrypt, sem password
utils/helpers.py                models/task.py  ←is_overdue() único
config/  (vazio)
controllers/  (vazio)
middlewares/  (vazio)
```

| Antes | Depois |
|---|---|
| `hashlib.md5` + fake JWT | `werkzeug` bcrypt, token removido |
| `password` em toda resposta API | Removido de `to_dict()` |
| N+1 em `GET /tasks` (2N+1 queries) | `joinedload(Task.user, Task.category)` |
| N+1 no relatório (M+1 queries) | `GROUP BY` com `sqlalchemy.case` |
| `datetime.utcnow()` deprecated | `datetime.now(timezone.utc)` |
| `Model.query.get()` deprecated | `db.session.get(Model, id)` |
| Lógica de overdue em 6 lugares | `Task.is_overdue()` — um único local |

---

### Checklist de validação

#### Projeto 1 — `code-smells-project`

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio descrito corretamente (E-commerce API — produtos, pedidos, usuários)
- [x] Número de arquivos condiz (4 arquivos-fonte)

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] 14 findings identificados (mínimo exigido: 5)
- [x] APIs deprecated incluídas (DEP-03 Flask `add_url_rule`)
- [x] Skill pausou e pediu confirmação `[y/n]` antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura MVC criada com `src/models/`, `src/controllers/`, `src/routes/`, `src/services/`
- [x] Config extraída para `src/config/settings.py` sem hardcoded secrets
- [x] Error handling centralizado em `src/middlewares/error_handler.py`
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

#### Projeto 2 — `ecommerce-api-legacy`

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (JavaScript/Node.js)
- [x] Framework detectado corretamente (Express)
- [x] Domínio descrito corretamente (LMS — cursos, checkout, matrículas)
- [x] Número de arquivos condiz (3 arquivos-fonte)

**Fase 2 — Auditoria**
- [x] Relatório segue o template
- [x] Findings com arquivo e linhas exatos
- [x] Ordenados por severidade
- [x] 13 findings identificados
- [x] APIs deprecated incluídas (DEP-02 sqlite3 callback API)
- [x] Skill pausou e pediu confirmação

**Fase 3 — Refatoração**
- [x] Estrutura Node.js MVC criada (`src/models/`, `src/controllers/`, `src/routes/`, `src/services/`)
- [x] Secrets movidos para `.env` via `process.env`
- [x] Callback hell eliminado com `async/await`
- [x] Aplicação inicia sem erros
- [x] Endpoints `/api/checkout`, `/api/admin/financial-report` e `/api/users/:id` respondem

#### Projeto 3 — `task-manager-api`

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.0.0 + SQLAlchemy 3.1.1)
- [x] Domínio descrito corretamente (Task Manager — tasks, users, categories)
- [x] 10 arquivos analisados

**Fase 2 — Auditoria**
- [x] Relatório segue o template
- [x] Findings com arquivo e linhas exatos
- [x] Ordenados por severidade
- [x] 12 findings (incluindo problemas em projeto parcialmente organizado)
- [x] APIs deprecated incluídas (DEP-01 `Query.get()`, DEP-04 `datetime.utcnow()`)
- [x] Skill pausou e pediu confirmação

**Fase 3 — Refatoração**
- [x] Controllers criados nos diretórios já existentes (sem criar `src/` desnecessário)
- [x] Config extraída para `config/settings.py`
- [x] Error handlers centralizados em `middlewares/error_handler.py`
- [x] Aplicação inicia sem erros
- [x] Todos os endpoints respondem corretamente

---

### Logs de validação (aplicações rodando após refatoração)

**Projeto 1 — `code-smells-project`**
```
$ python app.py
 * Running on http://0.0.0.0:5000

$ curl http://localhost:5000/produtos
[{"id":1,"nome":"Notebook Pro","preco":2999.99,...}]

$ curl http://localhost:5000/health
{"database":"connected","status":"ok","version":"1.0.0"}
# secret_key e db_path removidos da resposta

$ curl -X POST http://localhost:5000/login \
    -d '{"email":"joao@email.com","senha":"123456"}'
{"token":"...","usuario":{"email":"joao@email.com","id":2,"nome":"João Silva","tipo":"cliente"}}
# senha não retorna no payload
```

**Projeto 2 — `ecommerce-api-legacy`**
```
$ node index.js
Server running on port 3000

$ curl http://localhost:3000/api/courses
[{"id":1,"title":"Fullcycle 3.0","price":1997,"active":1}]

$ curl -X POST http://localhost:3000/api/checkout \
    -H "Content-Type: application/json" \
    -d '{"usr":"Test","eml":"t@test.com","pwd":"pass","c_id":1,"card":"4111111111111111"}'
{"message":"Matrícula realizada com sucesso","enrollment_id":1,"status":"PAID"}
# sem console.log de cardNumber ou gatewayKey
```

**Projeto 3 — `task-manager-api`**
```
$ python app.py
 * Running on http://0.0.0.0:5000

$ curl http://localhost:5000/
{"message":"Task Manager API","version":"1.0"}

$ curl http://localhost:5000/health
{"status":"ok","timestamp":"2026-04-16 22:30:13.274669+00:00"}

$ curl -X POST http://localhost:5000/users \
    -H "Content-Type: application/json" \
    -d '{"name":"Test","email":"t@t.com","password":"1234","role":"user"}'
{"active":true,"created_at":"...","email":"t@t.com","id":1,"name":"Test","role":"user"}
# campo "password" ausente da resposta

$ curl -X POST http://localhost:5000/login \
    -H "Content-Type: application/json" \
    -d '{"email":"t@t.com","password":"1234"}'
{"message":"Login realizado com sucesso","user":{"active":true,"email":"t@t.com","id":1,...}}
# sem password hash, sem fake token

$ curl http://localhost:5000/tasks/stats
{"cancelled":0,"completion_rate":0.0,"done":0,"in_progress":0,"overdue":0,"pending":1,"total":1}
```

---

### Observações sobre comportamento em stacks diferentes

- **Python/Flask com SQLite raw (`code-smells-project`):** a skill identificou SQL injection via concatenação mesmo sem ORM. O playbook PT-01 foi aplicado diretamente com placeholders `?` no módulo `sqlite3`.

- **Node.js/Express (`ecommerce-api-legacy`):** a skill adaptou a estrutura para convenção Node.js (`src/config/index.js` em vez de `config/settings.py`) e substituiu callbacks por `async/await` com `better-sqlite3`, conforme PT-08. A detecção de `badCrypto()` como AP-04 (Weak Crypto) foi correta mesmo sendo uma função customizada.

- **Python/Flask com ORM e estrutura parcial (`task-manager-api`):** a skill reconheceu os diretórios `controllers/`, `config/` e `middlewares/` já existentes (mas vazios) e os populou sem criar hierarquia `src/` desnecessária — comportamento correto da seção "Existing Partial Structure" do `04-mvc-guidelines.md`.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado (`npm install -g @anthropic-ai/claude-code`) e autenticado
- Python 3.10+ com suporte a `venv`
- Node.js 18+
- Conta Anthropic com acesso à API

### Executar a skill nos 3 projetos

```bash
# Clone o repositório
git clone <url-do-fork>
cd mba-ia-refactor-projects-skill

# ── Projeto 1 — Python/Flask (E-commerce) ──────────────────
cd code-smells-project
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
claude "/refactor-arch"
# Fase 1 imprime análise → Fase 2 imprime relatório e pausa
# Digite "y" para executar a Fase 3

# ── Projeto 2 — Node.js/Express (LMS) ──────────────────────
cd ../ecommerce-api-legacy
npm install
claude "/refactor-arch"

# ── Projeto 3 — Python/Flask (Task Manager) ────────────────
cd ../task-manager-api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
claude "/refactor-arch"
```

### Como validar que a refatoração funcionou

```bash
# ── Projeto 1 ───────────────────────────────────────────────
cd code-smells-project && python app.py &
curl http://localhost:5000/produtos          # deve retornar lista de produtos
curl http://localhost:5000/health            # NÃO deve conter "secret_key"
curl -X POST http://localhost:5000/login \
  -d '{"email":"joao@email.com","senha":"123456"}'
# resposta NÃO deve conter campo "senha"

# ── Projeto 2 ───────────────────────────────────────────────
cd ../ecommerce-api-legacy && node index.js &
curl http://localhost:3000/api/courses
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"usr":"Test","eml":"t@t.com","pwd":"pass","c_id":1,"card":"4111111111111111"}'
# logs NÃO devem exibir número do cartão

# ── Projeto 3 ───────────────────────────────────────────────
cd ../task-manager-api && python seed.py && python app.py &
curl http://localhost:5000/tasks
curl http://localhost:5000/reports/summary   # user_productivity via GROUP BY
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"1234"}'
# resposta NÃO deve conter "password" nem "fake-jwt-token"
```

### Relatórios gerados

| Arquivo | Projeto |
|---|---|
| [`reports/audit-project-1.md`](reports/audit-project-1.md) | code-smells-project |
| [`reports/audit-project-2.md`](reports/audit-project-2.md) | ecommerce-api-legacy |
| [`reports/audit-project-3.md`](reports/audit-project-3.md) | task-manager-api |

---

# Criação de Skills — Refatoração Arquitetural Automatizada

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.