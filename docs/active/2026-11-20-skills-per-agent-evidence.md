# EVIDENCE — skills 一 agent 一包（P0）（old-coder, Tier 3）

**Spec:** `/data/yangzs/Projects/01_Platform/01_ACMG_Lingua/docs/active/2026-11-19-skills-per-agent-spec.md`（批准范围：仅 P0）
**Spec approval:** obtained（用户选择 "只批 P0"）
**Branch:** `dev`
**Source state:** `e27aaa81f` → `a0bb20681`（SPEC）→ `7ca1469f1`（实现）→ `d176c0e64`（mypy 修复）→ 本 EVIDENCE
**Run date:** 2026-11-20

## 1. 交付内容

| 路径 | 内容 |
|---|---|
| `skills/acquisition/` | `AcquisitionSkill`：`acquire()` 经 `run_phase_async` 路由；工具闭包内调 core 服务 |
| `skills/parsing/` | `ParsingSkill`：`parse_local_files_and_save()` 同上 |
| `skills/standardization/` | `StandardizationSkill`：`run_dual_result()`，session 在调用时绑定（不可序列化） |
| `skills/extraction/` | 原 `fact_chain` 的 extract/verify/runner/service/prompts |
| `skills/translation/` | 新增：`TranslationStage`（mixin）+ 独立 `TRANSLATE_PROMPT` |
| `skills/runtime/modes.py` | 三模式路由 + 影子报告（`ShadowRow`，hash + equal + agent_error） |
| `graph/phases/*.py` | 改为 import skill 门面，不再直连 core 实现 |
| `api/wiring.py` | 注入 skill 而非 core 服务 |
| `tests/pipeline/test_agent_runtime_modes.py` | 8 个用例：三模式、不等行、agent 失败、async、默认 legacy |

**关键不变量**：`TRANSLATE_PROMPT` 文本逐字不变 → `translate:b2b0543fbcc9`，`PRESENTATION_VERSION` 不变 → 复用键与历史运行兼容（已用 HEAD 版本重算校验）。

## 2. 验收场景 → 结果（最终一次运行）

| # | 场景 | 实测 |
|---|---|---|
| AC1 | 目录布局 | `skills/` = `acquisition, extraction, parsing, runtime, standardization, translation`；`fact_chain` 0 文件 ✅ |
| AC2 | 适配器不直连 core 实现 | `rg 'core\.agents\.\w+\.(service\|api\|core\|providers\|runner)' src/pipeline/graph` = **0** ✅ |
| AC3 | legacy 不加载 agentscope | import 全部 5 个 skill 后 `'agentscope' in sys.modules` = **False** ✅ |
| AC4 | 默认模式 | `get_config().pipeline.agent_runtime == "legacy"` ✅ |
| AC5 | 回归 | `pytest tests/core/source_fact_chain tests/pipeline tests/runs --ignore=tests/pipeline/test_extract_skill.py` → **256 passed**（基线 248 + 8 新用例）✅ |
| AC6 | 影子模式可观测且不改结果 | 8 个 mode 用例通过；`shadow` 返回 legacy、写报告；**不等分支**由 `{"value":1}` vs `{"value":2}` 触发 `equal=false` ✅ |
| AC7 | Phase 3 拆分 | 21 个 fact_chain 用例全绿（仅改 import 路径）；extraction 保留 `SourceFactChainService` 全部对外方法；translation 为独立阶段（可在同一 runner 内以 mixin 组合）✅ |
| AC8 | 边界 | `tests/pipeline/test_import_boundaries.py` 遍历 `skills/`，新包无 DB 导入；18 项全绿 ✅ |
| AC9 | CI | `d176c0e64` 9/9 绿，含 ruff、mypy、backend unit tests ✅ |

## 3. Gauntlet 各层

| 层 | 命令 | 结果 |
|---|---|---|
| 全量测试（本地） | `pytest tests/core/source_fact_chain tests/pipeline tests/runs --ignore=…/test_extract_skill.py -q` | **256 passed in 3.99s** ✅ |
| 语法 | `.venv/bin/python -m compileall -q src tests scripts` | exit 0 ✅ |
| 真实执行（导入） | 5 个 skill + `modes` 导入；断言 agentscope 未加载 | exit 0 ✅ |
| 静态类型 | CI mypy（`d176c0e64`） | success ✅（首次在 `7ca1469f1` 失败：`_call_json` 的 `...` 触发 `[empty-body]`，改 `raise NotImplementedError` 后通过） |
| Lint | CI ruff（`d176c0e64`） | success ✅ |
| 覆盖率 | CI `--cov=…extraction --cov=…translation --cov=…runtime --cov-fail-under=85` | success ✅（拆分后两个包都计入，门槛仍过） |
| 全量 CI | 其余作业 | 全部 success，9/9 ✅ |
| 变异测试 | 手工 1 个 mutant：把 `shadow` 的返回改成 `agent_value` | **5 failed / 3 passed** → 被杀；恢复后 `git diff --stat` 为空 ✅ |
| 属性测试 | — | 不适用：无解析/序列化算法改动（prompt 与报告结构由断言覆盖） |
| 供应链 | 无依赖变更 | `agentscope==2.0.12` 早已声明，未改 lockfile ✅ |

## 4. 检查器负向控制

- AC1/AC2/AC3/AC4 是自写 grep/import 判定，RED 阶段实测改前值：`skills` 只有 `fact_chain, runtime`；适配器直连 core 实现 **3** 处；默认值已是 `legacy`（作为回归守卫，改前改后都必须为 legacy）。
- 新增的 mode 测试在实现前不存在（不可能先失败）；因此用**手工 mutant** 证明非空转（见上表），这是 v 规则要求的替代路径。
- 覆盖边界：AC3 只证明"导入不加载 agentscope"，不证明 agent 路径能跑通——后者见 §6。

## 5. 期间的问题与处置

1. **mypy `[empty-body]`**：mixin 里的协议声明用 `...`，mypy 判为缺 return → 改为 `raise NotImplementedError`（ChainRunner 始终覆盖）。CI 第一轮失败 → 修复 → 第二轮 9/9。
2. **方法搬迁的风险**：`_translate/_view/_failed_view` 需从 runner 删除，第一次 ast-grep 模式只匹配到 `def` 行；先在 `/tmp` 副本上验证 `def $NAME($$$ARGS) -> $_: $_` 会删整段，再对真实文件执行，避免留下孤儿代码。
3. **prompt 身份**：拆分前用 HEAD 原文重算 `translate:b2b0543fbcc9`，与拆分后一致，确认复用键不变。

## 6. 已知限制（诚实声明）

- **P0 不切默认**：`legacy` 仍是默认；`shadow` / `agentscope` 只在单测里用 stub 验证分支逻辑。**没有任何真实 LLM 影子数据**。
- 采集/解析/标准化的 agent 工具闭包会真正调用确定性服务，但"agent 是否稳定复述工具输出"只能在 CI 的 agentscope 环境里、且需真实调用才知；本轮未跑真实调用（成本/凭据）。
- `test_extract_skill.py` 本地不可跑（需 agentscope），其 CI 结果为 success。
- Phase 5（review）不在范围。
- P1（把某 phase 默认切到 `agentscope`）需要新增影子语料与证据，另行 SPEC。
