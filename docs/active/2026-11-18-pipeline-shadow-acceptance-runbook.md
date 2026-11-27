# Pipeline 迁移验收 Runbook（真实模型 / ReMe / 窗口并行）

> 配套方案：[`docs/planned/2026-11-17-pipeline-agentscope-reme-migration.md`](../planned/2026-11-17-pipeline-agentscope-reme-migration.md) §5
> 用途：在具备真实 LLM 凭证与黄金文档的环境执行阶段 2/3/4 的剩余验收项。代码侧门禁见各阶段实施记录。
> **Status:** active
> **Date:** 2026-11-18

## 1. 前置条件

| 项 | 要求 |
|---|---|
| LLM | `FAST_LLM_*` / `REASONING_LLM_*` 可用（extract/translate 用 fast，verify 用 reasoning） |
| 黄金文档 | 3–5 篇已解析文档（覆盖中文/英文、单窗口/多窗口、重叠区重复事实） |
| ReMe | 独立服务已部署，`/health` 返回 200；`PIPELINE_MEMORY_ENABLED=true` 时可用 |
| 运行环境 | `uv sync --frozen` 完成；`backend/` 为工作目录 |

## 2. 阶段 2/3：真实影子对照

同一文档、同一配置分别跑旧路径与 AgentScope 路径：

```bash
cd backend

# 1) 旧 provider
PIPELINE_AGENT_RUNTIME=legacy uv run uvicorn app.main:app --port 8000
# 提交一次 pipeline run，产出
#   data/pipeline/<run>/phase_3/<doc>/chain_run.json
mv data/pipeline/<run>/phase_3/<doc>/chain_run.json /tmp/legacy.json

# 2) AgentScope 全链路
PIPELINE_AGENT_RUNTIME=agentscope uv run uvicorn app.main:app --port 8000
# 同一文档重跑（建议 force_rebuild，避免复用旧 chain_run）
mv data/pipeline/<run>/phase_3/<doc>/chain_run.json /tmp/agent.json

# 3) 逐字段 diff
uv run python scripts/pipeline_shadow_compare.py /tmp/legacy.json /tmp/agent.json
```

判定：

- 退出码 `0` 且 `identical=true`：facts（id/字段/极性/主体/span/window）、verification（label+reason）、English（status+text）全部一致，且两次运行的 `ChainConfig` 与 `PromptVersions` 完全相同（配置或提示词不一致会直接失败，避免拿不同版本的 run 做对照）。
- 退出码 `1`：按输出逐条归因（模型随机性/提示词/校验顺序），记录到实施记录；不允许用“可接受差异”跳过 facts 差异。
- 成本：`legacy_provider_calls` vs `agent_provider_calls`，增幅 ≤15%。
- 延迟：用同一台机器各跑 5 次取 P95，增幅 ≤20%。

连续 ≥1 周影子运行无 P0/P1 差异后，才允许把 `PIPELINE_AGENT_RUNTIME` 切到 `agentscope`。

## 3. 阶段 4a：ReMe 联调

```bash
# 服务健康
curl -sS -H "X-API-Key: $PIPELINE_MEMORY_API_KEY" "$PIPELINE_MEMORY_URL/health"

# 开启记忆（默认关闭），其余保持 legacy 或 agentscope
PIPELINE_MEMORY_ENABLED=true
PIPELINE_MEMORY_URL=http://<reme-host>:<port>
PIPELINE_MEMORY_TIMEOUT=0.8
PIPELINE_MEMORY_TOP_K=5
PIPELINE_MEMORY_API_KEY=...
```

验收：

1. **故障注入**：停掉 ReMe 后跑同一文档，`chain_run.json` 必须与开启前一致（记忆不得进入 facts/verifications/english）。
2. **召回评测**：50–100 条历史相似文献查询，比较有无记忆的 top-5 命中率/相关性；指标先定义后执行。
3. **写入检查**：`auto_memory` 摘要只含计数/字段 id/verdict，不含原文与 quote；ReMe workspace 不含用户私有内容。
4. **降级**：`auto_memory` 失败只告警，不改变 run 状态。

## 4. 阶段 1：窗口并行等价性（未实现，验收前置）

窗口 `Send` fan-out 落地后，同一文档分别用串行与 `concurrency=2` 跑 5 次：

- `chain_run.json` 的 facts/verifications/english 集合逐字段相等（允许 event 顺序差异）；
- 重复 5 次结果稳定；
- 若出现差异，先修确定性合并（按 window 顺序、fact_id），不得放宽断言。

## 5. 角色与签字

| 项 | 责任人 | 证据 |
|---|---|---|
| 影子 diff 归因 | 领域开发 | `/tmp/legacy.json`、`/tmp/agent.json`、diff 输出 |
| 成本/延迟 | 平台开发 | 5 次运行记录 + P95 计算 |
| ReMe 运维/备份 | 运维 | workspace 备份、健康检查、容量 |
| 切流决定 | 需求方 | 本 runbook 验收结果 |
