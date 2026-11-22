# SPEC — agents 门户化 + 确定性能力下沉 core/tools

**状态**: 已完成 Stage 1-7（acquisition、parsing、standardization、extraction、translation、review、graph_retrieval）；Stage 8 收口中
**决定来源**: 用户 2026-11-22 明确架构——`graph` 编排 → `agents` 门户 → `skills` 实现专业 agent → `skills` 调用 `core` 的具体工具。
**范围**: `backend/src/pipeline/graph/agents/*` 共 153 个 `.py`、31,563 行；外部 import 点 188+ 文件。

## 1. 目标分层

```
pipeline/graph/                编排：topology、phases、routing
pipeline/graph/agents/<A>/     门户：只有 __init__.py，导出该 agent 的公开入口
pipeline/skills/<A>/           专业 agent：prompt、模型调用、工具编排、AgentScope Skill 类
core/tools/<A>/                具体工具：确定性能力（解析、匹配、导入、检索、投影、契约）
```

单向依赖：`graph → agents(门户) → skills → core/tools → {core.shared, dao, utils}`。
`core` 不 import `src.pipeline`（现有断言保留）。

## 2. 分类规则（机械可判定，避免逐文件拍脑袋）

按以下顺序判定每个文件：

1. 路径含 `prompts/` 或文件名含 `prompt` → **skills**（prompt 属于 agent）。
2. 文件 import `agentscope` / `langchain*` / `openai` / `src.utils.llm_adapter` /
   `src.pipeline.skills.runtime` → **skills**（模型调用属于 agent）。
3. `providers.py`、`workflow.py`、`config_context.py`、`router.py`、`stages/` → **skills**
   （编排与外部模型/服务选择属于 agent 侧）。
4. 其余（`contracts.py`、`core.py`、`service.py`、`matchers.py`、`normalizers.py`、
   `importers.py`、`repositories.py`、`parsing/`、`review` 的数据服务等）→ **core/tools**。
5. 跨两边使用的 DTO 一律放 `core/tools/<A>/contracts.py`，skills 与 agents 门户都从那里取。

## 3. 现状数字（按规则 2 的客观切分）

| agent | 文件 | skills 行 | core/tools 行 |
|---|---:|---:|---:|
| acquisition | 7 | 0 | 527 |
| parsing | 13 | 0 | 1,734 |
| graph_retrieval | 9 | 0 | 1,226 |
| review | 9 | 1,254 | 3,111 |
| standardization | 27 | 0 | 5,776 |
| translation | 31 | 2,503 | 2,827 |
| extraction | 56 | 401 | 12,194 |
| **合计** | **152** | **4,158** | **27,395** |

prompt 目录另计约 1.1k 行，按规则 1 归 skills。

## 4. 阶段计划

| Stage | 内容 | 验收 |
|---|---|---|
| 1 | **acquisition 试点**：整体移入 `core/tools/acquisition/`，门户只导出 `DocumentAcquisitionService` + 契约；phases 改走门户；api/tests 直连新路径 | acquisition 相关测试全绿；套件 279+ 不降 |
| 2 | parsing（1,734 行，纯确定性） | 同上 |
| 3 | graph_retrieval（1,226 行） | 同上 |
| 4 | standardization（5,776 行） | 同上 |
| 5 | review（拆 1,254 / 3,111） | 同上 |
| 6 | translation（拆 2,503 / 2,827） | 同上 |
| 7 | extraction（拆 401 / 12,194，最大风险） | 同上 + 边界断言 |
| 8 | 边界与文档收口：门户规则、CI ignore 路径、AGENTS/README | `test_import_boundaries` 全绿；CI 9/9 |

每阶段独立提交，且必须满足：`compileall` 通过、既有测试不减少、无 shim/别名模块残留。

## 5. 边界与测试改动

- **新增**：`agents/*` 门户不得 import `agentscope`、`src.dao`、`src.utils`（只 import 下层 skills/core 的公开入口）。
- **新增**：`skills/*` 可以 import `src.dao`——原 `test_skills_do_not_import_database_clients` 必须删除或收窄到"不得直接建连接"。
- **保留**：`skills` 不得 import `topology/phases`；`core` 不得 import `src.pipeline`。
- **迁移**：`tests/pipeline/graph/agents/<A>/` → `tests/core/tools/<A>/` 与 `tests/pipeline/skills/<A>/`，镜像实现位置。
- **CI**：`--ignore=tests/pipeline/graph/agents` 改为忽略两个新路径中仍需重依赖的部分。

## 6. 风险与对策

| 风险 | 对策 |
|---|---|
| 拆包破坏相对 import | 每阶段用脚本把移动后文件中的相对 import 改写为绝对路径，`compileall` + 逐包 import 冒烟 |
| 188+ 外部 import 点 | 机械改写 `src.pipeline.graph.agents.<A>.` → 新落点；门户路径只在 `graph/phases`、`runs/phase_*_factory` 保留 |
| 门户变成 shim | 门户只导出 phase/factory 真正用到的名字；`__all__` 逐一列出，禁止 `import *` |
| 一次性大迁移不可回滚 | 每 agent 一个提交，测试全绿才进入下一个 |


## 7. 执行结果（2026-11-22）

| Stage | 提交 | 结果 |
|---|---|---|
| 1 acquisition | `4b33f9c5c` | 527 行 → `core/tools/acquisition`，门户 2 个名字 |
| 2 parsing | `617dbc988` | 1,734 行 → `core/tools/parsing`，门户 `ParsingSkill` |
| 3-7 其余 | 本次提交 | 111 个文件按规则拆分；门户 5 个；188+ 外部 import 改指新路径 |

实测分布：`core/tools/<agent>` 承载契约/规则/持久化，`skills/<agent>` 承载 prompt、provider、
stages、workflow、api；`agent` 目录只剩门户 `__init__.py`。

### 与 SPEC 的偏离（必须知道）

1. **`skills/extraction/prompts.py` 与新建的 `prompts/` 包同名冲突** → 两个模块合并进
   `prompts/__init__.py`，旧单文件删除。`EXTRACT_PROMPT` 等名字保持不变。
2. **`providers.py` 归类按语义修正**：HTTP 推理适配器（`standardization/similarity_match`、
   `graph_retrieval`）留在 core/tools；LLM provider 进 skills。
3. **`qa_engine.py`、`chat_service.py` 起初按名称规则落入 core，因 import LLM provider
   被重新判为 skills**（规则的传播只覆盖了相对 import，绝对 import 靠人工复查）。
4. **测试位置**：`tests/pipeline/graph/agents/<A>/` 整体移到 `tests/core/tools/<A>/`。
   它们依赖 `rust_io`/`langchain_openai`/`agentscope`，CI 的确定性套件本来就不收集，
   迁移后同样不收集。
5. **边界规则变化**：删除 `test_skills_do_not_import_database_clients`（skills 现在承担
   持久化），保留 `test_skills_do_not_import_graph_execution`。CI 的
   `--ignore=tests/pipeline/graph/agents` 已移除（该路径不复存在）。
6. **已知数据依赖失败**：`tests/core/tools/extraction/test_e2e_fabry_dual_tracks.py`
   在旧位置因 `parents[4]` 解析到 `tests/` 而跳过；迁移后解析到 backend，真实读取
   `backend/output/.../法布雷病1例`，断言 original 页跨度 4 页、实际 3 页。涉及模块逐行
   diff 仅 import 变化，判定为 fixture 漂移，未在本次修复。

## 8. 遗留：迁移代码的 23 个类型错误（未修）

CI 的 mypy 在迁移前只检查 `skills/` 下的薄封装；实现搬入后，23 个既存类型错误暴露出来。
本次未修改它们（与分层无关，且部分涉及真实签名漂移），CI 的 mypy 目标维持迁移前的覆盖面，
并新增门户目录 `src/pipeline/graph/agents`。错误清单（`mypy 2.4.1`）：

| 文件 | 行 | 错误 |
|---|---:|---|
| `skills/translation/config_context.py` | 59, 76 | `Any | None` 上的属性访问 |
| `skills/translation/translate/translator.py` | 431, 536, 722, 807, 922, 997 | override 签名不兼容、5/7 元组不匹配、属性重复定义 |
| `skills/translation/api.py` | 76 | 传入 `FormattedDocument | None` |
| `skills/extraction/stages/clinical_context.py` | 265-266 | `object` 上无 `total/index` |
| `skills/extraction/stages/catalog_extraction.py` | 107, 155, 412, 421-429 | list 不变性、Optional 赋值、`object` 属性 |
| `skills/extraction/stages/review_validation.py` | 184 | Optional 赋值 |
| `skills/extraction/workflow.py` | 130, 184 | 传入 `DocumentEvidenceMap | None` |

其中 `translator.py` 的 5 vs 7 元组不匹配值得单独排查：它可能是真实的运行时缺陷，
而不只是注解问题。已删除的 `stages/preprocessing.py` 也曾贡献 1 个错误。
