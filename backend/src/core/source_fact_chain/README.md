# source_fact_chain — 原文事实链（Phase 3）

> 把解析后的原文按窗口切分，只从原文抽取事实，先核验再只翻译展示字段，最终产出
> 双语事实行和 Phase 4 可消费的双轨投影。全流程不再翻译整篇文档，也不再从译文
> 独立抽取第二套事实。

## Quick Start

```python
from src.core.source_fact_chain.api import SourceFactChainService
from src.core.config import get_config

service = SourceFactChainService(get_config())
document = service.build_document(
    document_id="doc-1",
    text=source_text,
    language="zh",
)
run = await service.run_async(document)
print(len(run.facts), len(run.bilingual_rows()))
service.write_outputs(run, "data/pipeline/run-1/phase_3/doc-1")
```

Phase 3 适配器已使用该服务；通常不需要直接调用。

## Architecture

```text
parsed document (Phase 2)
      │  chunk_document: 全覆盖窗口 + 重叠
      ▼
extract  ── 每个窗口一次调用：原文事实候选（不翻译）
      │      candidate_to_fact 校验：字段/原子性/极性/主体/引句定位
      ▼
verify   ── 每个有事实的窗口一次调用：supported / unsupported / uncertain
      │      失败或缺失 → unverified（不进入临床证据）
      ▼
translate── 仅 PRESENTED 字段；PRESERVED 逐字保留；英文原文走 passthrough
      │      EnglishView 只复制事实的极性与主体，不回写事实
      ▼
bilingual rows + dual-track projection (Phase 4)
```

事实 ID 只由源内容决定（document、source hash、字段、原值、极性、主体、span），
与窗口、模型、提示词和英文文本无关，因此重叠窗口命中同一 span 时自动合并。

## 分组与目标语义

- **按基因/变异分组**：`project_dual_result` 不再使用“首个基因 × 全部变异”。每个
  `A.gene_symbol` 事实建立自己的基因上下文，变异与其他事实归属到其 span 之前最近的
  基因；每个 `(gene, variant)` 生成独立 `group_id` 与 `EvidenceChain`。多基因文档因此
  不会把第二个基因的变异绑定到第一个基因。
- **目标守卫**：传入 `target_gene` 时，只有匹配目标基因的组进入 `evidence_chains`；
  非目标组的事实保留在 `evidence_items` 供审计，但状态标为
  `context_contamination`，不进入 Phase 4 候选生成。没有匹配组时文档
  `status=not_relevant`。不传目标时全部 `supported` 事实为 `found`。

## 重试复用

- `chain_run.json` 复用键 = `source_hash` + `ChainConfig`（窗口/模型/预算）+
  `PromptVersions`（抽取/核验/翻译/呈现提示词与呈现版本）。
- `facts=0` 的运行默认**不复用**：provider 瞬时返回合法空列表不应变成永久空证据。
- `Phase3Adapter.run(state, force_rebuild=True)` 可显式忽略已持久化运行并重新调用模型。
- 复用分支同样重写 `chain_run.json` 与全部 JSONL，修复“chain_run 之后、JSONL 之前
  崩溃”的不可恢复状态；`supported > 0` 时会清除遗留的 `skip_phase_4_reason`。

## Public API

### `SourceFactChainService`

| 方法 | 签名 | 说明 |
|------|------|------|
| `build_document` | `(*, document_id: str, text: str, language: str) -> SourceDocument` | 计算 SHA-256 并冻结原文 |
| `run` | `(document: SourceDocument) -> ChainRun` | 同步执行三阶段 |
| `run_async` | `async (document) -> ChainRun` | 在线程中执行，避免阻塞事件循环 |
| `write_outputs` | `(run: ChainRun, out_dir) -> ChainArtifacts` | 写 `chain_run.json`、facts/verifications/english/bilingual JSONL |
| `reuse_blocker` | `(run, *, source_hash) -> str \| None` | 返回不可复用原因（source/config/prompt/空运行）或 `None` |
| `prompt_versions` | `-> PromptVersions` | 当前抽取/核验/翻译/呈现版本，用于复用键 |
| `project_dual_result` | `(run, *, extraction_target, page_ranges, target_gene, target_disease, target_variant) -> DualEvidenceExtractionResult` | 生成 Phase 4 输入 |
| `supported_fact_count` | `(run) -> int` | 已核验通过的事实数 |

### `ChainRunner`

`ChainRunner(provider, config).run(document, manifest_hash=None)` 只连接阶段；
模型访问走 `Provider.invoke(stage, model_id, prompt, payload) -> str`。

### `project_dual_result`

- `original_result`：`supported` 事实的原文值；
- `translated_result`：同一批事实的英文呈现（preserved/passthrough/translated）；
- 双语视图因此仍按同一 `field_id`/`group_id` 对齐，但不产生第二套事实。

## Internal Design

- **窗口**：`windowing.chunk_document` 保证每个字符至少被一个窗口覆盖，窗口在换行
  处回退，重叠由 `window_overlap` 控制。
- **抽取校验**（`core.candidate_to_fact`）：字段必须在允许集合；值必须非空、原子
  （禁止分号列表，`&#59;` 同样视为分隔符）且出现在引句中；主体 `unknown` 不得带 ID；
  引句必须在窗口内且唯一定位；span 与引句必须逐字符（NFKC/空白不敏感）一致。
- **实体与空白归一化**：比较前统一解码 HTML 实体并做 NFKC/去空白。`&gt;` 等实体不再
  被误判为分号列表，`&gt;`/`>`/`&amp;` 三种写法都能定位；引句歧义按同一归一化形式
  计数，空白不同的同一句话不会被错误归属到第一个位置。
- **核验**：仅 `supported` 进入 Phase 4；`unsupported`/`uncertain`/`unverified`
  仍保留在 `facts.jsonl` 与 `bilingual.jsonl` 供审计，但不生成临床证据。
- **翻译**：`A.gene_symbol`、`A.variant_hgvs_c/p`、`B.age_of_onset` 逐字保留；
  `B.clinical_phenotypes`、`B.mode_of_inheritance_reported` 才送翻译。英文原文不
  调用翻译模型，直接 `passthrough`。
- **失败语义**：provider 失败按 `max_attempts` 重试；抽取失败该窗口零事实并记录
  `rejection`；核验失败全部标 `unverified`；翻译失败保留 `failed` 视图，不伪造英文。
- **预算**：`max_provider_calls > 0` 时超限抛 `BudgetExhausted`，不会静默截断。

## Extension Guide

- 新增字段：在 `contracts.FIELD_MODES` 增加 `field_id -> PRESERVED|PRESENTED`，并确认
  `backend/src/core/evidence_extraction/domain/catalog.py` 中存在该字段（Phase 4 需要）。
- 修改提示词：编辑 `prompts.py`；版本号由提示词哈希派生，会随核验/英文视图自动变化。
- 替换模型供应商：注入实现 `Provider` 协议的实例即可；默认实现使用 fast 层抽取/
  翻译、reasoning 层核验（AGENTS.md §23）。

## Testing

```bash
cd backend
uv run pytest tests/core/source_fact_chain tests/agents/test_phase_3_adapter.py
```

覆盖：窗口全覆盖、重叠去重、引句/原子性/主体/字段拒绝、实体引句与归一化歧义、
多基因/多变异分组、目标守卫、核验失败降级、英文 passthrough、哈希失配零调用、
Phase 4 双轨投影、适配器产物、空运行重建、配置/提示词版本失效、产物重生成与
`force_rebuild`。

CI 的 `backend-test` 作业通过 `[dependency-groups] ci` 安装最小依赖集，运行
`tests/core/source_fact_chain`、`tests/agents`、wiring 与 search-service 测试，
不下载 torch/NVIDIA wheel，也不构建 Rust 扩展。

## Dependencies

| 依赖 | 用途 |
|------|------|
| `pydantic` | 强类型契约 |
| `loguru` | 运行日志 |
| `langchain-core` / `langchain-openai`（默认 provider） | 模型调用 |
| `src.core.evidence_extraction.*` | Phase 4 证据契约、字段目录、分组规则 |
| `src.utils.llm_adapter` | 多 key LLM 客户端池 |
