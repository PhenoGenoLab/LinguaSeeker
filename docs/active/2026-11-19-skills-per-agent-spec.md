# SPEC — skills 一 agent 一包，Phase 3 拆分，行为由影子门禁控制（old-coder, Tier 3）

**Status:** awaiting approval
**Created:** 2026-11-19
**Tier:** 3（引入 LLM 决策路径、跨 5 个 phase 的调用面改造、行为可变化）
**Source state:** `dev` @ `e27aaa81f`
**Author:** agent（自主起草；批准后才进入实现）

---

## 0. 先说我判断的风险（不影响执行，但必须在文档里）

采集（HTTP/SDK）、解析（MinerU）、标准化（术语匹配 + 向量检索）本质是**确定性 I/O**，
把 LLM 放进来不产生正确性收益，却带来非确定性、成本与延迟。因此本 SPEC 的 agent 定义是
**工具约束型 agent**：agent 拥有的工具就是 `core/agents/<x>` 暴露的确定性函数，LLM 只允许
在「选哪个工具、如何分类错误/重试」这一层动作；**产出必须与 legacy 路径逐字段一致**，
由影子 diff 强制。达不到一致的 phase 不切默认，记录为已知限制。

## 1. 目标布局

```
src/pipeline/skills/
├── runtime/           # 不变：事件循环桥、模型档位、多 key 轮换（不是 agent）
├── acquisition/       # 新：Phase 1 agent（工具 = core.agents.acquisition.*）
├── parsing/           # 新：Phase 2 agent（工具 = core.agents.parsing.*）
├── extraction/        # 由 fact_chain 拆出：extract + verify + runner + prompts + service
├── translation/       # 由 fact_chain 拆出：translate 阶段（展示字段英译）
└── standardization/   # 新：Phase 4 agent（工具 = core.agents.standardization.*）

src/core/             # 工具与 mcp 的归属（已满足，不再变动）
├── shared/tools/     # 确定性能力
├── shared/contracts/ # 跨层 DTO
├── adapters/mcp/     # 外部协议
└── agents/<agent>/   # 被 skill 当工具调用的确定性实现
```

Phase 5（review）不在本次范围：它不是图节点，走 `runs/phase_5_factory.py`。

## 2. 运行模式（行为变化的开关）

配置已存在：`pipeline.agent_runtime: legacy | shadow | agentscope`（默认 `legacy`）。

| 模式 | 行为 |
|---|---|
| `legacy`（默认） | 适配器经 skill 门面直通 core 实现，**不构造 LLM、不 import agentscope**；输出与今天逐字节一致 |
| `shadow` | legacy 与 agent 各跑一次，`legacy` 结果返回；写 `shadow_report.json`（phase、legacy_hash、agent_hash、equal、token/耗时） |
| `agentscope` | 返回 agent 结果（**本次不切默认**，留给 P1） |

**本次授权只到 P0**：结构 + 三种模式的可运行骨架，默认 `legacy`。把某 phase 默认切到
`agentscope` 属于 P1，需要基于影子证据另立 SPEC。

## 3. 验收场景（可执行）

### AC1 — 目录布局
- `git ls-files backend/src/pipeline/skills | cut -d/ -f5 | sort -u` == `acquisition, extraction, parsing, runtime, standardization, translation`（6 个包，各含 `__init__.py`）
- `git ls-files backend/src/pipeline/skills/fact_chain | wc -l` == `0`

### AC2 — 适配器不再直连 core 实现
`rg -c 'src\.core\.agents\.\w+\.(service|api|core|providers|runner)' backend/src/pipeline/graph` → 无输出（0）
（仍允许 import `core.agents.*.contracts`：契约不是业务实现）

### AC3 — legacy 模式不加载 agentscope（延迟导入）
`cd backend && .venv/bin/python -c "import sys, src.pipeline.skills.acquisition, src.pipeline.skills.parsing, src.pipeline.skills.standardization; assert 'agentscope' not in sys.modules, 'eager import'; print('ok')"` → exit `0`

### AC4 — 默认值仍是 legacy
`cd backend && .venv/bin/python -c "from src.core.config import get_config; assert get_config().pipeline.agent_runtime == 'legacy'; print('ok')"` → exit `0`

### AC5 — legacy 行为不变（回归门槛）
`cd backend && .venv/bin/python -m pytest tests/core/source_fact_chain tests/runs tests/pipeline tests/core/agents/acquisition tests/core/agents/parsing tests/core/agents/standardization -q --ignore=tests/pipeline/test_extract_skill.py` → 全绿，且数量不少于改动前基线（基线值记录在 EVIDENCE）

### AC6 — shadow 模式可观测且不改变结果
新增单测：给定 stub agent 与 stub legacy，`shadow` 返回 legacy 结果、写出 `shadow_report.json`、`equal` 字段正确；`agentscope` 返回 agent 结果。测试必须能区分三种模式（mutant 检查：把 `shadow` 行为改成"返回 agent"时测试失败）

### AC7 — Phase 3 拆分保住 21 个既有用例
- `tests/core/source_fact_chain` 21 用例全绿（import 路径改为 `skills.extraction` / `skills.translation`）
- `skills/extraction` 暴露 `SourceFactChainService`（对外 API 不变：`build_document/run/run_async/write_outputs/project_dual_result/supported_fact_count`）
- `skills/translation` 暴露独立 translate 调用（输入：已验证事实 + 原文 span；输出：展示字段英文视图），并有单测证明它与抽取阶段解耦（给定事实即产出，不再触发抽取）

### AC8 — 层间边界
- 既有 `test_skills_do_not_import_database_clients` 自动覆盖新包（遍历 `skills/`），必须全绿
- 新增：`skills` 不得 import `src.dao`（同上测试已含）、不得 import `src.pipeline.graph`（graph 依赖 skills，不可反向）

### AC9 — CI
推送后 CI 9/9 绿（ruff / mypy / backend unit tests / frontend / rust / secret scan）

## 4. 负向约束（必须幸存）

- **默认行为不变**：`legacy` 下所有 phase 输出与 `e27aaa81f` 一致；不得改 `core/agents/**` 的逻辑。
- **不新增依赖**：`agentscope==2.0.12` 已在 `pyproject.toml`；不引入新包。
- **不切默认**：本 SPEC 不把任何 phase 的默认值改成 `agentscope`。
- **不删除测试**：Phase 3 的 21 用例只允许改 import 路径，断言不动。
- **工具/mcp 仍留在 core**：不把任何确定性实现搬进 `pipeline/skills`。
- 不触碰 `src/runs/**`、`src/api/**`（除必要 import 路径外零改动）。

## 5. 失败模式与对策（Tier 3）

| 失败模式 | 对策（可执行） |
|---|---|
| LLM 非确定性导致产出漂移 | 默认 `legacy`；`shadow` 记录 hash 比对；不相等不允许进入 P1 |
| 采集/解析 agent 误选工具（跳过 MinerU / 绕过 SDK） | 工具白名单 + 工具只读；单测对每个工具做 mock 断言调用序列 |
| 双跑成本翻倍 | `shadow` 默认关闭；报告记录调用次数与 token |
| Phase 3 拆分破坏 runner 语义（窗口/预算/复用键） | 21 用例 + `reuse_blocker`/prompt 版本键的既有断言不变 |
| 影子报告本身说谎（fail-open） | 报告由同一函数写；单测构造"不等"输入，断言 `equal=false` 且测试失败路径可达 |
| agentscope 被意外急切导入，legacy 环境崩 | AC3 断言 `sys.modules`；CI 与本地各跑一次 |

## 6. Setup 计划

- **隔离**：无 worktree（本地 `.venv` 是唯一能跑 legacy 套件的环境；worktree 会缺它）。
- **新依赖**：无（agentscope 已声明；本地 `.venv` 未装，agent 相关单测仅能在 CI 跑，见 §7）。
- **工具**：`.venv/bin/python`、`git`、`rg`、`pytest`；`ruff`/`mypy` 由 CI 承担。
- **git**：① SPEC 单独提交；② P0 实现一个 `refactor(pipeline):` 提交；③ EVIDENCE 一个 `docs:` 提交；④ 推送 `dev` 触发 CI。

## 7. 已知限制（将写入 EVIDENCE）

- 本地 `.venv` 无 agentscope：`shadow`/`agentscope` 两个模式的真实 LLM 路径只能在 CI 跑；
  本地用 stub 版本验证三种模式的分支逻辑，EVIDENCE 会明确区分「stub 验证」与「CI 真依赖验证」。
- 采集/解析/标准化 agent 的 LLM 收益无法量化，影子 diff 是唯一准入判据；本 SPEC 不承诺切默认。
- Phase 5（review）不在范围。

## 8. 交付物

1. `src/pipeline/skills/{acquisition,parsing,extraction,translation,standardization}/`
2. `fact_chain` 拆分后的 `extraction` + `translation`
3. `graph/phases/*.py` 改为经 skill 门面调用
4. `shadow_report.json` 写入器 + 单测
5. `tests/pipeline/test_agent_runtime_modes.py`（三模式 + 报告诚信）
6. EVIDENCE
