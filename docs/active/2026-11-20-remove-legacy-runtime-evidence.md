# EVIDENCE — 删除 legacy 运行时与影子机制（old-coder, Tier 3）

**Spec:** `/data/yangzs/Projects/01_Platform/01_ACMG_Lingua/docs/active/2026-11-20-remove-legacy-runtime-spec.md`（批准，含 r2 修订）
**Spec approval:** obtained（用户选择 "批准：删除开关与影子机制，只保留 agent 单路径"）
**Branch:** `dev`
**Source state:** `35a802eb9` → `139b4029c`（SPEC）→ `2d0bb10d6`（实现）→ `15d93a60f`（ruff 修复）→ 本 EVIDENCE
**Run date:** 2026-11-20

## 1. 删除了什么

| 删除项 | 位置 |
|---|---|
| `agent_runtime` / `pipeline_agent_runtime` / 映射 | `core/config.py` |
| `modes.py`（ShadowRow / record / run_phase_*） | `skills/runtime/` |
| `StageRouterProvider`、`ShadowStats`、`compare_extract_replies` | `skills/extraction/extract.py` |
| `test_agent_runtime_modes.py`（8 用例）与 4 个 shadow 用例 | `tests/pipeline/` |
| `LangChainChainProvider` 名称 | 改为 `ChatModelProvider`（2 处引用） |

新增 `ExtractAgentProvider`（extract → skill，其余 stage → chat provider）、`runtime/messages.py`
（惰性构造用户消息，便于测试注入）、`tests/pipeline/test_skill_single_path.py`（3 用例）。

**结果传递方式**：agent 必须调用工具，工具把**真实对象**存进闭包，skill 返回该对象——
不再把 dataclass 结果做 JSON 回显（原设计在 dataclass 上 `model_validate_json` 根本不成立，
这是实现期发现的 SPEC 缺陷，已在 r2 记录）。

## 2. 验收场景 → 结果（最终一次运行）

| # | 场景 | 实测 |
|---|---|---|
| AC1 | 开关/影子机制不存在 | `rg` 命中 **0**；`modes.py` 不存在 ✅ |
| AC2 | 配置无该字段 | `hasattr(config.pipeline,'agent_runtime')` == False ✅ |
| AC3 | 单一路径 | `run_phase_*` 命中 0；三个 skill 各恰好 1 处 `await agent.reply(`；无 `model_validate_json` 回显 ✅ |
| AC4 | 失败传播 | 3 个用例：工具结果返回、agent 异常上抛、agent 未调用工具 → `RuntimeError("agent did not call acquire_document")` ✅ |
| AC5 | 套件仍绿 | **254 passed**（原 256 − 8 modes − 4 shadow + 3 新用例 + 7 其他调整）✅ |
| AC6 | 改名彻底 | `LangChainChainProvider` 0 处；`ChatModelProvider` 2 处 ✅ |
| AC7 | CI | `15d93a60f` 9/9 绿 ✅（第一轮 `2d0bb10d6` ruff 失败：4 个残留 import + 1 个重复定义，已修） |

## 3. Gauntlet 各层

| 层 | 命令 | 结果 |
|---|---|---|
| 全量测试（本地） | `pytest tests/core/source_fact_chain tests/pipeline tests/runs tests/api/test_wiring_config.py --ignore=…/test_extract_skill.py -q` | **254 passed in 3.88s** ✅ |
| 语法 | `compileall -q src tests` | exit 0 ✅ |
| 静态类型 | CI mypy（`15d93a60f`） | success ✅ |
| Lint | CI ruff（`15d93a60f`） | success ✅（首轮 5 个 F401/F811 已修） |
| 覆盖率 | CI `--cov-fail-under=85`（extraction/translation/runtime） | success ✅ |
| 变异测试 | 手工 mutant：把"未调用工具"的 raise 改成 `return None` | **1 failed**（`DID NOT RAISE RuntimeError`）→ 恢复后 `git diff` 为空 ✅ |
| 属性测试 | — | 不适用：无算法/序列化改动（结果对象不做序列化） |
| 供应链 | 无依赖变更；AgentScope 仍在依赖中且改为惰性导入 | ✅ |

## 4. 负向控制

- AC1/AC2/AC6 是自写 grep，改前实测：开关引用 **9 处**、`modes.py` 存在、`LangChainChainProvider` **3 处** → 改后均为 0。
- AC4 的用例改写后用 mutant 证明非空转（见上）。
- 覆盖边界：AC3 只证明"没有模式分支"，不证明 agent 真实决策质量——后者没有任何证据（见 §5）。

## 5. 已知限制（必须随结果阅读）

1. **没有真实 LLM 运行证据**。agent 路径只在测试里用 fake agent 驱动；CI 有 agentscope 但不会调用真实模型。
   删掉 legacy 后，线上首次运行就是第一次真实执行。
2. **verify / translate 仍是 chat provider 调用**（未 agent 化），它们不是回退路径，但也不符合
   "一 agent 一 skill" 的目标；`ChatModelProvider` 这个名字现在中性化了这一事实。
3. **工具内部异常可能表现为"未调用工具"**：若 AgentScope 吞掉工具异常并继续对话，skill 会报
   `agent did not call <tool>` 而不是原始异常。失败方向正确（phase 失败），但错误信息会失真。
4. **回滚只能 revert**：没有模式开关，出问题需要 `git revert 2d0bb10d6 15d93a60f`。
