# Criação de Skills — Refatoração Arquitetural Automatizada

Skill `refactor-arch` para Claude Code que analisa, audita e refatora projetos legados para o padrão MVC em 3 fases sequenciais, de forma agnóstica de tecnologia.

---

## Análise Manual

Análise manual realizada antes da criação da skill para identificar padrões a detectar automaticamente.

### Projeto 1 — code-smells-project (Python/Flask — E-commerce API)

| # | Severidade | Arquivo:Linha | Problema | Justificativa |
|---|---|---|---|---|
| 1 | **CRITICAL** | models.py:28,47-50,109-110,289-295 | **SQL Injection** — todas as queries construídas por concatenação de strings | Qualquer parâmetro de URL ou JSON pode injetar SQL arbitrário; `login_usuario` é bypassável com `' OR '1'='1` |
| 2 | **CRITICAL** | app.py:59-78 | **Endpoint `/admin/query` sem autenticação** — executa SQL arbitrário enviado pelo cliente | Equivale a acesso root ao banco de dados para qualquer pessoa na rede |
| 3 | **CRITICAL** | app.py:7, controllers.py:289 | **Credenciais hardcoded + SECRET_KEY exposta na API** | SECRET_KEY comprometida quebra toda segurança de sessão; chave exposta via `/health` é crítico |
| 4 | **HIGH** | database.py:75-83 | **Senhas em plaintext no seed** — `"admin123"`, `"123456"` sem hash | Uma leitura do banco entrega todas as senhas; violação direta de OWASP A02 |
| 5 | **HIGH** | models.py:171-233 | **N+1 Queries** — 3 cursors aninhados por pedido: `pedidos` → `itens_pedido` → `produtos` | 100 pedidos com 5 itens = 601 queries; degrada O(N×M) |
| 6 | **MEDIUM** | models.py:235-273 | **Lógica de negócio no Model** — cálculo de desconto e relatório financeiro na camada de dados | Regras de desconto não podem ser testadas em isolamento nem reusadas |
| 7 | **MEDIUM** | controllers.py:208-210 | **Notificações simuladas no Controller** — email/SMS/push como `print()` direto no handler | Controller não deve disparar side effects; impossível substituir por implementação real |
| 8 | **LOW** | app.py:8,88 | **`DEBUG = True` hardcoded** | Werkzeug debugger expõe REPL Python no browser em qualquer exceção |
| 9 | **LOW** | controllers.py (15+ locais) | **Logging com `print()`** — sem timestamps, sem níveis, sem estrutura | Produção sem observabilidade alguma |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express — LMS API)

| # | Severidade | Arquivo:Linha | Problema | Justificativa |
|---|---|---|---|---|
| 1 | **CRITICAL** | src/utils.js:1-7 | **Credenciais hardcoded** — `dbPass`, `paymentGatewayKey: "pk_live_..."`, senha SMTP no código | Chave de pagamento live commitada em git é comprometimento permanente |
| 2 | **CRITICAL** | src/AppManager.js:1-141 | **God Class** — uma classe com init de banco, rotas, checkout, pagamento, matrícula e relatório | 7 responsabilidades em 141 linhas; zero testabilidade, zero reusabilidade |
| 3 | **HIGH** | src/utils.js:17-23 | **`badCrypto()` — criptografia falsa** — base64 em loop não é hashing, é reversível | Senha armazenada é recuperável trivialmente; não existe segurança real |
| 4 | **HIGH** | src/AppManager.js:45 | **Número de cartão logado** — `console.log(\`Processando cartão ${cc}...\`)` | Violação de PCI-DSS; dados de cartão em qualquer agregador de log |
| 5 | **HIGH** | src/AppManager.js:83-128 | **N+1 com Callback Hell** — 4 níveis de callbacks, query por matrícula por aluno | 100 cursos × 50 alunos = 10.001 queries por requisição de relatório |
| 6 | **HIGH** | src/AppManager.js:131-137 | **Delete sem cascade** — deleta usuário, deixa matrículas e pagamentos órfãos | O próprio código documenta o bug na mensagem de resposta |
| 7 | **MEDIUM** | src/AppManager.js:80 | **Rota admin sem autenticação** — `/api/admin/financial-report` pública | Qualquer pessoa pode ver faturamento e dados de alunos |
| 8 | **LOW** | src/AppManager.js:29-33 | **Nomes crípticos** — `u`, `e`, `p`, `cid`, `cc` sem semântica | Código ilegível sem decodificar intenção variável por variável |

### Projeto 3 — task-manager-api (Python/Flask — Task Manager)

| # | Severidade | Arquivo:Linha | Problema | Justificativa |
|---|---|---|---|---|
| 1 | **CRITICAL** | services/notification_service.py:9-10 | **Credenciais SMTP hardcoded** — `email_password = 'senha123'` no código | Senha de conta Gmail commitada em git |
| 2 | **HIGH** | models/user.py:28-32 | **MD5 para hash de senha** — `hashlib.md5(pwd.encode()).hexdigest()` | MD5 é computacionalmente reversível com rainbow tables disponíveis gratuitamente |
| 3 | **HIGH** | models/user.py:17-25 | **Senha exposta na API** — `to_dict()` retorna `'password': self.password` | Qualquer `GET /users` devolve todos os hashes MD5, facilitando o crack |
| 4 | **HIGH** | routes/user_routes.py:210 | **Token fake** — `'token': 'fake-jwt-token-' + str(user.id)` | Token é previsível para qualquer user_id conhecido; não há autenticação real |
| 5 | **MEDIUM** | task_routes.py:30-39,71-80; report_routes.py:33-43 | **Lógica de overdue duplicada em 6 lugares** — `Task.is_overdue()` existe mas nunca é chamado | Bug fix deve ser aplicado em 6 locais; inconsistências já presentes |
| 6 | **MEDIUM** | report_routes.py:53-67 | **N+1 no relatório** — query individual de tasks por usuário em loop | Com 100 usuários: 101 queries por requisição de relatório |
| 7 | **LOW** | models/task.py:15-16, user.py:14 | **`datetime.utcnow()` deprecated** — API removida no Python 3.12 | Warnings em log; breaking change em versão futura |
| 8 | **LOW** | task_routes.py, user_routes.py (10+ locais) | **`Model.query.get()` deprecated** — removido no SQLAlchemy 2.0 | Deprecation warnings; incompatível com SQLAlchemy 2.x |

---

## Construção da Skill

### Estrutura de Arquivos

```
.claude/skills/refactor-arch/
├── SKILL.md                    # Prompt principal — instrui o agente nas 3 fases
├── 01-project-analysis.md      # Heurísticas de detecção de stack e arquitetura
├── 02-antipatterns-catalog.md  # Catálogo com 14 anti-patterns e sinais de detecção
├── 03-audit-report-template.md # Template exato do relatório (formato e regras)
├── 04-mvc-guidelines.md        # Regras MVC por camada para Python/Flask e Node.js
└── 05-refactoring-playbook.md  # 10 transformações com código before/after
```

### Decisões de Design

**SKILL.md como prompt estruturado, não como script:** O SKILL.md instrui o agente com fases claras e verbo imperativo ("Read", "Scan", "Output"). Referencia cada arquivo de referência pelo nome para que o agente leia no momento certo — não tudo de uma vez. A pausa obrigatória na Fase 2 é explícita e absoluta: "Do NOT read, modify, or create any files until the user explicitly responds with 'y' or 'yes'."

**Separação entre conhecimento de domínio e instrução:** O SKILL.md contém apenas *o que fazer*. O *como fazer* e o *o que procurar* ficam nos arquivos de referência. Isso permite evoluir o catálogo de anti-patterns sem alterar o fluxo da skill.

**Catálogo com sinais de detecção concretos:** Cada anti-pattern tem exemplos literais de código a procurar (não descrições genéricas). Por exemplo, SQL Injection não está descrito como "uso inseguro de banco de dados" — está descrito como `cursor.execute("SELECT * FROM t WHERE id = " + str(id))`. Isso garante que o agente encontre o problema independente da linguagem.

**Agnóstico de tecnologia por desenho:** As heurísticas de detecção cobrem Python e Node.js explicitamente. Os guidelines MVC têm seções separadas para Flask (Blueprints) e Express (Router). O playbook tem exemplos before/after em ambas as linguagens. A skill se adapta ao que detectar na Fase 1.

**Anti-patterns selecionados:** Priorizamos anti-patterns que apareceram nos 3 projetos — SQL Injection, credenciais hardcoded e N+1 são universais. Adicionamos God Class (exclusivo do Projeto 2) e APIs deprecated (exclusivo do Projeto 3) para cobrir casos distintos. O catálogo resultante tem 14 anti-patterns (C1-C4, H1-H5, M1-M4, L1-L4), distribuídos entre as 4 severidades.

**Detecção de APIs deprecated:** Inclusa como categoria própria (L1) com exemplos específicos para Python (`datetime.utcnow()`, `Model.query.get()`) e Node.js (`new Buffer()`, `util.isArray()`). A skill detectou corretamente as APIs deprecated no Projeto 3 que usava SQLAlchemy.

**Desafio e solução:** O maior desafio foi garantir que a skill não fosse genérica demais. A primeira versão do catálogo descrevia problemas de forma abstrata. Refinamos para incluir exemplos literais de código — a partir disso, a skill passou a citar arquivo, linha e trecho exato de código em cada finding.

---

## Resultados

### Resumo dos Relatórios de Auditoria

| Projeto | Stack | Arquivos | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|---|
| code-smells-project | Python/Flask 3.1.1 | 5 (~780 LOC) | 4 | 5 | 4 | 3 | **16** |
| ecommerce-api-legacy | Node.js/Express 4.18 | 3 (~179 LOC) | 3 | 5 | 3 | 2 | **13** |
| task-manager-api | Python/Flask 3.0.0 + SQLAlchemy | 17 (~969 LOC) | 2 | 5 | 3 | 3 | **13** |

### Comparação Antes/Depois

#### Projeto 1 — code-smells-project

**Antes:**
```
code-smells-project/
├── app.py           (88 linhas — rotas + admin endpoints perigosos)
├── controllers.py   (292 linhas — HTTP handlers com print() como log)
├── models.py        (314 linhas — god file: 4 domínios + SQL injection + lógica de negócio)
└── database.py      (86 linhas — singleton global + seed com senhas em plaintext)
```

**Depois:**
```
code-smells-project/
├── app.py                          # Composition root — factory pattern
└── src/
    ├── config/settings.py          # Config de env vars
    ├── database.py                 # Conexão por-request via Flask g
    ├── models/
    │   ├── produto_model.py        # Queries parameterizadas, sem commit
    │   ├── usuario_model.py        # bcrypt hashing, sem senha em respostas
    │   └── pedido_model.py         # JOIN único — N+1 eliminado
    ├── services/
    │   ├── pedido_service.py       # Transação atômica para criação de pedidos
    │   ├── relatorio_service.py    # Desconto como constantes nomeadas
    │   └── notificacao_service.py  # Notificações via logger
    ├── controllers/
    │   ├── produto_controller.py   # Validação compartilhada extraída
    │   ├── usuario_controller.py   # Regex de email
    │   ├── pedido_controller.py    # Verificação de existência de usuário
    │   └── relatorio_controller.py
    ├── routes/                     # Blueprint — apenas mapeamento de URL
    │   └── (produto, usuario, pedido, relatorio, auth)_routes.py
    └── middlewares/error_handler.py # ValueError→400, Exception→500
```

#### Projeto 2 — ecommerce-api-legacy

**Antes:**
```
ecommerce-api-legacy/src/
├── app.js          # Entry point + wiring
├── AppManager.js   # God Class: DB + routes + checkout + payment + report + delete
└── utils.js        # Config com credenciais live hardcoded + badCrypto + globalCache
```

**Depois:**
```
ecommerce-api-legacy/src/
├── app.js
├── config/index.js             # process.env via dotenv
├── db/index.js                 # Schema + seeds + runInTransaction()
├── models/
│   └── (User, Course, Enrollment, Payment, AuditLog, Report)Model.js
├── services/
│   ├── CheckoutService.js      # Transação: user→enroll→pay→audit
│   └── ReportService.js        # JOIN único agrupado em JS
├── controllers/
│   └── (checkout, report, user)Controller.js
├── routes/
│   └── (checkout, report, user)Routes.js
├── middlewares/
│   └── auth.js                 # Bearer token para rotas admin
└── utils/logger.js             # Logger com níveis e timestamps ISO
```

#### Projeto 3 — task-manager-api

**Antes:** Estrutura parcial (models/, routes/, services/) mas com lógica de negócio nas routes, overdue duplicado 6 vezes, MD5 no model, senha exposta na API, `query.get()` e `utcnow()` deprecated.

**Depois:** Controllers criados (task, user, category, report), ReportService extraído com queries agregadas, `is_overdue()` chamado de um único lugar, `werkzeug.security` substituindo MD5, `to_dict()` sem campo password, `db.session.get()` e `datetime.now(timezone.utc)` substituindo APIs deprecated.

### Checklists de Validação

#### Projeto 1

**Fase 1 — Análise**
- [x] Linguagem detectada: Python
- [x] Framework detectado: Flask 3.1.1
- [x] Domínio: E-commerce (produtos, usuários, pedidos, relatórios de vendas)
- [x] Arquivos: 5 analisados (~780 LOC) — condiz com a realidade

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos (ex: `models.py:28, 47-50, 57-62...`)
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] 16 findings identificados (mínimo: 5)
- [x] Deprecated APIs: nenhuma encontrada (Flask 3.x + sqlite3 stdlib, sem SQLAlchemy)
- [x] Skill pausou e pediu confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura MVC: config/, models/, controllers/, routes/, services/, middlewares/
- [x] Config extraída para `src/config/settings.py` (env vars)
- [x] Models criados por domínio: produto_model, usuario_model, pedido_model
- [x] Routes separadas (Blueprints) — apenas mapeamento de URL
- [x] Controllers concentram fluxo HTTP + delegam para services
- [x] Error handling centralizado em `middlewares/error_handler.py`
- [x] Entry point claro: `app.py` com `create_app()` factory
- [x] Aplicação inicia sem erros
- [x] 15 endpoints validados com respostas corretas

#### Projeto 2

**Fase 1 — Análise**
- [x] Linguagem detectada: Node.js
- [x] Framework detectado: Express 4.18.2
- [x] Domínio: LMS (cursos, matrículas, checkout, relatório financeiro)
- [x] Arquivos: 3 analisados (~179 LOC)

**Fase 2 — Auditoria**
- [x] Relatório segue o template
- [x] Cada finding com arquivo e linha exatos
- [x] Findings ordenados por severidade
- [x] 13 findings (mínimo: 5)
- [x] Deprecated APIs: `new Buffer()` identificado no contexto de `badCrypto`
- [x] Skill pausou antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura MVC: config/, db/, models/, services/, controllers/, routes/, middlewares/, utils/
- [x] Config extraída para `config/index.js` (process.env + dotenv)
- [x] 6 Models criados (User, Course, Enrollment, Payment, AuditLog, Report)
- [x] Routes com Express Router — apenas URL mapping
- [x] Controllers validam input e delegam para services
- [x] Auth middleware protegendo rotas admin
- [x] Entry point: `app.js`
- [x] Aplicação inicia sem erros
- [x] 7 cenários validados (checkout aprovado, recusado, admin com/sem auth, delete com cascade)

#### Projeto 3

**Fase 1 — Análise**
- [x] Linguagem detectada: Python
- [x] Framework detectado: Flask 3.0.0 + SQLAlchemy (Flask-SQLAlchemy 3.1.1)
- [x] Domínio: Task Manager (tasks, users, categories, reports)
- [x] Arquivos: 17 analisados (~969 LOC) — estrutura parcial detectada corretamente

**Fase 2 — Auditoria**
- [x] Relatório segue o template
- [x] Cada finding com arquivo e linha exatos
- [x] Findings ordenados por severidade
- [x] 13 findings (mínimo: 5)
- [x] Deprecated APIs detectadas: `datetime.utcnow()` (10+ locais) e `Model.query.get()` (10+ locais)
- [x] Skill pausou antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura aprimorada: controllers/ criado, category_routes.py separado de report_routes
- [x] Config extraída para `src/config/settings.py`
- [x] Models mantidos e corrigidos (MD5→pbkdf2, utcnow→now(timezone.utc))
- [x] Routes thinned — apenas mapeamento de URL
- [x] Controllers e ReportService concentram lógica
- [x] Error handling centralizado com `logger.exception()`
- [x] Entry point: `app.py` com `create_app()`
- [x] Aplicação inicia sem erros
- [x] Todos os endpoints validados (GET /tasks, /users, /categories, /reports/summary, /login, etc.)

### Comportamento da Skill em Stacks Diferentes

A skill se adaptou corretamente às 3 situações distintas:

- **Projeto 1 (monolito plano):** Detectou a ausência total de camadas e criou toda a estrutura do zero. Maior quantidade de findings (16) e maior transformação estrutural.
- **Projeto 2 (God Class em Node.js):** Adaptou a linguagem dos padrões de refatoração para JavaScript async/callbacks. Criou auth middleware que não existia. Identificou corretamente `badCrypto` como variante de "Weak Cryptography".
- **Projeto 3 (parcialmente organizado):** Não recriou o que já existia — melhorou o que estava errado. Identificou que `Task.is_overdue()` já existia mas não era chamado. Detectou deprecated APIs do SQLAlchemy 2.0 corretamente.

---

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e configurado (`npm install -g @anthropic-ai/claude-code`)
- Python 3.11+ com `pip`
- Node.js 18+ com `npm`

### Executar a skill em cada projeto

```bash
# Projeto 1 — Python/Flask (E-commerce)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — Node.js/Express (LMS)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask (Task Manager)
cd ../task-manager-api
claude "/refactor-arch"
```

> A skill já está copiada em `.claude/skills/refactor-arch/` dentro de cada projeto.

### Fluxo de execução

1. **Fase 1** — A skill imprime automaticamente o resumo de stack e arquitetura
2. **Fase 2** — A skill gera o relatório completo e **pausa** com a mensagem:
   ```
   Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
   ```
3. Revise o relatório e digite `y` para autorizar a refatoração
4. **Fase 3** — A skill refatora e imprime os resultados de validação

### Validar que a refatoração funcionou

#### Projeto 1 (Python/Flask)
```bash
cd code-smells-project
pip install -r requirements.txt
python app.py
# Em outro terminal:
curl http://localhost:5001/health
curl http://localhost:5001/produtos
curl http://localhost:5001/usuarios
```

#### Projeto 2 (Node.js/Express)
```bash
cd ecommerce-api-legacy
npm install
node src/app.js
# Em outro terminal:
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"usr":"Test","eml":"t@t.com","pwd":"pass","c_id":1,"card":"4111111111111111"}'
```

#### Projeto 3 (Python/Flask + SQLAlchemy)
```bash
cd task-manager-api
pip install -r requirements.txt
python app.py
# Em outro terminal:
curl http://localhost:5000/health
curl http://localhost:5000/tasks
curl http://localhost:5000/reports/summary
```

### Relatórios de auditoria gerados

Os relatórios da Fase 2 estão em:
- [`reports/audit-project-1.md`](reports/audit-project-1.md) — code-smells-project (16 findings)
- [`reports/audit-project-2.md`](reports/audit-project-2.md) — ecommerce-api-legacy (13 findings)
- [`reports/audit-project-3.md`](reports/audit-project-3.md) — task-manager-api (13 findings)
