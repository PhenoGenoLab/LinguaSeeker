# Pipeline 阶段 2 迁移实施记录：AgentScope 运行时 + Phase 3 extract 试点

> 对应方案：[`docs/planned/2026-11-17-pipeline-agentscope-reme-migration.md`](../planned/2026-11-17-pipeline-agentscope-reme-migration.md)（§3.2 目录、§5 阶段 2）
>
> **Status:** in-progress
> **Date:** 2026-11-18
> **Branch:** `impl-stage-2-be70dc50bda0`（基于 `impl-stage-0-1-be70dc50bda0`，PR #32）
> 边界：只改领域层。HTTP/DI、状态 JSON、DB/队列语义、磁盘产物路径不变；ReMe 仍按外部服务处理，未接入。

## 1. 本次范围

| 方案阶段 2 产出 | 状态 | 说明 |
|---|---|---|
| `agentscope==2.0.12` 入 backend | 完成 | 同步升级 `certifi 2026.10.23`；新增 `mcp 2.3.0`、`httpx2 2.16.2` 等；`fastapi/numpy/openai/pydantic` 版本不变 |
| 目录迁移：`source_fact_chain` → `tools/fact_chain` + `skills/fact_chain` + `skills/runtime/llm.py` | 完成 | 56 个文件中本层 9 个；旧路径 9 个 shim（2026-11-18 已删除） |
| `AgentScopeNode` 适配（`reply(structured_schema=...)`、异常分类） | 完成 | `skills/runtime/agent.py`：`build_agent`、`run_reply_sync`；异常统一映射为 `SkillError`（默认 retryable） |
| 多 key 轮换 credential/model 包装 | 完成 | `skills/runtime/agentscope_llm.py`：仅 `AuthenticationError`/`PermissionDeniedError` 轮换，其余错误交回 runner 重试 |
| `ExtractAgent`（工具 + 结构化输出） | 完成 | `skills/fact_chain/extract.py`：`ExtractReply` schema；工具 `quote_in_window`、`atomic_value`；复用 `validate_reply_schema` |
| 影子模式 | 完成（逻辑） | `StageRouterProvider(mode="shadow")`：新旧同窗口各跑一次，逐条 diff 后返回旧结果；计数 `ShadowStats` |
| 成本/延迟埋点 | 部分 | 每次 skill 调用记录 `latency_ms`；shadow 差异/失败记 warning；未接入指标系统 |
| 真实文档影子验收（≥1 周、成本 +15% 内） | 未做 | 需要真实 LLM 凭证与黄金文档，非本次可离线完成 |

未触碰：`src/api/**`、`src/agents/{runner,dispatcher,state_persistence,processing_cache,concurrency,content_hash,phase_5_factory,contracts}.py`、`src/dao/**`、数据库迁移、`graph_rag`、`evidence_extraction`、`cross_lingual_translation`。

## 2. 目录与迁移映射

```text
backend/src/pipeline/
├── graph/                                # 阶段 1：拓扑与 phase 适配（本次未改语义）
├── skills/
│   ├── fact_chain/
│   │   ├── prompts.py                    # 原 source_fact_chain/prompts.py
│   │   ├── runner.py                     # 原 source_fact_chain/runner.py
│   │   ├── service.py                    # 原 source_fact_chain/api.py（服务门面）
│   │   └── extract.py                    # 新增：AgentScope extract skill + shadow 路由
│   └── runtime/
│       ├── llm.py                        # 原 source_fact_chain/providers.py（legacy）
│       ├── agentscope_llm.py             # 新增：OpenAI 兼容模型工厂 + key 轮换
│       └── agent.py                      # 新增：Agent 构建与 sync/async 桥接
├── tools/fact_chain/                     # contracts/core/windowing/projection
├── mcp/                                  # 阶段 4 接入 ReMe
└── contracts/skill_io.py                 # 新增：SkillRequest/SkillResult/SkillError
```

与方案 §3.2.2 的差异（有意）：

1. **服务门面放 `skills/fact_chain/service.py`，不放 `tools/fact_chain/api.py`**。方案硬边界规定 `tools/` 不得 import `skills/`，而门面要构造 provider；放在 `tools/` 会立刻违背边界。
2. **不新增 `graph/nodes.py`/`graph/progress.py`**。方案阶段 1 的拓扑显式化尚未实施（见阶段 0–1 记录 §7）；阶段 2 用 `Provider` 协议挂载 agent，不改 runner 的阶段语义。
3. **verify/translate 保持 legacy**，与阶段 3 计划一致。

## 3. 运行时开关

| 配置 | 默认 | 取值 | 行为 |
|---|---|---|---|
| `pipeline.agent_runtime`（env `PIPELINE_AGENT_RUNTIME`） | `legacy` | `legacy` / `shadow` / `agentscope` | legacy：完全不 import agentscope；shadow：extract 双跑、返回旧结果；agentscope：extract 走 agent，verify/translate 仍走旧 provider |

未知/非法值降级为 legacy 并记 warning（防止 mock 或手写配置让服务启动失败）；真实配置由 `PipelineConfig` 的 `Literal` 校验。

## 4. 验证

CI 等价环境：`uv export --frozen --only-group ci --no-emit-project` + `uv pip install`（PyPI），与 `.github/workflows/ci.yml` 一致。

| 检查 | 命令 | 结果 |
|---|---|---|
| 确定性单元套件 + 覆盖率 | `pytest tests/core/source_fact_chain tests/agents tests/pipeline tests/api/test_wiring_config.py tests/core/.../test_search_service.py --cov=src.pipeline.{tools.fact_chain,skills.fact_chain,skills.runtime,graph.phases.phase_3} --cov-fail-under=85` | **288 passed**，覆盖率 **88.15%** |
| pipeline API（独立进程） | `pytest tests/api/test_pipeline_api.py -q` | **18 passed** |
| Ruff | `ruff check` + `ruff format --check`（改动文件） | 通过 |
| Mypy | `mypy --ignore-missing-imports --follow-imports=silent src/pipeline/{tools,skills}/fact_chain src/pipeline/skills/runtime src/pipeline/graph/phases/phase_3.py src/agents/contracts.py` | Success, 16 files |
| 迁移清单 | `scripts/pipeline_migration_inventory.py` | `src/pipeline` 27 files / 3,507 lines；fact_chain 旧路径 9 files 全部为 shim，新路径 10 files / 2,029 lines |

真实模型影子对照（方案阶段 2 验证项 ①–⑤）未执行：需要真实 API key、黄金文档与 ≥1 周观察窗口。当前以 `FakeChatModel` 验证 AgentScope 结构化输出链路（工具注册、`GenerateStructuredOutput`、schema 校验）和 shadow 路由的确定性行为。

## 5. 顺带修复：阶段 1 的默认产物路径回归

阶段 1 把 `phase_2_adapter.py` / `phase_3_adapter.py` 移到 `src/pipeline/graph/phases/` 后，`Path(__file__).parent...` 的层数未调整，默认输出目录从 `<app root>/data/pipeline` 变成 `<app root>/src/data/pipeline`（本地为 `backend/src/data`）。本次改为 `parents[5]`，并新增位置守卫测试 `test_phase_modules_resolve_default_output_root_to_app_root`，防止后续移动再次静默改路径。容器内仍是 `/data/pipeline`（挂载点），语义与迁移前一致。

## 6. 回滚

1. `PIPELINE_AGENT_RUNTIME=legacy`（或删除配置）→ 新路径不再加载，行为等同阶段 1。
2. `shadow` 的 agent 失败只写日志，主路径继续用旧 provider；不影响产出。
3. 目录迁移可整体 revert 本分支；旧路径 shim 已在 2026-11-18 独立清理中删除。
4. 依赖可回退：删除 `agentscope` 后 `uv lock` 会恢复 certifi/mcp 版本；代码在 legacy 模式下不 import agentscope。

## 7. 未决与后续

- 阶段 2 的真实影子验收（成本增幅 ≤15%、P95 延迟 ≤20%、差异归因）需在具备凭证的环境执行。
- `graph/nodes.py`、`graph/progress.py`、Phase 3 窗口子图仍属阶段 1 未完成项。
- `agentscope` 引入的 `mcp 2.3.0` 与后续 ReMe MCP 客户端版本需要对齐（D4 已定 ReMe 为外部服务）。
- 旧路径 shim 已于 2026-11-18 作为独立清理删除，不与行为切换同 PR。
