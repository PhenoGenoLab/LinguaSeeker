# Core 核心模块

> 平台核心配置与业务流程编排层，提供全局配置管理及各业务阶段的入口。

## 概述

`core` 是 ACMG Lingua 后端的核心包，包含全局配置管理（`config.py`）和四个业务阶段子模块。配置系统基于 Pydantic Settings，从 YAML 文件和环境变量加载，以单例模式提供全局访问。

## 结构

```
core/
├── __init__.py                  # 空包标识
├── config.py                    # L0 全局配置（Settings 单例），所有层可 import
├── config_loader.py             # L0 向后兼容 shim，委托给 acmg_config_loader
├── foundation/                  # L1 跨切面基础
│   └── auth/                    #   认证契约与口令哈希
├── shared/                      # L2 共享能力与契约
│   ├── tools/fact_chain/        #   确定性能力：契约、校验、窗口、投影
│   └── contracts/skill_io.py    #   跨层 DTO（SkillRequest/SkillResult）
├── adapters/                    # L3 外部协议适配
│   └── mcp/                     #   ReMe 等（占位，只依赖 shared.contracts）
└── agents/                      # L4 agent 实现（同级互引）
    ├── acquisition/             #   文献采集（本地上传 / 在线获取）
    ├── parsing/                 #   文档解析（MinerU remote / local）
    ├── translation/             #   翻译（术语映射、句级对齐、校验）
    ├── extraction/              #   证据抽取（字段目录、双轨抽取、离线基准）
    ├── standardization/         #   实体标准化与知识对齐
    ├── review/                  #   证据可视化、专家反馈、问答
    └── graph_retrieval/         #   图谱构建与检索问答
```

> 本目录**不表达阶段编号**：阶段由 `src/pipeline/graph/` 的 LangGraph 拓扑编排，
> core 只回答"这个 agent 能做什么"。
>
> 依赖方向：`foundation ← shared ← agents`，`adapters` 只依赖 `shared.contracts`；
> `src.pipeline`（LangGraph 编排 + AgentScope skills）单向依赖 `src.core`。
> 反向依赖、以及跨层回指由 `tests/core/test_layer_boundaries.py` 与
> `tests/pipeline/test_import_boundaries.py` 断言。
>
> 已知的一处有意放宽：`shared/tools/fact_chain` 只读引用 `agents/extraction`
> 的字段目录与分组规则，因此 `shared → agents` 的方向被允许但仅限该处。

## 核心组件

### config.py — 全局配置中心

- **`Settings`**：根配置模型（Pydantic `BaseSettings`），包含所有子系统配置
- **Provider 配置**：`LLMConfig`、`ReasoningConfig`、`ChatLLMConfig`、`TranslationLLMConfig`、`EmbeddingConfig`、`RerankConfig`
- **基础设施配置**：`RedisConfig`、`PostgreSQLConfig`、`NetworkConfig`（代理/直连）、`WebSearchConfig`
- **文档解析配置**：`ParseDocumentConfig`、`MinerUConfig`
- **常量**：`PGVECTOR_DIMENSION=1024`、`BACKEND_ROOT`、`REPO_ROOT`
- **`get_config()`**：`@lru_cache` 单例访问器，返回全局 `Settings` 实例
- **`load_backend_config_into_env()`**：模块导入时自动从 YAML 加载配置到环境变量

### Agent 与分层子模块

| 子模块 | 说明 |
|--------|------|
| `foundation/auth/` | 认证契约与口令哈希 |
| `shared/tools/` | 确定性能力（含 `tools/fact_chain/` 契约、校验、窗口、投影）；无 agent 决策 |
| `shared/contracts/` | 跨层 DTO，如 `contracts/skill_io.py` 的 `SkillRequest`/`SkillResult` |
| `adapters/mcp/` | 外部服务协议适配（ReMe 等），占位待契约落地 |
| `agents/acquisition/` | 采集 agent：本地上传、在线获取、SDK 适配 |
| `agents/parsing/` | 解析 agent：MinerU remote/local、产物落盘 |
| `agents/translation/` | 翻译 agent：术语映射、句级对齐、语言校验 |
| `agents/extraction/` | 抽取 agent：ACMG 字段目录、双轨证据、分组规则 |
| `agents/standardization/` | 标准化 agent：精确/语义匹配、术语持久化、ACMG 投影 |
| `agents/review/` | 审核 agent：证据可视化、专家反馈、问答 |
| `agents/graph_retrieval/` | 图谱 agent：证据图构建与检索问答 |

> 原文事实链的编排与服务门面在 `src/pipeline/skills/fact_chain/`，确定性部分在
> `src/core/shared/tools/fact_chain/`；原 `src/core/source_fact_chain/` 已废弃删除。

## 数据流

```
YAML 配置 → load_backend_config_into_env() → Settings 实例
                                              ↓
                                    get_config() 单例
                                              ↓
                              各业务模块按需读取配置
```

## 使用

```python
from src.core.config import get_config

cfg = get_config()
# 访问 LLM 配置
print(cfg.llm.base_url, cfg.llm.model)
# 访问数据库连接串
print(cfg.get_postgresql_url("acmg_db"))
```
