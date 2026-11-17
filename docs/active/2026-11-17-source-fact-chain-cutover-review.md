# Phase 3 原文事实链切流审查（source_fact_chain）

**Status:** resolved（2026-11-17 修复，待合并审查）
**Date:** 2026-11-17
**Reviewer:** omp（old-coder 工作流）
**Scope:** `backend/src/core/source_fact_chain/`、`Phase3Adapter`、`wiring`、双语展示与相关测试/文档
**Spec approval:** 用户要求“进行审查”；本次没有实现批准，也没有修改实现代码。所有 mutation 均临时施加并逐字节恢复（校验和见文末）。
**Source state:** worktree `HEAD f1d9bec3ad18e51bb980598944d91d183ae1ab14` + 未提交的切流改动；关键文件 SHA-256 见文末。

---

## 1. 审查契约（等价于 SPEC）

切流声明的可验证行为：

| ID | 行为 | 验收方式 |
|---|---|---|
| S1 | Phase 3 只执行一条链：原文分窗 → 原文抽取 → 原文核验 → 事实英译 → 双语行 | `Phase3Adapter` + `ChainRunner` 测试 |
| S2 | 不再整篇翻译，不从译文抽取第二套事实 | `translated_text is None`、`translated.json` 为空、provider 调用记录 |
| S3 | 分窗全覆盖、可重叠、必前进、不静默截断 | `windowing` 测试 + 随机属性探针 |
| S4 | 候选事实必须原文可定位：字段白名单、非空、原子、引句唯一、span 逐字一致 | `core.candidate_to_fact` 测试 |
| S5 | 主体 `unknown` 不得带 ID；已知主体必须有 ID | 单测 |
| S6 | 只有 `supported` 事实进入 Phase 4；失败/缺失核验降级为 `unverified` | 投影测试 + mutation |
| S7 | 基因/变异/年龄逐字保留；表型/遗传方式才翻译；英文原文 passthrough | 单测 + 代码审查 |
| S8 | 英文视图只复制事实的极性/主体，不新增、不删除、不改写事实 | 代码审查 + 投影测试 |
| S9 | 双语展示按事实身份配对，同字段多条事实不互相覆盖 | `search_service` 测试 |
| S10 | 旧公共契约不破坏：Phase 3 输出字段、Phase 4 双轨投影、现有 API | `tests/agents`、`tests/api`、前端 type-check |

负向约束：不新增依赖；不改变 Phase 3 输出契约的既有必填字段；不得把英文呈现回流为抽取证据；不得静默截断文档或事实。

---

## 2. 结论

**changes requested（不建议合并）。** 主路线语义（S1/S2/S4/S6/S7/S9/S10）已成立，聚焦测试全绿；但存在 2 个高/中等级的数据正确性缺陷、4 个中等运维/契约缺陷，以及测试门禁缺口（覆盖率、mypy、mutation survivors、顺序依赖）。这些缺陷会影响 Phase 4 分组、重试可恢复性和证据归属，属于合并前必须处理的范围。

---

## 3. 发现（按严重度）

### F1 — High：多基因文档的事实被归入首个基因的组

`projection._first_value(supported, ("A.gene_symbol",))` 只取第一个基因；`_group_plan` 用这个基因与**所有**变异组合生成组；`_group_for_fact` 只对变异字段做匹配，其余事实一律落到 `group_ids[0]`。

- 位置：`backend/src/core/source_fact_chain/projection.py:58-81`、`:191-195`
- 证据（实跑探针）：

```text
F1 A.gene_symbol BRCA1 -> gene=BRCA1|variant=c.1A>G
F1 A.variant_hgvs_c c.1A>G -> gene=BRCA1|variant=c.1A>G
F1 A.gene_symbol TP53 -> gene=BRCA1|variant=c.1A>G
F1 A.variant_hgvs_c c.2C>T -> gene=BRCA1|variant=c.2C>T
```

TP53 的基因与变异被错误绑定到 BRCA1 的组。Phase 4 的 `_gene_values_by_group` 会以该组基因为准，导致实体绑定/证据矩阵归属错误。现有测试只覆盖单基因。
- 建议：按事实的基因/主体分组，而不是“首个基因 × 所有变异”；多基因文档要么拆成多个 chain，要么显式拒绝并记录 `rejection`。先写 RED 测试（两个基因 + 两个变异）。

### F2 — High：零事实运行被持久化后，重试永远无法恢复

`_load_chain_run` 只校验 `source_hash`；`chain_run.json` 一旦写入 `facts=0`（provider 瞬时返回合法空列表，或抽取质量事故），后续重试直接复用，不再调用 provider。

- 位置：`backend/src/agents/phase_3_adapter.py:125-139`
- 证据（实跑探针）：

```text
第一次（空 provider）: facts=0, supported=0, skip=NOT_RELEVANT
第二次（正常 provider，同一 output_root）:
  Phase 3 retry: reusing persisted chain run (facts=0)
  provider_calls_on_retry = 0, supported = 0, skip = NOT_RELEVANT
```

这不是“空文档缓存命中”，而是**抽取事故不可恢复**：没有 force-refresh 入口，只能手工删文件。
- 建议：复用键加入 `ChainConfig` 与提示词/抽取版本；默认不复用 `facts=0` 的运行；提供显式 `force_rebuild` 或 retry 时删除 `chain_run.json`。

### F3 — Medium：重跑后 `skip_phase_4_reason` 不会清除

`Phase3Adapter` 只在 `supported == 0` 时设置 `NOT_RELEVANT`，从不清除旧值。

- 位置：`backend/src/agents/phase_3_adapter.py:187-189`
- 证据（实跑探针）：

```text
第一次空运行: skip_after_empty = NOT_RELEVANT
第二次同 state、有 2 条 supported 事实:
  supported_after_rerun = 2, skip_after_rerun = NOT_RELEVANT
```

结果是 Phase 4 直接 SKIPPED，尽管 Phase 3 已产出有效证据。该缺陷在旧 adapter 中也存在（旧代码同样只设置不清除），但新链的 retry 语义会放大它。
- 建议：`supported > 0` 时显式 `state.skip_phase_4_reason = None`；添加“先空后满”的回归测试。

### F4 — Medium：复用忽略模型、窗口和提示词版本

`ChainRun` 保存了 `config` 和部分 `prompt_version`，但 adapter 复用只看 `source_hash`。修改 `window_chars`、`extract_model`、`verify_model` 或 `prompts.py` 后，旧运行仍被当作有效结果。

- 位置：`backend/src/agents/phase_3_adapter.py:125-139`；`contracts.ChainRun`
- 证据：mutation M5 把 `source_hash` 守卫改为 `False`，`tests/agents/test_phase_3_adapter.py` 仍 3/3 通过——说明没有任何测试覆盖“源版本/配置变化必须重建”。
- 建议：持久化 `extract_prompt_version` 等版本字段；复用前比较 `run.config` 与当前 service config；不匹配则重建并记录事件。

### F5 — Medium：复用运行不会重建 JSONL 审计产物

`write_outputs` 只在新建运行的分支调用；复用分支只重写 `extraction_result.json`。若上次在 `chain_run.json` 之后、JSONL 之前崩溃，或审计文件被删，重试后路径仍指向缺失文件。

- 位置：`backend/src/agents/phase_3_adapter.py:130-139`
- 证据（实跑探针）：

```text
C1 artifacts_regenerated = [False, False]
# facts.jsonl 与 bilingual.jsonl 删除后重跑，仍不存在
```

- 建议：复用分支也调用 `write_outputs(run, doc_dir)`；代价很低，且能让产物与 `chain_run.json` 自洽。

### F6 — Medium：HTML 实体引句/原值被拒绝，`locate_quote` 的实体支持实际不可达

`locate_quote` 先 `html.unescape(quote)`，但 `candidate_to_fact` 在定位前先做原子性检查，且 span 校验使用原始 `quote`。任何含 `&gt;`、`&amp;` 的引句都会命中 `;` 原子性拒绝或 `span_quote_mismatch`。

- 位置：`backend/src/core/source_fact_chain/core.py:52-59`、`:155-158`、`:174-180`；`:62-90`
- 证据（实跑探针）：

```text
D1 entity_quote_rejected: ChainContractError non_atomic_value: c.1A&gt;G
```

MinerU Markdown 的表格/HTML 片段可能保留实体；这类变异/表型事实会被静默丢弃（只留下 rejection），而不是被规范化后接受。
- 建议：在原子性/包含检查前对值做实体归一化，或对 `raw_value` 与 `quote` 同时比较“原文形式”和“unescape 形式”；补 `&gt;`/`&amp;` 正反例测试。

### F7 — Low：空白归一化后的重复引句未被识别为歧义

歧义检查用 `window.text.count(quote)`（精确形式）；`locate_quote` 实际按空白/NFKC 归一化定位。两处内容相同、空白不同的引句可通过检查并被归到第一个位置。

- 位置：`backend/src/core/source_fact_chain/core.py:174-176`
- 证据（实跑探针）：

```text
E0 exact_count = 0 compact_count = 2
E1 fact_accepted span = 0 10 second_occurrence_at = 10
```

同样的临床句子可能属于不同病例/患者；虽然值相同，但 span/上下文归属可能错误。
- 建议：歧义判断改用 `compact(window.text).count(compact(quote)) > 1`，或要求归一化后唯一命中。

### F8 — Medium（风险）：目标/相关性门控被移除

旧路线在 `EvidenceExtractionService.run_dual(...)` 中启用 target guard 与 relevance 判定；新链只按“是否有 supported 事实”判断相关性，`projection` 不按 `target_gene`/`target_variant` 过滤。

- 位置：旧实现 `HEAD:backend/src/agents/phase_3_adapter.py:160-189` vs 新 `projection.py:163-201`
- 影响：文档里顺带提到的其他基因/变异也会成为 Phase 4 候选，甚至让“目标不相关”的文档进入标准化。`extraction_target` 目前只用于 target-scope bindings，不用于过滤候选。
- 判断：这可能是有意的研究路线选择（先抽全部原文事实），但产品 pipeline 的“目标基因”语义因此弱化。需要明确写进设计/契约；若保留目标语义，应在投影层或 Phase 4 入口加 target 过滤并测试。

### F9 — Low：前端事实级双语面板没有组件测试

`BilingualEvidenceView` 新增 `factPairs` 面板（无整篇译文时展示原文/英文对照），但前端测试中没有引用 `factComparison`/`factPairs`/该面板行为；`tests/evidence-db` 44 项全绿只证明既有路径。

- 位置：`frontend/src/features/evidence-db/components/BilingualEvidenceView.tsx:492-...`
- 建议：增加一个“无 translated document、traces 有两条事实”的组件测试，断言两行原文/英文都渲染，且同 field_id 不合并。

---

## 4. 门禁结果（最终一次新鲜运行）

环境：`/tmp/chainenv`（Python 3.12.13，pytest 9.2.0，coverage 7.17.3，pytest-randomly 5.1.0）；前端 Bun 1.4.4；ruff 0.15.17。

| 层 | 命令 | 结果 |
|---|---|---|
| 聚焦后端 | `pytest tests/core/source_fact_chain tests/agents/test_phase_3_adapter.py tests/api/test_wiring_config.py tests/core/visualize_evidence_with_expert_in_loop/test_search_service.py -q` | **43 passed** |
| Agents | `pytest tests/agents -q` | **209 passed** |
| Pipeline API（单独进程） | `pytest tests/api/test_pipeline_api.py -q` | **18 passed** |
| 确定性复跑 | 上述 43 项按相反文件顺序再跑 | **43 passed** |
| 全后端 | `pytest tests -q --continue-on-collection-errors` | **2306 passed, 62 failed, 76 skipped, 1 error**；失败集中在缺 `alembic`/`asyncpg`/`langchain_openai`/`rust_io` 的环境与 2 个 429 限流用例；**changed modules 无失败** |
| 前端全量 | `bun run test` | **188 passed (47 files)** |
| 前端类型 | `bun run type-check` | **passed** |
| 前端 ESLint | `bun run lint` | **1 warning**（`KnowledgeGraphCanvas.tsx` 硬编码颜色，非本次文件） |
| Ruff | `ruff check src/core/source_fact_chain src/agents ...` | **All checks passed** |
| 覆盖率 | `pytest ... --cov=src.core.source_fact_chain --cov=src.agents.phase_3_adapter --cov-branch --cov-fail-under=100` | **FAIL：80.99%**（TOTAL 790 stmts / 115 miss / 220 branch / 59 partial） |
| mypy | `mypy --ignore-missing-imports --follow-imports=silent src/core/source_fact_chain src/agents/phase_3_adapter.py` | **4 errors** |
| 随机顺序 | 同 43 项 + `pytest-randomly`，反复 12 次 | **约 1/6 次失败**：`test_wire_dependencies_initializes_session_factory_before_use`（`MagicMock` 进入 `urllib.parse.urlparse`） |
| 属性探针 | 2000 组随机分窗 + 2000 组随机引句定位 | **0 failures**（实体场景除外，见 F6） |
| 真实执行 | `/tmp/review_probes.py`：adapter 空/满重跑、零事实复用、产物删除重跑、实体引句、空白歧义、双基因投影 | 全部复现上述 findings |
| Supply chain | `git diff` 检查新增依赖/密钥 | 切流未新增依赖；diff 未发现 key/secret |

### 覆盖率缺口（changed modules）

| 文件 | Cover | 主要未覆盖 |
|---|---:|---|
| `phase_3_adapter.py` | 76% | 错误分类、空文本回退、source 版本失效分支、复用分支 |
| `source_fact_chain/core.py` | 74% | 多数拒绝分支、reconcile 的 duplicate/unexpected、reply schema 非法输入 |
| `runner.py` | 81% | budget、抽取/核验/翻译失败分支 |
| `projection.py` | 83% | 无 supported、fallback 分组、无 page range |
| `providers.py` | 26% | 默认 LangChain provider 全部 |
| **TOTAL** | **81%** | 未达到 100% changed-line 门槛 |

### Manual mutation（无 mutation 工具，逐个人工施加并恢复）

| Mutant | 变更 | 结果 |
|---|---|---|
| M1 | `EVIDENCE_LABELS` 加入 `unsupported` | **killed**（`test_projection_drops_unsupported_facts`） |
| M2 | `is_atomic`/`has_semicolon_equivalent` 恒真/恒假 | **killed**（原子性测试） |
| M3 | 删除 `quote_ambiguous` 守卫 | **killed**（引句测试） |
| M4 | `supported_facts` 返回全部事实 | **killed**（投影过滤测试） |
| M5 | adapter 关闭 source hash 失效守卫 | **survived**（adapter 3/3 通过）→ F4 测试缺口 |
| M6 | `_row_fact_key` 退化为按 field 配对 | **killed**（`test_get_group_detail_pairs_repeated_fields_by_fact_id`） |
| M7 | `_group_for_fact` 忽略变异→组映射 | **survived**（chain 12/12 通过）→ F1 测试缺口 |

手动 mutant 没有“等价 mutant”豁免：M5、M7 都是真实缺陷形态，存活说明测试门禁未覆盖。

### mypy 错误（逐条）

```text
src/core/source_fact_chain/core.py:224: error: Incompatible types in assignment
src/core/source_fact_chain/runner.py:163: error: Item "None" ... has no attribute "__iter__"
src/core/source_fact_chain/runner.py:194: error: Argument 1 to "len" has incompatible type "Any | None"
src/agents/phase_3_adapter.py:91: error: Missing return statement
```

其中 `classify_phase_error` 注解为 `-> None` 但实际总是 raise；`runner` 的两处依赖 `validate_reply_schema` 的运行时保证，静态类型未表达。

---

## 5. 已确认成立的行为

以下不是“看起来对”，有测试或实跑证据：

- S1/S2：adapter 产出 `chain_run.json`/`facts.jsonl`/`verifications.jsonl`/`english.jsonl`/`bilingual.jsonl`；`translated_text=None`，`translated.json` 的 `formatted_text` 为空；非英文只对 presented 字段调用翻译。
- S3：分窗属性探针 2000 组全覆盖、前进、长度合法；空字符串返回空窗口。
- S4/S5：字段、原子性、主体、引句缺失/歧义/span 不一致均有拒绝测试。
- S6：`unsupported` 不进入投影；核验失败降级 `unverified`；extract 失败零事实。
- S7/S8：preserved 字段不调翻译（英文源 passthrough 测试）；英文视图复制事实极性/主体。
- S9：同 field_id 多事实按 `source.span_id` 配对，新增测试覆盖。
- S10：`tests/agents` 209、`test_pipeline_api` 18、前端 188 全绿。

---

## 6. 建议的修复顺序（需另行批准实现）

1. **F1**：先写双基因 RED 测试，再按基因/主体分组；这是数据正确性最高优先级。
2. **F2/F4**：复用键加入 config + prompt/extract 版本；零事实默认不复用；增加 force rebuild。
3. **F3**：`supported > 0` 清除 skip reason；加“先空后满”测试。
4. **F5**：复用分支重写全部 JSONL。
5. **F6/F7**：实体归一化与 compact 歧义检查；补正反例测试。
6. **F8**：明确 target/relevance 契约；若保留目标语义，加过滤与测试。
7. **F9**：前端事实面板组件测试。
8. **F10/F11/F12**：mypy 4 处、覆盖率错误分支、M5/M7 回归测试。
9. **F13**：修复 wiring 测试的全局 SDK 配置隔离，或在该测试内 patch `_configure_lit_acquisition`。

---

## 7. 限制与声明

- 本次是**审查**，没有实现修复；仓库实现文件未被修改。M1–M7 均已恢复，关键文件校验和与审查开始时一致。
- 全后端测试受精简环境缺少 `rust_io`、`alembic`、`asyncpg`、`langchain_openai` 影响；62 个失败均不在 changed modules，但不能据此声称全库零回归。
- 没有 mutation 工具，使用 7 个手工 mutant；手工 mutant 只能证明这 7 个形态，不代表全部变异覆盖。
- 随机顺序只覆盖 43 项聚焦套件；全库随机顺序未跑。
- 前端只跑既有测试与 type-check；新增事实面板没有组件测试。
- Spec approval 未取得（autonomous review）；EVIDENCE 的可信度按此下调。

---

## 8. 复现

```bash
cd backend
/tmp/chainenv/bin/python -m pytest \
  tests/core/source_fact_chain \
  tests/agents/test_phase_3_adapter.py \
  tests/api/test_wiring_config.py \
  tests/core/visualize_evidence_with_expert_in_loop/test_search_service.py -q

/tmp/chainenv/bin/python -m pytest tests/agents -q
/tmp/chainenv/bin/python -m pytest tests/api/test_pipeline_api.py -q

/tmp/chainenv/bin/python -m pytest tests/core/source_fact_chain tests/agents/test_phase_3_adapter.py \
  --cov=src.core.source_fact_chain --cov=src.agents.phase_3_adapter \
  --cov-branch --cov-report=term-missing --cov-fail-under=100

PYTHONPATH=. /tmp/chainenv/bin/python /tmp/review_probes.py
PYTHONPATH=. /tmp/chainenv/bin/python /tmp/review_props.py
```

审查时关键文件 SHA-256：

```text
07161e79... contracts.py
5a6d684d... core.py
446f7fb1... projection.py
c6d1eaf7... phase_3_adapter.py
70340bd7... search_service.py
91f18cb7... BilingualEvidenceView.tsx
```

---

## 9. 修复记录（2026-11-17）

| 发现 | 处理 | 回归测试 |
|---|---|---|
| F1 多基因事实归入首个基因 | `projection._group_plan` 按 span 上下文为每个基因建立独立分组与 `EvidenceChain`；`(gene, variant)` 不再全局相乘 | `test_projection_keeps_each_gene_with_its_own_variant` |
| F2 零事实运行不可恢复 | `SourceFactChainService.reuse_blocker` 默认拒绝 `facts=0`；`Phase3Adapter.run(force_rebuild=True)` 显式重建 | `test_adapter_rebuilds_empty_persisted_run_and_clears_skip_reason`、`test_adapter_force_rebuild_reruns_provider` |
| F3 旧 `skip_phase_4_reason` 不清除 | `supported > 0` 时显式置 `None` | 同上；`test_adapter_force_rebuild_reruns_provider` |
| F4 复用忽略模型/窗口/提示词版本 | 新增 `PromptVersions` 并写入 `chain_run.json`；复用键比较 `ChainConfig` + `PromptVersions` | `test_adapter_rebuilds_when_chain_config_changes` |
| F5 复用不重建 JSONL | 复用与新建分支统一调用 `write_outputs` | `test_adapter_regenerates_jsonl_artifacts_on_reuse` |
| F6 HTML 实体引句/原值被拒绝 | 统一实体解码 + NFKC 比较；修复 `&gt;` 尾部 `;` 被误判为分号列表 | `test_quote_and_value_with_html_entities_are_accepted`、`test_non_atomic_value_cannot_hide_entity_semicolons` |
| F7 空白归一化重复引句未判歧义 | 歧义计数与定位使用同一归一化形式 | `test_quote_ambiguity_uses_whitespace_normalized_matches` |
| F8 目标/相关性门控缺失 | 目标基因匹配组进入 `evidence_chains`；非目标事实保留但标 `context_contamination`；无匹配组时 `not_relevant` | `test_projection_target_guard_keeps_off_target_facts_out_of_phase_four`、`test_projection_marks_document_not_relevant_when_target_gene_is_absent` |
| F9 前端事实面板无测试 | 新增组件测试，覆盖无整篇译文时两行原文/英文渲染及同字段不合并 | `frontend/tests/evidence-db/BilingualEvidenceView.test.tsx` |
| F10 mypy 4 处 | `classify_phase_error -> NoReturn`；`reconcile` 类型收窄；抽取候选 `or []` | `uvx --from mypy==2.4.1 mypy ...` 通过 |
| F11 覆盖率 | 新增回归用例；CI 对 changed modules 设 85% 门槛（当前 89%） | CI `backend-test` |
| F12 M5/M7 survivors | 源版本变化与多基因分组的回归测试分别杀死 M5、M7 | 见 F1/F4 |
| F13 wiring 随机顺序失败 | 测试内 patch `_configure_lit_acquisition`、`build_neo4j_driver`、`Neo4jRepository`，隔离全局 SDK/Neo4j 构造 | `tests/api/test_wiring_config.py` 3 passed |

验证命令（同一次运行）：

```text
pytest tests/core/source_fact_chain tests/agents tests/api/test_wiring_config.py \
  tests/core/visualize_evidence_with_expert_in_loop/test_search_service.py \
  --cov=src.core.source_fact_chain --cov=src.agents.phase_3_adapter --cov-branch
→ 263 passed, TOTAL 89.17%

pytest tests/api/test_pipeline_api.py -q
→ 18 passed

bun run test → 190 passed (48 files); bun run type-check → passed; bun run lint → 1 pre-existing warning
```
