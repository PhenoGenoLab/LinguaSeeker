# Pipeline 阶段 0–1 迁移实施记录

> 对应方案：[`docs/planned/2026-11-17-pipeline-agentscope-reme-migration.md`](../planned/2026-11-17-pipeline-agentscope-reme-migration.md)（§3.2 目录结构、§5 阶段 0/1）
>
> 状态：阶段 0 完成；阶段 1 目录迁移完成（拓扑显式化留给后续阶段）
> 日期：2026-11-17
> 边界：只改领域层包布局与 import，外层 HTTP/DI、状态 JSON、DB、队列、产物与重试语义不变

## 1. 本次范围

| 阶段 | 本次完成内容 | 明确未做 |
|---|---|---|
| 0 | `src/pipeline/{graph,skills,tools,mcp,contracts}` 骨架；模块→目标层映射；import 基线脚本与记录；import 边界测试 | 抽取质量基线、真实文档 shadow 对照 |
| 1 | `orchestrator` + `phase_1..4_adapter` 迁入 `src/pipeline/graph`；测试 import 更新；旧路径 re-export shim；`src/api/wiring.py` 零改动 | Phase 3 窗口子图、节点级进度、并行窗口（方案 §5 阶段 1 的拓扑增强，另行实施） |

方案中的阶段 2–4（AgentScope 运行时、Phase 3 试点、ReMe）未在本 PR 触碰。

## 2. 模块 → 目标层映射

| 现有模块 | 目标层 | 迁移阶段 | 状态 |
|---|---|---|---|
| `src/agents/orchestrator.py` | `src/pipeline/graph/topology.py` | 1 | 已迁移，旧路径 shim |
| `src/agents/phase_1_adapter.py` | `src/pipeline/graph/phases/phase_1.py` | 1 | 已迁移，旧路径 shim |
| `src/agents/phase_2_adapter.py` | `src/pipeline/graph/phases/phase_2.py` | 1 | 已迁移，旧路径 shim |
| `src/agents/phase_3_adapter.py` | `src/pipeline/graph/phases/phase_3.py` | 1 | 已迁移，旧路径 shim |
| `src/agents/phase_4_adapter.py` | `src/pipeline/graph/phases/phase_4.py` | 1 | 已迁移，旧路径 shim |
| `src/core/source_fact_chain/{contracts,core,windowing,projection,api}.py` | `src/pipeline/tools/fact_chain/` | 2 | 未开始 |
| `src/core/source_fact_chain/{runner,prompts}.py` | `src/pipeline/skills/fact_chain/` | 2 | 未开始 |
| `src/core/source_fact_chain/providers.py` | `src/pipeline/skills/runtime/llm.py` | 2 | 未开始 |
| `src/core/ingest_and_digitize_data/document_acquisition/` | `src/pipeline/tools/acquisition/` | 3 | 未开始 |
| `src/core/ingest_and_digitize_data/parse_document/` | `src/pipeline/tools/parsing/` | 3 | 未开始 |
| `src/core/standardize_entities_and_align_knowledge/` 实现 | `src/pipeline/tools/terminology/` | 4 | 未开始 |
| 上者 `contracts.py` / `hgvs_normalizer.py` / `context_pack/` | `src/core/terminology_shared/` | 4 | 未开始 |
| `src/agents/contracts.py`、`runner`、`dispatcher`、`state_persistence`、`processing_cache`、`concurrency`、`content_hash`、`phase_5_factory` | 不迁（外层冻结） | — | 保持不变 |
| `src/core/graph_rag/`、`evidence_extraction/`、`cross_lingual_translation/` | 不迁（共享/休眠） | — | 保持不变 |
| `src/api/**`、`src/app/**`、`src/dao/**`、`src/utils/**` | 不迁（外层） | — | 保持不变 |

分层边界（由 `backend/tests/pipeline/test_import_boundaries.py` 强制）：

| 目录 | 职责 | 禁止 import |
|---|---|---|
| `graph/` | LangGraph 拓扑、phase 适配、状态写入 | `agentscope`；旧 `src.agents.orchestrator/phase_*_adapter` 路径 |
| `skills/` | AgentScope 子智能体、prompt、模型档位 | SQLAlchemy / Neo4j / asyncpg / psycopg / sqlite3 / `src.dao`；`src.pipeline.graph` |
| `tools/` | 确定性能力、校验、落盘、事务 | `agentscope`；`src.pipeline.skills`、`src.pipeline.graph` |
| `mcp/` | 外部服务协议适配 | `src.pipeline.skills`、`src.pipeline.tools` |
| `contracts/` | 跨层 DTO | 业务逻辑与外部客户端 |

## 3. Import 基线

复现命令（在 `backend/` 下）：

```bash
.venv/bin/python scripts/pipeline_migration_inventory.py
.venv/bin/python scripts/pipeline_migration_inventory.py --format json
```

`inbound imports` 统计的是 import 语句数（按 `src/tests/scripts/app` 分组），不是行数；统计口径见脚本内 `LayerSpec`。

### 3.1 迁移前（阶段 0，commit `9d402061c`）

| 层 | 目标 | 旧路径文件 | 旧路径行数 | 新路径文件 | 新路径行数 | 入向 import（src/tests/scripts/app） |
|---|---|---:|---:|---:|---:|---|
| graph | `src/pipeline/graph` | 5 | 1128 | 1（骨架） | 6 | 5 / 8 / 0 / 0 |
| fact_chain | `tools/fact_chain` + `skills/fact_chain` | 9 | 1858 | 0 | 0 | 5 / 10 / 0 / 0 |
| acquisition | `tools/acquisition` | 7 | 521 | 0 | 0 | 5 / 9 / 0 / 0 |
| parsing | `tools/parsing` | 13 | 1734 | 0 | 0 | 8 / 43 / 1 / 0 |
| terminology | `tools/terminology` + `core/terminology_shared` | 27 | 5776 | 0 | 0 | 10 / 60 / 4 / 0 |

### 3.2 迁移后（阶段 1）

| 层 | 目标 | 旧路径文件（全部为 shim） | 新路径文件 | 新路径行数 | 入向 import（src/tests/scripts/app） |
|---|---|---:|---:|---:|---|
| graph | `src/pipeline/graph` | 5 | 7 | 1139 | 5 / 10 / 0 / 0 |
| fact_chain / acquisition / parsing / terminology | 未开始 | 同基线 | 0 | 0 | 同基线 |

- `src/pipeline` 合计：12 个文件 / 1177 行（含骨架与 `__init__.py`）。
- 生产代码只剩 `src/api/wiring.py` 仍 import 旧路径，这是“wiring 零改动”的刻意选择；shim 一个发布周期后删除。
- 测试已切到新路径；`tests/pipeline/test_legacy_shims.py` 校验 shim 与新实现是同一个对象。

## 4. 验证

| 检查 | 命令 | 结果 |
|---|---|---|
| 迁移前基线 | `.venv/bin/python -m pytest tests/agents tests/api/test_pipeline_api.py tests/core/source_fact_chain -q` | 253 passed |
| 迁移后领域测试 | `.venv/bin/python -m pytest tests/agents tests/pipeline tests/core/source_fact_chain -q` | 246 passed |
| API/wiring 契约 | `.venv/bin/python -m pytest tests/api/test_pipeline_api.py tests/api/test_wiring_config.py -q` | 21 passed |
| 边界测试 | `.venv/bin/python -m pytest tests/pipeline -q` | 11 passed |
| Ruff | `ruff format --check` / `ruff check`（CI 版本 0.15.17，改动文件） | 通过 |
| Mypy（CI 目标） | `mypy --ignore-missing-imports --follow-imports=silent src/core/source_fact_chain src/pipeline/graph/phases/phase_3.py src/agents/contracts.py` | Success, 11 files |

CI 同步调整：mypy/coverage 目标从 `src/agents/phase_3_adapter.py` 改为 `src/pipeline/graph/phases/phase_3.py`，并把 `tests/pipeline` 加入确定性测试集。

## 5. 不变量与回滚

保持不变（本 PR 未改）：

- HTTP 路由、请求/响应模型、状态码、`status_url`、owner 404 语义；
- `pipeline_status` / `phase_*_status` 枚举与转移守卫；
- `PipelineGraphState` 字段、`state_json` 形状、四个 `*Output` 模型；
- `pipeline_run_states` / `pipeline_jobs` / `document_processing_cache` 表结构与索引；
- 阶段重试（3 次 / 30s / 60s）、并发 2、心跳与孤儿回收；
- `phase_2/*`、`phase_3/*.json(l)` 等磁盘产物路径与文件集。

回滚方式：

1. **阶段 1**：`git revert` 目录迁移 commit，旧路径恢复为真实实现，shim 一并消失；无数据/配置迁移。
2. **阶段 0**：删除 `src/pipeline` 骨架、`tests/pipeline` 与 inventory 脚本即可；不影响运行时。
3. 迁移本身不新增运行时开关，回滚不依赖配置。

## 6. 未决决策处理

按需求方指示，D1–D3、D5–D9 采用方案推荐项；本 PR 未引入任何会改变对外接口的选择：

- D1 记忆层、D2 四 phase 节点、D3 有界智能体、D5 版本钉法、D6 薄封装、D7 休眠不迁、D8 恢复语义不变、D9 目录划分：均按推荐，但阶段 0/1 只需 D9 的目录骨架。
- D9 的两个待确认点（无 LLM 的 skill 是否保留、MCP 配置存放位置）不影响本 PR，留到阶段 2 前确认。
- D4（ReMe 外部服务）已确认，本 PR 未接入。

## 7. 限制与后续

- 本 PR 的阶段 1 按任务定义只做**目录迁移**；方案 §5 阶段 1 中的“Phase 3 窗口子图、`Send` fan-out、节点级进度”尚未实施，不能据此认为拓扑显式化已完成。
- 旧路径 shim 需在发布一个周期后、确认无外部调用方时单独删除。
- 阶段 2 开始前需重新运行 inventory，并确认 `skills/` 与 `tools/` 的边界口径（尤其无 LLM 的 Phase 1/2 skill）。
