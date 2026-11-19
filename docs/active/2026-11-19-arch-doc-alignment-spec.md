# SPEC — 文档/脚本架构对齐（old-coder, Tier 1）

**Status:** awaiting approval
**Created:** 2026-11-19
**Tier:** 1 (trivial blast radius: two documentation artifacts, no product code)
**Source state:** `dev` @ `1762c58a7`（工作树干净，CI 全绿）
**Author:** agent, autonomous drafting; approval required before implementation

---

## 1. 问题

2026-11-18/19 两次架构调整后，两处产物仍在描述旧计划：

| 文件 | 旧主张 | 现状 |
|---|---|---|
| `docs/planned/2026-11-17-pipeline-agentscope-reme-migration.md` | 迁移后领域层为 `src/pipeline/{graph,skills,tools,mcp}`；§3.2/§3.2.3/阶段 2 的路径表把 tools 指向 `src/pipeline/tools/*` | `src/pipeline/` 只剩 `graph/` + `skills/`；tools/contracts 在 `src/core/shared/`，mcp 在 `src/core/adapters/`；core 已按 agent 命名 |
| `backend/scripts/pipeline_migration_inventory.py` | 迁移清单工具，目标是那次计划的 target 路径 | 目标路径永远不会存在；脚本可运行但输出恒为 0，且无任何标记提示 |

风险：后续 agent/人会照着这些表去创建 `src/pipeline/tools/*`，与已定架构冲突。

## 2. 授权范围（只改这两个文件）

1. `docs/planned/2026-11-17-pipeline-agentscope-reme-migration.md`
2. `backend/scripts/pipeline_migration_inventory.py`（仅 docstring，不改逻辑）

不改：任何 `backend/src/**`、`backend/tests/**`、`.github/**`、`AGENTS.md`。

## 3. 验收场景（可执行，逐条命令验证）

### AC1 — 计划文档带显式修订横幅
在文档前 30 行内出现且仅出现一次：
`> **架构修订（2026-11-19）**`
横幅须列出三处被取代的决策并指向 `src/core/README.md`：
`tools → core/shared/tools`、`mcp → core/adapters/mcp`、`contracts → core/shared/contracts`、`core 按 agent 命名`。

验证：`grep -c '^> \*\*架构修订（2026-11-19）\*\*' <doc>` == `1`

### AC2 — 文档状态不再声称 planned
`**Status:** planned` 行改为 `**Status:** superseded（2026-11-19 架构修订）`。

验证：`grep -c '^\*\*Status:\*\* superseded' <doc>` == `1` 且 `grep -c '^\*\*Status:\*\* planned' <doc>` == `0`

### AC3 — 三处旧主张各有就地失效标记
在以下三个位置各插入一行 `> ⚠ 本节路径已被 2026-11-19 架构修订取代，现行布局见 src/core/README.md。`：
1. `### 3.2 目标目录结构：graph / skills / tools / mcp` 标题之后、表格之前；
2. `#### 3.2.3 现有模块 → 目标层映射` 的表格之后（表体保持原样作为历史记录，不改行内容）；
3. `### 阶段 2 — AgentScope 运行时 + Phase 3 抽取试点（2–3 周）` 标题之后。

验证：`grep -c '本节路径已被 2026-11-19 架构修订取代' <doc>` == `3`

### AC4 — 头部“适用对象”不再指向 pipeline/tools
原句 `迁移后领域层为 backend/src/pipeline/{graph,skills,tools,mcp}` 改为
`迁移后领域层为 backend/src/pipeline/{graph,skills} + backend/src/core/{foundation,shared,adapters,agents}`。

验证：`grep -c 'src/pipeline/{graph,skills,tools,mcp}' <doc>` == `0`
且 `grep -c 'src/pipeline/{graph,skills} + backend/src/core/{foundation,shared,adapters,agents}'` == `1`

### AC5 — 清单脚本自我标记为历史，且仍可运行
docstring 内出现 `Status: historical` 与 `2026-11-19`，并说明现行布局与 `src/core/README.md`。

验证：
- `grep -c 'Status: historical' backend/scripts/pipeline_migration_inventory.py` == `1`
- `.venv/bin/python -m py_compile backend/scripts/pipeline_migration_inventory.py` → exit 0
- `cd backend && .venv/bin/python scripts/pipeline_migration_inventory.py --help` → exit 0

### AC6 — 脚本行为未变（输出仍可被消费）
`cd backend && .venv/bin/python scripts/pipeline_migration_inventory.py --format json | .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); assert isinstance(d["layers"], list)'` → exit 0

### AC7 — 负向约束：改动面
`git diff --name-only` 只包含上述两个文件（SPEC 文件本身在实现前单独提交）。
验证：`git diff --name-only | sort` 输出恰好等于这两行。

## 4. 负向约束（必须幸存）

- 不删除、不改写计划文档的正文表格与结论（只加横幅/标记，保留历史）。
- 不改脚本的 `LayerSpec` 数据、输出 JSON schema、命令行参数。
- 不新增依赖；脚本继续只用标准库。
- 不修改任何测试，不新增测试（Tier 1：纯文档/注释改动，无可执行行为变化）。
- 不触碰 `src/pipeline/**`、`src/core/**`。

## 5. Setup 计划

- **隔离**：无。Tier 1，两个文档文件，blast radius = 0 行可执行代码；不建 worktree（会丢失 gitignored 的 `.venv`，反而无法验证 AC5/AC6）。
- **新依赖**：无。
- **工具**：沿用现有 `.venv/bin/python`（AC5/AC6）与 `git`（AC7）。`ruff`/`pytest` 本地不可用（`.venv` 无 ruff，且全量测试依赖 agentscope 等 CI-only 依赖），因此静态检查与全量测试由 CI 承担，EVIDENCE 引用 CI run。
- **git**：授权后按两步提交 —— ① 只含 SPEC 文件的 `docs:` 提交；② 只含两个目标文件的 `docs:` 提交。若你不希望提交，请在批准时说明，我会只改文件不提交。

## 6. 已知限制（将写入 EVIDENCE）

- 本地无法运行 `ruff` 与全量 pytest：EVIDENCE 中这些层以 CI run 结果为准，并注明“本地不可用”。
- 本次改动为文档/注释，mutation testing 无适用目标（没有可变异的行为分支）——按“记录跳过原因”处理。
- AC3 只保证三处**已知**旧主张被标记；文档其余叙述性文字仍描述旧计划，属有意保留的历史内容。
