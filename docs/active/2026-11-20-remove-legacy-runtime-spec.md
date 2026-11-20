# SPEC — 删除 legacy 运行时开关与影子机制（old-coder, Tier 3）

**Status:** awaiting approval
**Created:** 2026-11-20
**Tier:** 3（删除回退路径：行为从"确定性兜底"变为"只有 agent 路径"）
**Source state:** `dev` @ `35a802eb9`
**Author:** agent（自主起草；批准后才进入实现）

---

## 0. 风险声明（必须随批准一起阅读）

删掉 legacy 后：

1. **没有确定性兜底**。采集/解析/标准化每次运行都要经一次 AgentScope 调用；模型不可用、
   配额耗尽、输出非 JSON 都会让该 phase 失败（按现有错误分类重试或终止），而不是回退到直连 core。
2. **成本与延迟**：每个 run 新增 3 次 LLM 调用（acquisition / parsing / standardization），
   加上 Phase 3 已有的 extract/verify/translate。
3. **行为未经影子验证**：P0 的 shadow 只有 stub 证据，没有真实语料对比。删掉 legacy 意味着
   承认"agent 输出即最终输出"，没有历史对照可回溯。
4. 若这些不可接受，应保留 `shadow` 一个版本先攒证据再删；本 SPEC 的选择是直接删。

## 1. 删除清单

| 位置 | 动作 |
|---|---|
| `core/config.py` | 删 `PipelineConfig.agent_runtime`、`pipeline_agent_runtime` 字段与映射 |
| `pipeline/skills/runtime/modes.py` | 删除整个文件（ShadowRow / record / run_phase_*） |
| `pipeline/skills/{acquisition,parsing,standardization}/service.py` | 删除 `run_phase_async` 分支，直接调用 agent；保留 `agent`/`agent_factory` 构造参数供测试注入（不是 legacy，是测试接缝） |
| `pipeline/skills/extraction/service.py` | `_build_provider` 删掉 mode 判断：extract 恒走 `ExtractSkill`，verify/translate 走 `ChatModelProvider`（原 `LangChainChainProvider` 改名） |
| `pipeline/skills/extraction/extract.py` | 删 `StageRouterProvider` 与 `ShadowStats`（双跑/统计），只保留 `ExtractSkill` |
| `tests/pipeline/test_agent_runtime_modes.py` | 删除；替换为 `tests/pipeline/test_skill_single_path.py`（单一路径 + 失败传播 + 注入） |
| 其余引用 | `tests/api/test_pipeline_api.py`、`tests/runs/test_phase_4_adapter.py` 中 modes 相关断言改为新行为 |

`LangChainChainProvider` 改名为 `ChatModelProvider`：它是 verify/translate 的模型客户端，
不是"旧路径"。**不做别名**，全仓一次改到位。

## 2. 目标行为

每个 phase 只有一条路径：

```
adapter → skill → agent(AgentScope) → tools(core/shared/tools 或 core/agents/*)
```

- `acquisition/parsing/standardization`：agent 调一次工具、回显 JSON，skill 校验成 pydantic 模型并返回。
- `extraction`：extract 走 `ExtractSkill`；verify/translate 仍由同一 runner 用 `ChatModelProvider` 调模型
  （这两段尚未 agent 化，记为已知限制，不是回退路径）。
- 任何 agent 错误：不吞、不回退，直接向上抛；adapter 现成的 `classify_phase_error` 决定重试/终止。

## 3. 验收场景（可执行）

### AC1 — 开关与影子机制不存在
- `rg -c 'agent_runtime|pipeline_agent_runtime|ShadowRow|run_phase_sync|run_phase_async' backend/src backend/tests backend/config -g '!*.md'` → 无输出（0）
- `test -f backend/src/pipeline/skills/runtime/modes.py` → 不存在

### AC2 — 配置不再有该字段
`cd backend && .venv/bin/python -c "from src.core.config import get_config; c=get_config(); assert not hasattr(c.pipeline,'agent_runtime'); print('ok')"` → exit `0`

### AC3 — 单一路径：skill 直接调用 agent
- `rg -c 'run_phase_async|run_phase_sync' backend/src/pipeline/skills` → 0
- 每个 skill 的公开方法内恰好一次 `await self._agent...`（以源码 grep 断言：`rg -c 'await self\._agent' <file>` == 1，共 3 个文件）

### AC4 — 失败传播
新增 `tests/pipeline/test_skill_single_path.py`：
- 注入会抛异常的 agent → skill 抛出，异常类型/信息保留（不被吞、不再返回 legacy 值）
- 注入正常 agent → 返回值经 pydantic 校验
- 注入 agent 返回非法 JSON → `ValidationError` 向上抛

### AC5 — 现状套件仍绿
`cd backend && .venv/bin/python -m pytest tests/core/source_fact_chain tests/pipeline tests/runs tests/api/test_wiring_config.py --ignore=tests/pipeline/test_extract_skill.py -q`
→ 全绿；用例数 = P0 基线 256 − 8（删除 modes 用例）+ 新增用例数。

### AC6 — 改名彻底
`rg -c 'LangChainChainProvider' backend/src backend/tests` → 0；`rg -c 'ChatModelProvider' backend/src` ≥ 1。

### AC7 — CI 9/9 绿（ruff / mypy / backend unit tests / frontend / rust / secret scan）。

## 4. 负向约束

- 不改 `core/shared/tools/fact_chain` 与 `core/agents/*` 的业务逻辑。
- 不删 `agentscope` 依赖；不新增依赖。
- 不删除任何与"单路径"无关的测试；`test_extract_skill.py` 的断言不动（只可能改 import）。
- 不保留 `agent_runtime` 的兼容字段/别名/警告分支。
- 不改 graph 拓扑、状态契约、错误分类。

## 5. Setup 计划

- **隔离**：无 worktree（本地 `.venv` 是唯一能跑套件的环境）。
- **新依赖**：无。
- **git**：① SPEC 提交；② 实现一个 `refactor(pipeline):` 提交；③ EVIDENCE 提交；④ 推送 `dev` 触发 CI。

## 6. 已知限制（将写入 EVIDENCE）

- 本地 `.venv` 无 agentscope：agent 真路径只能在 CI 的依赖环境构造；本地用注入的 fake agent 验证分支与失败传播。
- verify/translate 两段仍是 provider 调用，未 agent 化；本 SPEC 删的是"开关"，不是这两段的实现方式。
- 真实 LLM 影子数据仍为零；删掉 legacy 后没有对照基线，回滚只能 revert 本提交。
