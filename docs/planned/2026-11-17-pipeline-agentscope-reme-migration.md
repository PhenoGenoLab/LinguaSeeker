# Pipeline 技术栈替换调研与分阶段迁移方案

> LangGraph 状态图 + AgentScope 子智能体 + ReMe 知识/记忆层，仅改领域层，外层服务不动
>
> 状态：实施中（阶段 0–4 代码已完成；真实模型影子验收与 ReMe 服务联调待执行）
> **Status:** active
> **Created:** 2026-11-17
> **Revised:** 2026-11-18（r3：阶段 0–4b 实施结果、决策落定、偏差与未完成项，见 §5.6）
> **PR:** #30（r2 修订；初版 #28 已合并）；实施 PR #32 / #33 / #34 / #35 / #36
> 目标仓库：`/data/yangzs/Projects/01_Platform/01_ACMG_Lingua`
> 适用对象：pipeline 服务（`backend/src/agents/` + 其调用的 `backend/src/core/*` 领域切片 + `backend/src/api/v1/pipeline.py`；迁移后领域层为 `backend/src/pipeline/{graph,skills,tools,mcp}`）
> 结论摘要：**总体可行，3 处定位调整已按建议落地**；ReMe 已按外部知识库服务接入（默认关闭）；阶段 0–4b 代码完成，9 个架构决策点全部落定（见 §8）；真实模型影子验收（成本/延迟/差异归因）与 ReMe 服务联调仍未执行。

---

## 0. 结论摘要（先看这一页）

### 0.1 一句话结论

技术栈替换**可行**，但“每个节点都变成自主 AgentScope 智能体、ReMe 全面替换现有知识库”如果按字面执行，会把临床事实的产出交给非确定性组件，削弱现有证据链的确定性与可追溯性；建议采用**“LangGraph 定拓扑 + AgentScope 有界子智能体 + ReMe 记忆/文献知识层”**的组合，其中**术语库（HGNC/ClinVar/OMIM/HPO/ClinGen）与证据图（Neo4j）继续作为权威事实存储**，ReMe 承担子智能体的记忆、召回与文献知识沉淀。

### 0.2 五个事实判断

| # | 判断 | 依据 |
|---|---|---|
| 1 | **LangGraph 已经是本仓库的编排引擎**，不是要“新引入” | `orchestrator.py:247`、`evidence_extraction/workflow.py:370`、`cross_lingual_translation/api.py:103` 共 3 个 `StateGraph`；`langgraph>=1.2.0` 已在 `backend/pyproject.toml` |
| 2 | 缺的是**拓扑显式化 + 断点/人工介入语义 + 节点级可观测**，不是图引擎本身 | 全仓库无 `checkpointer`、无 `interrupt()`、无 `Send`；崩溃恢复是“标记 FAILED 后整阶段重跑”，不是断点续跑（`state_persistence.py:560`、`contracts.py`） |
| 3 | **“自研 agent pipeline”实体上是 Phase 3 的 `source_fact_chain`（1858 行）及各阶段 adapter/服务**，AgentScope 化真正有收益的是 Phase 3 的抽取/核验/翻译推理 | `phase_3_adapter.py:37-40`、`source_fact_chain/api.py:114`；Phase 4 是确定性术语匹配（5776 行），Phase 1/2 主要是外部 SDK/HTTP 适配 |
| 4 | **ReMe 不是通用文档 RAG/图数据库**，它是“文件原生、可演化的 Agent 知识/记忆库”：Markdown + BM25/可选向量 + wikilink | ReMe 0.4.2.3 README、`reme/steps/index/search.py`（BM25+向量 RRF）、`auto_resource` 仅支持 md/txt/json/jsonl/csv/yaml/html |
| 5 | **依赖存在真实冲突**，不能“直接 `uv add` 了事” | 实测：`reme-ai[core]==0.4.2.3` 钉死 `agentscope==2.0.11`；`reme-ai` 基础包要求 `fastapi>=0.162.0`、`numpy>=2.5.4`（Py≥3.12）；`agentscope 2.0.12` 要求 `certifi>=2026.10.19`；当前锁文件是 fastapi 0.136.3 / numpy 2.3.5 / certifi 2026.5.20 |

### 0.3 建议的目标形态（与字面要求的差异）

```text
字面要求                                 建议落点
─────────────────────────────────────   ─────────────────────────────────────────
LangGraph 状态图整体编排          →      保留并显式化：4 个 phase 节点 + 每个 phase 内
                                        的 stage 子图（extract/verify/translate 等）
每个节点用 AgentScope 子智能体    →      每个 phase 一个“有界子智能体”（bounded agent）：
                                        工具=现有确定性服务，输出=现有 Pydantic 契约；
                                        推理与工具编排归 AgentScope，校验/落库仍归领域代码
知识库采用 ReMe                   →      ReMe 作为子智能体记忆 + 文献知识层（Markdown 卡片、
                                        BM25/向量召回、wikilink）；术语库与证据图保持权威
pipeline 领域层目录调整           →      按职责拆到 src/pipeline/{graph,skills,tools,mcp,contracts}：
                                        graph=LangGraph 拓扑，skills=AgentScope 子智能体，
                                        tools=确定性能力，mcp=ReMe 等外部协议；
                                        旧路径过渡期 shim，外层 API/数据结构不变
外层服务不动                      →      不新增/不修改 HTTP 契约、表结构、队列语义、状态枚举
```

### 0.4 工作量级别

| 范围 | 估算 |
|---|---|
| 核心替换（阶段 0–4：拓扑、AgentScope 运行时、四阶段 agent 化、ReMe 记忆接入） | **10.5–12.5 人周**（1–2 名熟悉该仓库的工程师；含 20% 缓冲为 12.5–15 人周） |
| 目录迁移与 import 改写（r2 新增：`src/pipeline/{graph,skills,tools,mcp}`） | 约 **1.5 人周**（56 个文件 `git mv`、56 个测试文件/153 行 import 改写、约 15 个 shim） |
| 可选的知识库整体切换（Neo4j GraphRAG → ReMe，含数据迁移与 Phase 5 QA 改造） | 额外 **3–5 人周**，且不建议在本轮做 |
| 风险缓冲 | 上述基础上 +20%（影子运行、对照评测、回滚演练） |

> 目录迁移的 1.5 人周已计入“核心替换”的 10.5–12.5 区间；若不做目录重构，核心部分仍为原估算 9–11 人周。

### 0.5 决策点（9 项已全部落定，详见 §8）

1. **D1 ReMe 的定位**：✅ 记忆/文献知识层（非权威库）；术语库（PG）与证据图（Neo4j）保持权威。
2. **D2 节点粒度**：✅ 4 个 phase 节点；Phase 3 内部 extract/verify/translate 以 skill 形式挂载。
3. **D3 智能体自主度**：✅ 有界工具调用 + 结构化输出；不使用自由 ReAct。
4. **D4 ReMe 部署形态**：✅ **已确认（需求方，2026-11-17）——ReMe 作为外部服务，用于知识库调用**，不计入“外层服务不动”的冻结范围。
5. **D5 版本钉法**：✅ backend `agentscope==2.0.12`（`certifi` 随之上调）；ReMe 未装进 backend。
6. **D6 Phase 4 是否 agent 化**：✅ 不封装（纯确定性匹配，无无行为转发层）；目录仍迁入 `tools/terminology`。
7. **D7 遗留代码处置**：✅ `evidence_extraction` 与 `cross_lingual_translation` 保持休眠、不迁移。
8. **D8 恢复与人工介入语义**：✅ v1 保持不变（未引入 checkpointer/`interrupt()`）。
9. **D9 领域层目录划分**：✅ `src/pipeline/{graph,skills,tools,mcp,contracts}`；skills/tools 边界与 MCP 配置位置见 §3.2 与 §5.6 的偏差记录。

> 决策落定时间：D4 于 2026-11-17 由需求方确认；其余按推荐项在阶段 2 前统一落定，实施结果与偏差见 §5.6。

---

## 1. 范围、方法与判定标准

### 1.1 什么是本仓库的 “pipeline 服务”

该仓库是单体仓库（FastAPI backend + React frontend + Rust 扩展），**pipeline 不是独立部署单元**，而是 backend 内的一个垂直模块：

| 层 | 位置 | 本次是否可改 |
|---|---|---|
| 外层 HTTP/DI | `backend/src/api/v1/pipeline.py`、`api/wiring.py`、`app/main.py` | **不可改**（契约冻结） |
| 外层调度/持久化 | `backend/src/agents/{runner,dispatcher,state_persistence,processing_cache}.py`、`dao/postgresql/*`、`database/migrations/*` | **不可改**（属于外层服务） |
| **领域层（本次替换对象）** | 现状：`backend/src/agents/{orchestrator,phase_1..4_adapter}.py` + `backend/src/core/{ingest_and_digitize_data,source_fact_chain,standardize_entities_and_align_knowledge}`；目标：按 `backend/src/pipeline/{graph,skills,tools,mcp,contracts}` 组织（见 §3.2） | **可改**（仅包布局与内部实现） |
| 领域共享（不迁） | `backend/src/agents/contracts.py`（冻结契约）、`backend/src/core/{graph_rag,evidence_extraction,cross_lingual_translation,terminology_shared}` | 仅允许必要的 import 适配 |
| 外部依赖 | LLM（OpenAI 兼容）、Embedding/Rerank、MinerU、lit-acquisition、Neo4j、PostgreSQL、Redis、Rust `net_io/files_io` | 接口保持不变 |
| 新增外部服务 | ReMe（知识库调用，HTTP/MCP） | 允许新增；不改动现有外层服务 |

> 说明：`src/agents/runner.py`、`dispatcher.py`、`state_persistence.py` 虽然物理上位于 `agents/`，但它们是**外层契约的实现**（队列、租约、心跳、JSONB 快照）。迁移中把它们视为“不可改”，只允许在其内部实现细节上做兼容性调整。

### 1.2 调研方法

- 静态阅读：14 个 `agents/` 文件、4 个领域切片、API 契约、DB 模型与迁移、19 个 `tests/agents` 测试文件、18 个 pipeline API 测试。
- 目录与 import 统计（r2）：3 个待迁包 56 个 py 文件 / 9,889 行；20 条非测试 import；56 个测试文件 / 153 条 import；13 个随迁 README（2026-11-17 工作区 `find`/`grep` 实测，见 §3.2.5）。
- 依赖实测：用 `uv lock` 在独立临时工程中解析 `agentscope 2.0.12` + `reme-ai 0.4.2.3` + 现有锁定版本（结果见 §4.4）。
- 上游事实核对：PyPI 元数据、AgentScope 2.0.12 文档与 wheel 源码、ReMe 0.4.2.3 README/源码，均标注版本与日期。
- 本次**不修改业务代码**；所有结论以 `path:line` 或版本事实为据。

### 1.3 判定标准

| 结论 | 含义 |
|---|---|
| **可直接替换** | 接口/语义有 1:1 对应，替换后行为可验证一致 |
| **需适配** | 能力可覆盖，但需要适配层/契约转换/新依赖 |
| **不建议替换** | 替换会引入正确性、可追溯性或运维风险，收益不足 |
| **不可行** | 存在硬阻塞（版本冲突、能力缺失、数据不可迁移） |

---

## 2. 现状（As-Is）

### 2.1 调用链：一次 pipeline run 的完整路径

```mermaid
flowchart TD
  A["POST /api/v1/pipeline/run<br/>pipeline.py:301"] --> B["去重/缓存/落 upload<br/>pipeline.py:360-455"]
  B --> C["enqueue pipeline_jobs<br/>pipeline.py:484-492"]
  C --> D["SingleJobDispatcher.claim_next<br/>FOR UPDATE SKIP LOCKED<br/>dispatcher.py:93"]
  D --> E["PipelineGraphState.from_request_data<br/>contracts.py:526"]
  E --> F["PipelineRunner.start<br/>durable claim + heartbeat<br/>runner.py:95-187"]
  F --> G["PipelineSemaphore(2)<br/>runner.py:131"]
  G --> H["PipelineOrchestrator.run<br/>LangGraph ainvoke<br/>orchestrator.py:315"]
  H --> P1["Phase1Adapter<br/>DocumentAcquisitionService"]
  P1 --> P2["Phase2Adapter<br/>ParseDocumentService (MinerU)"]
  P2 --> P3["Phase3Adapter<br/>SourceFactChainService"]
  P3 --> P4["Phase4Adapter<br/>EntityStandardizationService"]
  P4 --> Z["COMPLETED / FAILED<br/>orchestrator.py:358-381"]
  Z --> Q["job_queue.complete/fail<br/>dispatcher.py:128-136"]
  G -. "每阶段 save + on_state_change" .-> R["pipeline_run_states.state_json<br/>runner LRU"]
  R --> S["GET /runs/{id}/status<br/>前端每 2s 轮询"]
```

关键事实：

- **状态真相源**是 `pipeline_run_states.state_json`（JSONB），每阶段入口/出口各保存一次；runner 另有 100 条 LRU 内存缓存（`runner.py:64`）。
- **没有 LangGraph checkpointer**：图在内存中 `ainvoke`，崩溃后由 `recover_orphaned_runs` 把心跳超时的 run 标为 `FAILED`（`state_persistence.py:560`），不是断点续跑。
- **重试**在 adapter 外层：`RetryablePhaseExecutor(max_retries=2, backoff_base=30s)`，仅对 `RetryablePhaseError` 重试（`concurrency.py:31-80`）。
- **阶段重跑**通过 `mode=phase + target_phase` 触发；重跑前会清理该阶段产物与派生行（`state_persistence.py:208-280`）。
- **并发**只有进程内信号量（同时 2 个 run）；阶段内部大多串行，Phase 3 的窗口循环是同步的（`source_fact_chain/runner.py:81-111`）。

### 2.2 四个阶段与领域代码的真实执行路径

#### Phase 1 — 文献/文档获取

| 项 | 内容 |
|---|---|
| Adapter | `Phase1Adapter.run`（`phase_1_adapter.py:53-156`） |
| 领域服务 | `DocumentAcquisitionService.acquire`（`ingest_and_digitize_data/document_acquisition/service.py`） |
| 真实执行 | 上传文件落盘 / 在线检索与下载委托给外部 `lit-acquisition==0.4.1` SDK（`wiring.py`），HTTP 由 Rust `net_io` 承担，失败回退 httpx |
| 输入 | `DocumentAcquisitionRequest`（source/filename/content/query/identifiers/relevance_gate/literature_types） |
| 输出 | `AcquisitionOutput(pdf_path)`；若 SDK 已预解析则写入 `state.pre_parsed_markdown` |
| 失败分类 | 无可下载 PDF → `PermanentPhaseError`；超时/限流 → `RetryablePhaseError` |
| AgentScope 化收益 | **低**：本质是外部 SDK 编排与错误分类；agent 只能包一层，LLM 不参与 |

#### Phase 2 — 文档解析

| 项 | 内容 |
|---|---|
| Adapter | `Phase2Adapter.run`（`phase_2_adapter.py`） |
| 领域服务 | `ParseDocumentService.parse_local_files_and_save` |
| 真实执行 | MinerU 远端优先、本地容器兜底（`MinerULocalParser`，`:44321`），产出 `metadata.json`（pages/content_blocks）、`md`、图片 |
| 输出 | `ParseOutput(md_path, metadata_path, output_dir, images_dir)` |
| AgentScope 化收益 | **很低**：纯外部解析服务调用，无推理 |

#### Phase 3 — 原文事实链（当前生产路径）

| 项 | 内容 |
|---|---|
| Adapter | `Phase3Adapter.run`（`phase_3_adapter.py:91-240`） |
| 领域服务 | `SourceFactChainService`（`source_fact_chain/api.py`） |
| 内部阶段 | 窗口切分（4000 字符 / 200 重叠）→ 每窗口 `extract` → 每窗口 `verify` → 仅展示字段 `translate` → 双轨投影 |
| 模型 | extract/translate 用 `cfg.llm`（fast tier），verify 用 `cfg.reasoning`（`providers.py:31-43`，符合 AGENTS §23） |
| 关键语义 | 事实 ID 只由源内容决定（document/source hash/字段/原值/极性/主体/span），与模型、提示词无关；`supported=0` → `skip_phase_4_reason=not_relevant`；复用键 = `source_hash + ChainConfig + PromptVersions` |
| 产物 | `chain_run.json`、`facts.jsonl`、`verifications.jsonl`、`english.jsonl`、`bilingual.jsonl`、`extraction_result.json`、`original.json`、`translated.json` |
| 确定性 | 强：schema 校验、原子性/极性/主体/引句定位校验都在 `core.py`，provider 只返回文本 |
| AgentScope 化收益 | **最高**：窗口级抽取、核验、翻译天然是“子智能体 + 工具 + 结构化输出”的场景 |

> 注意：仓库中另有 `evidence_extraction`（12,214 行，内部也是 LangGraph，18 个节点）与 `cross_lingual_translation`（5,328 行，内部 LangGraph）。它们在当前 pipeline 路径中**不再承担 Phase 3 生产抽取**（Phase 3 已切到 `source_fact_chain`），主要作为历史/基准/类型来源保留。迁移方案不要把这两块当作“必须 agent 化”的主体，否则工作量会翻倍。

#### Phase 4 — 实体标准化与知识对齐

| 项 | 内容 |
|---|---|
| Adapter | `Phase4Adapter.run`（`phase_4_adapter.py:54-168`） |
| 领域服务 | `EntityStandardizationService.run_dual_result` |
| 真实执行 | 读 Phase 3 的 `extraction_result.json` → 混合匹配（精确别名优先 → pgvector 语义召回 → rerank 阈值）→ 写 PG（标准实体/匹配/绑定/证据）→ 可选写 Neo4j 文献图 → ACMG 投影 |
| 术语库 | HGNC / ClinVar / OMIM / HPO / ClinGen，PG 表 + `terminology_embeddings`（`Vector(1024)`，`models.py:514-542`） |
| 输出 | `StandardizationOutput(match_count, standardized_count, ambiguous_count, unmapped_count)`；零候选 → `skip_phase_4_reason=no_candidates` |
| AgentScope 化收益 | **低–中**：核心是确定性匹配与持久化；只有“歧义消解/跨语言疾病名兜底”适合 LLM 参与 |
| ReMe 化可行性 | **不可**（术语库是有约束的结构化数据，不是 Markdown 记忆） |

### 2.3 状态机与持久化契约（外层依赖，冻结）

`PipelineGraphState`（`contracts.py:433-569`）是跨节点唯一状态，字段分五组：

| 组 | 字段 | 说明 |
|---|---|---|
| 身份 | `processing_run_id`、`source_document_id`、`owner_user_id` | UUID 字符串；owner 用于多租户 404 语义 |
| 模式 | `mode`、`source_type`、`target_phase` | FULL / PHASE；LOCAL / ONLINE |
| 去重 | `source_key`、`content_hash` | 活动 run 唯一索引 + L1/L2 缓存键 |
| 状态 | `pipeline_status`、`phase_1..4_status` | 状态转移守卫（`contracts.py:117-174`） |
| 产物 | `phase_1..4_output` | 四个强类型 Pydantic 模型 |
| 控制 | `extraction_target`、`extraction_profile`、`extraction_mode`、ablation 开关、`review_reject_policy`、`extraction_track_mode` | 直接传给领域层 |
| 其他 | `error_message/error_phase`、时间戳、`skip_phase_4_reason`、`upload_file_path`、`pre_parsed_markdown`、在线检索字段 | — |

状态转移表（合法边）：

```text
PipelineStatus: PENDING→RUNNING/FAILED; RUNNING→COMPLETED/FAILED; FAILED→PENDING; COMPLETED→PENDING
PhaseStatus:    PENDING→RUNNING/SKIPPED/FAILED; RUNNING→COMPLETED/FAILED/SKIPPED;
                COMPLETED/SKIPPED/FAILED→PENDING（阶段重跑）
```

持久化表（不可改列名/类型）：

- `pipeline_run_states(processing_run_id, source_document_id, owner_user_id, state_json, pipeline_status, last_completed_stage, source_key, owner_worker_id, heartbeat_at, ...)`，活动 run 的部分唯一索引 `(owner_user_id, source_key) WHERE status IN ('pending','running')`（`models.py:661-723`）。
- `pipeline_jobs`（队列，`FOR UPDATE SKIP LOCKED` 认领）、`document_processing_cache`（content_hash → 结果快照）。
- 领域层还会写 `source_documents` 的正文/块/语言列（渲染与证据检索读取）以及磁盘 `backend/data/pipeline/<run_id>/phase_{2,3}/...` 产物。

### 2.4 现有 LangGraph 使用情况（关键现状）

| 图 | 位置 | 节点 | 特点 |
|---|---|---|---|
| 外层 pipeline | `agents/orchestrator.py:247` | `phase_1..4` | 条件入口（PHASE 模式）、条件边、FAILED 短路；**无 checkpointer** |
| 证据抽取（历史/基准路径） | `evidence_extraction/workflow.py:370` | relevance_scan / graph_context / extraction / grounding / review / quality… | 同步 + 异步两套图；复杂 stage 逻辑在类里 |
| 翻译（历史路径） | `cross_lingual_translation/api.py:103` | format / detect / translate / skip | 简图，当前 Phase 3 不再整篇翻译 |

**结论**：LangGraph 不是缺口。真正缺口是：
1. 图的粒度太粗（4 个 phase），阶段内部仍是手写 `for` 循环/顺序调用，无法在图上观察与恢复；
2. 没有 `interrupt()`/checkpointer，人工介入只存在于 Phase 5（图外）；
3. 节点内是普通 Python 服务，没有“子智能体”抽象，模型调用、工具、记忆耦合在 provider 里。

### 2.5 知识库与检索调用点（现状）

| 调用点 | 存储 | 用途 | 当前开关 |
|---|---|---|---|
| 术语匹配 | PostgreSQL 表 + `terminology_embeddings`（pgvector 1024 维）+ 外部 rerank | Phase 4 把基因/变异/疾病/表型映射到标准术语 | 始终启用 |
| GraphRAG 上下文 | Neo4j（`:Gene/:Variant/:Disease/:Phenotype/:Evidence/:Document/:ProcessingRun`） | 证据抽取时注入子图上下文；Phase 4 写回文献图；Phase 5 QA 查询 | `graph_rag.enabled: false`（`config/defaults/main.yaml:128`），但 Phase 4 写图未受该开关约束（`standardize.../api.py:192`） |
| 处理缓存 | Redis L1 + PG L2 | 相同内容哈希直接返回历史结果 | 可配置 |
| 文献搜索/画像 | PG（`source_documents`、文献档案）+ 搜索索引 | 前端列表/检索 | 始终启用 |

**关键**：当前所谓“知识库”实际是**两套不同性质的东西**：
- **术语知识库**（强约束、精确匹配、事务写入）—— ReMe 无法替代；
- **证据图/文献记忆**（关系型知识、可检索上下文）—— ReMe 可以部分承接，但会失去 Cypher 的类型化查询与约束。

### 2.6 模型、配置与工具接入

| 类别 | 现状 |
|---|---|
| 模型配置 | 环境名实际为 `FAST_LLM_MODEL` / `REASONING_LLM_MODEL` / `TRANSLATION_LLM_MODEL`（仓库中不存在 `LLM_MODEL`/`MULTIMODAL_LLM_MODEL`）；AGENTS §23 要求按场景取用；provider 用 `create_llm_client`（OpenAI 兼容 base_url + 多 key 轮换） |
| Embedding/Rerank | 外部容器 `:8002`/`:8003`，模型 `BAAI/bge-m3` / `BAAI/bge-reranker-v2-m3`（`config/defaults/main.yaml:63-84`） |
| 文档解析 | MinerU 外部容器 `:44321` + 本地兜底 |
| 工具调用 | 无通用 tool-calling 框架；各 provider 直接构造 prompt，模型返回 JSON 后由领域代码解析/校验 |
| 结构化输出 | Pydantic `model_validate` + 自定义 schema 校验（`source_fact_chain/core.py`） |
| 重试 | 阶段级分类重试；provider 内部对超时/限流有局部重试 |

### 2.7 测试与可观测性

| 项 | 现状 |
|---|---|
| 测试 | `tests/agents/` 19 个文件、179 个用例（编排、状态转移守卫、持久化、缓存、队列、四个 adapter、Phase 5 工厂）；`tests/api/test_pipeline_api.py` 18 个用例；`tests/core/source_fact_chain/` 21 个用例；另有 `standardize` 218、`ingest` 191、`evidence_extraction` 595、`translation` 275（后两者维护休眠路径） |
| 黄金样本 | `tests/core/source_fact_chain/test_source_fact_chain.py`（21 个用例）与 `test_e2e_fabry_dual_tracks.py`（依赖 `backend/output/**/法布雷病1例`，缺失即 skip）；迁移时应把可获得的真实文档作为 parity 基线 |
| 日志 | `loguru`，阶段开始/结束/失败均有结构化日志 |
| 追踪 | `src/utils/observability.py` 有 tracing 基础；LangGraph 无节点级 trace |
| 指标 | 无指标导出；API `PhaseStatusResponse.nodes/count` 字段存在但**从未被填充**（`api/v1/contracts.py:97-121`、`pipeline.py:148-157`） |
| 前端进度 | 每 2 秒轮询相位状态；节点级进度 UI 已预留但未使用 |

### 2.8 外层边界冻结清单（摘要）

完整清单见附录 B。迁移中**必须保持**的核心项：

| # | 冻结项 | 原因 |
|---|---|---|
| 1 | HTTP 路由、请求/响应模型、状态码、`status_url` | 前端与测试直接依赖 |
| 2 | `pipeline_status` 取值 `pending/running/completed/failed`（API 另有合成值 `queued`） | DB 过滤、前端联合类型 |
| 3 | `PipelineGraphState` 现有字段名/类型（可加可选字段，不可改名/删） | API 构造、持久化、证据检索读 JSON |
| 4 | 四个 `*Output` 模型字段 | API 测试构造、证据检索读 `phase_3_output.output_dir/source_language` |
| 5 | `PhaseStatusDetail` / `PhaseErrorDetail` / 枚举值 | UI 展示、缓存、重跑 |
| 6 | `PipelineRunner` / `SingleJobDispatcher` / `JobQueueRepository` 方法签名 | `app/main.py`、路由、测试按名调用 |
| 7 | `pipeline_run_states` / `pipeline_jobs` / `document_processing_cache` 表结构与索引语义 | 队列、去重、恢复、证据检索 SQL |
| 8 | 阶段入口先写 `RUNNING` 再执行；失败/取消写 FAILED 并保留相位 | 轮询不出现 `pending→completed` 跳变；关闭不留孤儿 running |
| 9 | 重试语义（3 次、30/60s、仅 retryable）与错误对象投影 | UI 显示 attempt/max_retries；最坏时延预期 |
| 10 | 磁盘产物布局与 `phase_3` 文件集 | 重试复用、Phase 4 输入、渲染兜底 |
| 11 | 阶段重跑清理范围 | 避免残留临床行/索引 |
| 12 | owner 404 语义 | 多租户隔离 |

---

## 3. 目标架构（To-Be）

### 3.1 分层与不变量

```mermaid
flowchart TD
  subgraph OUTER["外层服务（冻结）"]
    API["FastAPI /api/v1/pipeline"]
    RUN["PipelineRunner + SingleJobDispatcher"]
    DB[("pipeline_run_states / pipeline_jobs<br/>document_processing_cache")]
  end
  subgraph GRAPH["LangGraph 状态图（领域层）"]
    N1["phase_1 节点"] --> N2["phase_2 节点"] --> N3["phase_3 节点"] --> N4["phase_4 节点"]
  end
  subgraph AS["AgentScope 子智能体（领域层）"]
    A1["AcquisitionAgent"]
    A2["ParseAgent"]
    A3["FactChainAgent<br/>extract / verify / translate"]
    A4["StandardizeAgent（薄）"]
  end
  subgraph DET["确定性领域内核（保留，作为 tool）"]
    T1["lit-acquisition SDK"]
    T2["MinerU 解析"]
    T3["candidate_to_fact / validate / locate_quote"]
    T4["术语匹配 + PG/pgvector + rerank"]
  end
  subgraph KB["知识与记忆（领域层边界外）"]
    R["ReMe 服务（HTTP/MCP）<br/>Markdown + BM25/向量 + wikilink"]
    PG[("PostgreSQL 术语库 + 证据表")]
    NEO[("Neo4j 证据图（保留）")]
  end
  API --> RUN --> DB
  RUN --> GRAPH
  N1 --> A1 --> T1
  N2 --> A2 --> T2
  N3 --> A3 --> T3
  N4 --> A4 --> T4
  A3 -. "recall / capture（非权威）" .-> R
  A4 --> PG
  A4 -. "best-effort" .-> NEO
```

**不变量（任何阶段都不得破坏）**

1. `pipeline_run_states.state_json` 仍是唯一运行状态真相源；不引入第二个“运行状态”数据库。
2. 临床事实（`SourceFact`/`Verification`/`EvidenceItem`/标准实体）只能由确定性代码写入；智能体只能产出候选。
3. 产物文件（`phase_3/*.json(l)`、`extraction_result.json`、`original.json`/`translated.json`）路径与结构不变。
4. 阶段失败语义、重试次数与错误对象投影不变（UI 与测试依赖）。
5. 外部 HTTP/DB/队列契约不变（附录 B）。
6. 任何新依赖的故障都不得让 pipeline 主路径失败（降级为无记忆/无上下文）。

> 上述逻辑分层在代码中的落点、模块映射与 import 变化见 §3.2；§3.3–§3.6 只定义行为与契约，不重复包路径。

### 3.2 目标目录结构：graph / skills / tools / mcp

> 本节为 2026-11-17 r2 新增：需求方要求 pipeline 领域层按 `skills/`、`mcp/`、`tools/` 这类职责划分来组织，与“LangGraph 状态图 + 每节点 AgentScope 子智能体 + ReMe 外部知识库”的组合一一对应。**本节只描述目标包布局与迁移方式，不实现代码。**

#### 3.2.1 分层职责边界

| 目录 | 对应组件 | 只负责 | 明确不负责 |
|---|---|---|---|
| `graph/` | LangGraph `StateGraph` | 图拓扑、条件边、PHASE 模式入口、失败/`skip_phase_4` 短路、节点适配、节点级进度 | prompt、模型调用、业务规则、持久化 |
| `skills/` | AgentScope `Agent` | 每个节点/阶段的 prompt、模型档位、工具白名单、结构化输出 schema、有界重试 | 直接写 PG/Neo4j/文件；最终业务校验；跨阶段状态 |
| `tools/` | AgentScope `Toolkit` 函数 / 普通 Python 服务 | 确定性能力：外部 SDK 适配、解析、校验、匹配、投影、落盘、事务 | 自主决策、对话状态、prompt/LLM 调用 |
| `mcp/` | MCP 客户端（备选 HTTP 客户端） | 外部服务协议：连接、鉴权、超时、重试、健康检查、降级 | 业务规则；权威数据存储；临床事实 |
| `contracts/` | Pydantic / dataclass | 跨层共享的输入输出、错误、记忆 DTO | 业务逻辑 |

四条硬边界（由 import 边界测试保证）：

1. `graph/` 不 import `agentscope`；只 import `src.agents.contracts`（冻结状态）、`skills/` 注册表与 `tools/` 的产物/契约函数；不写 prompt、不直接调模型。
2. `skills/` 不直接 import SQLAlchemy / Neo4j 客户端；只 import 本 skill 的 `tools`、`mcp` 与 `pipeline/contracts`；不直接落盘。
3. `tools/` 不 import `agentscope`；同一函数既可注册为 AgentScope tool，也可被领域代码/测试直接调用。
4. `mcp/` 不 import `skills`/`tools`；只依赖 `contracts/` 与配置，保证外部服务故障时可整体禁用。

> 判定口径：**需要 prompt/模型调用 → `skills/`；纯确定性函数 → `tools/`；跨进程协议 → `mcp/`。** 这条口径同时回答 D9 中“skills 与 tools 的边界”的主问题。

#### 3.2.2 目标目录树（终态）

```text
backend/src/pipeline/                      # pipeline 领域层（新根）
├── graph/                                 # LangGraph 编排层
│   ├── topology.py                        # StateGraph 组装、条件边、PHASE 入口、失败短路
│   ├── nodes.py                           # SkillNode：图节点 ↔ skill 调用 ↔ 状态增量
│   ├── progress.py                        # 节点级进度 → PhaseStatusResponse.nodes
│   └── phases/
│       ├── phase_1.py                     # 原 Phase1Adapter：装配/错误分类/状态写入
│       ├── phase_2.py
│       ├── phase_3.py
│       └── phase_4.py
├── skills/                                # AgentScope 子智能体（有界）
│   ├── runtime/
│   │   ├── agent.py                       # Agent 构建、structured_schema、异常分类
│   │   ├── llm.py                         # OpenAIChatModel 工厂 + 多 key 轮换 credential
│   │   └── registry.py                    # 节点名 → skill 工厂；工具白名单
│   ├── acquisition/skill.py               # AcquisitionAgent（LLM 默认关闭）
│   ├── parsing/skill.py                   # ParseAgent（LLM 不参与）
│   ├── fact_chain/
│   │   ├── skill.py                       # FactChainAgent：窗口循环/预算/阶段顺序
│   │   ├── extract.py                     # extract 阶段（prompt + 结构化输出）
│   │   ├── verify.py                      # verify 阶段（reasoning 模型）
│   │   ├── translate.py                   # translate 阶段（仅 PRESENTED 字段）
│   │   └── prompts.py                     # 原 source_fact_chain/prompts.py
│   └── standardization/skill.py           # StandardizeAgent（薄；LLM 默认关闭）
├── tools/                                 # 确定性工具（无 agent 决策）
│   ├── acquisition/                       # 原 document_acquisition/*
│   ├── parsing/                           # 原 parse_document/*
│   ├── fact_chain/                        # service / windowing / core 校验 / projection / 落盘
│   └── terminology/                       # 原 standardize... 实现（共享三件套在 src/core/terminology_shared）
├── mcp/                                   # 外部服务协议适配
│   ├── reme/
│   │   ├── client.py                      # search / auto_memory / auto_resource
│   │   ├── contracts.py                   # 召回卡片、写入回执、错误
│   │   └── config.py                      # 读取 cfg.pipeline.mcp.reme.*（位置待 D9 确认）
│   └── registry.py                        # 客户端注册、超时、健康检查、降级
└── contracts/                             # 跨层共享契约
    ├── skill_io.py                        # SkillRequest / SkillResult / 错误分类
    └── memory.py                          # ReMe 卡片/召回的共享 DTO
```

**不迁入 `src/pipeline/`、留在原处的模块**（避免破坏非 pipeline 调用方）：

```text
backend/src/agents/                 # 外层实现与冻结契约
├── contracts.py                    # PipelineGraphState / 状态枚举 / Phase 输出（API 也 import）
├── runner.py / dispatcher.py / state_persistence.py / processing_cache.py
├── concurrency.py / content_hash.py / phase_5_factory.py
└── orchestrator.py / phase_1..4_adapter.py   # 过渡期只保留 re-export shim
backend/src/core/
├── config.py / auth/
├── terminology_shared/             # 从 standardize... 抽出的共享契约/规范化（graph_rag、evidence_extraction 共用）
├── graph_rag/                      # Phase 4/5、chat、evidence_extraction 共用，不是 pipeline 专属
├── evidence_extraction/            # D7：休眠，不迁
├── cross_lingual_translation/      # D7：休眠，不迁
└── visualize_evidence_with_expert_in_loop/   # Phase 5，图外
```

> `graph_rag` 不迁的理由：`src/api/v1/graph_rag.py`、`src/api/wiring.py`、休眠的 `evidence_extraction` 都直接 import 它；把它并入 pipeline 会把 pipeline 领域层变成事实上的共享层，违背“只改 pipeline、外层不动”。pipeline 的 Phase 4 工具按需调用它即可。

#### 3.2.3 现有模块 → 目标层映射

| 现有模块/入口 | 目标层与路径 | 迁移内容 | 旧路径 shim |
|---|---|---|---|
| `src/agents/orchestrator.py` | `src/pipeline/graph/topology.py` | 图组装、条件边、重试归属 | 保留 |
| `src/agents/phase_1_adapter.py` | `src/pipeline/graph/phases/phase_1.py` | 装配、错误分类、状态写入 | 保留 |
| `src/agents/phase_2..4_adapter.py` | `src/pipeline/graph/phases/phase_2..4.py` | 同上 | 保留 |
| `src/core/source_fact_chain/runner.py` | `src/pipeline/skills/fact_chain/skill.py` + `extract/verify/translate.py` | 窗口循环、预算、阶段顺序 | 保留 |
| `src/core/source_fact_chain/prompts.py` | `src/pipeline/skills/fact_chain/prompts.py` | prompt 与版本号 | 保留 |
| `src/core/source_fact_chain/providers.py` | `src/pipeline/skills/runtime/llm.py` | 模型客户端、多 key 轮换；legacy 路径保留 provider | 保留 |
| `src/core/source_fact_chain/{contracts,core,windowing,projection,api}.py` | `src/pipeline/tools/fact_chain/` | 确定性校验、窗口切分、双轨投影、落盘 | 保留 |
| `src/core/ingest_and_digitize_data/document_acquisition/` | `src/pipeline/tools/acquisition/` | SDK 适配、上传落盘、错误分类 | 保留 |
| `src/core/ingest_and_digitize_data/parse_document/` | `src/pipeline/tools/parsing/` | MinerU remote/local、解析产物落盘 | 保留 |
| `src/core/standardize_entities_and_align_knowledge/` 实现部分 | `src/pipeline/tools/terminology/` | 精确/语义/跨语言匹配、术语持久化、ACMG 投影 | 保留 |
| 上者的 `contracts.py` / `hgvs_normalizer.py` / `context_pack/` | **不迁**：`src/core/terminology_shared/` | `graph_rag` 与休眠 `evidence_extraction` 也依赖的共享契约/规范化 | 保留 |
| `src/core/graph_rag/` | **不迁**（`src/core/graph_rag/`） | Phase 4 best-effort 写图、Phase 5 QA、chat 共用 | 不需要 |
| `src/agents/contracts.py` | **不迁** | 外层冻结状态契约 | 不需要 |
| `src/agents/{runner,dispatcher,state_persistence,processing_cache,concurrency,content_hash,phase_5_factory}.py` | **不迁** | 外层语义（队列/租约/重试/缓存/Phase 5） | 不需要 |
| `src/api/**`、`src/app/**`、`src/dao/**`、`src/utils/**` | **不迁** | 外层 HTTP、DI、持久化、共享工具 | 不需要 |
| `backend/scripts/{e2e_standardize_entities,build_terminology_embeddings,e2e_full}.py` | 路径不动，只改 import | 运维/评测脚本 | 不需要 |

**新增而非迁移的模块**：`graph/nodes.py`、`graph/progress.py`、`skills/runtime/*`、四个 `skills/*/skill.py`、`mcp/reme/*`、`mcp/registry.py`、`contracts/*`。其中 `graph/nodes.py` 就是 §3.4.1 的“统一节点适配器”。

> `standardize_entities_and_align_knowledge` 不能整体 `git mv`：`graph_rag` 依赖它的 `contracts.py`，休眠的 `evidence_extraction` 依赖 `hgvs_normalizer.py` 与 `context_pack/`。因此先把这三项抽到中立的 `src/core/terminology_shared/`，再迁其余实现；否则会形成 `src/core/graph_rag → src/pipeline` 的反向依赖。

#### 3.2.4 与 LangGraph 图/节点、AgentScope、ReMe 的对应

| LangGraph 节点 | `skills/` | 主要 `tools/` | `mcp/` | 输出契约 |
|---|---|---|---|---|
| `phase_1` | `AcquisitionAgent` | `tools/acquisition`（lit-acquisition SDK、上传落盘） | — | `AcquisitionOutput` |
| `phase_2` | `ParseAgent` | `tools/parsing`（MinerU remote/local、产物保存） | — | `ParseOutput` |
| `phase_3` | `FactChainAgent`（extract/verify/translate） | `tools/fact_chain`（窗口、校验、`candidate_to_fact`、`locate_quote`、投影、落盘） | `reme.search` / `reme.auto_memory`（只读参考 + 异步写记忆） | `ChainRun` 投影、`TranslationExtractionOutput` |
| `phase_4` | `StandardizeAgent`（薄） | `tools/terminology`（精确/语义匹配、事务写入、ACMG 投影）+ `src.core.graph_rag`（best-effort） | — | `StandardizationOutput` |

```mermaid
flowchart LR
  subgraph G["graph/ · LangGraph"]
    N1["phase_1"] --> N2["phase_2"] --> N3["phase_3"] --> N4["phase_4"]
  end
  subgraph S["skills/ · AgentScope"]
    A1["AcquisitionAgent"]; A2["ParseAgent"]; A3["FactChainAgent"]; A4["StandardizeAgent"]
  end
  subgraph T["tools/ · 确定性"]
    T1["acquisition"]; T2["parsing"]; T3["fact_chain"]; T4["terminology"]
  end
  subgraph M["mcp/ · 外部协议"]
    R["reme client"]
  end
  N1 --> A1 --> T1
  N2 --> A2 --> T2
  N3 --> A3 --> T3
  N4 --> A4 --> T4
  A3 -. "recall / capture（非权威）" .-> R
  A4 --> T4
```

> 与 §3.4.2 的 agent 映射是同一张表的两面：§3.4.2 回答“谁做决策”，本节回答“代码放哪里”。两者必须同步修改。

#### 3.2.5 内部 import 路径变化

| 旧路径 | 新路径 | 主要调用方 |
|---|---|---|
| `src.agents.orchestrator` | `src.pipeline.graph.topology` | `src/api/wiring.py`、`tests/agents/test_orchestrator.py` |
| `src.agents.phase_{1..4}_adapter` | `src.pipeline.graph.phases.phase_{1..4}` | `src/api/wiring.py`、`tests/agents/test_phase_*` |
| `src.core.source_fact_chain.api` | `src.pipeline.tools.fact_chain.service` | `src/api/wiring.py`、`src/agents/phase_3_adapter.py` |
| `src.core.source_fact_chain.{contracts,core,windowing,projection}` | `src.pipeline.tools.fact_chain.{contracts,core,windowing,projection}` | Phase 3 适配器、测试、脚本 |
| `src.core.source_fact_chain.prompts` | `src.pipeline.skills.fact_chain.prompts` | 仅 FactChainAgent |
| `src.core.source_fact_chain.providers` | `src.pipeline.skills.runtime.llm` | Phase 3 适配器、legacy 路径 |
| `src.core.ingest_and_digitize_data.document_acquisition.*` | `src.pipeline.tools.acquisition.*` | `api/v1/pipeline.py`、`api/wiring.py`、测试 |
| `src.core.ingest_and_digitize_data.parse_document.*` | `src.pipeline.tools.parsing.*` | `api/v1/chat.py`、`api/wiring.py`、`scripts/e2e_full.py`、测试 |
| `src.core.standardize_entities_and_align_knowledge.*` | `src.pipeline.tools.terminology.*`（共享三件套 → `src.core.terminology_shared.*`） | `api/wiring.py`、`graph_rag`、`evidence_extraction`、脚本、测试 |
| （新增） | `src.pipeline.mcp.reme.*` | 仅 `FactChainAgent` 与 `mcp/registry.py` |

**不变化的 import 路径（冻结）**：`src.agents.contracts`、`src.agents.runner`、`src.agents.dispatcher`、`src.agents.state_persistence`、`src.agents.processing_cache`、`src.agents.concurrency`、`src.agents.content_hash`、`src.agents.phase_5_factory`、`src.api.**`、`src.app.**`、`src.dao.**`、`src.utils.**`、`src.core.graph_rag.**`、`src.core.evidence_extraction.**`、`src.core.cross_lingual_translation.**`。

**影响面实测（基于本次工作区）**：

| 类别 | 数量 | 处理方式 |
|---|---:|---|
| 待迁移 Python 文件（不含 `graph_rag`） | 56（9 + 20 + 27） | `git mv`，迁移提交内不改逻辑 |
| 待迁移 Python 代码行 | 9,889 | 同上 |
| 非测试 import 行（待迁 3 包 → 外部调用方） | 20 | 机械改写；外层运行时用 shim 可为零 |
| 不迁的 `graph_rag` 外部 import 行 | 3 | 保持不变，不算迁移量 |
| 引用旧路径的测试文件 / import 行 | 56 / 153 | 机械改写；不在首批移动测试目录 |
| 额外脚本 | 3 | 只改 import |
| README / 文档示例 | 13 个随迁 README + 2 处外部文档 | 随包迁移更新；`database/terminology_database/README.md` 与覆盖率命令文档同步 |

> 数量会随实现进展变化；阶段 0 必须重新生成一次基线，不能直接照抄本表。

#### 3.2.6 与“外层服务不动”的兼容性

**不变量（必须保持）**

| # | 外层契约 | 为什么不受目录调整影响 |
|---|---|---|
| 1 | HTTP 路由、请求/响应模型、状态码、`status_url` | 目录调整不碰 `src/api/v1/*.py` 的签名；只可能改 import |
| 2 | `pipeline_status` / `phase_*_status` 取值与转移守卫 | 状态与枚举仍在 `src/agents/contracts.py`，不移动 |
| 3 | `PipelineGraphState` 字段名/类型、`state_json` 形状 | `contracts.py` 冻结；graph 只 import 它 |
| 4 | 四个 `*Output` 模型字段 | 仍由 `contracts.py` 定义；skill 只产出候选，经工具校验后写回 |
| 5 | `pipeline_run_states` / `pipeline_jobs` / `document_processing_cache` 表结构与索引 | 不新增/不删除列，不做 DB 迁移 |
| 6 | 阶段重试、心跳/租约、并发 2、重跑清理 | `concurrency.py` / `runner.py` / `state_persistence.py` 不移动、不改签名 |
| 7 | 磁盘产物路径与文件集（`phase_2/*`、`phase_3/*.json(l)` 等） | 工具层仍用原落盘函数，路径参数不变 |
| 8 | 前端轮询与错误展示 | API 响应不变；`nodes` 字段只增不改 |

**允许变化的内部项**

- Python 包路径与 import 行（本节的映射表）；只改“从哪 import”，不改类名/函数签名/参数默认值。
- DI 装配处的 import：若采用旧路径 shim，`src/api/wiring.py` 可**零改动**；若直接改，只改 import 行，装配顺序与对象不变。
- 测试 import 与覆盖率命令路径（如 `--cov=src.core.source_fact_chain` → `--cov=src.pipeline.tools.fact_chain`）。
- 文档/README 中的示例路径；`database/terminology_database/README.md` 的 importer 示例。

**保证机制**

1. **shim 过渡**：旧路径保留 `re-export` 模块（只覆盖外层运行时真正 import 的约 15 个模块路径），一个发布周期后删除；shim 内不写业务逻辑。
2. **纯搬迁提交**：目录迁移 commit 只做 `git mv` + import 重写，不夹带行为变更；行为变更（引入 agent/ReMe）单独 commit，便于二分与回滚。
3. **契约测试**：`tests/agents`（179）、`tests/api/test_pipeline_api.py`（18）、`tests/api/test_wiring_config.py`、`tests/core/source_fact_chain`（21）必须全绿；`state_json` golden 与产物 diff 作为阶段门禁。
4. **import 边界测试**：新增 `tests/pipeline/test_import_boundaries.py`，断言 `graph/` 不 import `agentscope`、`tools/` 不 import `agentscope`/`skills`、`mcp/` 不 import `tools`/`skills`，以及旧路径 import 只出现在 shim allowlist 中。
5. **开关不变**：`pipeline.agent_runtime`、`pipeline.topology`、`memory.enabled` 等开关语义不变；目录迁移本身不新增运行时开关。

> 结论：**外部 API、数据库结构、状态 JSON、产物格式、队列/重试语义都不变；变化仅限于领域层内部包布局及其 import。** 这是一次“可机械验证”的重构，不是接口迁移。

#### 3.2.7 过渡态与终态

| 阶段 | 旧路径 | 新路径 | 外层是否改 import |
|---|---|---|---|
| 过渡态（阶段 1–4） | shim（re-export） | 真实实现 | 否（走 shim） |
| 终态（阶段 4 后 + 1 个发布周期） | 删除 | 唯一实现 | 否（外层早已指向新路径或已随 shim 删除更新） |

回滚方式：目录迁移 commit 可整体 revert；未 revert 时旧路径 shim 仍可 import，运行时行为不变；agent/ReMe 行为由各自开关回退，与目录无关。

### 3.3 LangGraph 拓扑设计

**代码落点**：`src/pipeline/graph/topology.py`（图组装）+ `nodes.py`（节点适配）+ `progress.py`（节点进度）；详见 §3.2.2。

**推荐拓扑（方案 A）：4 个 phase 节点 + 只在 Phase 3 内部展开子图。**

```text
START
  └─(PHASE 模式按 target_phase 条件入口)
phase_1 ──► phase_2 ──► phase_3 ──► phase_4 ──► END
                          │
                          └─ 子图（可选，阶段 2 引入）：
                             prepare → fan-out(windows) → extract* → verify* → translate* → merge
```

- **节点状态**：继续使用 `PipelineGraphState`（Pydantic），新增字段一律可选并带默认值；`state_json` 无版本号，加载侧必须容忍缺失字段。
- **条件边**：PHASE 模式的入口选择、`skip_phase_4_reason` 短路、失败终止沿用现状（`orchestrator.py:245-285`）。
- **子图**：Phase 3 的窗口级 fan-out 用 `Send`（每个窗口一个 `extract` 任务），`facts/verifications/english` 用 `Annotated[list, operator.add]` reducer 汇总；事实 ID 已由内容决定，合并顺序不影响结果，最后统一排序落盘。
- **并发上限**：图内并发受 `asyncio.Semaphore` 约束（建议 4–8，按 provider 限流调整）；外层 `PipelineSemaphore(2)` 不变。
- **重试归属**（关键）：
  - 阶段级重试：仍由 `RetryablePhaseExecutor` 负责（3 次、30/60s，写入 `PhaseErrorDetail`）。
  - 节点内传输重试：仍由 provider 负责（Phase 3 `max_attempts=2`）。
  - **不要**再叠加 LangGraph `RetryPolicy`，否则最坏 3×2×N 次调用，UI 的 attempt 语义也会失真。
- **断点/恢复**：v1 **不引入** LangGraph checkpointer。现有契约是“崩溃→标记 FAILED→阶段重跑”，重跑复用 `chain_run.json`（source_hash+config+prompt_versions）。引入 PostgresSaver 会形成第二套恢复语义，并与 `heartbeat/owner_worker_id` 租约冲突。若未来要做“节点级续跑”，需单独立项并修改外层契约（见 D8）。
- **HITL**：v1 不做图内人工介入；Phase 5 仍是图外请求-响应服务。若未来要做，只允许一个 owner：LangGraph `interrupt()` + checkpointer，同时关闭 AgentScope 的 `ASK` 权限暂停（否则双重挂起）。
- **节点级可观测**：把每个 phase 的 `summary` 扩展为 `{"nodes": [...]}` 或填充 `PhaseStatusResponse.nodes`（API 模型已有该字段，且 `summary` 是 `extra=allow`），前端可逐步启用，不影响旧字段。

**方案 B（字面执行）：把 18+ 个 stage 全部提升为图节点。** 不推荐作为第一步，原因：
- 阶段内部存在大量共享可变状态（`ChainRun`、`StandardizationService` 的会话/事务），拆成节点后需要在图状态里序列化这些中间对象；
- Phase 4 的 6 次持久化是一个事务边界，拆节点会破坏原子性；
- 外层只认 4 个 phase 的状态与错误，节点增多不会改善用户体验，反而放大状态迁移成本。

### 3.4 AgentScope 子智能体设计

#### 3.4.1 统一节点适配器

**代码落点**：`src/pipeline/graph/nodes.py`（`SkillNode`）+ `src/pipeline/skills/runtime/agent.py`（Agent 构建与异常分类）；见 §3.2.2。

AgentScope 2.0.12 的核心是 `Agent`（无 `__call__`），异步 `reply(inputs, structured_schema=...)` 返回 `Msg`，结构化结果在 `msg.structured_output`（dict）。因此每个图节点写成：

```python
# 领域层伪代码，非最终实现
class AgentNode:
    def __init__(self, agent_factory, schema: type[BaseModel]):
        self._factory = agent_factory
        self._schema = schema

    async def __call__(self, state: PipelineGraphState) -> PipelineGraphState:
        agent = self._factory.build(state)          # 每次调用新建，避免跨 run 污染
        payload = self._render_input(state)          # 只传必要字段，不整包序列化
        try:
            msg = await agent.reply(
                UserMsg(name="orchestrator", content=payload),
                structured_schema=self._schema,
            )
        except Exception as exc:
            raise classify_agent_error(exc)          # → Retryable/PermanentPhaseError
        output = self._schema.model_validate(msg.structured_output or {})
        return self._apply(state, output)            # 只写本阶段字段
```

要点：

- **输入渲染**：只把该节点需要的字段/文件路径传给 agent，不把整个 `PipelineGraphState` 塞进 prompt（避免泄漏、token 爆炸、隐式耦合）。
- **结构化输出**：schema 直接复用现有契约（`AcquisitionOutput`、`ParseOutput`、`TranslationExtractionOutput`、`StandardizationOutput` 或阶段内部 schema）。AgentScope 内置结构化输出工具会强制校验并在失败时回喂错误重试；但**业务校验仍必须在领域代码里再跑一遍**（见 3.4.3）。
- **工具**：把现有服务包成 AgentScope `Toolkit` 函数（docstring 自动生成 JSON schema），例如 `acquire_document(request_json) -> result_json`、`parse_pdf(path) -> paths`、`match_entities(payload) -> matches`。工具内部仍然调用原服务，**不复制业务逻辑**。
- **模型接入**：`OpenAIChatModel(credential=OpenAICredential(base_url=cfg..., api_key=...), model=cfg.llm.model, stream=False)`。现有 `LLMPoolAdapter` 有**多 key 轮换**，AgentScope credential 是单 key；需要实现一个 `RotatingCredential`/自定义 model 包装，或在每次节点调用时按轮询选择 key。这是阶段 2 必须先解决的小适配点。
- **禁用项**：v1 不使用 `GoalPipeline`/`TeamPipeline`（会形成第二套编排器），不使用 AgentScope 的 `service`/`workspace` 运行时，不使用 AgentScope 自带 RAG 知识库（知识层由 ReMe + 现有 PG/Neo4j 承担）。
- **超时/预算**：AgentScope `ReActConfig` 的迭代上限、模型层 `max_retries`、节点级 `asyncio.timeout` 三层要显式设定，且总和不得超过阶段级超时。

#### 3.4.2 每个 phase 的 agent 映射

| Phase | Agent | 工具（现有服务） | 输出 schema | 自主度 |
|---|---|---|---|---|
| 1 | `AcquisitionAgent` | `search_literature`、`download_fulltext`、`store_upload`（lit-acquisition SDK） | `AcquisitionOutput` | 低：LLM 只做检索式改写/来源选择；**默认关闭**，先 1:1 包一层 |
| 2 | `ParseAgent` | `parse_remote`、`parse_local`、`save_parse_artifacts`（MinerU） | `ParseOutput` | 极低：固定 remote→local 回退；LLM 不参与 |
| 3 | `FactChainAgent`（内含 extract/verify/translate 三个子步骤） | 技能子步骤：`extract`/`verify`/`translate`（prompt+模型）；tools：`validate_candidate`、`locate_quote`、`reconcile`、`project_dual_result`、`write_chain_outputs` | `ChainRun` 投影 + `TranslationExtractionOutput` | 中：窗口循环与预算由 agent 编排；**校验/落盘归工具层** |
| 4 | `StandardizeAgent`（薄） | `precise_match`、`cross_lingual_resolve`、`semantic_match`、`persist_standardization`、`project_acmg` | `StandardizationOutput` | 低：匹配仍是确定性内核；LLM 仅用于歧义解释（可选） |

> 结论：**真正值得 agent 化的是 Phase 3**；Phase 1/2/4 的 agent 主要是“统一运行时 + 可观测 + 记忆”的结构收益，不是能力收益。这一点必须在验收标准里写清楚，避免为了形式而引入 LLM 调用。

#### 3.4.3 有界智能体（bounded agent）的三个约束

1. **工具白名单**：每个 agent 只暴露本阶段工具，禁止通用 `python`/`shell`/`http` 工具（AgentScope 默认不启用，需显式不注册）。
2. **输出守门**：所有模型输出必须经过现有校验器（`validate_reply_schema`、`candidate_to_fact`、`reconcile`、`locate_quote`、`db_ready_gate`）；校验失败时 agent 可收到结构化错误并重试一次，仍失败则该窗口/阶段按现有语义失败。
3. **写权限**：agent 不直接写 PG/Neo4j/文件；写操作只通过工具函数，由工具在领域事务内完成。ReMe 写入是例外，但它是“记忆”，不参与临床事实。

### 3.5 ReMe 外部知识服务设计（已确认作为外部服务）

**代码落点**：`src/pipeline/mcp/reme/`（client/contracts/config）+ `src/pipeline/mcp/registry.py`；只有 `FactChainAgent` 通过它召回/写记忆，见 §3.2.4。

#### 3.5.1 部署形态

**已确认（需求方，2026-11-17）：ReMe 作为外部服务，用于知识库的调用**，不装进 backend 进程，也不计入“外层服务不动”的冻结范围。落地形态为独立进程/容器（单独 venv 或镜像），后端通过 HTTP（或 MCP）调用。

> 该确认解决的是“ReMe 能不能作为新外部服务引入”；**不改变**术语库（PG/pgvector）与证据图（Neo4j）作为权威存储的定位（见 D1）。

理由（依赖实测，见 §4.4）：`reme-ai` 要求 `fastapi>=0.162.0`、`numpy>=2.5.4`（Py≥3.12），装进 backend 会把 FastAPI 0.136.3→0.163.1、numpy 2.3.5→2.5.5、openai 2.41→3.52、langchain-core 1.4.3→1.8.1 一并升级，直接冲击“外层不动”。独立服务让 ReMe 在自己的环境里用 `reme-ai[core]`（含 agentscope 2.0.11），与 backend 的 AgentScope 2.0.12 解耦。

```text
backend (py3.12, agentscope 2.0.12, langgraph 1.2.4)
   │  HTTP/MCP: search / auto_memory / auto_resource
   ▼
reme service (独立 env/容器, reme-ai[core] 0.4.2.3, workspace 卷)
   └─ workspace/{resource,daily,digest,metadata}/
```

- 单写者：一个 workspace 只允许一个 ReMe 运行时（官方限制）；多 backend worker 只读/只发请求，不各自 `ReMe(...)`。
- 隔离：按环境一个 workspace；多用户场景不做租户隔离（ReMe 无多租户），只存“公共文献知识/运行记忆”，不存用户私有数据。
- 故障降级：检索超时（建议 300–800ms）→ 返回空记忆，节点继续；`auto_memory` 异步 best-effort，失败只告警。

#### 3.5.2 数据流

| 来源 | 写入方式 | 用途 |
|---|---|---|
| Phase 2 的 `output.md` + `metadata.json` | `auto_resource`（md/json 均支持） | 文献知识卡：标题、基因/变异/疾病、关键结论（带 `source_resource` 溯源） |
| 每次 Phase 3 的 `chain_run.json` 摘要 | 领域层生成结构化摘要 → `auto_memory`（session_id=run_id） | 运行记忆：本次抽到哪些事实、哪些被拒/未核验，供后续 run 召回 |
| 人工审核结论（Phase 5 feedback） | 领域层写卡片（frontmatter: reviewer/decision/date） | 程序性记忆：某类证据的接受/拒绝先例 |
| 现有 Neo4j 证据图 | 一次性导出脚本：节点→卡片、关系→wikilink/frontmatter | 文献知识迁移（可选，阶段 5） |

**明确不写入 ReMe 的内容**：原始事实的权威副本、术语表、逐条审计字段、任何需要事务/唯一约束的数据。

#### 3.5.3 检索与注入

- 召回时机：每个 Phase 3 agent 在 extract 前检索一次（query = 基因/变异/疾病 + 文档标题），把 top-k（≤5）卡片作为 **参考上下文** 注入 system/user prompt，并标注“仅供参考，不得作为证据来源”。
- 注入格式：`<memory source="reme" path="..." lines="...">...</memory>`；禁止把记忆内容当作 `quote`（quote 必须来自源文档，`locate_quote` 会拒绝）。
- 评测：离线构造 50–100 条“历史相似文献”查询，比较有无记忆时的抽取召回/精确率；记忆不得改变 `supported` 判定（用同一验证器）。

**与“Hermes 概念”的对应**：用户提到的 Hermes 模式可拆成两半——① 模型调用前按当前任务召回记忆并注入上下文；② 一轮任务完成后把可复用的结论异步写回记忆。本方案用 ReMe 同时承接这两半：① 即上面的 `search` → 注入；② 由节点在阶段成功后提交结构化摘要给 `auto_memory`（`session_id=run_id`，异步、失败不阻塞）。区别在于：Hermes 记忆的是“对话/任务经验”，这里记忆的是“文献知识与运行经验”，**都不进入临床事实链**。

#### 3.5.4 数据迁移（仅当 D1 选择“知识库替换”）

1. 导出 Neo4j：`MATCH (n)-[r]->(m) RETURN ...` → JSONL（节点/关系/来源文档/run）。
2. 卡片模板：一个基因/变异/疾病一个 `digest/wiki/<type>/<slug>.md`，frontmatter 保存 `source_document_id`、`processing_run_id`、`evidence_label`、`updated_at`；正文用 wikilink 表达关系。
3. 幂等写入：按 `source_document_id + fact_id` 生成稳定 slug；重复导入覆盖而非追加。
4. 校验：节点/关系计数对账；抽样 30 条做“图查询 vs ReMe 检索”结果对比；记录不可表达的关系（如带属性的边）作为已知损失。
5. 回滚：Neo4j 保留只读双写期 ≥ 2 个迭代；ReMe 故障时 Phase 5 回退图查询。

### 3.6 数据流与产物兼容

| 产物 | 生产者（迁移后） | 消费者 | 兼容要求 |
|---|---|---|---|
| `pipeline_run_states.state_json` | 外层持久化（不变） | API、证据检索、缓存 | 只加可选字段；`phase_4_status` 存在性启发式保留 |
| `data/pipeline/<run>/phase_2/*` | ParseAgent 的工具（原服务） | Phase 3、渲染 | 路径/文件名不变 |
| `phase_3/chain_run.json`、`*.jsonl`、`extraction_result.json`、`original.json`、`translated.json` | FactChainAgent 的工具（原 `write_outputs`） | Phase 4、证据检索、渲染、benchmark | 字段/行序/ID 规则不变 |
| PG 术语/匹配/证据表 | StandardizeAgent 的工具（原 repository） | Phase 4 之后、ACMG 投影、前端 | 事务边界不变 |
| Neo4j 证据图 | 工具（best-effort） | Phase 5 QA | 失败不阻塞 |
| ReMe workspace | ReMe 服务 | Agent 召回、Phase 5 QA（可选） | 可重建、可备份；不参与审计 |

---

## 4. 可行性逐项结论

### 4.1 LangGraph 能否覆盖现有语义

| 语义 | 现状 | LangGraph 1.2.x 能力 | 结论 |
|---|---|---|---|
| 顺序阶段 | 4 节点链 | `add_edge` | ✅ 已有 |
| 条件分支 | PHASE 模式入口、skip Phase 4、失败终止 | `add_conditional_edges`（返回节点名/列表/END） | ✅ 已有 |
| 循环 | 无（阶段内 `for` 循环） | 条件边回跳 + `recursion_limit` | ✅ 可覆盖；建议只用于“验证-重试”类小循环 |
| 子图 | 无（阶段内服务） | 共享 state 可直接 `add_node(compiled_subgraph)`；不同 schema 用包装节点 | ✅ 可覆盖 Phase 3 窗口子图 |
| 并发 fan-out | 无（串行窗口） | `Send` + reducer（`Annotated[list, operator.add]`） | ✅ 可覆盖；需处理顺序/去重 |
| 人工介入 | 图外（Phase 5） | `interrupt()` + `Command(resume=...)`（需 checkpointer） | ⚠️ 能力有，但 v1 不建议改契约 |
| 断点恢复 | 阶段级：`state_json` + `chain_run.json` 复用；崩溃→FAILED | `PostgresSaver`（需 `langgraph-checkpoint-postgres`，plain PG，不依赖 pgvector） | ⚠️ 能力有，但与现有租约/恢复语义冲突；v1 保持现状 |
| 节点重试 | 阶段级 executor | `RetryPolicy`（按节点） | ⚠️ 不要叠加；保持 executor 单一职责 |
| 流式/追踪 | 无 | `stream_mode`、`subgraphs=True`、`stream_writer` | ✅ 可选增强 |

**结论：LangGraph 覆盖全部所需语义，不存在“换引擎”风险。** 需要决策的只是“是否改变恢复/HITL 契约”，而不是“能否表达”。

### 4.2 AgentScope 与现有节点的对应关系

| 现有单元 | 目标层 | 建议 | 说明 |
|---|---|---|---|
| `Phase1Adapter` / `Phase2Adapter` / `Phase4Adapter` | `graph/phases` + 对应 `skills/*` | **装配/错误分类留在 graph，业务交给 skill + tools** | 只做装配/错误分类/状态写入（156/175/168 行），没有独立业务规则 |
| `DocumentAcquisitionService.acquire` | `tools/acquisition` + `skills/acquisition` | 1:1 `AcquisitionAgent` | 明确输入输出；付费墙 vs 超时的错误语义独立 |
| `lit-acquisition` SDK | `tools/acquisition` | **不迁**，作为外部工具（首期不做 MCP） | 独立库，已有配置边界与测试；重写成本高、收益低 |
| `DocumentParseOrchestrator.parse` | `tools/parsing` + `skills/parsing` | 1:1 `ParseAgent` | remote→local 回退是策略，适合 agent 工具编排 |
| `Phase3Adapter` | `graph/phases/phase_3.py` | **拆分**：文本拼接/断点复用留在 graph；链执行交给 `FactChainAgent` | 适配器混了三件事 |
| `ChainRunner`（extract/verify/translate × window） | `skills/fact_chain` + `tools/fact_chain` | 1 个 `FactChainAgent` + 3 个 stage 子步骤 | 唯一真正的推理核心；预算、重试、审计必须整体迁移 |
| `EXTRACT` / `VERIFY` / `TRANSLATE` | `skills/fact_chain/{extract,verify,translate}.py` | 可拆为 3 个子步骤（同一 agent 内或 3 个节点） | verify 用 reasoning 模型，translate 只处理 2 个字段；拆分开销可控 |
| `candidate_to_fact` / `validate_reply_schema` / `reconcile` / `locate_quote` | `tools/fact_chain` | **不建 agent**，作为强制 tool/validator | 纯函数，是输出守门器 |
| `project_dual_result` | `tools/fact_chain/projection.py` | 纯函数留在工具层，不建 `ProjectionAgent` | 381 行业务规则（gene 归属、off-target 污染），可独立测试 |
| `StandardizationService.run` | `skills/standardization` + `tools/terminology` | **拆分**：薄 skill 编排 + `PersistenceTool` | 匹配有 HTTP/DB 混合依赖；持久化是事务边界，必须由工具持有 |
| `PreciseTerminologyMatcher` / `CrossLingualDiseaseResolver` | `tools/terminology` | **tool** | 确定性查表/模糊匹配 |
| `SimilarityTerminologyMatcher`（embedding+pgvector+rerank） | `tools/terminology` | **tool**（不单独建 agent；由 `StandardizeAgent` 调用） | 3 个外部依赖、阈值/边际策略、失败降级语义 |
| `AcmgReadyProjector` | `tools/terminology` | tool 或 merge | 纯投影 |
| `graph_rag`（Neo4j 读写、QA） | **不迁**：`src/core/graph_rag/` | Phase 4 best-effort 调用 | 与 Phase 5/chat/休眠模块共用，迁入会形成反向依赖 |
| `evidence_extraction`（12k 行，18 节点，595 测试） | **不迁**（D7） | 生产未接线；若产品需要 166 字段，整体作为 1 个 `DeepExtractionAgent`，不要拆 18 个 | — |
| `cross_lingual_translation`（5.3k 行，275 测试） | **不迁**（D7） | 全文翻译已被 fact-level presentation 取代；只抽 `estimate_tokens`/`detect_language` | — |
| `FeedbackService.patch_evidence`（Phase 5） | **不迁**（图外） | 可独立为 HITL agent（后续） | 唯一人工改判点，需要审计链；不属于 pipeline 图 |

**结论：AgentScope 可覆盖，但“每个节点都是 agent”应理解为“每个有独立契约的语义单元一个 agent”，而不是把纯函数也包成 agent。** 按上表，实际新增 agent 4 个（Acquisition / Parse / FactChain / Standardize），其余为工具或保留。

### 4.3 ReMe 替换现有知识库的成本与数据迁移

#### 4.3.1 能力对照

| 能力 | 现有实现 | ReMe 0.4.2.3 | 结论 |
|---|---|---|---|
| 术语精确匹配（HGNC/ClinVar/OMIM/HPO/ClinGen） | PG 表 + 别名优先级 + 唯一约束 | 无表/无唯一约束；Markdown 卡片 | ❌ 不能替代 |
| 语义检索 | pgvector 1024 维 + rerank（top_k=10、阈值 0.7、margin 0.05） | BM25 + 可选向量（faiss/zvec）+ RRF；需注入 embedding | ⚠️ 可提供近似召回，但阈值/边际/维度需重建 |
| 类型化图谱查询 | Neo4j Cypher（节点/关系/属性） | wikilink 图（frontmatter 存少量属性） | ⚠️ 只能表达“链接”，不能表达带属性关系与约束 |
| 证据溯源/审计 | PG 行 + JSONL + fact_id + span | 卡片 frontmatter + line range；无事务 | ⚠️ 不能作为权威审计源 |
| 文档接入 | MinerU→Markdown | `auto_resource` 支持 md/txt/json/jsonl/csv/yaml/html | ✅ Phase 2 产物可直接接入 |
| 跨会话记忆 | 无 | 内建（daily/digest、auto_memory/auto_dream） | ✅ 新增能力 |
| 多租户/权限 | PG + owner_user_id + 404 语义 | 无多租户，一个 workspace 一个 owner | ❌ 不能承载用户私有数据 |
| 运维 | PG 备份、Neo4j 备份 | Markdown 目录 + 可重建索引 | ✅ 简单，但需文件备份策略 |

#### 4.3.2 两种落地范围

**范围 A（推荐，与已确认的“外部知识库服务”一致）：ReMe 作为“记忆/文献知识层”，不替换权威 KB**
- 新增：ReMe 服务 + Phase 3 召回 + Phase 5 QA 的补充上下文。
- 保留：PG 术语库、Neo4j 证据图、JSONL 审计产物。
- 成本：**2–3 人周**（服务部署、卡片模板、召回评测、降级）。
- 风险：低（不改变证据路径）。

**范围 B（字面）：ReMe 替换现有知识库**
- 需要：Neo4j 全量迁移到 Markdown 卡片；Phase 4 语义匹配改为 ReMe 检索（失去精确别名优先级与唯一约束）；Phase 5 QA 改为卡片检索；补充事务/审计的替代方案。
- 成本：**3–5 人周**迁移 + **2–3 人周** Phase 4/5 改造 + 持续的对账成本。
- 风险：高（临床证据可追溯性、精确匹配回退、性能/一致性）。
- 结论：**不建议在本轮做**；若一定要做，先做范围 A，用 2 个迭代验证召回质量，再决定是否切换。

#### 4.3.3 数据迁移方式（范围 B 时）

见 §3.5.4（导出→卡片→幂等导入→对账→双写回滚）。关键难点：
- Neo4j 关系上的属性（如 `evidence_label`、`source_span`）在 wikilink 中只能放进目标卡片 frontmatter，多来源同一关系会合并/丢失；
- 同一实体多别名（HGNC symbol/previous symbol、ClinVar 别名）在 Markdown 中需要显式 alias 列表，否则检索召回下降；
- 删除/更正语义：文件系统没有事务，需“软删除 + 版本目录”。

### 4.4 依赖 / Python / uv 约束（实测）

测试方法：`uv 0.11.28` + CPython 3.12.13，临时工程，索引使用仓库同款本地镜像 `http://127.0.0.1:3141/root/pypi/+simple/`（与 `backend/pyproject.toml` 一致）。以下为真实解析结果，不是纸面推断。

#### 4.4.1 结论一：AgentScope 可以进 backend，代价很小

在**保持现有锁定版本**的前提下加入 `agentscope==2.0.12`：

```text
agentscope==2.0.12    ✅
langgraph==1.2.4      ✅ 保持不变
langchain-core==1.4.3 ✅ 保持不变
fastapi==0.136.3      ✅ 保持不变
numpy==2.3.5          ✅ 保持不变
neo4j==6.2.0          ✅ 保持不变
pydantic==2.13.4      ✅ 保持不变
openai==2.41.0        ✅ 保持不变
certifi==2026.10.23   ⬆ 从 2026.5.20 升级（agentscope 要求 >=2026.10.19）
httpx2==2.16.2        ➕ 新增
mcp==2.3.0            ➕ 新增
```

→ **backend 内进程使用 AgentScope 是低风险的**；只需 `uv lock` 更新 certifi 并接受两个新包。

#### 4.4.2 结论二：ReMe 不能进 backend（会强制升级外层栈）

`reme-ai`（无论是否 `[core]`）要求 `fastapi>=0.162.0`；实测与 `fastapi==0.136.3` 不可满足：

```text
× No solution found when resolving dependencies:
╰─▶ Because reme-ai==0.4.2.3 depends on fastapi>=0.162.0 and you require
    reme-ai==0.4.2.3, we can conclude that you require fastapi>=0.162.0.
    And because you require fastapi==0.136.3, we can conclude that your
    requirements are unsatisfiable.
```

不钉旧版本时，解析器给出的一体化升级集为：`fastapi 0.163.1`、`numpy 2.5.5`、`openai 3.52.0`、`langchain-core 1.8.1`、`pydantic 2.14.3`、`neo4j 6.4.1`、`certifi 2026.10.23`。这直接触碰“外层服务不动”，因此 **ReMe 应独立部署**。

#### 4.4.3 结论三：`reme-ai[core]` 与 AgentScope 2.0.12 互斥（同环境）

```text
× Because reme-ai[core]==0.4.2.3 depends on agentscope[model-ollama]==2.0.11
  and your project depends on agentscope==2.0.12, ... unsatisfiable.
```

原因：`reme-ai` 的 `as` extra 钉 `agentscope[...]==2.0.11`，`core` 依赖 `as`；`hermes` extra 更旧（2.0.10）。可选路径：
- **A**：backend 用 `agentscope==2.0.12`；ReMe 服务独立环境用 `reme-ai[core]`（内部 2.0.11）——推荐；
- **B**：同环境 `agentscope==2.0.11` + `reme-ai[core]`——牺牲 AgentScope 一个补丁版本，换取“单环境”；
- **C**：同环境 `agentscope[reme]==2.0.12` + 显式 `faiss-cpu`/`zvec`/`neo4j`——能装，但 `reme-ai` 仍会拉高 fastapi/numpy，等于回到结论二。

#### 4.4.4 其他版本事实

| 项 | 事实 |
|---|---|
| Python | 项目 `>=3.12`；AgentScope `>=3.11`；ReMe `>=3.11` → **无冲突** |
| LangGraph | 现锁 1.2.4；最新 1.2.22（2026-11-14）。1.2.22 要求 `langchain-core>=1.4.7`，而现锁 1.4.3 → 仅当升级 LangGraph 才需同步升级 core；**本方案不强制升级** |
| Pydantic | ReMe 要求 `>=2.13.4`；现锁 2.13.4 → 恰好满足；若整体升级会被带到 2.14.x |
| openai | ReMe 要求 `>=2.24.0`；现锁 2.41.0 → 满足；一体化升级会到 3.52（大版本，需评估） |
| uv | 本地镜像已提供 `agentscope` 与 `reme-ai`（三次解析实测均可获取）；`uv lock` 需全量重解析（实测 153–167 包） |
| 构建/部署 | backend 镜像需新增 agentscope（+httpx2/mcp）；ReMe 需新增一个服务/镜像与 workspace 卷；docker compose/K8s 变更属于运维范畴 |

### 4.5 总评

| 项 | 结论 | 说明 |
|---|---|---|
| LangGraph 状态图 | **可行（已具备）** | 3 处 StateGraph；语义覆盖完整；建议只做拓扑显式化 |
| AgentScope 子智能体 | **可行，需适配** | 2.0.12 API 稳定；需写 LangGraph 节点适配器、消息转换、key 轮换；**建议有界智能体** |
| ReMe 知识库 | **需调整** | 已确认作为外部知识库服务；可承担记忆/文献知识层；作为术语/图谱权威 KB 不可行 |
| 依赖/Python/uv | **可行，需分层** | AgentScope 进 backend 代价小；ReMe 必须独立环境 |
| 外层服务 | **可保持不变** | 所有冻结项见附录 B；前提是不引入第二套恢复/HITL 语义 |

---

## 5. 分阶段迁移方案

设计原则：**每个阶段都能独立上线、独立验证、独立回滚**；默认关闭新路径，用影子运行（shadow）对照旧路径，确认一致后再切流。任何阶段都不修改外层 HTTP/DB/队列契约。

**目录迁移总则（r2 新增，适用于阶段 0–4）**

1. 目录迁移必须单独成 commit：只做 `git mv` + import 重写 + 空 `__init__.py`/shim，不夹带行为变更；行为变更（agent/ReMe/并行窗口）另起 commit。
2. 一个阶段只迁一个层或一组同层模块；迁移后立即跑该层测试与 import 边界测试，不把多个层的搬迁压到同一个 PR。
3. 旧路径 shim 至少保留一个发布周期；删除 shim 单独立项，不在行为切换的同一 PR 里做。
4. 每个阶段结束都重新生成一次 §3.2.5 的影响面统计（文件数、import 行数、shim 数），确认没有新增反向依赖。
5. 目录迁移不新增运行时开关；回滚依靠 revert 搬迁 commit + 保留 shim，而不是新增开关。

### 阶段 0 — 基线与契约冻结（1 人周）

| 项 | 内容 |
|---|---|
| 目标 | 建立“改前基线”，让后续每个阶段都有可对照的数值与契约快照 |
| 目录迁移 | 只产出 §3.2.3 的模块→层映射与旧 import 基线（56 文件 / 20 非测试行（另 3 行为不迁的 `graph_rag`）/ 56 测试文件）；创建 `src/pipeline/{graph,skills,tools,mcp,contracts}/__init__.py` 空骨架；新增 `tests/pipeline/test_import_boundaries.py`（只对空骨架与 allowlist 断言）；**不改任何 import、不移动文件** |
| 产出 | ① 现有测试基线报告（`tests/agents` 179 + `tests/api/test_pipeline_api.py` 18 + `tests/core/source_fact_chain` 21）；② 3–5 篇代表性文档的抽取基线（facts/verifications/english 的 JSONL、耗时、token/费用、provider 调用次数）；③ 版本与依赖快照（当前 lock 的 12 个关键包）；④ 配置开关骨架 `pipeline.agent_runtime = legacy \| shadow \| agentscope`（默认 legacy）；⑤ 冻结契约清单（附录 B）评审签字；⑥ 目录迁移映射表与 import 基线 |
| 验证 | 基线测试全绿；同一文档重复运行结果稳定（事实 ID 集合一致）；基线数据存档；`python -c "import src.pipeline"` 与 import 边界测试通过；旧 import 计数与基线一致（无非预期新增） |
| 回滚 | 无行为变更，无需回滚；空骨架与边界测试可直接删除 |
| 退出条件 | 基线报告 + 开关合并；团队确认“外层不改”的边界与目录迁移映射 |

> 建议同时把 `docs/` 中本方案的状态从 planned 改为 active，并关联 issue。

### 阶段 1 — LangGraph 拓扑显式化（2 人周）

| 项 | 内容 |
|---|---|
| 目标 | 把“阶段内部手写循环”提升为图节点/子图，为 AgentScope 提供稳定挂载点；**不引入 agent、不改模型调用** |
| 目录迁移 | `git mv src/agents/orchestrator.py → src/pipeline/graph/topology.py`；`phase_{1..4}_adapter.py → src/pipeline/graph/phases/phase_{1..4}.py`；旧路径留 re-export shim；新增 `graph/nodes.py`、`graph/progress.py`；`contracts.py`/`runner.py` 等外层文件不动；本阶段不移动 `src/core/*` |
| 产出 | ① `src/pipeline/graph/` 显式拓扑：4 个 phase 节点 + Phase 3 窗口子图（`prepare → fan-out → extract/verify/translate → merge`）；② 节点级进度写入 `PhaseStatusResponse.summary.nodes`（前端可后续启用）；③ 窗口 fan-out 的 reducer 与确定性合并（按 `fact_id`/`window_id` 排序）；④ 图级单元测试（分支、skip、失败短路、并发上限）；⑤ 旧路径 shim 与 import 边界测试 |
| 验证 | ① 现有 218 个相关测试全绿；② 黄金文档的 `chain_run.json` 与基线**语义一致**（facts/verifications/english 集合逐字段相等；允许时间戳/耗时差异）；③ 并发窗口下结果与串行一致（重复 5 次）；④ API 契约测试不变；⑤ `src/api/wiring.py` 零改动仍可 import，边界测试通过 |
| 回滚 | 开关 `pipeline.topology = legacy \| staged`；legacy 走原 `PipelineOrchestrator`；目录迁移 commit 可整体 revert，shim 未删时旧路径继续可用 |
| 退出条件 | 影子对照零差异；P95 耗时不超过基线 +10%；旧路径 shim 生效且无新增反向依赖 |

> 该阶段是“低风险高价值”：即使后续不做 AgentScope，图显式化本身也能带来节点级可观测与并行窗口收益。

### 阶段 2 — AgentScope 运行时 + Phase 3 抽取试点（2–3 人周）

| 项 | 内容 |
|---|---|
| 目标 | 打通 LangGraph ↔ AgentScope 的最小闭环，只替换 Phase 3 的 `extract` stage |
| 目录迁移 | 新增 `src/pipeline/skills/{runtime,fact_chain}` 与 `src/pipeline/tools/fact_chain`；`source_fact_chain/{contracts,core,windowing,projection,api}.py → tools/fact_chain`、`{runner,prompts}.py → skills/fact_chain`、`providers.py → skills/runtime/llm.py`；`src/core/source_fact_chain/api.py` 留 shim；更新 3 个测试文件 import；不移动测试目录 |
| 产出 | ① 依赖：`agentscope==2.0.12` 入 backend（certifi 升级 + httpx2/mcp）；② `AgentScopeNode` 适配器（`reply(structured_schema=...)`、`Msg`↔图状态转换、异常→`RetryablePhaseError`/`PermanentPhaseError`）；③ 多 key 轮换的 credential/model 包装；④ `ExtractAgent`（工具：`validate_candidate`/`locate_quote`/`schema_check`；输出：候选事实列表）；⑤ 影子模式：同一窗口同时跑旧 provider 与新 agent，逐条 diff；⑥ 成本/延迟埋点；⑦ 目录迁移与 shim |
| 验证 | ① 影子 diff：黄金文档上 facts 集合 100% 一致（ID、字段、值、极性、subject、span）；② 不一致样本必须能归因（模型随机性/校验顺序/提示词差异），并记录处置；③ 失败注入：provider 超时、空回复、非法 JSON、预算耗尽 → 错误分类与旧路径一致；④ 连续 1 周影子运行无 P0/P1 差异；⑤ 成本增幅 ≤15%，P95 延迟增幅 ≤20%；⑥ 旧路径 shim 与 `src/api/wiring.py` 兼容，`source_fact_chain` 21 用例全绿 |
| 回滚 | `pipeline.agent_runtime=legacy` 即回旧 provider；agentscope 延迟导入，未启用时不加载；目录迁移 commit 可整体 revert，shim 保留 |
| 退出条件 | 影子验收通过；形成“可切换”结论（不强制全量切流）；目录迁移后覆盖率不低于原 `source_fact_chain` 80.99% 基线 |

### 阶段 3 — verify/translate 与 Phase 1/2 agent 化（2 人周）

| 项 | 内容 |
|---|---|
| 目标 | 完成 Phase 3 全链路 agent 化；Phase 1/2 只做“统一运行时”的薄封装（默认不启用 LLM 决策） |
| 目录迁移 | `document_acquisition → pipeline/tools/acquisition`、`parse_document → pipeline/tools/parsing`；`src/core/ingest_and_digitize_data/` 留 shim；新增 `skills/{acquisition,parsing}`；`api/v1/chat.py`、`api/wiring.py` 可走 shim 或改 import；更新 24 个测试文件 import |
| 产出 | ① `VerifyAgent`（reasoning 模型，输出仅 `supported/unsupported/uncertain/unverified`，只追加不改事实）；② `TranslateAgent`（只处理 2 个 PRESENTED 字段，EN 源文档零调用）；③ `AcquisitionAgent`/`ParseAgent` 薄封装（工具直连现有服务）；④ 统一错误映射与重试归属（executor 唯一负责阶段重试）；⑤ 审计事件（events/rejections）对齐；⑥ 两个工具的目录迁移与 shim |
| 验证 | ① 全链路影子 diff 零差异；② verify 的 `unverified` 原因与旧路径一致（`missing_verdict`/`invalid_label`/`verify_call_failed`）；③ translate 的 `PRESERVED/PASSTHROUGH/MISSING/FAILED` 语义一致；④ Phase 1/2 在关闭 LLM 时与旧路径完全等价；⑤ 断点复用（source_hash+config+prompt_versions）仍生效；⑥ 191 个 ingest 用例 + acquire/wiring 测试全绿，旧路径 shim 可用 |
| 回滚 | 按节点开关（`phase3.extract/verify/translate`、`phase1/2.agent`）；任一节点可单独回退；目录迁移 commit 可整体 revert |
| 退出条件 | Phase 3 影子零差异 ≥1 周；Phase 1/2 无行为变化；迁移后 import 边界测试全绿 |

### 阶段 4 — Phase 4 薄 agent + ReMe 记忆层（2–3 人周）

| 项 | 内容 |
|---|---|
| 目标 | 验证“记忆/知识层”价值，同时不改变临床证据路径 |
| 目录迁移 | ① 先把共享三件套 `contracts.py`/`hgvs_normalizer.py`/`context_pack/` 抽到 `src/core/terminology_shared/`，更新 `graph_rag`、`evidence_extraction` 的 7 个文件 / 8 处 import；② 其余 `standardize_entities_and_align_knowledge` 实现 `git mv` 到 `pipeline/tools/terminology/`；③ `src/core/standardize_entities_and_align_knowledge/api.py` 留 shim；④ 新增 `skills/standardization`、`mcp/reme`；⑤ 更新 29 个测试文件与 3 个脚本 import；`database/terminology_database/README.md` 示例同步 |
| 产出 | ① ReMe 外部服务（已确认；镜像/venv、workspace 卷、HTTP/MCP、健康检查、备份脚本）；② 卡片模板与 `auto_resource` 接入（Phase 2 的 `output.md`/`metadata.json`）；③ Phase 3 agent 的召回（search → 注入参考上下文，标注非证据）；④ `StandardizeAgent` 薄封装（LLM 默认关闭，仅保留工具编排）；⑤ 降级策略（超时/不可用→空记忆，主路径继续）；⑥ 运维文档（workspace 备份、版本升级、容量）；⑦ 目录迁移、shim 与 `terminology_shared` 抽取 |
| 验证 | ① ReMe 故障注入：主路径成功率 100%，仅记忆为空；② 召回评测：50–100 条查询的 top-5 命中率/相关性相对基线提升（预先定义指标）；③ 证据输出与阶段 3 完全一致（记忆不得改变 facts/supported）；④ Phase 4 计数与旧路径一致；⑤ 敏感数据检查（workspace 不含用户私有内容）；⑥ 218 个 standardize 用例与 graph_rag/evidence_extraction 相关测试全绿；⑦ 无 `src/core/graph_rag → src/pipeline` 反向依赖 |
| 回滚 | `memory.enabled=false`；ReMe 服务可整体下线，不影响 pipeline；目录迁移 commit 可整体 revert，shim 保留 |
| 退出条件 | 记忆收益可量化且无临床路径影响；运维可接管；import 边界测试全绿 |

### 阶段 5（可选）— 知识库整体切换（3–5 人周）

| 项 | 内容 |
|---|---|
| 前提 | D1 明确选择“ReMe 替代 Neo4j/术语库”；阶段 4 的召回评测达标；Phase 5 产品确认可接受语义变化 |
| 目录迁移 | 不新增目录；Neo4j → Markdown 迁移脚本放 `backend/scripts/`（或 `pipeline/mcp/reme/migrations/`，待定），不改变已定布局 |
| 产出 | ① Neo4j → Markdown 卡片迁移脚本（幂等、可重跑、计数对账）；② Phase 4 语义匹配的 ReMe 适配（保留精确匹配作为第一层）；③ Phase 5 QA 检索切换 + 双写期；④ 回滚手册 |
| 验证 | ① 节点/关系计数与抽样一致；② QA 评测集上答案质量不低于基线；③ 术语精确匹配零回退（精确层不动）；④ 双写期数据一致性对账 |
| 回滚 | Neo4j 保留只读 ≥2 个迭代；开关切回图查询 |
| 退出条件 | 评测达标 + 产品签字 + 运维接受文件型存储 |

### 阶段依赖与关键路径

```text
阶段0 ──► 阶段1 ──► 阶段2 ──► 阶段3 ──► 阶段4 ──► 阶段5(可选)
             │           │
             └─ 可独立交付 └─ 可在此暂停（已获得大部分收益）
```

- **阶段 1 可独立交付**：图显式化 + 节点可观测，即使不做 AgentScope 也有价值。
- **阶段 2 是决策点**：影子验收通过后，可选择“只切 Phase 3”或“继续阶段 3/4”。
- **阶段 4 可与阶段 3 并行**（ReMe 服务部署不依赖 verify/translate 改造），但召回接入需要在阶段 3 之后。
- **目录迁移与行为改造解耦**：阶段 1 只迁 `graph/` + adapters，阶段 2 迁 `fact_chain`，阶段 3 迁 acquisition/parsing，阶段 4 迁 terminology + 新增 `mcp/`；任何一层的搬迁失败都可单独 revert，不影响其他层的行为开关。

### 5.6 实施状态（2026-11-18）

| 阶段 | 状态 | 交付 | 验证（CI 等价环境） |
|---|---|---|---|
| 0 | 完成 | 骨架、import 基线、边界测试、inventory 脚本 | 边界测试通过 |
| 1 | **部分完成** | `graph/` 目录迁移、orchestrator + 4 adapter 迁入、节点级进度写入 `summary.nodes`（`graph/progress.py`）；窗口 `Send` fan-out 与 `graph/nodes.py` **未实现** | 202→382 相关测试通过 |
| 2 | 完成（代码） | fact_chain 迁移、AgentScope extract、`legacy/shadow/agentscope` 开关、多 key 轮换 | 288 passed / 88.15% |
| 3 | 完成（代码） | acquisition/parsing 迁移、verify/translate skill、`SkillError→ProviderError` | 294 passed / 88.55%；ingest 154 |
| 4a | 完成（代码） | ReMe HTTP 客户端/registry、记忆注入、counts-only 摘要、默认关闭 | 308 passed / 88.84% |
| 4b | 完成（代码） | `terminology_shared` + terminology 迁移（27 files） | 376 passed / 89.34%；术语+graph_rag+evidence 841 |
| 5 | 未做（可选） | — | — |

实施记录：`docs/active/2026-11-17-pipeline-stage-0-1-migration.md`、`2026-11-18-pipeline-stage-2-agentscope-runtime.md`、`2026-11-18-pipeline-stage-3-phase3-agents-and-ingest-migration.md`、`2026-11-18-pipeline-stage-4a-reme-memory.md`、`2026-11-18-pipeline-stage-4b-terminology-migration.md`。

**与方案的偏差（均为有意）**

1. 服务门面 `SourceFactChainService` 落在 `skills/fact_chain/service.py`，而非 `tools/fact_chain/api.py`：`tools/` 禁止 import `skills/`，门面需要构造 provider。
2. `terminology_shared` 额外下沉 `normalizers.py` 与 `amino_acids.py`：`context_pack` 依赖 `collapse_spaces`、`hgvs_normalizer` 依赖 `AA3_TO_1`，不下沉会形成 shared → pipeline 反向依赖。
3. ReMe 配置使用 `pipeline.memory.*`（env `PIPELINE_MEMORY_*`），而非 `pipeline.mcp.reme.*`：沿用仓库扁平配置约定。
4. 单一 `pipeline.agent_runtime` 覆盖 Phase 3 三个阶段，不引入按节点开关（回滚粒度已足够）。
5. Acquisition/Parse/Standardize 的“薄 agent 封装”未做：无 LLM 决策，按 `AGENTS.md` §20.2 不引入无行为转发层。
6. 阶段 1 的窗口 `Send` fan-out 与 `graph/nodes.py` 未实现：skill 已通过 `Provider` 协议挂载，独立节点适配器无额外价值；窗口并行缺少黄金文档基线，无法验证“并发与串行语义一致”。节点级进度（`summary.nodes`）已实现。

**仍未执行的验收项**

- 真实模型影子对照：阶段 2/3 的成本（≤+15%）、P95 延迟（≤+20%）与逐条差异归因，需要真实 API 凭证与黄金文档。
- ReMe 服务联调与 50–100 条查询的召回评测；`auto_resource` 接入 Phase 2 产物。
- 阶段 1 窗口并行的等价性验收（同黄金文档）；节点级进度已交付。

---

## 6. 风险与回滚

| # | 风险 | 影响 | 概率 | 缓解 | 回滚 |
|---|---|---|---|---|---|
| R1 | 智能体自主决策改变临床事实（漏抽/错抽/改写） | **高**（临床可信度） | 中 | 有界智能体；模型输出必须过现有校验器；shadow 零差异门槛；agent 无写权限 | 关闭 agent 开关，回旧 provider |
| R2 | 并行窗口导致事实重复/顺序不稳定 | 中 | 中 | 确定性 `fact_id`；按 ID 去重合并；落盘前统一排序；重复运行一致性测试 | 回串行窗口 |
| R3 | 三套状态存储（LangGraph/AgentScope/ReMe）不一致 | 中–高 | 中 | v1 不引入 checkpointer；AgentState 不持久化；ReMe 只存记忆；单一真相源 `state_json` | 关闭 agent 记忆/状态 |
| R4 | 重试放大（executor × agent × provider） | 中（费用/时延） | 中 | 明确唯一 owner：阶段重试=executor，节点内=provider，agent 仅一次自校正；预算上限 | 降 `max_attempts`/关闭 agent 重试 |
| R5 | ReMe 数据丢失/不可审计（Markdown、无事务） | 中 | 中 | 定位为“可重建记忆”；workspace 备份；不存权威数据；卡片带溯源 frontmatter | 删除/重建 workspace，不影响主路径 |
| R6 | ReMe 版本/API 频繁变动（0.4.x，3 个月 89 个 release） | 中 | 高 | 独立服务 + 精确 pin；契约测试（search/write 响应 schema）；升级前跑召回归 | 回滚服务镜像版本 |
| R7 | 依赖升级破坏外层（FastAPI/numpy/openai 大版本） | **高** | 中 | ReMe 独立环境；backend 只加 agentscope（实测仅 certifi 升级）；锁文件分服务 | 回滚 lock/镜像 |
| R8 | 成本/延迟上升（agent 循环、记忆检索） | 中 | 中–高 | 迭代上限、结构化输出、模型分级、缓存、预算告警；阶段 2 设 +15%/+20% 门槛 | 关闭 agent/记忆 |
| R9 | Phase 4 事务边界被 agent 破坏 | **高**（数据一致性） | 低–中 | 持久化只经 tool，事务由 `StandardizationService` 持有；agent 不直接拿 session | 回旧 adapter |
| R10 | 可观测性不足导致排障困难 | 中 | 中 | 节点/agent 级 trace（OpenTelemetry）、request_id 贯通、事件落盘；保留现有 loguru | 无需回滚（增强项） |
| R11 | 敏感数据进入 ReMe Markdown（无加密/无租户） | **高**（合规） | 中 | 只存公开文献与脱敏运行摘要；workspace 权限/卷加密；不存用户私有内容；上线前评审 | 清空/隔离 workspace |
| R12 | 迁移期间双实现漂移（旧路径修复未同步） | 中 | 高 | 影子期“旧路径仍为唯一真相”；新路径只读对照；设定切换窗口；差异看板 | 延长 shadow，不切流 |
| R13 | AgentScope 2.x API 变动（2.0.0 是大重写） | 中 | 中 | 精确 pin 2.0.12；适配器隔离（只在 1–2 个文件引用 agentscope）；升级需过适配器测试 | 回旧 provider |
| R14 | 阶段 1 并行窗口触发 provider 限流 | 中 | 中–高 | 并发信号量、按 key 限流、退避；先串行后并行灰度 | 降并发/回串行 |
| R15 | 目录迁移导致 import/测试/脚本断裂（尤其 `graph_rag`、休眠模块、3 个脚本） | 中 | 中–高 | 纯搬迁 commit；旧路径 shim；import 边界测试；每阶段只迁一组模块；阶段 0 生成 import 基线 | revert 该层搬迁 commit；shim 保留 |
| R16 | 共享模块归属错误，形成 `src/core/graph_rag → src/pipeline` 反向依赖 | 中–高 | 中 | 先抽 `src/core/terminology_shared/`（contracts/normalizer/context_pack），再迁实现；边界测试禁止反向依赖；代码评审检查 import 方向 | revert `standardize` 搬迁；graph_rag 不动 |

**统一回滚原则**：每个新路径都有配置开关；开关默认关闭；旧路径在切换后至少保留 2 个迭代；数据库/文件产物不删除（只追加）；ReMe 可整体下线。

---

## 7. 工作量估算

| 阶段 | 内容 | 人周（1–2 人） | 主要角色 |
|---|---|---|---|
| 0 | 基线、契约冻结、开关骨架 | 1 | 后端 |
| 1 | LangGraph 拓扑显式化 + 节点进度 + 并行窗口 | 2 | 后端 |
| 2 | AgentScope 适配器 + Phase 3 extract 试点 + shadow | 2–3 | 后端 + 算法 |
| 3 | verify/translate + Phase 1/2 薄 agent | 2 | 后端 + 算法 |
| 4 | Phase 4 薄 agent + ReMe 服务 + 记忆接入 | 2–3 | 后端 + 运维 |
| 5（可选） | KB 整体切换 + 数据迁移 | 3–5 | 后端 + 运维 + 产品 |
| —（分摊 1–4） | 目录迁移、shim、import/测试/脚本改写（r2 新增） | 1.5 | 后端 |
| — | 风险缓冲（20%） | 2 | — |
| **合计（0–4）** | **不含可选 KB 切换** | **10.5–12.5 人周（含 20% 缓冲 12.5–15）** | |
| **合计（0–5）** | 含 KB 切换 | **13.5–17.5 人周（含 20% 缓冲 16–21）** | |

说明：
- 估算基于“1 名熟悉仓库的后端 + 0.5 名算法/评测”并行投入；若只有 1 人，日历时间约翻倍。
- 目录迁移的 1.5 人周是 r2 新增：56 个文件 `git mv`、56 个测试文件/153 行 import 改写、约 15 个 shim；不做目录重构时按原估算 9–11 / 12–16 人周。
- 不含产品/临床专家评审时间（影子结果的抽样复核建议每阶段 0.5 人周）。
- 不含 ReMe 服务的生产运维成本（容量、备份、监控）。

---

## 8. 架构决策与落定结果

> 2026-11-18：D1–D3、D5–D9 按各节推荐项落定，D4 由需求方确认；实施结果见 §5.6。以下各节保留原始选项与理由，作为决策依据。

### D1 — ReMe 的定位：记忆层还是权威知识库？

| 选项 | 内容 | 成本 | 风险 | 推荐 |
|---|---|---|---|---|
| A | **记忆/文献知识层**：ReMe 存运行记忆、文献卡片、审核先例；术语库（PG）与证据图（Neo4j）继续权威 | 2–3 人周 | 低 | ✅ |
| B | **整体替换**：Neo4j 图 + 术语语义匹配都迁到 ReMe | +3–5 人周迁移 + 2–3 人周改造 | 高（精确匹配、审计、事务） | ❌ |

**推荐 A**。若选 B，必须先完成阶段 4 的召回评测，并提供“精确匹配零回退”的证明。

### D2 — 节点粒度：4 个 phase 还是每个 stage 一个节点？

| 选项 | 内容 | 优点 | 缺点 | 推荐 |
|---|---|---|---|---|
| A | **4 个 phase 节点 + Phase 3 子图**（窗口并行） | 改动可控；外层状态不变；能拿到主要收益 | 节点级观测粒度中等 | ✅ |
| B | 18+ stage 全上图 | 最细粒度、可单点重试 | 中间状态需序列化；Phase 4 事务被拆；迁移成本翻倍 | ❌（首期） |

### D3 — 智能体自主度：有界工具调用还是自由 ReAct？

| 选项 | 内容 | 风险 | 推荐 |
|---|---|---|---|
| A | **有界**：固定工具白名单、结构化输出、确定性校验器守门、迭代上限 | 低；可审计 | ✅ |
| B | 自由 ReAct：agent 自行决定工具/步骤 | 高（不可预测、成本、临床风险） | ❌ |

### D4 — ReMe 部署形态：独立服务还是进程内嵌？✅ 已确认

**决定（需求方，2026-11-17）：ReMe 作为外部服务，用于知识库的调用。**

| 选项 | 内容 | 优点 | 缺点 | 结论 |
|---|---|---|---|---|
| A | **独立服务**（HTTP/MCP，独立 env） | 不动 backend 依赖；可独立扩缩/重启；符合单写者 | 多一个部署单元、网络跳 | ✅ **采纳** |
| B | 进程内 `ReMeMiddleware` | 调用简单、低延迟 | 强制 FastAPI/numpy/openai 升级；多 worker 抢 workspace | ❌ 不采纳 |

该决定关闭“部署形态”问题，但落地前仍需确定三项实现细节（不阻塞阶段 0/1）：
1. 调用协议：优先 MCP（AgentScope 原生工具协议），备选普通 HTTP（`search`/`write`/`auto_resource`）。
2. 鉴权与网络边界：内网 mTLS 或服务令牌；workspace 卷权限。
3. 高可用：单写者约束下如何重启/备份（建议单实例 + 健康检查 + 卷快照）。

### D5 — 版本钉法

| 选项 | backend AgentScope | ReMe 环境 | 结论 |
|---|---|---|---|
| A（推荐） | **2.0.12** | `reme-ai[core]==0.4.2.3`（内含 2.0.11） | 两边解耦，各自最新稳定 |
| B | 2.0.11 | `reme-ai[core]==0.4.2.3` | 同版本但 backend 落后一个补丁 |
| C | 2.0.12 + `agentscope[reme]` + 显式后端 | 同环境 | 依赖升级连锁，不推荐 |

### D6 — Phase 4 是否 agent 化？

| 选项 | 内容 | 结论 |
|---|---|---|
| A | **薄封装**：agent 只做工具编排，LLM 默认关闭；匹配/持久化仍是确定性服务 | ✅ 满足“每节点有 agent”的结构要求，不引入 LLM 风险 |
| B | 完全保留确定性服务，不建 agent | 结构上不满足“每节点 AgentScope”，但风险最低 |
| C | LLM 参与歧义消解 | 需单独评测；建议作为后续增强，不进首期 |

### D7 — 遗留代码（`evidence_extraction` 12k 行 / `cross_lingual_translation` 5.3k 行）如何处置？

| 选项 | 内容 | 结论 |
|---|---|---|
| A | **不迁移、保持休眠**，仅保留测试 | ✅ 首期 |
| B | 若产品确需 166 字段全量抽取：整体作为 1 个 `DeepExtractionAgent`，内部保留现有 LangGraph | 单独立项 |
| C | 删除 | 需产品确认无路线图依赖；单独 PR，不与本次混做 |

### D8 — 恢复与人工介入语义是否改变？

| 选项 | 内容 | 结论 |
|---|---|---|
| A | **v1 不变**：阶段级持久化 + 崩溃标 FAILED + 阶段重跑复用 | ✅ |
| B | 引入 LangGraph checkpointer + `interrupt()` 做节点级续跑/人工审批 | 需修改外层契约（心跳/租约/状态枚举），单独立项 |

### D9 — 领域层目录划分：`src/pipeline/{graph,skills,tools,mcp,contracts}` 是否采纳？

**背景（r2 新增）**：需求方要求 pipeline 领域层按 `skills/`、`mcp/`、`tools/` 这类职责划分来组织，与“LangGraph 状态图 + 每节点 AgentScope 子智能体 + ReMe 外部知识库”的组合一致。§3.2 给出完整目标布局、模块映射、import 变化与阶段步骤。

| 选项 | 内容 | 优点 | 缺点 | 结论 |
|---|---|---|---|---|
| A | **新建 `src/pipeline/{graph,skills,tools,mcp,contracts}`**：pipeline 专属实现迁入；共享模块（`graph_rag`、`terminology_shared`、休眠切片、外层 `agents/` 文件）不动；旧路径 shim 一个发布周期 | 职责边界最清晰；与三技术组合一一对应；每层可独立 review/revert | import 改写面较大（56 文件 / 153 测试 import）；需维护约 15 个 shim | ✅ 推荐 |
| B | 保留 `src/core/<feature>`，只在 `src/pipeline/` 加 `skills/` + `mcp/`，`tools/` 做薄 facade | 改动最小；不动 5.7k 行术语实现 | `tools/` 只是包装，目录并未真正按层组织；只部分满足新增约束 | 备选 |
| C | 直接放在 `src/agents/{graph,skills,tools,mcp}` | 不新增顶层包；复用现有 `agents/` | 与 AGENTS §2.1“`agents/` = Orchestrator”冲突；feature 代码进入编排目录，边界更模糊 | ❌ |

**推荐 A**。理由是它把“谁做决策（skills）/ 谁做确定性工作（tools）/ 谁跨进程（mcp）/ 谁定拓扑（graph）”变成可检查的目录边界，而不是靠命名约定；同时通过“共享模块不迁 + 旧路径 shim”把外层风险压到接近零。

**仍需用户确认的点**：

1. **skills 与 tools 的边界**：§3.2.1 的口径是“需要 prompt/模型调用 → `skills/`，纯确定性 → `tools/`”。灰区是 Phase 1/2 中**不使用 LLM 的 agent**：推荐仍保留为 skill（统一运行时、观测与未来扩展），但也可以降级为“graph 节点直接调 tool、不建 AgentScope agent”。需确认是否接受“无 LLM 的 skill”。
2. **MCP 配置存放位置**：推荐非敏感拓扑（`transport`/`url`/`timeout_ms`/`workspace`）放 `backend/config/defaults/main.yaml` 的 `pipeline.mcp.reme.*`，密钥（token）放 `backend/config/vault/<env>.yaml`，部署端口/卷放 `deploy/compose` 或 `deploy/ansible`；备选是单独 `backend/config/mcp/*.yaml`。需确认采用“应用配置 + vault”模式，避免 MCP 配置分裂。
3. **外部知识服务是否统一收口到 `mcp/`**：本轮 `graph_rag` 不迁（它不是 MCP，且有 Phase 5/chat 调用方）；若未来 Neo4j/ReMe 都统一为 MCP 服务，再单独立项。
4. **`AGENTS.md` 映射更新**：`src/pipeline/` 是 pipeline 专属例外，阶段 1 需同步更新 AGENTS §2.1 的后端映射（单独 docs PR，不在本次修订内）。
5. **测试目录是否镜像源码**：本轮只改 import、不移动测试；终态是否把 `tests/core/<feature>` 迁到 `tests/pipeline/*`，可后续决定。
6. **shim 生命周期**：建议保留一个发布周期；需与团队发布节奏对齐后确认。

> D9 不阻塞阶段 0/1；但阶段 2 开始前需确认第 1/2 点，阶段 4 前确认第 3/6 点。

---

## 9. 附录

### 9.1 附录 A — 版本与事实来源（2026-11-17）

| 组件 | 版本/事实 | 来源 |
|---|---|---|
| LangGraph | 1.2.4（锁定）；最新 1.2.22（2026-11-14）；Python ≥3.10；MIT | PyPI JSON、项目 `uv.lock` |
| langchain-core | 1.4.3（锁定）；1.2.22 要求 ≥1.4.7 | 同上 |
| AgentScope | 2.0.12（2026-11-16）；Python ≥3.11；Apache-2.0；36k stars；2.0.0 为 2026-05-25 重写 | PyPI JSON、wheel 源码 |
| ReMe | `reme-ai` 0.4.2.3（2026-11-17）；Python ≥3.11；Apache-2.0；Beta；3.8k stars | PyPI JSON、README、wheel |
| ReMe 检索 | BM25 + 向量 RRF（`_RRF_K=60`）；wikilink 扩展；chunk 带行号 | `reme/steps/index/search.py` |
| ReMe 接入格式 | md/txt/json/jsonl/csv/yaml/html（无 PDF/docx） | ReMe 文档/源码 |
| 依赖实测 | `uv 0.11.28` + CPython 3.12.13 + 本地镜像；三条真实解析结论见 §4.4 | 本次实测 |
| AgentScope 结构化输出 | `reply(..., structured_schema=PydanticModel)` → `Msg.structured_output` | wheel 源码 |
| AgentScope 模型 | `OpenAIChatModel` + `OpenAICredential(base_url=...)`（OpenAI 兼容） | wheel 源码 |
| LangGraph 能力 | 条件边/循环/子图/`Send`/`interrupt`/`PostgresSaver` | LangGraph 官方文档 |
| 项目基线 | branch `dev` @ `65b127752`（PR #28 合并后） | `git log` |
| 目录/import 统计（r2） | 56 个待迁移 py 文件 / 9,889 行；20 条非测试 import（另有 3 条 `graph_rag` 不变）；56 个测试文件 / 153 条 import；13 个随迁 README（另 1 个在 `graph_rag` 不迁） | 2026-11-17 工作区 `find`/`grep` 实测 |

> 注：AgentScope 与 ReMe 均无“与 LangGraph 集成”的官方示例（两仓库全文检索 `langgraph` 命中 0），节点适配器需要自研；这是工程量的一部分，不是配置工作。

### 9.2 附录 B — 外层冻结契约（摘要）

完整调研覆盖 37 条接口级细节，下表按组归纳；迁移中必须保持：

| 组 | 冻结项 |
|---|---|
| HTTP | `POST /pipeline/run`（202 + `status: queued/accepted/cached`）、`GET /runs/{id}/status`（四相位齐全、`error` 形状）、`GET /runs`、`POST /acquire`、`status_url` 格式、owner 404 语义、限流 |
| 模型 | `PipelineRunRequest`、`PipelineRunResponse`、`PipelinePhasesResponse`、`PhaseStatusResponse`（含 `nodes/count` 可空）、`PhaseNodeResponse`、`AcquireRequest/Response` |
| 状态 | `PipelineGraphState` 字段名/类型（只可加可选字段）；`PipelineStatus`/`PhaseStatus`/`SkipPhase4Reason` 取值；转移守卫语义；`PhaseError` 分类 |
| 外层类 | `PipelineRunner` 方法集、`SingleJobDispatcher.start/stop`、`JobQueueRepository`、`DocumentProcessingCacheService`、`PipelineRunSummaryRow`、`get/set_pipeline_runner`、`get/set_job_queue` |
| 持久化 | `pipeline_run_states`（含活动 run 部分唯一索引）、`pipeline_jobs`、`document_processing_cache`、`source_documents` 正文列；`state_json` 的 `_migrate_legacy_state_json` 启发式（按 `phase_4_status` 存在性） |
| 行为 | 阶段入口先 RUNNING；失败/取消写 FAILED 且保留相位；重试 3 次/30s/60s；并发 2；重跑清理范围；心跳/孤儿回收；缓存键（content_hash） |
| 产物 | `phase_2/*`、`phase_3/*.json(l)`、`extraction_result.json`、`original.json`、`translated.json` 的路径与结构 |

### 9.3 附录 C — 领域代码规模（迁移范围参考）

| 模块 | 文件数 | 行数 | 是否在生产 pipeline 路径 | 目标层（r2） |
|---|---|---|---|---|
| `src/agents/`（编排/适配器/状态/队列） | 14 | 3,514 | 是（外层实现占多数） | 编排/适配器 → `graph/`；队列/状态/runner 等留 `agents/` |
| `src/core/source_fact_chain/` | 9 | 1,858 | 是（Phase 3） | `skills/fact_chain` + `tools/fact_chain` |
| `src/core/ingest_and_digitize_data/` | 20 | 2,255 | 是（Phase 1/2） | `tools/acquisition` + `tools/parsing` |
| `src/core/standardize_entities_and_align_knowledge/` | 27 | 5,776 | 是（Phase 4） | 实现 → `tools/terminology`；共享三件套 → `terminology_shared` |
| `src/core/graph_rag/` | 9 | 1,226 | 可选（Phase 5/上下文） | **不迁** |
| `src/core/evidence_extraction/` | 55 | 12,214 | **否**（休眠，595 测试维护） | **不迁** |
| `src/core/cross_lingual_translation/` | — | 5,328 | **否**（仅 e2e 脚本使用） | **不迁** |

**实际需要 agent 化的推理核心 ≈ 1,858 行（Phase 3）+ 适配层**；其余是确定性服务/外部 SDK 适配。这是“工作量可控”的关键依据。目录迁移只移动上述 56 个文件（9 + 20 + 27）/ 9,889 行，不改业务逻辑。

### 9.4 附录 D — 复现与验证命令

```bash
# 1) 依赖解析（本次实测，不写仓库 lock）
uv pip compile req.txt --python-version 3.12 \
  --index-url http://127.0.0.1:3141/root/pypi/+simple/

# 2) 现有基线测试 + import 边界
cd backend && uv run pytest tests/agents tests/api/test_pipeline_api.py \
  tests/core/source_fact_chain tests/pipeline/test_import_boundaries.py -q

# 3) 迁移后的覆盖率（路径随目录调整；阶段 2 起）
cd backend && uv run pytest tests/core/source_fact_chain tests/agents \
  --cov=src.pipeline.tools.fact_chain --cov=src.pipeline.graph --cov-branch -q

# 4) 影子对照（阶段 2 落地后提供，命令名待实现时确定）
# uv run python -m <shadow-diff-module> --run-id <id> --phase 3
```

### 9.5 附录 E — 术语

| 术语 | 含义 |
|---|---|
| 有界智能体（bounded agent） | 工具白名单 + 结构化输出 + 确定性校验器守门，自主度受限的 agent |
| Shadow / 影子运行 | 同一输入并行跑新旧两条路径，只读比较、不切流 |
| 阶段（phase）/ 步骤（stage） | 外层四阶段 vs 阶段内部步骤（extract/verify/translate） |
| 权威存储 | 需要事务/约束/审计的数据存储（PG 术语库、证据表、JSONL） |
| 记忆层 | 可重建、非权威、用于召回与上下文的知识（ReMe workspace） |
| `graph/` / `skills/` / `tools/` / `mcp/` | r2 目标目录：LangGraph 拓扑 / AgentScope 子智能体 / 确定性工具 / 外部服务协议适配 |
| shim | 旧路径的 `re-export` 模块，过渡期保持外层 import 不变，一个发布周期后删除 |
| 外层冻结项 | HTTP/DB/队列/状态/产物契约；目录迁移中行为与签名不变的模块 |
