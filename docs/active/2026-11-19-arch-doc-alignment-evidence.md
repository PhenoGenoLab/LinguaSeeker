# EVIDENCE — 文档/脚本架构对齐（old-coder, Tier 1）

**Spec:** `/data/yangzs/Projects/01_Platform/01_ACMG_Lingua/docs/active/2026-11-19-arch-doc-alignment-spec.md`（批准，含 r2–r5 修订）
**Spec approval:** obtained（用户在批准表单选择 “approve”，含两步提交）
**Branch:** `dev`（任务中途用户曾切到 `fix/parsing-p0`；按用户指示，四个提交已 fast-forward 到 `dev`
并推送，`fix/parsing-p0` 已指回 base `1762c58a7`。见 Spec r2 与 §5）
**Source state:** `1762c58a7` → `1238fda95`（`origin/dev` 已同步）
**Run date:** 2026-11-19

## 1. 变更集

| 提交 | 内容 |
|---|---|
| `6f334f844` | SPEC 初版（批准后立即提交，作为契约基线） |
| `8478bf513` | 两个目标文件：计划文档横幅/标注 + 脚本 docstring |
| `7f208117b` | SPEC 的 r2–r5 修订（保留批准后的可见漂移） |
| `1238fda95` | 本 EVIDENCE 报告（含 CI 层结果回填） |

工作树最终状态：`git status --porcelain` 空；`origin/dev` = `1238fda95`。

> ⚠ 已知瑕疵（未修复）：`8478bf513` 与 `7f208117b` 的**提交信息与内容互换**——前者的
> message 写的是 "amend the alignment spec"，实际内容是那两个目标文件。四个提交现已推送到
> `origin/dev`；修正需要 rebase 改写已推送历史，未在未授权情况下执行。

## 2. 验收场景 → 验证结果（最终一次全新运行）

命令均在 `/data/yangzs/Projects/01_Platform/01_ACMG_Lingua` 下执行，
`doc=docs/planned/2026-11-17-pipeline-agentscope-reme-migration.md`，
`script=backend/scripts/pipeline_migration_inventory.py`。

| # | 场景 | 命令 | 结果 |
|---|---|---|---|
| AC1 | 修订横幅唯一 | `grep -c '^> \*\*架构修订（2026-11-19）\*\*' $doc` | `1`（期望 1）✅ |
| AC2 | 状态改为 superseded | `grep -c '^> \*\*Status:\*\* superseded' $doc` / `grep -c 'Status:\*\* planned' $doc` | `1` / `0`（期望 1/0）✅ |
| AC3 | 三处就地失效标记 | `grep -c '本节路径已被 2026-11-19 架构修订取代' $doc` | `3`（期望 3）✅ |
| AC4 | 旧布局串全部标注“原计划” | `grep -c 'src/pipeline/{graph,skills,tools,mcp}' $doc` / `...}``（原计划）'` / 新布局串 | `1` / `1` / `1`（期望 1/1/1）✅ |
| AC5 | 脚本标历史且可运行 | `grep -c 'Status: historical' $script`；`py_compile`；`--help` | `1`；exit `0`；exit `0` ✅ |
| AC6 | 输出仍可消费 | `… --format json \| python -c 'json.load(stdin)["layers"]'` | `layers=5`，exit `0` ✅ |
| AC7 | 改动面 | `git show --name-only --format= 8478bf513` | 恰为 `backend/scripts/pipeline_migration_inventory.py`、`docs/planned/2026-11-17-pipeline-agentscope-reme-migration.md` ✅；`git diff --name-only` 为空、`git status` 干净 |

AC7 的判定从“`git diff --name-only`”改为“承载改动的提交的文件清单”：SPEC 的修订也在
工作区产生 diff，用提交清单才能同时表达“变更集只含两个目标文件”与“规格修订可见”。

## 3. Gauntlet 各层

| 层 | 命令 | 结果 |
|---|---|---|
| 全量测试 | CI `backend unit tests`（commit `1238fda95`，push 到 `dev` 的 Actions run） | success ✅ |
| 架构守护测试 | `.venv/bin/python -m pytest tests/core/test_layer_boundaries.py -q` | `5 passed in 0.19s` ✅ |
| 语法 | `.venv/bin/python -m py_compile backend/scripts/pipeline_migration_inventory.py` | exit `0` ✅ |
| 真实执行 | `.venv/bin/python scripts/pipeline_migration_inventory.py --format json` | 正常输出，`layers=5` ✅ |
| 静态类型 | CI `backend type-check (mypy)`（`1238fda95`） | success ✅（本地无 mypy，改由 CI 承担） |
| Lint | CI `backend lint (ruff)`（`1238fda95`） | success ✅（本地 `.venv` 无 ruff，改由 CI 承担） |
| 其余 CI 作业 | `frontend lint + type-check`、`frontend test (vitest)`、`rust test (files-io/net-io/rust-io)`、`secret scan` | 全部 success —— 该 commit 共 9/9 checks 绿 |
| 覆盖率 | — | 不适用：无新增/修改代码路径 |
| 变异测试 | — | 不适用：没有可变异的行为分支（改动全部为注释/文档） |
| 属性测试 | — | 不适用：无算法/序列化面 |
| 供应链 | 无依赖变更 | `git show 8478bf513 --stat` 仅两文件；无 import 增加 |
| 套件健康 | — | 未触及测试执行路径；CI 套件在该 commit 上全绿 |

### 代码面证明（补充 lint/类型层）

`git show 8478bf513 -- backend/scripts/pipeline_migration_inventory.py` 的全部 `+` 行都是
docstring 行；过滤掉文档行后剩余 `+` 行只有空行（验证命令见 §2 运行记录）。因此脚本的
可执行语句、`LAYER_SPECS` 数据与 JSON schema 均未改变（AC6 的 `layers=5` 输出即为佐证）。

## 4. 检查器的负向控制（home-grown checks）

AC1–AC5 是自写的 grep 判定，按规则必须先证明它能失败。改前（RED）实测：

| 检查 | 改前值 | 期望 |
|---|---|---|
| AC1 | `0` | 1 |
| AC3 | `0` | 3 |
| AC4 旧串 | `bare=1, labelled=0`（即未标注） | 1/1 |
| AC5 | `0` | 1 |

即每个判定都在已知坏输入上走过失败分支。**覆盖边界**：AC4 只证明“旧串出现处带标注”，
不证明文档其余叙事文字已无旧路径描述——那是范围内有意保留的历史内容（Spec §6）。
AC2 的先验版本曾是一个恒真空断言，RED 阶段发现并修订（Spec r3），说明这类自写判据本身
也需要被质疑。

## 5. 跳过与限制

- **全量测试 / mypy / ruff 未在本地运行**：`.venv` 缺 `ruff`，全量 pytest 依赖 CI-only 包
  （agentscope 等）。已按用户指示把这四个提交 fast-forward 到 `dev` 并推送，CI 在
  `1238fda95` 上跑完：`backend unit tests`、`backend type-check (mypy)`、`backend lint (ruff)`
  及其余 6 个作业全部 success（9/9）。这三层的证据是 CI run，不是本地跑出来的。
- **分支**：任务中途用户在 `fix/parsing-p0` 上，后按用户指示 fast-forward 到 `dev` 并推送；
  `fix/parsing-p0` 已指回 base `1762c58a7`（其提交现存于 `dev`，可通过 reflog 找回）。
- **提交信息与内容互换**（见 §1 警告）：`8478bf513` 的 message 与内容不符，已推送到
  `origin/dev`，未擅自改写已推送历史。
- 计划文档正文的路径表格按“保留历史”原样保留，仅在表格前后加失效标记。
