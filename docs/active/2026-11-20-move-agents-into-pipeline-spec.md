# SPEC — 把 agent 实现移出 core，落到 pipeline/graph/agents（old-coder, Tier 3）

**Status:** awaiting approval
**Created:** 2026-11-20
**Tier:** 3（174 个源文件 + 约 125 个测试文件搬迁；跨层依赖重排；不改业务逻辑但改所有 import 面）
**Source state:** `dev` @ `383a54f4a`
**Author:** agent（自主起草；批准后才进入实现）

---

## 0. 目标与硬约束

把 `src/core/agents/*`（7 个包、174 文件、约 31k 行）整体移到 `src/pipeline/graph/agents/*`，
让 core 回到"配置 + foundation/shared/adapters"。

**硬约束**：搬完后依赖图必须仍是单向 DAG。当前有 4 处会让它成环，必须一并处理：

| 环 | 现状 | 处理 |
|---|---|---|
| core → pipeline | `core/shared/tools/fact_chain/projection.py` 引 `agents/extraction/{contracts,core.grouping,domain.catalog}` | 把这三样下沉到 `core/shared/` |
| runs → pipeline | `runs/contracts.py` 引 `extraction.contracts`、`parsing.exceptions` | 契约/异常下沉到 `core/shared/` |
| runs → pipeline | `runs/content_hash.py` 引两个默认常量 | 常量下沉到 `core/shared/contracts/extraction_defaults.py` |
| runs → pipeline | `runs/phase_5_factory.py` 引 review 实现 | 工厂移到 `src/api/phase_5_factory.py`（api → pipeline 本就允许） |

## 1. 目标布局

```
src/core/
├── config.py, config_loader.py
├── foundation/auth/
├── shared/
│   ├── contracts/
│   │   ├── skill_io.py
│   │   ├── evidence.py            ← 原 core/agents/extraction/contracts.py
│   │   ├── extraction_defaults.py ← 两个默认常量
│   │   └── parsing_errors.py      ← 原 core/agents/parsing/exceptions.py
│   └── tools/fact_chain/
│       ├── contracts.py, core.py, projection.py, windowing.py
│       ├── grouping.py            ← 原 extraction/core/grouping.py
│       └── catalog.py             ← 原 extraction/domain/catalog.py
└── adapters/mcp/

src/pipeline/graph/
├── topology.py
├── phases/phase_1..4.py
└── agents/                        ← 原 core/agents/*
    ├── acquisition/ parsing/ translation/ extraction/
    ├── standardization/ review/ graph_retrieval/

src/api/phase_5_factory.py         ← 原 src/runs/phase_5_factory.py
```

`src/pipeline/skills/**` 不变（agent 定义与工具门面），只是它 import 的 agent 实现路径改变。

## 2. 验收场景（可执行）

### AC1 — 目录搬迁完成
- `git ls-files backend/src/core/agents | wc -l` == `0`
- `git ls-files backend/src/pipeline/graph/agents | wc -l` == `174`（7 个包）
- `git ls-files backend/tests/core/agents | wc -l` == `0`
- `git ls-files backend/tests/pipeline/graph/agents | wc -l` == 原 `tests/core/agents` 文件数（125）

### AC2 — 全仓无旧路径
`rg -c 'src\.core\.agents' backend/src backend/tests backend/scripts -g '!*.md'` → 无输出（0）

### AC3 — 依赖仍是 DAG
- `pytest tests/pipeline/test_import_boundaries.py tests/core/test_layer_boundaries.py -q` 全绿
- 其中必须存在的断言：
  - `src/core` 不 import `src.pipeline`
  - `src/runs` 不 import `src.pipeline`
  - `src/pipeline/graph/agents` 不 import `src.pipeline.graph.topology` / `phases`
- 新增：`test_core_has_no_agents_package`（`src/core/agents` 不存在）

### AC4 — 下沉的四块代码就位
- `backend/src/core/shared/contracts/evidence.py` 存在，且 `rg -c 'src\.core\.agents' <file>` == 0
- `backend/src/core/shared/tools/fact_chain/{grouping,catalog}.py` 存在
- `backend/src/core/shared/contracts/{extraction_defaults,parsing_errors}.py` 存在
- `rg -c 'src\.pipeline' backend/src/core/shared/tools/fact_chain/projection.py` == 0

### AC5 — runs 不再依赖 pipeline
- `rg -c 'src\.pipeline' backend/src/runs` → 0
- `rg -c 'phase_5_factory' backend/src/runs` → 0；`backend/src/api/phase_5_factory.py` 存在
- `rg -c 'from src\.api\.phase_5_factory|api\.phase_5_factory' backend/src/api` ≥ 1

### AC6 — 行为不变
- 搬迁文件的差异仅为 import 行（抽查 3 个：extraction/api.py、review/chat_service.py、graph_retrieval/api.py；输出贴进 EVIDENCE）
- `cd backend && .venv/bin/python -m compileall -q src tests scripts` → exit 0
- 本地可跑套件全绿：`pytest tests/core/source_fact_chain tests/pipeline tests/runs tests/api/test_wiring_config.py --ignore=tests/pipeline/test_extract_skill.py -q`
- 推送后 CI 9/9（含 ruff、mypy、backend unit tests 的真依赖环境）

### AC7 — 配置与 CI 路径
- `.github/workflows/ci.yml` 中 mypy/coverage 路径同步（`src/core/shared/tools/fact_chain` 仍有效；新增 `src/pipeline/graph/agents/extraction` 视覆盖率门槛决定）
- `backend/config/**` 与 `deploy/**` 无 `core/agents` 引用（`rg` 0）

## 3. 负向约束

- **不改任何业务逻辑**：只动 import 路径、文件位置、模块归属。
- 不删除任何测试；只改路径与 import（`tests/core/agents` → `tests/pipeline/graph/agents`）。
- 不新增依赖；不动 `AGENTS.md` 的架构规则条目（除路径指向，另行说明）。
- 不保留 shim/别名：`src.core.agents` 一次性消失。
- `src/pipeline/skills/**` 的对外 API 不变（`AcquisitionSkill`、`ParsingSkill`、`StandardizationSkill`、`SourceFactChainService` 等签名不动）。

## 4. Setup 计划

- **隔离**：无 worktree（本地 `.venv` 是唯一能跑套件的环境）。
- **新依赖**：无。
- **git 提交**：① SPEC；② 下沉 core/shared 的四块；③ agents 搬迁 + import 重写；④ 测试目录搬迁；⑤ CI/文档；⑥ EVIDENCE。每步跑一次本地套件。

## 5. 已知限制（将写入 EVIDENCE）

- 本地跑不了 `test_extract_skill.py`（需 agentscope）。
- 搬迁后 `tests/pipeline/graph/agents/**` 的路径层级变深，`Path(__file__).parents[N]` 之类相对定位需要逐个核对（属于行为风险，不是纯 import 改）。
- 文档：`docs/active` 中带日期的历史记录保留旧路径；`AGENTS.md` 的仓库映射条目需更新为 `pipeline/graph/agents`。
- 一次性提交量很大（约 300 个路径），review 以 `git show --stat -M` 的 rename 视图为准。

## 6. 修订记录（实现前，可见）

**r2 — 2026-11-20（缩小解耦面：不搬 extraction/contracts）**：原计划把整个
`extraction/contracts.py` 下沉到 `core/shared/contracts/evidence.py`。实现前实测：
agents 内有 **230 处相对 import（77 文件）**，其中大量是 `from .contracts` / `from ..contracts`
指向各自子包的**本地** contracts；整体搬迁会让这些相对路径大面积失真，属于"为了解耦制造
静默错误"。修订为最小切口：

1. **core 侧唯一真实依赖**是 `core/shared/tools/fact_chain/projection.py`（3 处 import）。
   → 把 `projection.py` 移到 `pipeline/graph/agents/extraction/projection.py`（它本身就是
   extraction 的投影逻辑），改写它的 3 处 import 与 3 个引用方。core 由此对 agents 零依赖。
2. **runs 侧**（contracts / content_hash / phase_5_factory 共 9 处）不再搬迁上游模块，
   而是修订边界语义：`runs` **允许** import `pipeline.graph.agents`（它执行图、需要 agent
   契约），仍**禁止** import `pipeline.graph.topology` / `phases`。断言相应改写。
3. `phase_5_factory` 留在 `src/runs/`（它引 review 服务，属于允许的 agents 引用）。

其余（agents 整体搬迁、测试目录搬迁、import 前缀重写）不变。AC4/AC5 随之改写：
- AC4 改为：`core/shared/tools/fact_chain/projection.py` 不存在；`pipeline/graph/agents/extraction/projection.py` 存在；`rg -c 'src\.pipeline|src\.core\.agents' src/core` == 0。
- AC5 改为：`rg -c 'pipeline\.graph\.(topology|phases)' src/runs` == 0；`runs → agents` 允许且被断言覆盖。
