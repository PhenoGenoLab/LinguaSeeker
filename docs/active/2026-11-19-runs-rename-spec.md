# SPEC — 把 `src/agents` 重命名为 `src/runs`（old-coder, Tier 2）

**Status:** awaiting approval
**Created:** 2026-11-19
**Tier:** 2（结构性重命名：不改变行为，但触及 38 个代码文件、58 个模块路径、18 个字符串 patch 目标、20 个测试文件、CI 与文档）
**Source state:** `dev` @ `785e32888`（工作树干净）
**Author:** agent（自主起草；批准后才进入实现）

---

## 1. 问题

`src/agents/` 里没有一个 agent：装的是 `PipelineRunner`、`SingleJobDispatcher`、两级缓存、内容哈希、状态持久化、并发重试基元、`GraphState`/错误层级契约，以及 Phase 5 的服务工厂。真正的 agent 能力实现在 `src/core/agents/{acquisition,parsing,translation,extraction,standardization,review,graph_retrieval}`。

两个 `agents` 同名不同义，是本仓库最容易误读的一处：读 `from src.agents.contracts import PipelineGraphState` 的人会以为在碰 agent 实现，实际是 run 的状态契约。

## 2. 授权范围

| 动作 | 路径 |
|---|---|
| 改名 | `backend/src/agents/` → `backend/src/runs/`（`git mv`，10 个文件） |
| 改名 | `backend/tests/agents/` → `backend/tests/runs/`（20 个文件，镜像源码） |
| 改 import | `src/runs` 内部、`src/api/**`、`src/pipeline/**`、`tests/**`、`scripts/**` 中引用 `src.agents` 的 58 个模块路径 + 18 个字符串 patch 目标 |
| 改 CI | `.github/workflows/ci.yml` 的 `src/agents/contracts.py` 与 `tests/agents` |
| 改文档 | `src/runs/README.md`（重写）、`docs/active/**`、`docs/README.md`、`AGENTS.md`、`backend/AGENTS.md`、各 `src/**/README.md` 中的 `src/agents` 路径 |
| 加断言 | `tests/pipeline/test_import_boundaries.py`：`src.agents` 进 `REMOVED_LEGACY_MODULES` |
| 不改 | `docs/archive/**`、`docs/planned/**`、`docs/codereview/**`（历史记录保留旧路径）；`src/core/**` 与 `src/pipeline/**` 的任何逻辑 |

## 3. 验收场景（可执行；命令均在仓库根执行）

### AC1 — 目录改名完成且内容完整
- `git ls-files backend/src/agents | wc -l` == `0`
- `git ls-files backend/src/runs | wc -l` == `10`（9 个 `.py` + `README.md`）
- `git ls-files backend/tests/agents | wc -l` == `0`
- `git ls-files backend/tests/runs | wc -l` == `20`

### AC2 — 代码里不再有旧路径 import
`rg -c '^\s*from src\.agents|^\s*import src\.agents' backend/src backend/tests backend/scripts -g '!*.md'` → 无输出（0）

### AC3 — 字符串 patch 目标同步
`rg -o '"src\.agents[A-Za-z0-9_.]*"' backend/src backend/tests backend/scripts -g '!*.md'` → 无输出（0）

### AC4 — 新路径可导入
`cd backend && .venv/bin/python -c 'import src.runs.contracts, src.runs.runner, src.runs.dispatcher, src.runs.state_persistence, src.runs.concurrency, src.runs.processing_cache, src.runs.content_hash, src.runs.phase_5_factory'` → exit `0`

### AC5 — CI 路径正确
- `rg -c 'src/agents|tests/agents|src\.agents' .github/workflows/*.yml` → 无输出（0）
- `rg -n 'src/runs/contracts.py' .github/workflows/ci.yml` → 1 行

### AC6 — 活跃文档不再指向旧路径
`rg -c 'src/agents' docs/active docs/README.md AGENTS.md backend/AGENTS.md backend/src --glob '*.md'` → 无输出（0）
（`docs/archive`、`docs/planned`、`docs/codereview` 中的历史记录不受此约束，见 §4）

### AC7 — 反向依赖被断言锁死
- `tests/pipeline/test_import_boundaries.py` 的 `REMOVED_LEGACY_MODULES` 含 `"src.agents"`
- 新增/保留断言：`src/runs` 不得 import `src.pipeline`
- `cd backend && .venv/bin/python -m pytest tests/pipeline/test_import_boundaries.py tests/core/test_layer_boundaries.py -q` → 全绿

### AC8 — 无行为变化 + 套件绿
- `git diff -M --stat` 中每个改名文件的差异仅为 import 行与 docstring（人工核对 3 个代表文件，输出贴进 EVIDENCE）
- `cd backend && .venv/bin/python -m compileall -q src tests scripts` → exit `0`
- 本机可跑的测试全绿：`pytest tests/core/source_fact_chain tests/pipeline tests/agents -q`（`tests/agents` 改名后为 `tests/runs`）
- 推送后 CI 9/9 绿（ruff / mypy / backend unit tests / frontend / rust / secret scan）

## 4. 负向约束（必须幸存）

- **行为不变**：不改任何函数体、默认值、异常分支；只改 import 路径、docstring 路径提及、README、CI 路径。
- **历史文档不改**：`docs/archive/**`、`docs/planned/**`、`docs/codereview/**` 保留 `src/agents`，因为它们是当时状态的记录；不做全局替换。
- **不动 `core/` 与 `pipeline/` 逻辑**：`src/core/**` 与 `src/pipeline/**` 只允许 import 行变化。
- **不新增/删除模块**：`src/runs` 与 `src/agents` 文件集合逐一对应（10 → 10）。
- 不新增依赖；不改 `pyproject.toml` 依赖段。

## 5. Setup 计划

- **隔离**：无 worktree。Tier 2 但在同一工作树操作：worktree 缺 gitignored 的 `.venv` 与数据，反而跑不了 AC4/AC8；前两次重构已验证 CI 是唯一全依赖环境。
- **新依赖**：无。
- **工具**：`.venv/bin/python`（pytest/compileall）、`git`、`rg`；`ruff`/`mypy` 本地不可用 → 由 CI 承担。
- **git**：授权 ① SPEC 单独一个 `docs:` 提交；② 改名 + import + 测试 + CI 一个 `refactor:` 提交；③ EVIDENCE 一个 `docs:` 提交；④ 推送 `dev` 触发 CI。

## 6. 已知限制（将写入 EVIDENCE）

- `ruff`/`mypy` 本地缺失，只能引用 CI 结果。
- 30 个提及 `src/agents` 的文档中，archive/planned/codereview 三类按 §4 保留旧路径，AC6 已按目录分层排除。
- 变异测试不适用：无行为分支被改动。
- 改名会让外部脚本（仓库外）中对 `src.agents` 的引用失效；仓库内已全覆盖，仓库外无法验证。

## 7. 命名决定（已由用户确认）

`src/runs`；测试目录镜像为 `tests/runs`。
