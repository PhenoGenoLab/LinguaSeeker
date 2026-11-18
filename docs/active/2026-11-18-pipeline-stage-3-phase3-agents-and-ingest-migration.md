# Pipeline 阶段 3 迁移实施记录：Phase 3 全链路 agent 化 + ingest 目录迁移

> 对应方案：[`docs/planned/2026-11-17-pipeline-agentscope-reme-migration.md`](../planned/2026-11-17-pipeline-agentscope-reme-migration.md)（§3.2 目录、§5 阶段 3）
>
> **Status:** in-progress
> **Date:** 2026-11-18
> **Branch:** `impl-stage-3-be70dc50bda0`（基于阶段 2 `ca8ef9d`，PR #33）
> 边界：只改领域层。HTTP/DI、状态 JSON、DB/队列语义、磁盘产物路径不变；ReMe 仍未接入。

## 1. 本次范围

| 方案阶段 3 产出 | 状态 | 说明 |
|---|---|---|
| `document_acquisition` → `pipeline/tools/acquisition` | 完成 | 7 个文件整体移动；旧路径 7 个 re-export shim |
| `parse_document` → `pipeline/tools/parsing` | 完成 | 13 个文件整体移动；旧路径 13 个 re-export shim |
| `VerifyAgent`（reasoning 模型，只输出 verdict 标签） | 完成 | `skills/fact_chain/verify.py`；schema 用 `Literal` 锁死 `supported/unsupported/uncertain` |
| `TranslateAgent`（仅 PRESENTED 字段） | 完成 | `skills/fact_chain/translate.py`；EN 源文档仍由 runner 直接 passthrough，零调用 |
| 统一错误映射与重试归属 | 完成 | `StageRouterProvider` 把 `SkillError` 统一转成 `ProviderError`，runner 的 `max_attempts`/budget/事件语义不变；executor 仍是唯一阶段重试方 |
| 审计事件对齐 | 完成（复用） | runner 的 `events/rejections` 未改，agent 只替换 provider 调用 |
| `AcquisitionAgent` / `ParseAgent` 薄封装 | **未做（有意）** | 两个阶段没有 LLM 决策，薄封装只是对现有服务做一层无行为转发；按 `AGENTS.md` §20.2 不引入一次性抽象。目录已迁到 `tools/`，后续若需要统一 skill 接口再加 |
| 按节点开关（`phase3.extract/verify/translate`） | **未做（有意）** | 仍由单一 `pipeline.agent_runtime` 控制；三个 stage 均已接入，回滚粒度足够，避免过度配置 |

## 2. 结构调整

```text
backend/src/pipeline/
├── skills/fact_chain/
│   ├── agent_skill.py     # 新增：stage skill 公共执行器（payload→agent→结构化校验）
│   ├── extract.py         # 收敛为 ExtractSkill（窗口工具保留）
│   ├── verify.py          # 新增：VerifySkill（reasoning 档）
│   ├── translate.py       # 新增：TranslateSkill（fast 档）
│   ├── router.py          # StageRouterProvider（按 stage 路由；shadow diff）
│   └── prompts.py / runner.py / service.py
└── tools/
    ├── acquisition/       # 原 document_acquisition（7 files）
    └── parsing/           # 原 parse_document（13 files）
```

- 旧路径 `src/core/ingest_and_digitize_data/{document_acquisition,parse_document}` 每模块一个 shim（共 20 个），供冻结外层（`agents/contracts.py`、`api/v1/pipeline.py`、`api/v1/chat.py`）过渡；外层 import 已切到新路径，shim 只服务外部调用方。
- 迁移清单：`src/pipeline` 51 files / 5,901 lines；shim 34 个（graph 5 + fact_chain 9 + acquisition 7 + parsing 13）。

## 3. 路由与开关（与阶段 2 一致）

| 模式 | 行为 |
|---|---|
| `legacy`（默认） | 完全不 import agentscope；extract/verify/translate 全走旧 provider |
| `shadow` | 三个 stage 各双跑一次，返回旧结果，记录 `ShadowStats` 与逐条 diff |
| `agentscope` | 三个 stage 全走 AgentScope；skill 失败 → `ProviderError` → runner 重试/记录事件 |

Rollback：`PIPELINE_AGENT_RUNTIME=legacy` 立即回到阶段 2 前的调用路径，无数据迁移。

## 4. 验证

CI 等价环境（`uv export --frozen --only-group ci` + PyPI 安装）：

| 检查 | 命令 | 结果 |
|---|---|---|
| 确定性套件 + 覆盖率 | `pytest tests/core/source_fact_chain tests/agents tests/pipeline tests/api/test_wiring_config.py tests/core/.../test_search_service.py ...` | **294 passed**，覆盖率 **88.55%** |
| pipeline/acquire API | `pytest tests/api/test_pipeline_api.py tests/api/test_acquire_api.py -q` | **26 passed** |
| ingest 层 | `pytest tests/core/ingest_and_digitize_data --ignore=test_rust_io_facade.py --ignore=parse_document/test_mineru_parser.py` | **154 passed, 6 skipped** |
| Ruff | `ruff check` / `ruff format --check` | 通过 |
| Mypy | 20 source files | Success |
| 清单 | `scripts/pipeline_migration_inventory.py` | acquisition 7/7、parsing 13/13 全部为 shim，新路径文件数/行数与迁移前一致 |

未执行：`tests/core/ingest_and_digitize_data/test_rust_io_facade.py` 与 `parse_document/test_mineru_parser.py` 依赖本地 `rust_io` 扩展，本机与 CI 精简环境均未构建（迁移前同样无法运行）；真实模型影子对照仍需凭证与黄金文档。

## 5. 不变量

- `ChainRun`/`Verification`/`EnglishView` 契约与 JSONL 字段不变；
- verify 的 `missing_verdict`/`invalid_label`/`verify_call_failed` 生成逻辑不变（agent 仅替换 provider 返回）；
- translate 的 `PRESERVED/PASSTHROUGH/MISSING/FAILED` 语义不变，EN 文档保持零翻译调用；
- 阶段重试次数、预算 `max_provider_calls`、事件名与顺序不变；
- 采集/解析服务的公开 API 与磁盘产物路径不变（shim 指向同一对象）。

## 6. 后续

- 真实影子验收（三 stage 全链路 diff、成本/延迟阈值）与阶段 2 一致，待凭证环境。
- `graph/nodes.py`、`graph/progress.py`、Phase 3 窗口子图仍属阶段 1 未完成项。
- 阶段 4：`standardize_entities_and_align_knowledge` → `pipeline/tools/terminology`、`terminology_shared` 抽取、ReMe `mcp/reme` 客户端与记忆开关。
- 旧路径 shim 删除单独立项。
