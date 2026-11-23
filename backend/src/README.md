# Src

> 后端核心源码——包含配置管理、业务逻辑、API 路由、数据访问和工具函数。

## Overview

`src/` 是 Lingua Seeker 后端的核心代码包，按职责分为 6 个子包：配置管理（`core/`）、pipeline 编排层（`pipeline/`）、运行生命周期（`runs/`）、HTTP API（`api/`）、数据访问（`dao/`）和通用工具（`utils/`）。

## Structure

```
src/
├── core/                # 配置与基础层
│   ├── config.py                # Settings 单例（Pydantic Settings）
│   ├── foundation/              # L1 跨切面基础（auth）
│   ├── shared/                  # L2 共享能力与契约（fact_chain、skill_io）
│   ├── tools/                   # 具体工具（acquisition/、parsing/、extraction/、standardization/ …）
│   └── adapters/                # L3 外部协议适配（mcp）
├── pipeline/            # pipeline 领域层
│   ├── graph/                   # LangGraph 拓扑与阶段适配器（acquisition/parsing/fact_chain/standardization）
│   └── skills/                  # 专业 agent 实现（prompt、模型调用、编排）+ runtime
├── runs/                # 一次 run 的生命周期（runner、dispatcher、状态持久化）
│   ├── runner.py                # 后台管线运行器
│   ├── dispatcher.py            # 单任务作业调度器
│   ├── contracts.py             # 状态模型、错误层次、状态转换守卫
│   ├── state_persistence.py     # PostgreSQL 状态持久化
│   ├── processing_cache.py      # 两级缓存（L1 Redis + L2 PostgreSQL）
│   ├── content_hash.py          # 内容哈希去重
│   ├── concurrency.py           # 信号量和重试执行器
│   └── review_factory.py        # 审核（review）服务工厂
├── api/                 # HTTP API 层
│   ├── wiring.py                # 依赖注入和服务组装
│   ├── auth.py                  # API Key 和会话认证
│   ├── deps.py                  # FastAPI 依赖项
│   ├── body_size_limit.py       # 请求体大小限制中间件
│   ├── rate_limit.py            # Redis 限流
│   └── v1/                      # V1 API 路由
├── dao/                 # 数据访问层
│   ├── postgresql/              # SQLAlchemy ORM 和仓储
│   ├── redis/                   # Redis 缓存操作
│   ├── neo4j/                   # 图数据库（预留）
└── utils/               # 通用工具函数
    ├── logger.py                # 日志配置（loguru）
    ├── exceptions.py            # 统一异常层次
    ├── health.py                # 启动健康检查
    ├── middleware.py             # 请求监控中间件
    ├── security_headers.py      # 安全头中间件
    └── text.py                  # 文本处理工具
```

## Key Components

### 依赖关系图

```
app.main → src.api.wiring → src.runs.* → src.pipeline.* / src.core.*
                ↓
           src.dao.* (PostgreSQL / Redis)
                ↓
           src.utils.* (日志、LLM 适配器、异常)
```

### 管线架构

| 阶段 | 模块 | 职责 |
|------|------|------|
| acquisition | `pipeline/skills/acquisition/` + `core/tools/acquisition/` | 文献采集 |
| parsing | `pipeline/skills/parsing/` + `core/tools/parsing/` | MinerU 文档解析 |
| fact_chain | `pipeline/skills/extraction/`（+`translation/`） + `core/tools/extraction/` | 分窗 → 抽取 → 核验 → 事实英译 |
| standardization | `pipeline/skills/standardization/` + `core/tools/standardization/` | 实体标准化 + 术语对齐 |
| review | `pipeline/skills/review/` + `core/tools/review/` | 审核、聊天、审计、溯源（非图节点） |

前四个阶段由 `pipeline/graph/topology.py`（LangGraph）编排为有向图，对应 `graph/phases/{acquisition,parsing,fact_chain,standardization}.py`；
review 是独立的请求-响应式服务，由 `runs/review_factory.py` 创建。

## Usage / Patterns

### 获取配置

```python
from src.core.config import get_config
cfg = get_config()
```

### 导入异常

```python
from src.utils.exceptions import NotFoundException, ValidationException
```

### 创建 LLM 客户端

```python
from src.pipeline.skills.runtime.agentscope_llm import build_chat_model
from src.core.config import get_config

model = build_chat_model(get_config(), tier="fast")   # AgentScope chat model
```

## Dependencies

| 依赖 | 用途 |
|------|------|
| FastAPI | HTTP 框架 |
| SQLAlchemy 2.0 | 异步 ORM |
| LangGraph | 管线编排 |
| LangChain | LLM 客户端抽象 |
| loguru | 结构化日志 |
| Pydantic | 数据验证和 Settings |
