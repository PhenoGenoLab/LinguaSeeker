# API v2 — 设计（model / DTO 先行）

> 状态：DTO 已落代码（`src/api/v2/contracts.py`，含 `tests/api/test_v2_contracts.py`）；路由尚未挂载。
> 目标：**run = 跑完一个目录**；**每个子智能体可单独调用**。

## 1. 版本与挂载

- 新前缀：`/api/v2`。
- v1 保持挂载，v2 稳定后删除 v1（一次性切换，不做字段级兼容）。
- 路由文件：`src/api/v2/router.py`；契约：`src/api/v2/contracts.py`。
- 健康检查独立于版本：`/health`（v2 挂载时一并调整）。

## 2. 核心模型变化

### 2.1 run = 目录

一次 `POST /api/v2/runs` 接收一个**服务端目录**，展开为 N 个按文档的 run：

```
DirectoryRunRequest(directory, recursive, filename_patterns, 抽取选项…)
   └─ batch_id 分组 N 个 PipelineGraphState（每文档一个 source_document_id）
```

- 目录根：`backend/data/pipeline/inputs`（配置键 `pipeline.input_root` 后续加入）。
  只允许相对路径；解析后必须仍在根内，否则 400。
- 需要新增持久化：`pipeline_runs.batch_id`（可空、带索引）与 `source_directory`。
  迁移脚本在路由实现阶段加入；同一目录重复提交按 `source_key` 去重（沿用现有机制）。
- 状态聚合：`GET /api/v2/runs/batches/{batch_id}` 返回计数与逐文档句柄。

### 2.2 子智能体单独路由

每个智能体一个入口，统一异步任务模型（202 + job 轮询）：

```
POST /api/v2/agents/{agent}/runs            → AgentJobAccepted
GET  /api/v2/agents/jobs/{job_id}           → AgentJobStatus
GET  /api/v2/agents/jobs/{job_id}/result    → <Agent>Result
```

- `agent ∈ {acquisition, parsing, fact_chain, standardization, review, graph_retrieval}`
- 新增表 `agent_jobs`：`job_id, agent, status, request jsonb, result jsonb, error, created_at, started_at, finished_at`。
- 结果 DTO 按 agent 分别定义（见 §4），`result` 端点按 `agent` 返回对应模型。
- review 是请求-响应型，按动作再分：`/agents/review/search`、`/agents/review/feedback`、
  `/agents/review/chat`，共用 `ReviewJob*` 外层。

## 3. 路由表

| 方法 | 路径 | 请求 | 响应 |
|---|---|---|---|
| POST | `/api/v2/runs` | `DirectoryRunRequest` | `DirectoryRunResponse`（202） |
| GET | `/api/v2/runs` | `limit/offset/status` | `RunListResponse` |
| GET | `/api/v2/runs/{run_id}` | — | `RunStatusResponse` |
| GET | `/api/v2/runs/batches/{batch_id}` | — | `BatchStatusResponse` |
| POST | `/api/v2/runs/{run_id}/rerun` | `StageRerunRequest` | `RunHandle`（202） |
| POST | `/api/v2/agents/acquisition/runs` | `AcquisitionAgentRequest` | `AgentJobAccepted` |
| POST | `/api/v2/agents/parsing/runs` | `ParsingAgentRequest` | `AgentJobAccepted` |
| POST | `/api/v2/agents/fact_chain/runs` | `FactChainAgentRequest` | `AgentJobAccepted` |
| POST | `/api/v2/agents/standardization/runs` | `StandardizationAgentRequest` | `AgentJobAccepted` |
| POST | `/api/v2/agents/graph_retrieval/runs` | `GraphRetrievalAgentRequest` | `AgentJobAccepted` |
| POST | `/api/v2/agents/review/search` | `ReviewSearchRequest` | `AgentJobAccepted` |
| POST | `/api/v2/agents/review/feedback` | `ReviewFeedbackRequest` | `AgentJobAccepted` |
| POST | `/api/v2/agents/review/chat` | `ReviewChatRequest` | `AgentJobAccepted` |
| GET | `/api/v2/agents/jobs/{job_id}` | — | `AgentJobStatus` |
| GET | `/api/v2/agents/jobs/{job_id}/result` | — | 按 agent 的结果模型 |

## 4. DTO 清单

### 4.1 run / batch

| 模型 | 关键字段 |
|---|---|
| `DirectoryRunRequest` | `directory`, `recursive`, `filename_patterns`, `extraction_target`, `extraction_profile`, `extraction_mode`, `ablation_*`, `review_reject_policy`, `extraction_track_mode`, `fail_fast`, `dry_run` |
| `RunHandle` | `processing_run_id`, `source_document_id`, `relative_path`, `status`, `status_url` |
| `DirectoryRunResponse` | `batch_id`, `status`, `documents: list[RunHandle]`, `status_url` |
| `BatchCounts` | `total/queued/running/completed/failed/skipped` |
| `BatchStatusResponse` | `batch_id`, `directory`, `status`, `counts`, `created_at`, `documents` |
| `RunStatusResponse` | `processing_run_id`, `source_document_id`, `batch_id`, `relative_path`, `pipeline_status`, `current_stage`, `skip_standardization_reason`, `stages`, `error_message`, `error_stage`, 时间字段 |
| `StagesResponse` | `acquisition`, `parsing`, `fact_chain`, `standardization`（`StageStatusResponse`） |
| `StageStatusResponse` | `status`, 时间字段, `error`, `summary`, `nodes`, `count` |
| `StageRerunRequest` | `stage: Literal["acquisition","parsing","fact_chain","standardization"]`, `force: bool` |

### 4.2 agent job 外层

| 模型 | 关键字段 |
|---|---|
| `AgentName` | `acquisition \| parsing \| fact_chain \| standardization \| graph_retrieval \| review` |
| `AgentJobAccepted` | `job_id`, `agent`, `status`, `status_url`, `result_url` |
| `AgentJobStatus` | `job_id`, `agent`, `status`, `created_at`, `started_at`, `finished_at`, `error` |
| `AgentJobError` | `kind`(transient/permanent), `message`, `stage` |

### 4.3 各 agent 请求/结果

| Agent | 请求 | 结果 |
|---|---|---|
| acquisition | `mode: online \| files \| directory`；`query`/`identifiers`/`files`/`directory`；`relevance_gate`、`literature_types`、`download_pdfs` | `AcquisitionAgentResult`：`documents: list[AcquiredDocument]`（`path`, `sha256`, `title`, `source`, `source_document_id?`） |
| parsing | `files` 或 `directory`；`output_dir`；`force` | `ParsingAgentResult`：`documents: list[ParsedDocument]`（`md_path`, `metadata_path`, `images_dir`, `pages`） |
| fact_chain | `source: {document_id} \| {md_path, metadata_path}`；`extraction_target`、`extraction_profile`、`extraction_mode`、`window_chars`、`window_overlap`、`max_provider_calls` | `FactChainAgentResult`：`chain_run_path`, `facts`, `verifications`, `rejections`, `projection_path`, `prompt_versions` |
| standardization | `source: {document_id} \| {dual_result_path}`；`force` | `StandardizationAgentResult`：`standardized_count`, `unstandardized_count`, `ambiguous_count`, `output_path`, `skipped_reason` |
| graph_retrieval | `mode: retrieve \| qa`；`query`；`extraction_target?`；`hops` | `GraphRetrievalAgentResult`：`context`, `nodes`, `edges`, `sources` |
| review | `ReviewSearchRequest`/`ReviewFeedbackRequest`/`ReviewChatRequest` | `ReviewSearchResult` / `ReviewFeedbackResult` / `ReviewChatResult` |

## 5. 校验与错误

- 统一错误体 `ErrorResponse {code, message, details?}`；路径越界、目录为空、非法文件名模式返回 422/400。
- 目录展开上限 `max_documents`（默认 200），超出返回 413。
- 所有时间字段 ISO-8601；所有 ID 为字符串 UUID。

## 6. 待确认的两个结构选择

1. **批次聚合落库**：`pipeline_runs` 增加 `batch_id` 列（本设计采用），还是只把 batch 放在 `agent_jobs`/内存里？
2. **agent 路由默认异步**：全部 202+轮询（本设计采用），还是轻量 agent（acquisition search、graph_retrieval）同步返回？

确认后按 §3 实现路由、表结构与迁移。
