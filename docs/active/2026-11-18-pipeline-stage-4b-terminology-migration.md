# Pipeline 阶段 4b 迁移实施记录：术语库迁移与 terminology_shared 抽取

> 对应方案：[`docs/planned/2026-11-17-pipeline-agentscope-reme-migration.md`](../planned/2026-11-17-pipeline-agentscope-reme-migration.md)（§3.2 目录映射、§5 阶段 4）
>
> **Status:** in-progress
> **Date:** 2026-11-18
> **Branch:** `impl-stage-4b-terminology`（基于阶段 4a `3645991`，PR #35）
> 边界：只改领域层包布局与 import；术语库表结构、事务边界、匹配语义与 ACMG 投影不变。

## 1. 本次范围

| 方案阶段 4 产出 | 状态 | 说明 |
|---|---|---|
| 共享三件套抽取到 `src/core/terminology_shared/` | 完成 | `contracts.py`、`hgvs_normalizer.py`、`context_pack/` |
| `normalizers.py` + `amino_acids.py` 一并下沉 | 完成（扩展） | `context_pack` 依赖 `collapse_spaces`，`hgvs_normalizer` 依赖 `AA3_TO_1`；不下沉会形成 shared → pipeline 反向依赖 |
| 其余实现迁移到 `src/pipeline/tools/terminology/` | 完成 | 27 files / 5,788 行（含 `precise_match`、`similarity_match`、`db_ready_gate`） |
| 旧路径 shim | 完成 | 27 个模块全部保留 re-export shim |
| 更新 `graph_rag` / 休眠 `evidence_extraction` / `wiring` / `phase_4` import | 完成 | 外部消费只指向 `terminology_shared` 或新 tools 路径 |
| `StandardizeAgent` 薄封装 | **未做（有意）** | Phase 4 是确定性匹配 + DB 事务，无 LLM 决策；按 `AGENTS.md` §20.2 不做无行为转发层 |
| ReMe `auto_resource` 接入 Phase 2 产物、召回评测 | **未做** | 依赖 ReMe 服务部署；已记录在 4a §6 |

## 2. 分层结果

```text
src/core/terminology_shared/          # 中立共享层（graph_rag / evidence_extraction 也依赖）
├── contracts.py
├── hgvs_normalizer.py
├── normalizers.py
├── amino_acids.py                    # 新增：AA3_TO_1（原在 importers）
└── context_pack/{__init__,contracts,core}.py

src/pipeline/tools/terminology/       # pipeline 领域能力
├── api.py / core.py / matchers.py / repositories.py / importers.py ...
├── acmg_projection.py / adapters.py / cross_lingual_disease.py / variant_id.py
├── db_ready_gate/
├── precise_match/
└── similarity_match/
```

边界测试新增：`src/core/terminology_shared` 不得 import `src.pipeline`；`src/pipeline` 不得 import 旧术语路径。旧路径仅保留 shim。

## 3. 不变量

- `EntityStandardizationService` 公开方法、`DualResultAdapter`、`AcmgReadyProjector` 行为不变；
- PG 表名、事务边界、匹配阈值与排序不变；
- `context_pack` 的函数签名与 JSON 输入输出不变；
- 旧路径 `from src.core.standardize_entities_and_align_knowledge...` 仍可用（shim 指向同一对象）。

## 4. 验证

CI 等价环境（`uv export --frozen --only-group ci` + PyPI 安装）：

| 检查 | 命令 | 结果 |
|---|---|---|
| 确定性套件 + 覆盖率 | CI 同款命令（已扩展到 terminology/graph_rag/evidence） | **1234 passed, 3 skipped**，覆盖率 **88.36%** |
| pipeline API（独立进程） | `pytest tests/api/test_pipeline_api.py -q` | **18 passed** |
| 术语库 + graph_rag + evidence_extraction | 三目录联合 | **841 passed, 3 skipped** |
| 全后端离线套件 | `pytest tests`（排除 `rust_io` facade、`test_mineru_parser`、`cross_lingual_translation`、pipeline API 单独跑） | **2148 passed, 14 skipped, 2 failed**；2 个失败为 `pgvector` 迁移断言与 `origin/dev` 完全一致（`git diff origin/dev...HEAD -- backend/database backend/tests/dao` 为空），非本次改动 |
| Ruff / Mypy | `ruff check` / `ruff format --check` / mypy（29 files） | 通过 |
| 清单 | `scripts/pipeline_migration_inventory.py` | terminology 27/27 shim；`src/pipeline` 77 files / 11,145 lines |

> 注意：`test_pipeline_api.py` 与 graph/evidence 套件同进程运行会因既有全局 mock 泄漏失败，CI 已按独立进程执行；本次沿用该隔离方式验证。
>
> Mypy 未覆盖 `pipeline/tools/terminology` 与 `pipeline/tools/parsing`：迁移前即存在 11 + 7 处类型错误（变量复用、TypedDict 键、可选值等），不属本次布局迁移；已记录为独立技术债。`graph/topology.py`、`graph/progress.py`、`contracts/skill_io.py` 已纳入类型检查（29 files）。

## 5. 回滚

目录迁移可整体 revert 本分支；旧路径 shim 未删，外部调用方无需同步修改；无数据迁移、无配置变更。

## 6. 剩余工作

- 真实模型影子验收（阶段 2/3）与 ReMe 服务联调/召回评测（阶段 4a）；
- ReMe `auto_resource` 接入 Phase 2 产物；
- 阶段 5（可选，Neo4j → ReMe 整体切换）不做；
- 旧路径 shim 删除单独立项。
