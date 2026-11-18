# Pipeline 阶段 4a 迁移实施记录：ReMe 外部记忆服务接入

> 对应方案：[`docs/planned/2026-11-17-pipeline-agentscope-reme-migration.md`](../planned/2026-11-17-pipeline-agentscope-reme-migration.md)（§3.5 ReMe 外部知识服务、§5 阶段 4）
>
> **Status:** in-progress
> **Date:** 2026-11-18
> **Branch:** `impl-stage-4a-reme-memory`（基于阶段 3 `9474ad7`，PR #34）
> 边界：ReMe 仅作外部知识服务；术语库（PG）与证据图（Neo4j）仍是权威存储；默认关闭。

## 1. 本次范围

| 方案阶段 4 产出 | 状态 | 说明 |
|---|---|---|
| ReMe 外部服务客户端 | 完成 | `pipeline/mcp/reme/{contracts,client,config}.py` + `mcp/registry.py` |
| 召回注入（extract 前一次检索） | 完成 | `ExtractSkill._system_prompt` 追加 `<memory source="reme">` 块，标注仅供参考、不得作为证据 |
| `auto_memory` 运行摘要（best-effort） | 完成 | `SourceFactChainService._remember`，只写计数/字段 id/verdict 统计，不写原文与 quote |
| 降级策略 | 完成 | 检索失败/超时 → 空记忆；写入失败 → `accepted=False`，不抛异常 |
| 配置开关 | 完成 | `pipeline.memory`（`PIPELINE_MEMORY_ENABLED/URL/API_KEY/TIMEOUT/TOP_K`），默认 `enabled=False` |
| 术语库迁移（`standardize_entities_and_align_knowledge` → `tools/terminology`） | **未做（拆到 4b）** | 27 files / 5.8k 行 + `terminology_shared` 抽取会影响 `graph_rag` 与休眠模块，单独 PR 降低回滚半径 |
| `StandardizeAgent` 薄封装 | **未做（同 4b）** | 纯确定性匹配，无 LLM 决策；按 `AGENTS.md` §20.2 不做无行为转发层 |

## 2. 接口与配置

```text
POST /search        {"query","top_k"}            → {"cards":[{"text","path","score"}]}
POST /auto_memory   {"session_id","text"}        → {"accepted","detail"}
POST /auto_resource {"path","content"}           → {"accepted","detail"}
GET  /health                                     → 200
```

- 契约文件：`pipeline/mcp/reme/contracts.py`（`MemoryCard` / `RecallResult` / `MemoryWriteReceipt`）；HTTP 契约见 [ReMe 外部知识服务 HTTP 契约](2026-11-18-reme-http-contract.md)。
- 注入格式：`<memory source="reme" note="reference only; never use as evidence or quote">…</memory>`；卡片文本做 XML 转义，防止记忆内容闭合注入块。
- 召回 query：当前窗口文本前 400 字符；`top_k` 来自配置（默认 5）。
- 写入内容：`language/windows/facts/field_ids/verifications/rejections/prompt_versions`；不含任何原文、quote、用户名或文件路径。
- 配置偏离：方案写作 `cfg.pipeline.mcp.reme.*`，实现按仓库现有扁平配置约定使用 `cfg.pipeline.memory.*`（env `PIPELINE_MEMORY_*`）。

## 3. 不变量

- `PIPELINE_MEMORY_ENABLED=false`（默认）时使用 `NullMemoryClient`，零 HTTP、零行为变化；
- 记忆只进入 extract 的 system prompt，不改变 verify/translate，不进入 `facts/verifications/english` 产物；
- runner 的重试、预算、事件与 `ChainRun` 契约不变；
- ReMe 不可用时主路径成功率不受影响（检索降级为空、写入失败仅告警）。

## 4. 验证

CI 等价环境（`uv export --frozen --only-group ci` + PyPI 安装）：

| 检查 | 命令 | 结果 |
|---|---|---|
| 确定性套件 + 覆盖率（含 `src.pipeline.mcp`） | `pytest tests/core/source_fact_chain tests/agents tests/pipeline tests/api/test_wiring_config.py ...` | **308 passed**，覆盖率 **88.84%** |
| pipeline API | `pytest tests/api/test_pipeline_api.py -q` | **18 passed** |
| Ruff / Mypy（26 files，含 `src/pipeline/mcp`） | `ruff check` / `ruff format --check` / `mypy` | 通过 |
| ReMe 故障注入（单测） | `httpx.MockTransport`：500、连接失败 | 检索返回空、写入返回 `accepted=False`，无异常 |
| 禁用路径 | `NullMemoryClient` | 不发起任何 HTTP，`run` 行为与阶段 3 一致 |

未执行：真实 ReMe 服务联调（服务端尚未部署）与 50–100 条查询的召回评测；需在 ReMe 容器就绪后执行。

## 5. 回滚

`PIPELINE_MEMORY_ENABLED=false` 即完全回退；`mcp/` 与 skills 的 memory 参数均有默认空实现，删除配置后不加载 `HttpMemoryClient`。

## 6. 后续（4b）

- 抽取 `src/core/terminology_shared/`（`contracts.py`、`hgvs_normalizer.py`、`context_pack/`），迁移其余实现到 `pipeline/tools/terminology/` 并保留 shim；
- 更新 `graph_rag`、休眠 `evidence_extraction` 的 7 个文件 / 8 处 import；
- ReMe `auto_resource` 接入 Phase 2 产物（`output.md`/`metadata.json`）与召回评测。
