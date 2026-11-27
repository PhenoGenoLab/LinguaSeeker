# LinguaSeeker

> 医学遗传学文献自动化和结构化证据提取的多智能体基础设施平台。提供证据管线：文献获取与数字化、原文事实链（分窗→抽取→核验→事实英译→双语展示）、实体标准化与知识对齐、双语可视化与专家反馈。

## 发布状态

| 组件 | 版本 | 来源 |
|------|------|------|
| 后端 | `1.0.0` | `backend/pyproject.toml` |
| 前端 | `1.3.0` | `frontend/package.json` |

生产部署应将后端和前端镜像固定到相同的不可变标签。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vite、React 18、TypeScript（strict）、Ant Design、Zustand、React Query、Axios、React Router；按 `src/features/` 垂直切片 |
| 后端 | Python 3.12、FastAPI、SQLAlchemy 2.0（async）、Alembic、LangGraph、AgentScope |
| 原生 I/O | Rust 扩展 `rust-io`（PyPI wheel，含 `rust_io.net` / `rust_io.files`） |
| 推理 | 外部 Docker 容器：Embedding(:8002)、Rerank(:8003)；文档解析使用远程 MinerU API |
| 存储 | PostgreSQL 18（pgvector）、Redis 8.0、Neo4j 5.26（图检索） |
| 基础设施 | Docker Compose、Ansible、GitHub Actions |

## 项目结构

```
.
├── backend/                        # FastAPI 应用
│   ├── app/                        # 入口点（main.py）
│   ├── src/                        # 业务逻辑（编排垂直切片架构）
│   │   ├── pipeline/
│   │   │   ├── graph/              #   LangGraph 拓扑 + 阶段适配器（拓扑、acquisition、parsing、fact_chain、standardization、lifecycle）
│   │   │   └── skills/             #   垂直 agent 包：acquisition、parsing、extraction、translation、review、standardization、graph_retrieval、runtime
│   │   ├── runs/                   # 一次 run 的生命周期（runner、dispatcher、状态持久化）
│   │   ├── api/                    # FastAPI 路由：v1（业务）、v2（目录 run / 批处理 agent job）
│   │   ├── core/                   # 配置 + 基础层（foundation、shared 契约与确定性工具、tools、adapters）
│   │   ├── ports/                  # 外部服务端口定义
│   │   ├── dao/                    # 数据访问（PostgreSQL、Redis、Neo4j）
│   │   └── utils/                  # 共享工具
│   ├── config/                     # 分层 YAML 配置（defaults + environments + vault）
│   ├── tests/                      # 后端测试
│   └── pyproject.toml              # Python 项目（uv 管理，uv.lock 锁定）
├── frontend/                       # Vite + React 应用
│   ├── src/
│   │   ├── pages/                  # 路由级页面组件
│   │   ├── features/               # 垂直 UI 特性：pipeline、evidence-db、evidence-search、graphrag、chat、audit、auth
│   │   ├── components/             # 共享 UI 组件（layout、ui）
│   │   ├── lib/                    # API 客户端、hooks、types、utils、i18n、constants
│   │   └── stores/                 # Zustand 状态存储
│   ├── tests/                      # 前端单元测试 + e2e
│   └── package.json                # Node 项目（bun 管理，bun.lock 锁定）
├── libs/
│   ├── config-loader/              # acmg-config-loader（可编辑路径依赖，分层 YAML 加载）
│   └── lit-acquisition/            # 文献获取 SDK 源码（运行时按 pyproject 版本安装）
├── database/                       # Alembic 迁移 + 术语数据
│   ├── migrations/versions/        # SQL 迁移脚本
│   ├── seeds/                      # 种子数据
│   └── terminology_database/       # 参考数据（ClinVar、ClinGen、HPO 等）
├── deploy/                         # 部署配置
│   ├── compose/                    # Docker Compose 部署
│   │   ├── dev-infra/              # 本地外部数据库容器：Postgres + Redis + Neo4j
│   │   ├── backend-host/           # 后端（数据库为外部容器）
│   │   ├── frontend-host/          # Nginx + 预构建 SPA
│   │   └── staging/                # 预发布环境
│   ├── archive/                    # 已归档部署变体（single-server、debug-prod）
│   └── ansible/                    # Ansible 部署自动化
│       ├── inventories/            # production、staging
│       ├── playbooks/              # site.yml、healthcheck.yml
│       └── roles/                  # common、backend、frontend、postgres、redis、nginx
├── docs/                           # 文档（active、planned、archive、diagrams）
├── benchmark/                      # 管线基准测试 + 评估
├── scripts/                        # 项目级运维脚本（dev、回填、基准、同步）
├── data/                           # 测试 PDF + 管线运行产物
├── artifacts/                      # 数据库导出和术语导出
├── AGENTS.md                       # 项目规则和约定
└── README.md
```

## 快速开始

### 前置条件

- Docker & Docker Compose
- [bun](https://bun.sh/)（前端包管理器和运行时）
- [uv](https://docs.astral.sh/uv/)（Python 包管理器）

> `rust-io` 以 PyPI wheel 形式安装，无需本地 Rust 工具链。

### 本地开发

```bash
# 1) 启动开发基础设施（Postgres 18 + Redis 8 + Neo4j 5.26）
./scripts/dev/start_backend_dev.sh --infra up -d

# 2) 后端（:8000）
cd backend
uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload

# 或一步启动基础设施 + 后端
./scripts/dev/start_backend_dev.sh --with-infra
```

**前端：**

```bash
cd frontend
bun install
bun run dev     # http://localhost:3000
```

| 服务 | 地址 |
|------|------|
| 前端 | `http://localhost:3000` |
| 后端 API | `http://localhost:8000` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |
| Neo4j | `http://localhost:7474`、`bolt://localhost:7687` |

**推理服务（外部）：**

模型推理（Embedding、Rerank）由外部 Docker 容器提供，在 `backend/config/` 中配置服务 URL。

## 开发命令

| 命令 | 描述 |
|------|------|
| `cd backend && uv run ruff check` | 后端代码检查 |
| `cd backend && uv run pytest` | 运行所有后端测试 |
| `cd frontend && bun run lint` | 前端代码检查 |
| `cd frontend && bun run type-check` | TypeScript 类型检查 |
| `cd frontend && bun run build` | 生产构建（tsc + vite build） |
| `cd frontend && bun run test` | 前端单元测试（vitest） |
| `cd frontend && bun run test:e2e` | 前端 e2e（Playwright） |
| `cd backend && uv run python -c "import rust_io.net, rust_io.files"` | 检查 Rust 扩展可用 |

CI（`.github/workflows/ci.yml`）执行后端 Ruff + Mypy + 确定性单测，以及前端 lint + type-check + 单测。

## 部署

### 数据库环境

| 环境 | 数据库 | Schema | 用户 |
|------|--------|--------|------|
| Development | `dev_lingua_seeker` | `lingua_seeker` | `lingua_seeker` |
| Staging | `staging_lingua_seeker` | `lingua_seeker` | `lingua_seeker` |
| Production | `lingua_seeker` | `lingua_seeker` | `lingua_seeker` |

### 分离前后端（当前生产架构）

前端（nginx + SPA）和后端（FastAPI）部署在独立主机；Postgres、Redis、Neo4j 为外部容器服务。详见 [deploy/compose/README.md](deploy/compose/README.md) 和 [后端主机部署指南](docs/active/2026-06-27-backend-host-deployment-guide.md)。

```bash
# 后端主机
docker compose -f deploy/compose/backend-host/docker-compose.yml \
               --env-file deploy/compose/backend-host/.env up -d

# 前端主机
docker compose -f deploy/compose/frontend-host/docker-compose.yml \
               --env-file deploy/compose/frontend-host/.env up -d

# 预发布（仅后端，数据库为外部容器）
docker compose -f deploy/compose/staging/docker-compose.yml \
               --env-file deploy/compose/staging/.env up -d
```

> 早期的一体化单机（single-server）方案已归档至 [deploy/archive/](deploy/archive/)。

### Ansible

裸机 / systemd 部署，覆盖 `production` 和 `staging` 两套 inventory。详见 [deploy/ansible/](deploy/ansible/)。

## 分支策略

- **`dev`** — 主开发分支
- **`master`** — 仅手动合并，禁止直接推送

## 约定

详见 [AGENTS.md](./AGENTS.md)。关键要点：

- 包管理器：`uv`（Python）、`bun`（Node.js）；Rust 扩展以 PyPI wheel 形式引入，无需本地工具链
- 日志：`loguru`，输出到 `logs/`
- 测试：`pytest`（后端）、`vitest` / Playwright（前端）
- 代码风格：Google Style Guide，Ruff（Python）和 ESLint（TypeScript）
- 提交信息：Conventional Commits（`feat:`、`fix:`、`docs:` 等）
- API 版本：`/api/v1/` 承载业务 API，`/api/v2/` 承载目录 run 与批处理 agent job；破坏性变更升级版本号
