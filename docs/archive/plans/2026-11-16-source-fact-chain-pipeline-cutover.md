# Pipeline Phase 3 切换为原文事实链

**Status:** completed
**Created:** 2026-11-16
**Completed:** 2026-11-16
**PR:** not created

## 目标

把产品 Phase 3 从「整篇翻译 + 原文/译文双轨抽取」切换为当前主实验路线：

```text
原文分窗 → 原文事实抽取 → 原文证据核验 → 事实英译 → 双语展示
```

## 实现

- 新增 `backend/src/core/source_fact_chain/`：
  - `windowing.py`：全覆盖、可重叠、不静默截断的分窗；
  - `contracts.py`：`SourceDocument`、`SourceFact`、`Verification`、`EnglishView`、
    `BilingualRow`、`ChainConfig`、`ChainRun`；
  - `core.py`：引句定位（NFKC/空白容错）、原子性/主体/字段/span 校验、稳定事实 ID、
    provider 回复 reconciliation；
  - `prompts.py`：版本化抽取/核验/翻译提示词；
  - `providers.py`：默认 provider（抽取/翻译用 fast 层，核验用 reasoning 层）；
  - `runner.py`：extract → verify → translate 三阶段编排与逐窗进度；
  - `projection.py`：只把 `supported` 事实投影为 Phase 4 双轨证据（原文值 + 英文呈现）；
  - `api.py`：`SourceFactChainService` 门面与产物写出。
- `Phase3Adapter`：调用事实链；输出 `chain_run.json`、`facts.jsonl`、
  `verifications.jsonl`、`english.jsonl`、`bilingual.jsonl`、`extraction_result.json`；
  零支持事实时 `skip_phase_4_reason=NOT_RELEVANT`；重试按 source hash 复用已持久化运行。
- `TranslationExtractionOutput` 增加 `bilingual_rows_path`/`source_facts_path`/
  `chain_run_path`；`wiring.py` 用 `SourceFactChainService` 替换
  `TranslationService` + `EvidenceExtractionService`。
- Phase 3 重跑时清除旧整篇译文文本/块，避免事实链文档残留旧双语展示载荷。
- 双语展示：`search_service` 的 trace 去重与配对改为按事实身份（`source.span_id` 的
  `<track>-<fact_id>`），同一字段多条事实不再互相覆盖；`BilingualEvidenceView` 在无整篇
  译文时新增事实级原文/英文对照面板（en/zh i18n）。

## 不变量

- 事实集只有一套；英文由事实翻译得到，不回流作为抽取证据。
- 只有 `supported` 事实进入 Phase 4；其余标签保留在 JSONL 供审计。
- 基因/变异/年龄字段逐字保留；表型/遗传方式才翻译；英文原文 passthrough。
- 引句必须唯一定位并与 span 逐字符一致；`unknown` 主体不得携带 ID。

## 验证

| 套件 | 结果 |
|---|---|
| `tests/core/source_fact_chain` | 12 passed |
| `tests/agents/test_phase_3_adapter.py` | 3 passed |
| `tests/agents` | 209 passed |
| `tests/api/test_wiring_config.py` | 3 passed |
| `tests/api/test_pipeline_api.py`（单独运行） | 18 passed |
| `tests/core/visualize_evidence_with_expert_in_loop/test_search_service.py` | 25 passed |
| Frontend `bun run type-check` / `tests/evidence-db` | passed / 44 passed |
| Ruff（新增/修改文件） | all checks passed |

## 限制与后续

- 前端证据详情仍以双轨 `traces` 展示逐字段原文/英文；整篇译文区块在事实链路线下为空，
  这是路线设计要求，不是缺失。
- 与 `tests/agents` 同进程运行 `tests/api/test_pipeline_api.py` 时存在既有全局 mock
  隔离问题；两套测试分开运行均通过，本批未修改该测试基础设施。
- 事实分组按观测到的基因/变异组合生成，单一文档多变异时非变异事实归入首个组合；
  如需更细的主体/病例分组，另立设计任务。
