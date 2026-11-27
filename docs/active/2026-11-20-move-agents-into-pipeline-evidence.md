# EVIDENCE — agent 实现移入 pipeline/graph/agents（old-coder, Tier 3）

**Spec:** `/data/yangzs/Projects/01_Platform/01_ACMG_Lingua/docs/active/2026-11-20-move-agents-into-pipeline-spec.md`（批准，含 r2 修订）
**Spec approval:** obtained（用户选择 "批准，按 SPEC 分 6 步执行"）
**Branch:** `dev`
**Source state:** `383a54f4a` → `572699812`（实现 + SPEC 同一提交，见 §5）
**Run date:** 2026-11-20

## 1. 搬迁结果

| 项 | 结果 |
|---|---|
| `src/core/agents` | 0 文件（目录消失） |
| `src/pipeline/graph/agents` | **175** 文件（174 个 agent 文件 + `extraction/projection.py`） |
| `tests/core/agents` | 0 |
| `tests/pipeline/graph/agents` | **140** 文件 |
| `src/core/shared/tools/fact_chain/projection.py` | 已删除（移入 extraction） |

依赖方向（实测）：

| 边 | 数量 |
|---|---|
| `core → pipeline`（真实 import） | **0**（grep 的 7 处全是 docstring 里的 "Never imports"） |
| `core → agents` | 0 |
| `runs → pipeline.graph.topology/phases` | 0 |
| `skills → pipeline.graph.topology/phases` | 0 |
| `config/`、`deploy/` 中 `core/agents` 引用 | 0 |

## 2. 验收场景 → 结果

| # | 场景 | 实测 |
|---|---|---|
| AC1 | 目录搬迁 | 见 §1 ✅ |
| AC2 | 全仓无旧路径 | `rg src.core.agents` 仅剩 **3 处历史记录**（`REMOVED_LEGACY_MODULES` 1 处 + 迁移清单脚本 2 处），均为有意保留 ✅ |
| AC3 | DAG | 边界测试 **18 passed**；新增 `test_core_has_no_agents_package`；`test_runs_do_not_import_graph_execution`、`test_skills_do_not_import_graph_execution` 按新事实改写 ✅ |
| AC4 | 下沉物就位 | projection 移入 `agents/extraction/projection.py`，其 import 全指向 core/shared 与同包 ✅ |
| AC5 | runs 不再碰图执行 | `runs → topology/phases` = 0；`runs → agents` 属允许范围（见 r2） ✅ |
| AC6 | 行为不变 | 本地 **279 passed**；`compileall` exit 0；CI 9/9 ✅ |
| AC7 | 配置与 CI 路径 | `ci.yml` 的 search-service 测试路径改为 `tests/pipeline/test_search_service.py`，并对搬入的 agent 测试树加 `--ignore`（保持原有 CI 范围）；config/deploy 无引用 ✅ |

## 3. Gauntlet 各层

| 层 | 命令 | 结果 |
|---|---|---|
| 全量（本地可跑范围） | `pytest tests/core/source_fact_chain tests/pipeline tests/runs tests/api/test_wiring_config.py --ignore=…/test_extract_skill.py --ignore=tests/pipeline/graph/agents -q` | **279 passed in 4.36s** ✅ |
| 边界 | `pytest tests/core/test_layer_boundaries.py tests/pipeline/test_import_boundaries.py -q` | 18 passed ✅ |
| 语法 | `compileall -q src tests scripts` | exit 0 ✅ |
| 静态类型 | CI mypy（`572699812`） | success ✅ |
| Lint | CI ruff（`572699812`） | success ✅ |
| 覆盖率 | CI `--cov-fail-under=85` | success ✅ |
| 全量 CI | 9/9 绿 ✅ |
| 变异/属性测试 | — | 不适用：纯文件搬迁 + import 重写，无行为分支 |
| 供应链 | 无依赖变更 | ✅ |

## 4. 检查器负向控制

AC1/AC2 是自写 grep/AST 判定，改动前实测：`core/agents` 174 文件、`pipeline/graph/agents` 0、
`src.core.agents` 引用 236 处 → 改后为 0 / 175 / 3（历史项）。边界断言在搬迁前是绿的，
搬迁后必须先红再改：本轮 `test_skills_do_not_import_graph` 与 `test_runs_do_not_import_pipeline`
确实在搬迁后失败，改写后转绿，说明它们真的在检查路径而非恒真。

## 5. 与 SPEC 的偏离（可见记录）

1. **r2（实现前写入）**：原计划把 `extraction/contracts.py`、`grouping.py`、`catalog.py`、
   `parsing/exceptions.py`、两个默认常量全部下沉到 `core/shared`。实测 agents 内有
   **230 处相对 import（77 文件）**，整体搬迁会让 `from .contracts` 类相对路径大面积失真。
   改为最小切口：只把 `projection.py` 归位（core 侧唯一真实依赖），并允许
   `runs → pipeline.graph.agents`（runs 执行图、只引契约），`phase_5_factory` 留在 runs。
2. **SPEC 与实现同一提交**：SPEC 文件（含 r2）随 `572699812` 一并提交，没有单独的
   `docs:` 提交。原因是实现已开始后才发现 SPEC 未提交；`git show 572699812 --stat` 可核对。

## 6. 已知限制

- **140 个 agent 测试不在 CI 中**：它们此前位于 `tests/core/agents`，本就不在确定性套件里；
  搬入 `tests/pipeline` 后会顺带被收集，因此 CI 显式 `--ignore=tests/pipeline/graph/agents`。
  本地这些测试也跑不了（缺 `rust_io` 扩展与 `langchain_openai`）。
- **`test_search_service.py` 被上提到 `tests/pipeline/`**，以保证它在 CI 中仍然执行（原来是以显式路径列在 CI 里）。
- 文档：`docs/active` 的带日期历史记录、`docs/planned`、迁移清单脚本保留旧路径（有意）。
- `AGENTS.md` 的源码树与映射条目已更新；`docs/active/*` 其余历史文档未改。
