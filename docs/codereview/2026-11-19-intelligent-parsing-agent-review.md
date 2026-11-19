# 智能解析 Agent 评审（ACMG_Lingua）

**Status:** review only — 本次不改业务代码
**Date:** 2026-11-19
**Reviewed revision:** `1762c58a7`（`dev`，含 `refactor(core)` 分层重构）
**Scope:** Phase 1 acquisition、Phase 2 MinerU parsing、Phase 3 source-fact chain / AgentScope extract，以及 LangGraph 对应节点
**Method:** 静态阅读 + 3 个只读探针；未调用真实 MinerU/LLM，未使用生产数据

---

## 1. 结论摘要

当前实现的主干是清晰的：**LangGraph 定拓扑，Phase 3 用“分窗 → 原文抽取 → 原文核验 → 事实英译”的单链，AgentScope 只接管 extract，校验与落盘仍由确定性代码完成**。这个方向是对的，不建议把每个节点改成自主 agent。

但“智能”部分目前有三类会直接影响证据正确性的问题：

1. **部分窗口抽取失败会被当成成功**：运行仍标记 COMPLETED，失败窗口不重试，且结果会被持久化复用。
2. **AgentScope 的 `SkillError` 被分类为永久失败**：新运行时的瞬时故障没有重试，反而比 legacy 更脆弱。
3. **没有章节门控**：参考文献、致谢、补充材料等全文进入抽取；核验只校验“窗口内可定位”，会把引用文献中的描述当成该病例的证据。

另外，成本/超时/CI 覆盖也存在明显缺口。建议先修 3 个 P0（约 3–4 人日），再补 P1 的失败语义与可观测性，最后再评估 ReMe 接入。

---

## 2. 当前实际执行路径

```text
POST /pipeline
  └─ PipelineRunner（后台任务，semaphore=2）
       └─ PipelineOrchestrator（LangGraph，4 个 phase 节点）
            ├─ phase_1  Phase1Adapter
            │    └─ DocumentAcquisitionService
            │         ├─ local  upload → 临时文件
            │         └─ online → lit-acquisition SDK（可能返回 pre_parsed_markdown）
            ├─ phase_2  Phase2Adapter
            │    └─ ParseDocumentService.parse_local_files_and_save
            │         └─ MinerURemoteParser（batch 上传 → 轮询 → 下载 zip → content_list）
            ├─ phase_3  Phase3Adapter
            │    └─ SourceFactChainService
            │         └─ ChainRunner：extract → verify → translate（逐窗口、同步）
            │              └─ Provider
            │                   ├─ legacy: LangChainChainProvider（默认）
            │                   └─ shadow/agentscope: StageRouterProvider
            │                        └─ extract: ExtractSkill（AgentScope 有界 agent）
            │                           verify/translate: 仍走 legacy
            └─ phase_4  Phase4Adapter
                 └─ EntityStandardizationService
```

关键事实：

- **默认运行时是 legacy**：`PipelineConfig.agent_runtime = "legacy"`（`backend/src/core/config.py:221`），`SourceFactChainService._build_provider` 只在 `shadow`/`agentscope` 时加载 AgentScope（`backend/src/pipeline/skills/fact_chain/service.py:47-57`）。因此线上默认并没有跑 AgentScope。
- **AgentScope 只覆盖 extract**，verify/translate 仍是 legacy（`service.py:47-57`、`extract.py:196-235`）。这是有意的“有界子智能体”，不是端到端自主解析。
- Phase 2 的产品路径是 **MinerU remote batch**（`phase_2.py:84` → `orchestrator.py:120-132` → `remote/parser.py:242-295`），不是 `DocumentParseOrchestrator.parse` 的 remote-first/local fallback（`orchestrator.py:36-118`）。
- LangGraph 只有 4 个 phase 节点，没有窗口子图、`Send` fan-out、checkpointer 或节点级进度（`topology.py:245-285`；阶段 2 记录 §7 也确认未做）。

### 2.1 已休眠 / 未接线的旧实现

| 模块 | 现状 | 证据 |
|---|---|---|
| `core/agents/extraction`（旧 LLM 证据抽取，约 12.2k 行） | 不在产品图里；仅 `scripts/e2e_extract_evidence.py` 调用。contracts/catalog/grouping 仍被 Phase 3/4 复用 | `scripts/e2e_extract_evidence.py:28,216-220`；`phase_4.py:27` |
| `core/agents/translation`（旧整篇翻译，约 5.3k 行） | Phase 3 只用 `detect_language`；`translated.json` 为空是切流设计 | `phase_3.py:36,180-194` |
| `DocumentParseOrchestrator.parse` + `MinerULocalParser` | 产品 Phase 2 不走；local parser 仅 chat 上传和 fallback 用 | `phase_2.py:84`；`api/v1/chat.py:249` |
| `core/adapters/mcp`（ReMe 适配层） | 只有 `__init__.py` 占位，没有 client / 协议 / 超时语义 | `backend/src/core/adapters/mcp/__init__.py` |
| `docs/` 中的 `src/pipeline/tools/fact_chain`、`core/source_fact_chain` 路径 | 已被 `core/shared/tools/fact_chain` 取代，文档未同步 | `docs/active/2026-11-18-pipeline-stage-2-agentscope-runtime.md` §2 |

---

## 3. 发现与建议（按优先级）

### P0 — 必须做（正确性/临床证据安全）

#### P0-1 部分窗口抽取失败被静默吞掉，且失败结果会被复用

**证据**
- 逐窗口执行阶段，失败只写 `StageProgress`，不聚合、不抛出：`backend/src/pipeline/skills/fact_chain/runner.py:97-112`。
- extract 失败只返回 `StageOutcome.FAILURE`：`runner.py:160-161`；verify 失败 `runner.py:228-231`；translate 失败 `runner.py:306-309`。
- Phase 3 只看 `supported == 0`：为 0 时标 `NOT_RELEVANT`，否则清空 skip 并标 COMPLETED：`phase_3.py:196-202`。
- 复用只拒绝 `facts == 0`，不拒绝“部分窗口失败”：`service.py:98-116`。

**只读探针（本次实跑）**：2 个窗口，第 1 个窗口 provider 超时，第 2 个成功：

```text
facts: 1
PROGRESS w0001 extract failure provider or schema failure after retries
reuse_blocker: None        # 同一 source/config 下仍可复用
```

**影响**
- 文档缺一段证据，但 pipeline 显示 COMPLETED，Phase 4 继续标准化；
- 重跑不会重新调用失败窗口，因为 `chain_run.json` 被复用；
- 所有窗口都失败时，`facts=0` → `NOT_RELEVANT`，把“抽取事故”误标成“文档不相关”。

**最小改法**
1. `ChainRun` 增加 `failed_stage_count` 或 `has_failures`（从 `stage_progress` 派生即可）；
2. Phase 3 在写 `phase_3_output` 前检查：存在 `FAILURE` 时抛 `RetryablePhaseError`（严格模式），或写入 `PARTIAL` 并禁止 Phase 4 进入；
3. `reuse_blocker` 拒绝含失败阶段的 run；
4. 补测试：一个窗口失败、一个成功，断言 phase 不完成且不复用。

**成本**：0.5–1 人日。**必须做**；这是本次最高优先级缺陷。

#### P0-2 AgentScope 的 `SkillError` 被当作永久失败，没有重试

**证据**
- `ExtractSkill` 把 agent/schema 异常统一抛成 `SkillError`，默认 `RETRYABLE`：`extract.py:123-128`。
- runner 的重试循环只捕获 `ProviderError`：`runner.py:406-411`。
- Phase 3 的可重试元组只含 `ProviderError`：`phase_3.py:42`。
- 未知异常在 `classify_phase_error` 中落到 `PermanentPhaseError`：`backend/src/agents/contracts.py:336-339`。

**只读探针**：

```text
ProviderError          -> RETRYABLE
SkillError(retryable)  -> PERMANENT
SkillError(permanent)  -> PERMANENT
```

**影响**：一旦启用 `PIPELINE_AGENT_RUNTIME=agentscope`，模型超时、结构化输出校验失败等瞬时问题会直接让 Phase 3 永久失败，没有 legacy 的 2 次重试。新运行时反而更脆弱。

**最小改法**
1. runner 的 `_call_json` 捕获 `SkillError`，按其 `kind` 决定重试或失败；
2. 或在 `StageRouterProvider` 中把 `SkillError` 包装成 `ProviderError`（保留 permanent 语义）；
3. Phase 3 的 retryable 元组加入 `SkillError`；
4. 补测试：agentscope 模式下第一次 `SkillError(RETRYABLE)`、第二次成功。

**成本**：0.5 人日。**必须做**；这是启用 AgentScope 前的门槛。

#### P0-3 没有章节门控，参考文献/致谢等全文进入抽取

**证据**
- Phase 3 直接拼接 `metadata.pages` 的全部 markdown：`phase_3.py:108-116`；没有 section/block 过滤。
- 旧抽取链本来有非证据章节过滤（references、acknowledgements、supplementary 等），但只在休眠的 `extraction` 路径里：`backend/src/core/agents/extraction/infrastructure/document_parsing.py:143-205`（`_filter_evidence_blocks` / `_filter_evidence_text`）。
- extract prompt 没有“排除参考文献/不得抽取他文描述”的约束：`prompts.py:17-25`。
- verify 只校验“该窗口内可定位”，引用文献中的句子同样会被标 `supported`。

**影响**：参考文献、讨论中引用的其他病例、补充材料里的变异/表型可能进入 Phase 4，变成这篇文档的临床证据；target guard 只按基因过滤，挡不住同一基因的错误来源。这是证据归属问题，不只是解析质量问题。

**最小改法**
1. 在构造 `SourceDocument` 前复用旧链的 section/block 过滤（先按 block type + heading 过滤，再拼接文本）；
2. 过滤后重新计算 `page_ranges`，并在 `ChainRun` 记录 `filtered_sections` 供审计；
3. prompt 增加一句负向约束：只抽取本文报告的对象，不抽取参考文献/他文转述；
4. 补测试：正文 + References 各放一条同基因事实，断言只保留正文。

**成本**：1.5–2 人日（主要是偏移和页映射）。**必须做**；如果研究路线确实要求“全文事实”，至少也要默认排除 references 并保留 section 元数据。

### P1 — 应该做（稳定性/成本/可维护性）

#### P1-1 MinerU API 错误全部按永久失败处理

**证据**：所有 transport/API 错误都被包成 `MinerUAPIError`（`remote/parser.py:185-186,220-221,309-310,334-335`）；Phase 2 用 `classify_phase_error` 分类（`phase_2.py:112-113`），但可重试元组不含 `MinerUAPIError`（`contracts.py:270-301`），最终是 `PermanentPhaseError`。

**影响**：MinerU 的 429/5xx/短暂网络错误会直接让 Phase 2 失败，外层 2 次重试不会发生。

**最小改法**：区分 HTTP 状态/错误类型；4xx（参数、页数限制）永久，429/5xx/transport 可重试；或让 `MinerUAPIError` 带 `retryable` 标志。补 429、500 两个用例。**成本**：0.5 人日。

#### P1-2 重试没有退避/限流

**证据**：`runner.py:398-418` 在 `ProviderError` 后直接 `continue`，没有 sleep、jitter 或 `Retry-After`；`max_attempts` 默认 2。

**影响**：限流时连续打两次，容易把短时限流放大成整窗失败；与 P0-1 叠加就是静默缺证据。

**最小改法**：指数退避 + jitter（例如 2s/8s），尊重 `Retry-After`，并在 `ChainEvent` 记录等待时间。**成本**：0.5 人日。

#### P1-3 成本/预算没有接线

**证据**：`SourceFactChainService` 的 `max_provider_calls` 默认 0（`service.py:70`；`ChainConfig` 注释明确 0 表示不限制，`contracts.py:274-276`）；wiring 没有传该参数（`api/wiring.py:223`）；`ChainRun` 只记 `provider_calls`，没有 token；`LangChainChainProvider` 只取文本，不读 usage（`llm.py:57-72`）。

**影响**：长文档窗口数线性增长，无法在配置层设上限；没有 token/费用数据，无法做成本回归。

**最小改法**：把 `max_provider_calls`、`max_tokens_per_run` 接进 `PipelineConfig`；从 provider 响应读取 usage 并累计到 `ChainRun` / Phase 3 summary；超预算时明确失败而不是静默截断。**成本**：1.5–2 人日。

#### P1-4 没有阶段级超时

**证据**：MinerU 轮询固定 `150 × 2s`（`remote/parser.py:328-354`，配置 `core/config.py:198-199`）；LLM 超时默认 60s（`core/config.py:65-75`）；外层没有 `asyncio.wait_for`。`asyncio.to_thread` 中的同步调用被卡住时会一直占住线程和 pipeline semaphore。

**影响**：单个坏文档可能长期占用 2 个并发槽之一，表现为“pipeline 卡住”，且没有阶段级超时错误。

**最小改法**：为 Phase 2/3 增加整体 deadline（配置化），在 `_execute_phase` 外层 `asyncio.wait_for`；每个窗口也设 deadline；超时映射为可重试错误。**成本**：1 人日。

#### P1-5 CI 不跑 parsing/acquisition 测试

**证据**：CI 的确定性套件只跑 `tests/core/source_fact_chain`、`tests/agents`、`tests/pipeline`、`test_wiring_config.py` 和 review search（`.github/workflows/ci.yml:138-153`）；`tests/core/agents/parsing`（约 2,969 行）和 acquisition 测试不在其中。mypy 也只覆盖 fact_chain/phase_3（`ci.yml:90-101`）。

**影响**：Phase 1/2 的解析回归不会被 PR 门禁发现；本次评审中 Phase 2 的失败语义问题就没有测试兜底。

**最小改法**：新增一个 parsing 单元测试 job（mock `rust_io.net`，不依赖真实 MinerU），至少覆盖 remote parser 的 poll/zip/content_list、local parser 的 page 构建、Phase 2 adapter 的异常分类。**成本**：1 人日。

#### P1-6 表格保真不足，且表格来源在 Phase 3 丢失

**证据**：
- `html_table_to_markdown` 不转义单元格里的 `|`，一行会被拆成多列；`TableParser` 不处理 `rowspan`/`colspan`（`converters.py:8-27`、`parsers.py:9-31`）。
- Phase 3 投影把所有证据的 `block_type` 固定为 `text`、`context_type="case_report"`（`projection.py:190-194`），表格里的变异/表型无法回溯到表格。

**只读探针**：

```text
| Gene | Variant |
| --- | --- |
| BRCA1 | c.1A>G | pathogenic |     # 单元格里的 | 把列拆坏

rowspan 表：第二行只剩 “ovarian cancer | ”，基因列为空
```

**影响**：表格中的变异/表型可能错列或错行；Phase 4 无法区分正文与表格证据。

**最小改法**：markdown 转换时转义 `|`；结构化 `tables` 保留 `rowspan/colspan` 或至少补全合并单元格；投影时按 block/page 记录 `block_type=table` 与表索引。**成本**：1.5–2 人日。

#### P1-7 同一基因多个变异时，表型事实只归到第一个变异

**证据**：`_group_plan` 对非变异事实取该基因的 `variants[0]`（`projection.py:149`）；`_context_gene` 只按“最近的前一个基因”归属，没有变异上下文。

**影响**：复合杂合/多变异病例中，第二个变异链没有表型证据，Phase 4 的基因-变异-表型配对不完整；这是当前 `EvidenceChain` 语义下的系统性偏差。

**最小改法**：非变异事实按“最近的变异”或基因级 group 归属；如果 Phase 4 需要变异级 chain，至少给同一基因的所有变异复制共享表型并标注 `shared`。补复合杂合用例。**成本**：1–2 人日（需与 Phase 4 语义确认）。

#### P1-8 节点级进度没有暴露到 API

**证据**：API 已有 `PhaseNodeResponse`/`nodes` 字段（`api/v1/contracts.py:97-104`），但 Phase 3 summary 只有 windows/facts/provider_calls（`phase_3.py:218-228`），没有把 `ChainRun.stage_progress` 映射成 nodes；事件没有时间戳，也没有 trace id。

**影响**：出问题时只能翻 `chain_run.json` 或 loguru 日志，无法从状态接口看出“第几个窗口、哪个 stage 失败”。

**最小改法**：把 `stage_progress` 聚合为每个 stage 的 `nodes`（status/progress/失败数/耗时），在 Phase 3 summary 增加 `failed_stages`、`latency_ms`；日志加 `run_id/window_id/stage` 结构化字段。**成本**：1.5 人日。

### P2 — 锦上添花（先记录，不阻塞）

| # | 问题 | 证据 | 建议 | 成本 |
|---|---|---|---|---|
| P2-1 | ReMe 只有占位，没有 client/契约 | `core/adapters/mcp/__init__.py`；迁移方案 D4 | 先定只读 MCP 契约（search/fetch、超时、熔断、降级），作为 sidecar；不要进 Phase 3 关键路径，也不要用 ReMe 替代术语库/Neo4j 权威存储 | 2–3 人日设计+spike |
| P2-2 | pre-parsed markdown 丢失页结构 | `phase_2.py:143-157` 固定 `total_pages=1`、`content_blocks=[]` | 从 acquisition 保留页映射，或按分页标记切分 | 0.5 人日 |
| P2-3 | 本地上传临时文件不清理 | `local_upload/service.py:63-77`；`phase_1.py:97` 传 `upload_dir=None` | 在 run 结束/失败时清理，或统一落到 run 目录 | 0.5 人日 |
| P2-4 | zip 下载无大小上限，整包读入内存 | `remote/parser.py:356-369` | 流式下载 + 最大字节数；校验 content-type | 0.5 人日 |
| P2-5 | 置信度硬编码 0.9 | `projection.py:196` | 按 verification label/uncertain 映射，或暂时置空并标注 | 0.5 人日 |
| P2-6 | 窗口可能从单词/句子中间切开 | `windowing.py:36-47` 只找换行 | 优先在句末/段落边界切，overlap 内回退 | 0.5 人日 |
| P2-7 | 文档与代码路径漂移；休眠代码约 17.5k 行 | `docs/active/2026-11-18-...md`；extraction 12.2k + translation 5.3k | 更新迁移文档；休眠模块单独立项删除/归档，不要和当前修复混做 | 0.5 人日文档 |

---

## 4. 高危缺陷清单（本次只记录，不改代码）

1. **部分窗口失败被 COMPLETED + 复用**（P0-1）：可导致临床证据缺失且不可恢复。
2. **AgentScope `SkillError` 永久失败**（P0-2）：启用新运行时后瞬时故障无重试。
3. **参考文献进入抽取**（P0-3）：可能把他文描述当作本文证据。
4. **MinerU 429/5xx 永久失败**（P1-1）：外部服务短时抖动导致整阶段失败。
5. **无阶段级超时**（P1-4）：坏文档可长期占用并发槽。

---

## 5. 建议实施顺序

1. **P0-1 + P0-2**（约 1–1.5 人日）：先把“失败必须可见、可重试”补上；
2. **P0-3**（1.5–2 人日）：章节门控 + 负向 prompt + 测试；
3. **P1-1 / P1-2 / P1-4**（约 2 人日）：统一外部调用失败语义；
4. **P1-3 + P1-8**（约 3 人日）：预算、token、节点进度；
5. **P1-5 / P1-6 / P1-7**（约 3.5–5 人日）：CI 门禁、表格、分组；
6. P2 按产品节奏处理；ReMe 接入前先完成 P0。

**不建议做的事**
- 不要为了“agent 化”把 verify/translate 也交给自由 agent；现有确定性校验是资产。
- 不要在 P0 未修复前扩大 shadow 流量；shadow 差异会被同样的失败语义污染。
- 不要把 ReMe 放进 Phase 3 同步调用链；先做只读、可超时、可降级的旁路。

---

## 6. 验证与限制

- 已读 revision `1762c58a7`，工作区干净；本次未修改业务代码。
- `pytest tests/core/source_fact_chain -q`：**21 passed**。
- 只读探针：
  - 部分窗口失败：`facts=1`、`w0001 extract failure`、`reuse_blocker=None`；
  - `SkillError(RETRYABLE)` 经 `classify_phase_error(3, ...)` 得到 `PERMANENT`；
  - `html_table_to_markdown` 在单元格含 `|` / `rowspan` 时列错位。
- **未执行**：真实 MinerU/LLM 调用、生产数据回放、AgentScope 测试（本地 `.venv` 未安装 `agentscope`；CI 的 `ci` 依赖组会安装）。因此本文对 AgentScope 运行时的结论来自代码路径和错误分类探针，不是端到端运行结果。
- 未覆盖：Phase 4 标准化内部质量、前端展示、数据库迁移；这些不在本次“解析 agent”范围内。
