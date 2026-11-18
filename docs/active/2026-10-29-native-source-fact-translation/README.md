# 原文事实抽取与英文呈现：当前路线

**Status:** in-progress
**Created:** 2026-10-29
**Updated:** 2026-11-11
**PR:** not created

当前状态（2026-11-16）：产品 Phase 3 已切换为原文事实链（`backend/src/core/source_fact_chain/`，见[归档计划](../../archive/plans/2026-11-16-source-fact-chain-pipeline-cutover.md)）；研究侧 C04 集成状态与下述历史记录不变。R5已接受，R6同步C04；上方历史发布记录不代表当前运行状态。[发布50](../../archive/papers/2026-11-12-native-source-task-release-50/README.md)开始实验设计实质补强：主比较、参考、强基线、功效与冻结仍需证据，不以产品离线通过声称SOTA。

[发布49 REMAINING-WORK-LEDGER-R5](../../archive/papers/2026-11-11-native-source-task-release-49/README.md)已发布：另存台账 R5，同步 C07 产品启用接受（EVIDENCE-ROLE-IMPL-R1）；C04 仍开放。路由 `commandcode`；种子 evidence-role-impl-r1；dsh 执行中。不关闭 G-02/BASE。

[发布48 EVIDENCE-ROLE-IMPL-R1](../../archive/papers/2026-11-11-native-source-task-release-48/README.md)已交付；omp [独立审核](../../archive/papers/2026-11-11-native-evidence-role-impl-r1-review/README.md)无阻断项；协调方[限定接受](../../archive/papers/2026-11-11-native-evidence-role-impl-r1-coordinator-acceptance/README.md)为 `accepted_for_offline_evidence_role_impl_scope`（有限枚举 + 独立注解、默认关闭；保留 O1/O2 跟进）。不关闭 G-02/BASE；不接 C04。

[发布47 REMAINING-WORK-LEDGER-R4](../../archive/papers/2026-11-10-native-source-task-release-47/README.md)已交付；omp [独立审核](../../archive/papers/2026-11-10-native-remaining-work-ledger-r4-review/README.md) 25/25；协调方[限定接受](../../archive/papers/2026-11-10-native-remaining-work-ledger-r4-coordinator-acceptance/README.md)为 `accepted_for_offline_remaining_work_ledger_r4_scope`（C06 产品启用已同步；C04/C07 仍开放）。不关闭 G-02/BASE。

[发布46 THREE-QUEUE-IMPL-R2](../../archive/papers/2026-11-10-native-source-task-release-46/README.md)已交付；omp [独立审核](../../archive/papers/2026-11-10-native-three-queue-impl-r2-review/README.md) 20/20；协调方[限定接受](../../archive/papers/2026-11-10-native-three-queue-impl-r2-coordinator-acceptance/README.md)为 `accepted_for_offline_three_queue_impl_scope`（F1 已修；选项 C）。不关闭 G-02/BASE；不接 C07。

[发布45 THREE-QUEUE-IMPL-R1](../../archive/papers/2026-11-10-native-source-task-release-45/README.md)已交付并由 omp [独立审核](../../archive/papers/2026-11-10-native-three-queue-impl-r1-review/README.md)为 `changes_requested`；协调方[不接受](../../archive/papers/2026-11-10-native-three-queue-impl-r1-coordinator-acceptance/README.md)（阻断 F1：重复 legacy rejection 同行载荷碰撞 `candidate_id`）。交付封条 `c924aa74…` 保留；交 R2 修复。不关闭 G-02/BASE；不接 C07。

协调方（2026-11-09）：[发布44 REMAINING-WORK-LEDGER-R3](../../archive/papers/2026-11-09-native-remaining-work-ledger-r3-coordinator-acceptance/README.md)限定接受为 `accepted_for_offline_remaining_work_ledger_r3_scope`（omp 26/26）。C04/C08 已同步；C06/C07 产品启用仍待拍板。不关闭 G-02/BASE。

协调方（2026-11-09）：gpt-6-luna 续跑处置完成——[R4 Chat 限定接受](../../archive/papers/2026-11-09-native-pilot-r1-gpt6-luna-run-r4-coordinator-acceptance/README.md)、[R6 Responses 限定接受](../../archive/papers/2026-11-09-native-pilot-r1-gpt6-luna-run-r6-coordinator-acceptance/README.md)（omp 审核后）、[R5 不接受/由 R6 替代](../../archive/papers/2026-11-09-native-pilot-r1-gpt6-luna-run-r5-coordinator-acceptance/README.md)。描述性运行范围；不关闭 G-02/BASE；无准入冻结。

协调方（2026-11-09）：发布34–36 按 omp 建议限定接受——[ledger-r2](../../archive/papers/2026-11-09-native-remaining-work-ledger-r2-coordinator-acceptance/README.md)、[subject-crossdoc-r1](../../archive/papers/2026-11-09-native-subject-crossdoc-r1-coordinator-acceptance/README.md)、[display-norm-design-r1](../../archive/papers/2026-11-09-native-display-norm-design-r1-coordinator-acceptance/README.md)。R6 Responses 完整成功（32 facts，translate 触达）；omp 独立审核进行中。R4 Chat 完整成功待协调抽查。R5 因脏账本未完成 translate，由 R6 对照补全。不关闭 G-02/BASE。

[发布43 PILOT-R1-GPT6-LUNA-STABLE-RESPONSES-RUN-R6](../../archive/papers/2026-11-09-native-source-task-release-43/README.md)按用户确认补跑完整 Responses 1+1+1：种子固定 R3 ledger（calls=6），禁止 R4/R5 账本；模型 `gpt-6-luna:stable`。注：R4 已在 Chat 上完整成功（28 facts）。

[发布42 PILOT-R1-GPT6-LUNA-STABLE-RESPONSES-RUN-R5](../../archive/papers/2026-11-09-native-source-task-release-42/README.md)按控制台 API：`POST /v1/responses` + 模型后缀 `:stable`（success_rate 路由）；不设分组、不加 provider.sort。准备包[gpt6-luna-stable-responses-prep](../../archive/papers/2026-11-09-native-pilot-model-switch-delivery/gpt6-luna-stable-responses-prep/README.md)。

[发布41 PILOT-R1-GPT6-LUNA-STABLE-RUN-R4](../../archive/papers/2026-11-09-native-source-task-release-41/README.md)按用户指定模型 ID `gpt-6-luna:stable`（Chat、不设分组）续跑；准备包[gpt6-luna-stable-chat-prep](../../archive/papers/2026-11-09-native-pilot-model-switch-delivery/gpt6-luna-stable-chat-prep/README.md)；账本继承 calls=6 / USD0.161865。

[发布40 PILOT-R1-GPT6-LUNA-RUN-R3](../../archive/papers/2026-11-09-native-source-task-release-40/README.md)按用户给出的官方文档 [quickstart-python](https://docs.linxi.chat/en/tutorials/quickstart-python) 将端点从 Responses 改为 **Chat Completions**（`chat.completions` / `gpt-6-luna`）；仍不设分组。准备包[gpt6-luna-chat-prep](../../archive/papers/2026-11-09-native-pilot-model-switch-delivery/gpt6-luna-chat-prep/README.md)；交 omp 续跑 R3（账本继承 calls=5 / USD0.150399）。

[发布39 PILOT-R1-GPT6-LUNA-RUN-R2](../../archive/papers/2026-11-09-native-source-task-release-39/README.md)已按用户提供的上游可用性（`gpt-6-luna` 约99.7%–99.86%）发布第二次续跑：仍不设分组、上游自动链式；新 runtime `logs/pilot-r1-gpt6-luna-resume-r2-20261109`，账本继承 R1 的 calls=4/USD0.138933。交 omp 执行。

宿主封包（2026-11-09）：发布34–36交付已写入 archive——[remaining-work-ledger-r2](../../archive/papers/2026-11-09-native-remaining-work-ledger-delivery/remaining-work-ledger-r2/README.md)、[subject-crossdoc-r1](../../archive/papers/2026-11-09-native-subject-crossdoc-delivery/subject-crossdoc-r1/README.md)、[display-norm-design-r1](../../archive/papers/2026-11-09-native-display-norm-design-delivery/display-norm-design-r1/README.md)；omp 独立审核进行中。ledger-r2 首两轮半包另存 failed-host-build-r1/r2（active README / append-only 漂移）。不关闭 G-02/BASE；C06/C07 仍待产品拍板。gpt-6-luna 续跑仍为 404 model_not_found（不设分组；待上游通道）。

用户约束（2026-11-09）：供应商计费/通道**分组不要在客户端设置**，上游会自动链式调用。价表 `group_ratio` 仅作本地预留保守上界；404 `model_not_found` 的 groups 列表只作错误原文记录，不得写成“去 token 设置选组”的操作建议。客户端请求保持 `model`+Responses 正文，无 group/channel 字段。

[发布38 PILOT-R1-GPT6-LUNA-RUN](../../archive/papers/2026-11-09-native-source-task-release-38/README.md)已按用户「授权发布任务」发布：在发布37离线接受与发布12的USD10总授权下，交omp执行`gpt-6-luna`单窗`rett_007__w01`真实续跑（Responses；最多3新调用；历史预留USD0.127467继承）。见[运行单](../../archive/papers/2026-11-09-native-source-task-release-38/pilot-r1-gpt6-luna-run.md)与[authorization](../../archive/papers/2026-11-09-native-source-task-release-38/authorization.json)。不批准主比较/准入冻结；容量与现价仍未核实。

[发布37 PILOT-R1-GPT6-LUNA-PREP](../../archive/papers/2026-11-09-native-source-task-release-37/README.md)已按用户「换成gpt-6-luna」发布并完成离线准备：extract/verify/translate 均用`gpt-6-luna`、Responses `/v1/responses`；交付[gpt6-luna-prep](../../archive/papers/2026-11-09-native-pilot-model-switch-delivery/gpt6-luna-prep/README.md)；协调方[限定接受](../../archive/papers/2026-11-09-native-pilot-gpt6-luna-prep-coordinator-acceptance/README.md)为`accepted_for_offline_gpt6_luna_preparation`。历史 gpt-5-mini 三次429/USD0.127467 与已接受 Qwen 离线包保留为历史；本包为下一续跑草案，**不授权真实运行**，仍`awaiting_external_inputs`（凭据轮换、容量/现价）。单窗新预留上界历史快照 USD0.034398、加历史累计 USD0.161865（非实付）。不关闭 G-02/BASE。

[发布34 REMAINING-WORK-LEDGER-R2](../../archive/papers/2026-11-09-native-source-task-release-34/README.md) / [发布35 SUBJECT-CROSSDOC-R1](../../archive/papers/2026-11-09-native-source-task-release-35/README.md) / [发布36 DISPLAY-NORM-DESIGN-R1](../../archive/papers/2026-11-09-native-source-task-release-36/README.md)已按并发 dsh 授权同时发布：台账 R2（同步 31–33）、跨文档主体边界探针、展示规范化只读设计；均 `commandcode/deepseek/deepseek-v4.1-flash`；种子 constructor-seal。见[dsh-34](dsh-remaining-work-ledger-r2-execution.json)、[dsh-35](dsh-subject-crossdoc-r1-execution.json)、[dsh-36](dsh-display-norm-design-r1-execution.json)（派发后写入）。不关闭 G-02/BASE；C06/C07 产品启用仍待另发。

[发布32 CONSTRUCTOR-SEAL-R1](../../archive/papers/2026-11-08-native-source-task-release-32/README.md)已按用户确认封堵与并发 dsh 授权发布：dsh（`commandcode/deepseek/deepseek-v4.1-flash`）封堵新链直接构造（仅 `create()`）；与发布31/33 并发。工作树`.worktrees/native-constructor-seal-r1`；dsh 因沙箱只读超时后，协调方宿主封交付[constructor-seal-r1](../../archive/papers/2026-11-08-native-constructor-seal-delivery/constructor-seal-r1/README.md)（78项）；omp[独立审核](../../archive/papers/2026-11-08-native-constructor-seal-r1-review/README.md)后，协调方[限定接受](../../archive/papers/2026-11-08-native-constructor-seal-r1-coordinator-acceptance/README.md)为 `accepted_for_offline_constructor_seal_scope`；见[dsh回执](dsh-constructor-seal-r1-execution.json)与[审核回执](omp-constructor-seal-r1-review-execution.json)。不关闭 G-02/BASE。

[发布33 THREE-QUEUE-DESIGN-R1](../../archive/papers/2026-11-08-native-source-task-release-33/README.md)已按并发 dsh 授权发布：dsh（`commandcode/deepseek/deepseek-v4.1-flash`）交付 C06 三队列**只读设计**（不实现）；与发布31/32 并发。工作树`.worktrees/native-three-queue-design-r1`；dsh 因沙箱只读超时后，协调方宿主自 staging 封交付[three-queue-design-r1](../../archive/papers/2026-11-08-native-three-queue-design-delivery/three-queue-design-r1/README.md)；omp[独立审核](../../archive/papers/2026-11-08-native-three-queue-design-r1-review/README.md)后，协调方[限定接受](../../archive/papers/2026-11-08-native-three-queue-design-r1-coordinator-acceptance/README.md)为 `accepted_for_offline_three_queue_design_scope`；见[dsh回执](dsh-three-queue-design-r1-execution.json)与[审核回执](omp-three-queue-design-r1-review-execution.json)。不关闭 G-02/BASE；设计接受≠启用。

[发布31 EVIDENCE-ROLE-DESIGN-R1](../../archive/papers/2026-11-08-native-source-task-release-31/README.md)已按本活动入口与 C07 remaining-work 发布：dsh（`commandcode/deepseek/deepseek-v4.1-flash`）交付新链 `evidence_role` **只读枚举设计**（对照旧链自由字符串、与 `FIELD_MODES`/术语链接正交；不写入 `SourceFact`、不复活旧字段），交付封条后由 omp（同模型）独立审核。工作树`.worktrees/native-evidence-role-design-r1`，交付`docs/archive/papers/2026-11-08-native-evidence-role-design-delivery/evidence-role-design-r1/`；种子为已接受 REMAINING-WORK-LEDGER-R1。dsh 因沙箱只读超时后，协调方宿主封交付[evidence-role-design-r1](../../archive/papers/2026-11-08-native-evidence-role-design-delivery/evidence-role-design-r1/README.md)（39成员级）；omp[独立审核](../../archive/papers/2026-11-08-native-evidence-role-design-r1-review/README.md)后，协调方[限定接受](../../archive/papers/2026-11-08-native-evidence-role-design-r1-coordinator-acceptance/README.md)为 `accepted_for_offline_evidence_role_design_scope`；见[dsh回执](dsh-evidence-role-design-r1-execution.json)与[审核回执](omp-evidence-role-design-r1-review-execution.json)。不关闭 G-02/BASE；设计接受≠产品启用。

[发布30 REMAINING-WORK-LEDGER-R1](../../archive/papers/2026-11-08-native-source-task-release-30/README.md)已按本活动入口发布：dsh（`commandcode/deepseek/deepseek-v4.1-flash`）另存 C01–C09 remaining-work 台账刷新（标注已接受探针/审计与仍待产品决策项；不改业务、不封堵、不设计三队列/`evidence_role`），交付封条后由 omp（同模型）独立审核。工作树`.worktrees/native-remaining-work-ledger-r1`，交付`docs/archive/papers/2026-11-08-native-remaining-work-ledger-delivery/remaining-work-ledger-r1/`；种子为已接受 ARRAY-BOUNDARY-R1。dsh 完成实现后因沙箱只读无法写 archive，协调方宿主封交付[remaining-work-ledger-r1](../../archive/papers/2026-11-08-native-remaining-work-ledger-delivery/remaining-work-ledger-r1/README.md)（44项封条，416完整离线测试/5新测/0网络；首轮半包另存 failed-host-build-r1）；omp/commandcode [独立审核](../../archive/papers/2026-11-08-native-remaining-work-ledger-r1-review/README.md)后，协调方[限定接受](../../archive/papers/2026-11-08-native-remaining-work-ledger-r1-coordinator-acceptance/README.md)为 `accepted_for_offline_remaining_work_ledger_scope`；见[dsh回执](dsh-remaining-work-ledger-r1-execution.json)与[审核回执](omp-remaining-work-ledger-r1-review-execution.json)。不关闭 G-02/BASE，零研究请求。

[发布29 ARRAY-BOUNDARY-R1](../../archive/papers/2026-11-08-native-source-task-release-29/README.md)已按本活动入口与 C05 remaining-work 发布：dsh（`commandcode/deepseek/deepseek-v4.1-flash`）实施新链候选数组边界探针（多候选列表各自成事实、混合批次局部拒绝、类数组字面量边界记录；不改 `core.is_atomic`、不自动拆值），交付封条后由 omp（同模型）独立审核。工作树`.worktrees/native-array-boundary-r1`，交付`docs/archive/papers/2026-11-08-native-array-boundary-delivery/array-boundary-r1/`；种子为已接受 SUBJECT-ID-EVIDENCE-R1。dsh 完成实现后因沙箱只读无法写 archive，协调方宿主封交付[array-boundary-r1](../../archive/papers/2026-11-08-native-array-boundary-delivery/array-boundary-r1/README.md)（40项封条，411完整离线测试/9新测/0网络）；omp/commandcode [独立审核](../../archive/papers/2026-11-08-native-array-boundary-r1-review/README.md)后，协调方[限定接受](../../archive/papers/2026-11-08-native-array-boundary-r1-coordinator-acceptance/README.md)为 `accepted_for_offline_array_boundary_probe_scope`；见[dsh回执](dsh-array-boundary-r1-execution.json)与[审核回执](omp-array-boundary-r1-review-execution.json)。不关闭 G-02/BASE，零研究请求；本批不新增逗号/JSON 拆分。

[发布28 SUBJECT-ID-EVIDENCE-R1](../../archive/papers/2026-11-07-native-source-task-release-28/README.md)已按本活动入口与 C08 remaining-work 发布：dsh（`commandcode/deepseek/deepseek-v4.1-flash`）实施新链主体 ID 原文充分性探针（结构不变量回归、id∉原文负例边界、跨文档不映射），交付封条后由 omp（同模型）独立审核。工作树`.worktrees/native-subject-id-r1`，交付`docs/archive/papers/2026-11-07-native-subject-id-delivery/subject-id-evidence-r1/`；种子为已接受 CONSTRUCTOR-PATH-R1。dsh 完成实现后因沙箱只读无法写 archive，协调方宿主封交付[subject-id-evidence-r1](../../archive/papers/2026-11-07-native-subject-id-delivery/subject-id-evidence-r1/README.md)（37项封条，402完整离线测试/0网络）；omp/commandcode [独立审核](../../archive/papers/2026-11-07-native-subject-id-r1-review/README.md)后，协调方[限定接受](../../archive/papers/2026-11-07-native-subject-id-r1-coordinator-acceptance/README.md)为 `accepted_for_offline_subject_id_evidence_probe_scope`；见[dsh回执](dsh-subject-id-r1-execution.json)与[审核回执](omp-subject-id-r1-review-execution.json)。不关闭 G-02/BASE，零研究请求；本批不强制 id∈quote。

[发布27 CONSTRUCTOR-PATH-R1](../../archive/papers/2026-11-06-native-source-task-release-27/README.md)已按本活动入口与 C01 remaining-work 发布：dsh（`qwen-token-plan-cn/deepseek-v4.1-flash-1017`）实施新链构造路径一致性核查（调用点清单、产品入口走 `create()`、直接构造绕过与下游读者边界探针；不封堵直接构造），交付封条后由 omp（`alibaba-token-plan/deepseek-v4.1-flash-1017`）独立审核。工作树`.worktrees/native-constructor-path-r1`，交付`docs/archive/papers/2026-11-06-native-constructor-path-delivery/constructor-path-r1/`；种子为已接受 NFKC-EXPANSION-R1。首轮因磁盘满未封条；续派遇 token-plan 月额度耗尽；协调方宿主封交付[constructor-path-r1](../../archive/papers/2026-11-06-native-constructor-path-delivery/constructor-path-r1/README.md)（51项封条，390完整离线测试/0网络）；omp/alibaba-token-plan 与 omp/sbs 均因额度失败后，协调方[离线独立验收](../../archive/papers/2026-11-06-native-constructor-path-r1-review/README.md)为 `accepted_for_offline_constructor_path_audit_scope`；见[dsh回执](dsh-constructor-path-r1-execution.json)与[审核回执](omp-constructor-path-r1-review-execution.json)。不关闭 G-02/BASE，零研究请求。

[发布26 NFKC-EXPANSION-R1](../../archive/papers/2026-11-05-native-source-task-release-26/README.md)已按本活动入口与 C09 remaining-work 发布：dsh（`qwen/deepseek-v4.1-flash-1017`）实施一对多 NFKC 展开样本探针，交付封条后由 omp（同模型）独立审核。工作树`.worktrees/native-nfkc-expansion-r1`，交付`docs/archive/papers/2026-11-05-native-nfkc-expansion-delivery/nfkc-expansion-r1/`。首轮因 headless 未注册 qwen 适配器失败并保留；随后按用户要求改用 `qwen-token-plan-cn` 续派；dsh 完成实现后因沙箱无法写 archive，协调方于2026-11-06宿主机封交付[nfkc-expansion-r1](../../archive/papers/2026-11-05-native-nfkc-expansion-delivery/nfkc-expansion-r1/README.md)（40项封条），omp/`alibaba-token-plan` [独立审核](../../archive/papers/2026-11-05-native-nfkc-expansion-r1-review/README.md)后，协调方[限定接受](../../archive/papers/2026-11-06-native-nfkc-expansion-r1-coordinator-acceptance/README.md)为 `accepted_for_offline_nfkc_expansion_probe_scope`（保留 D1 `replicas/` 悬空链接与 D2 索引过期叙述）；见[dsh回执](dsh-nfkc-expansion-r1-execution.json)与[审核回执](omp-nfkc-expansion-r1-review-execution.json)。不关闭 G-02/BASE，零研究请求。

[发布25 ATOMICITY-R1](../../archive/papers/2026-11-05-native-source-task-release-25/README.md)已发布。首轮 omp/DeepSeek 请求因五小时额度 HTTP429 中断并保留；随后按授权切换 SBS（`sbs/deepSeek-v4.1-flash-1017`），实现与本地验证完成，最终交付在供应商余额不足的 403 前由协调方用离线 uv 完成。[交付包](../../archive/papers/2026-11-05-native-atomicity-delivery/atomicity-r1/README.md)已由协调方限定接受为 `accepted_for_offline_native_semicolon_validation_scope`，33项封条、346完整测试、31项回归、Ruff、AST、2580保护路径和链接检查通过；[独立验收记录](../../archive/papers/2026-11-05-native-atomicity-r1-review/README.md)与[回执](omp-atomicity-r1-execution.json)记录了供应商中断、本地封包和过程偏差。原任务只补新链 NFKC 等价分号检查，不规范化存储、不拆值、不改共享 core/历史管线；G-02/BASE 整体及其他门不提升。

[发布24 CONTRACT-COVERAGE-R1](../../archive/papers/2026-11-05-native-source-task-release-24/README.md)首版changes_requested保留；omp/DeepSeek另交C1，[独立验收](../../archive/papers/2026-11-05-native-contract-coverage-r1-c1-review/README.md)为accepted_for_contract_coverage_audit_scope，须结合协调方范围勘误使用：23项交付封条、28输入、6快照、18行映射、2509保护路径及补丁重放通过；根uv344测试/0网络、全部新增Ruff/递归AST、6类扫描反例与2个封后拒写探针通过。旧not_reported对象返回不等于正向提升；首轮独立Ruff实际覆盖全部四个原新增文件。首版重封史及C1一次交付目录启动uv偏差保留。不修业务、不批准合并或切默认，G-02整体/BASE及其他门保持，见[C1回执](omp-contract-coverage-r1-c1-execution.json)。

[发布21 FROZEN-INPUT-R1](../../archive/papers/2026-11-04-native-source-task-release-21/README.md)首版[独立复核](../../archive/papers/2026-11-04-native-frozen-input-r1-review/README.md)为changes_requested；C1、C2封包复核分别发现封条成员漏列。C3另存后独立复跑：44封条集合闭合，291测试、12非法manifest反例、Ruff、AST、四臂恢复、16/16 golden、1850保护路径通过，0网络。仅接受[offline frozen input scope](../../archive/papers/2026-11-04-native-frozen-input-r1-c3-independent-review/README.md)，见[执行回执](omp-frozen-input-r1-c3-execution.json)；不关闭G-07整体，不切换旧入口。BASE审计范围先前已接受，本轮不重做。协调方误派旧BASE任务导致的12文件改写已按事前独立哈希完整恢复，见[事件记录](../../archive/papers/2026-11-04-base-c1-dispatch-incident/README.md)；误派结果另存不接受，原审计接受保留。

[发布23 SOURCE-ACCESS-R1](../../archive/papers/2026-11-04-native-source-task-release-23/README.md)首版[独立复核](../../archive/papers/2026-11-04-native-source-access-r1-review/README.md)保持changes_requested。C1因omp周额度429中断后改由DeepSeek provider续办，现已[限定范围接受](../../archive/papers/2026-11-04-native-source-access-r1-c1-review/README.md)：复核包18项封条、交付64项封条、315项离线测试、0网络尝试，6项I/O子类探针与golden 16/16通过。只限显式opt-in与合成/stub，不关闭G-05整体、不切换默认、不批准合并；首版与中断过程记录保留。

[发布22](../../archive/papers/2026-11-05-native-eval-task-release-22/README.md)误派已于2026-10-31接受的F01–F03，现[撤回重复派发](../../archive/papers/2026-11-04-eval-release22-duplicate-review-final/README.md)。omp保留旧c3另交c6；26封条/20输入及28行回放通过，561旧路径不变，指标/判定/合成结果与c5一致，不计新完成或替换c5接受。发布22原路径保留其错误的11月5日标注；实际执行为11月4日。

用户已同意：只从原文提取事实，英文由该事实集翻译得到，不再从全文译文独立提取。此处是新路线的活动入口；[协议修订与发布 06](../../archive/papers/2026-10-29-native-source-task-release-06/README.md)保存本次决定和任务定义。路线已批准，EVAL设计补正已于2026-10-31限定接受；NATIVE-C1离线实现已于2026-11-02限定接受。主比较选择及正式实验冻结仍须分别处理。

[发布20 PAIRED-SCREEN-R1](../../archive/papers/2026-11-03-native-source-task-release-20/README.md)已交付，并由[独立复核](../../archive/papers/2026-11-03-native-paired-r1-review-final5/README.md)限定接受为 `accepted_for_offline_fixed_view_screening_scope`；见[执行回执](omp-paired-screen-r1-execution.json)。本批只计算同一观察运行的 `D_off=A` 与 `D_on=A∩S`，不创建真实关闭核验运行，不调用外部服务或研究模型。

```text
原文分窗 → 原文事实抽取 → 原文证据核验 → 事实英译/术语映射 → 双语展示
                         保留事实 ID、主体、极性、原文引句与坐标
```

英文原文的事实可直接复用为英文呈现；非英文事实只翻译需呈现的语言字段。英译不产生第二套事实，不补猜主体，也不回流作为抽取证据。详见[协议修订](../../archive/papers/2026-10-29-native-source-task-release-06/protocol-amendment.md)。

## 当前：发布17实现运行到评价的连接

另发[发布18 DESIGN-R2](../../archive/papers/2026-11-03-native-source-task-release-18/README.md)，其 C1 补正已由 omp 交付并独立接受为设计范围：DF01–DF04 的集合、输出/参考单位、部分交付和方向/null边界均已复算；执行方9条直接python临时检查偏差保留。所有 primary/SESOI/threshold/freeze 仍未选，c5不改，不能替代论文实测。验收见[design-r2-c1-review](../../archive/papers/2026-11-03-native-design-r2-review/c1-final/README.md)。

[发布19 REFERENCE-PROTOCOL-R1](../../archive/papers/2026-11-03-native-source-task-release-19/README.md)已交付，[内容复核](../../archive/papers/2026-11-03-native-reference-r1-content-review/README.md)更正前轮过早接受结论，当前 delivered / changes_requested。封条38/38、原118用例、18输入hash、1481保护路径通过；另有RF01 undecidable误报精确值、RF02缺NFKC/空白规范化、RF03审查决定变更不被检测，交omp按[C1任务单](../../archive/papers/2026-11-03-native-reference-r1-content-review/reference-protocol-r1-c1.md)另存补正。只做本地合成协议，不读候选正文或临床材料、不调用研究模型。实际56个bash中10次直接python3；源码偏差是同文件两处替换，不是两文件。

[发布17](../../archive/papers/2026-11-03-native-source-task-release-17/README.md)的 EVAL-CORE-R1 首版 changes_requested 保留；[C1 最终验收](../../archive/papers/2026-11-03-native-eval-core-r1-review/acceptance.json)已为 accepted_for_offline_evaluation_core_scope：248 测试、24 独立边界探针、8 旧 golden、1398 保护路径通过。原封条79项漏列封后 seal.log，由协调方81项完整成员清单绑定当前字节，未修改交付。此前本入口的 C1 running 文字过时，现同步已存在的接受记录；不重做旧验收，不批准合并，首版过程偏差保留。

验证须贯通实际ChainRun和预算中止，以28行纯合成fixture回放作定义对照，不能手填阶段完成或终态。原生当前没有关闭核验开关，本批原生集成仅开启臂；关闭臂仅合成观察验证。完整27指标层、独立可评估参考和实际实验数据仍待后续，本批不能证明论文观点。主比较、阈值、正式实验冻结与所有旧门状态不变；不处理外部服务。

REFERENCE-PROTOCOL-R1-C1 的 [changes_requested 复核](../../archive/papers/2026-11-03-native-reference-r1-c1-review/README.md)保留。omp 已另交 C2，[独立验收](../../archive/papers/2026-11-03-native-reference-r1-c2-review/README.md)为 accepted_for_protocol_synthetic_scope：41封条/23输入、145回放、21封包测试、92独立检查及Ruff通过；1623历史路径不变，RF03b反向关联已拒绝。执行方曾删除自己未封存的失败构建后重建，其“未删除”声明由验收记录N1更正。见 [执行回执](omp-reference-r1-c2-execution.json)。不产生真实参考标签或论文实测证据。

## 发布16的G04/G03本地范围已接受

用户要求继续并暂不考虑外部服务。[发布16](../../archive/papers/2026-11-02-native-source-task-release-16/README.md)由omp在隔离工作树 `.worktrees/native-local-r1` 实施，首版经复核后另存[C1补正](../../archive/papers/2026-11-02-native-local-gap-delivery/local-r1-c1/README.md)。[协调方独立验收](../../archive/papers/2026-11-02-native-local-r1-review/README.md)接受本批工程范围：根uv完整未过滤176测试/0网络拦截；689图计分oracle、3697区间覆盖对照及75组分窗检查通过；20份Dev原文129窗覆盖453010字符，两张台账与首版字节一致。C1封条40/40、54输入/8快照、1203保护路径核对通过；执行与接受另见 `omp-native-local-r1-execution.json`。

G03只接受生成窗口覆盖，模型访问、抽取完整性和跨窗口引句未证明；G04只接受历史retained scorer边界，不改EVAL null规则。G01/G02/G05/G06/G07/G08仍开放，BASE-R1整体仍in-progress / changes_requested，旧八项汇总未接受，G0未就绪/WP00未观察。首版sed与C1辅助命令直接python的过程偏差保留，不批准合并；旧封包原字节、REV/G1/G2及候选状态不变。本批没有外部依赖或新增研究请求。

## NATIVE-C1离线实现与BASE-C1审计已限定接受

[协调方独立验收](../../archive/papers/2026-11-02-native-base-c1-coordinator-review/README.md)已完成：[发布15](../../archive/papers/2026-11-02-native-source-task-release-15/README.md)的F01文字补正由omp交付，四表9字段差异独立复算一致；WP02三行CSV结构另存补充后成为9×5，WP08真实行7字段非空比较相等。C08原始片段转录错误由验收记录B-N02更正，旧交付不改。BASE-C1与两份补充组合accepted_for_audit_scope，BASE-R1仍in-progress / changes_requested，八本地与两外部缺口全部开放，G0尚未准备好申请验收。

NATIVE-C1当前三文件与封存快照一致；仓库根uv环境独立115项测试（含链路41项）、Ruff、8份golden及两份补丁检查通过，accepted_for_offline_implementation_scope。原复核临时环境偏离保留；本轮未合并或切默认流程。1067保护路径未变，两份新补充分别8/7封条通过；发布快照保留issued，运行及接受写入活动回执。

## Qwen替代研究模型离线准备已接受；真实运行待外部输入

用户指定“采用gpt或者qwen”。[发布14](../../archive/papers/2026-11-02-native-source-task-release-14/README.md)选择qwen3.8-flash抽取/事实英译、qwen3.8-max原文证据核验，采用供应商历史清单声明的Chat Completions；GPT备选只登记、不自动回退。omp已交配置/Decimal预算和合成mock，[协调方独立验收](../../archive/papers/2026-11-02-native-pilot-qwen-review/README.md)为accepted_for_offline_qwen_preparation：15项交付封条、29输入hash、1020保护、38代码绑定通过；8接口mock与4命令防覆盖案例通过，零新增研究请求。现有业务代码及旧封包保持原字节，未切默认流程。

本次换型不声称供应商限额已解决；真实执行仍待研究凭据持有方轮换确认、所选Qwen渠道权限/容量与当前价格核对。USD10与累计9次调用上限持续有效，历史3预留USD0.127467继续继承。旧GPT恢复命令仅保留历史版本，不能直接套到新模型；30候选与BASE/G1/G2/REV状态不变。omp实施模型仍为用户此前指定DeepSeek，区别于本批Qwen研究模型。

历史报价上的单窗新预留上界USD0.21959432，加历史后USD0.34706132，累计最多6次调用；不是当前报价或实付。Qwen命令仍draft_not_executed，只有本地独立探针运行了截去live后的前导；当前awaiting_external_inputs。准备包固定generated_at常量不作为实际时间证据，元数据观察N01在验收记录中保留。

## 发布13恢复准备已验收；真实运行待外部输入

[恢复准备最终验收](../../archive/papers/2026-11-01-native-pilot-recovery-ready-review/README.md)限定接受原prep13项和命令补充prep-c1 6项；账本继承/48输入/首窗/Decimal预算通过，RC01防覆盖问题经独立隔离探针关闭。只使用补充命令，已有runtime拒绝后须先审查原账本，禁止重拷seed。业务38代码hash未变、未重跑118测试，零新增真实请求。用户本轮确认外部输入“尚无更新”，当前awaiting_external_inputs；不再返工离线包。

[发布13](../../archive/papers/2026-11-01-native-source-task-release-13/README.md)交omp离线对账3次失败请求、保全旧账本种子，准备原首窗最多新增3次调用的续跑草案；本轮不改代码、不重跑回归、不发网络请求。原累计调用上限9与USD10持续有效，草案只能旧3+新最多3，不能清零。无新供应商/轮换完成记录；真实运行仍待下述外部输入和具体运行单。

[恢复准备中间复核](../../archive/papers/2026-11-01-native-pilot-recovery-prep-review/README.md)记录原RC01复现；现由上文最终验收与prep-c1补充命令关闭，不改旧封包。

[最终独立验收](../../archive/papers/2026-11-01-native-pilot-ops-final-review/README.md)：omp OPS-C2最终54封条/38代码绑定/118测试和独立响应头脱敏探针通过；只接受离线技术补正，过程偏差保留、不批准合并。真实运行仍3次HTTP429、0事实，历史预留USD0.127467、实付unknown，本阶段零追加研究请求。

继续真实运行前须取得[供应商限额/错误/计费证据并完成研究凭据轮换](../../archive/papers/2026-11-01-native-pilot-ops-final-review/supplier-evidence-request.md)。独立检查证实先前回显的凭据写入两份任务日志；已收紧为600但尚未轮换，旧“未入日志”说法被更正。用户USD10授权持续有效，无须重新索取一般授权；当前awaiting_external_inputs，不能把模型列表/额度字段或空集相等当成功比较。

## OPS-C1复核与最小续办记录

[OPS-C1独立复核](../../archive/papers/2026-11-01-native-pilot-ops-c1-review/README.md)：116项测试/零网络拦截、38条代码绑定及55项封条通过；仍缺研究请求的响应头持久化，且新诊断模块有4处裸dict返回，已发布最小OPS-C2交omp。只读诊断实际4 GET（每类2次）超出单次上限，过程偏差保留；429根因仍unknown。此阶段零网络、零诊断GET、零研究请求；原账本3预留USD0.127467不退，真实试运行不接受为成功比较。

## 首轮运行记录

[RUN独立复核](../../archive/papers/2026-10-31-native-pilot-run-r1-review/README.md)：三首窗extract共3次请求均HTTP429，0事实/0核验翻译；失败包45封条通过。预算持久占用USD0.127467，usage/实付unknown。适配器失败仍ok及HTTP审计未落盘已交omp新OPS-C1修复、只读诊断，当前禁止额外研究请求，不将空事实相等当成功。用户USD10授权持续有效，后续恢复需容量证据与新实现独立核对。

## 准备接受与首轮执行记录（已由上文失败结论取代当前状态）

[准备独立接受与运行单](../../archive/papers/2026-10-31-native-pilot-ready-acceptance/README.md)：当时omp补正prep-c1的95封条/101测试及代码版本/价格依据通过，规划上界USD0.892269，继而交omp执行首轮。该轮已返回3次429；当前状态以上文最终验收为准。正式实验/候选准入冻结及其他包/门状态不变。

## 发布12：用户授权USD10的C1开发试运行

用户已明确授权真实模型试运行并给定总费用上限十美元。[发布12](../../archive/papers/2026-10-31-native-source-task-release-12/README.md)授权在已暴露Dev材料rett_007/078/071上进行C1固定事实核验开/关探索试验；omp先完成隔离适配、价格/模型/累计预算控制与mock验证，由协调方独立复核后直接执行。不再重复请求一般实验授权；若价格或凭据缺失，报告具体输入缺口。本授权取代下文旧轮次对该开发试运行的未授权描述，旧封包保持历史字节。正式主比较/统计目标/测试冻结未批准，30候选继续not_admitted/frozen=false。

## 当前分工与发布11：omp执行，协调方独立验收

用户已指定：本协调会话负责发布任务、解释验收要求及独立验收，具体实现交给omp。实现方不得自批接受，协调方不代写任务内生成器/评价实现。任务单、验收证据及状态更新仍由协调方维护。

[发布11执行单](../../archive/papers/2026-10-31-native-source-task-release-11/eval-c3-omp.md)续办原EVAL任务，EVAL-C3-OMP现为delivered / accepted_for_this_scope。[最终独立验收](../../archive/papers/2026-10-31-omp-eval-final-review/README.md)接受omp完成的c5设计补正，F01–F03本轮关闭，F04限定关闭保留，不再返工封包。首次默认模型因套餐拒绝退出、第二次短标识未匹配，均未实施；解析用户指定模型为commandcode/deepseek/deepseek-v4.1-flash后，两次实施会话依次完成c4与新c5，协调方均独立复核，未代写实现。后续omp交接沿用该模型，未改用户全局配置；目前使用已安装CLI，不新增MCP服务或改认证。

启动与执行状态见[活动回执](omp-eval-c3-execution.json)；发布快照保留issued，运行及接受状态不回写封包。c5封条24/24、交接包7/7、23成果/17输入、28行回放/5探针及声明同步独立通过；561条保护路径不变。主比较、阈值、样本量与预算等继续null，execution_authorized=false、frozen=false。历史16份正文恢复仍单列开放；BASE、G1/G2、REV及候选状态不变。

## 发布10：EVAL原任务续办与c2复核（前轮记录，已由c5限定接受取代当前裁定）

[发布10](../../archive/papers/2026-10-30-eval-c1-resume-reissue-10/README.md)只续发同一EVAL-C1-RESUME，提升为P0。发布时为 issued / not_delivered；2026-10-31已复核[c2交付](../../archive/papers/2026-10-30-native-source-review-and-design-delivery/eval-c1-resume-c2/README.md)，[最新独立复核](../../archive/papers/2026-10-31-eval-c1-resume-c2-review/README.md)仍为delivered / changes_requested。F04含义澄清限定关闭；M01主体盲匹配及分臂桶守恒通过。F01的M03d集合定义、F02已有视图却被阶段partial覆盖及判定表同步、F03分臂指标生成仍开放。

[原输出位置](../../archive/papers/2026-10-30-native-source-review-and-design-delivery/eval-c1-resume/)曾被就地覆盖。协调方已将观察到的补正版逐字节保存为[独立c1副本](../../archive/papers/2026-10-30-native-source-review-and-design-delivery/eval-c1-resume-c1/README.md)，25文件相同、其中24项封条通过。该副本只固定当前补正版，不恢复旧版。TASK.md与execution-state.json仍为控制记录，不计作实质成果。具体文件与完成条件见[执行单](../../archive/papers/2026-10-30-eval-c1-resume-reissue-10/eval-c1-resume.md)。

c2封条24/24、23必需文件、17输入hash及5链接通过，25行合成结果回放一致；开启臂桶21/21、关闭臂2/2。独立重算M13b应为开启6/7、关闭1/1，M10b应为开启14/21、关闭1/2；当前汇总混用了两臂，不能据守恒接受。旧封条已重建并验证，8个旧正文已定位、16个仍本地未恢复，本轮未扩大恢复搜索；旧审查与420保护文件未变。下一补正另存eval-c1-resume-c3，原目录/c1/c2只读，见[原任务续办清单](../../archive/papers/2026-10-31-eval-c1-resume-c2-review/follow-up.md)。NATIVE/BASE复核接受裁定及其他工作包状态未在本轮处理，不运行真实模型或改变参考、准入/冻结状态。

## 发布09任务的当前交付状态

[发布09](../../archive/papers/2026-10-30-native-source-task-release-09/README.md)原发布快照不改。两个复核现已交付，用户独立核对其封条32/32与9/9；这不等于协调方接受内容。EVAL原未交付，已按发布10交付，不重复计算工作包。

| 任务 | 优先级 | 执行状态 | 验收状态 | 首个动作 |
|---|---|---|---|---|
| [NATIVE-C1-REV](../../archive/papers/2026-10-30-native-source-review-and-design-delivery/native-c1-rev/README.md) | P0 | delivered | accepted_for_review_scope（2026-11-02） | 当前根环境独立复核通过；原环境偏离记录保留，未合并 |
| [BASE-C1-REV](../../archive/papers/2026-10-30-native-source-review-and-design-delivery/base-c1-rev/README.md) | P0 | delivered | accepted_for_audit_scope（与F01/CSV补充及B-N02组合） | 十项缺口仍开放，BASE-R1仍changes_requested |
| [EVAL-C1-RESUME](../../archive/papers/2026-10-30-native-source-review-and-design-delivery/eval-c1-resume-c5/README.md) | P0（发布10/11） | delivered | accepted_for_this_scope | 本轮设计补正关闭；下一阶段统计目标/比较批准另发，不改已封版本 |

两个复核的本轮范围裁定见页首2026-11-02验收。EVAL接口以已封存C1为明确版本。成果交`docs/archive/papers/2026-10-30-native-source-review-and-design-delivery/<task-id>/`。原发布08任务仍是父任务，不重复计算WP完成度。

## 发布08补正交付状态

[发布08](../../archive/papers/2026-10-30-native-source-task-release-08/README.md)承接[发布07独立验收](../../archive/papers/2026-10-30-release-07-independent-review/README.md)。原交付均changes_requested。NATIVE-C1与BASE-C1的当前限定裁定见下表；EVAL的后续c5设计范围接受见页首，其早期C1副本保留历史状态。

| 补正任务 | 优先级 | 执行状态 | 验收状态 | 下一动作 |
|---|---|---|---|---|
| [NATIVE-R1-IMPL-C1](../../archive/papers/2026-10-30-native-source-task-release-08/native-r1-impl-c1.md) | P0 | delivered | accepted_for_offline_implementation_scope（2026-11-02） | [当前交付](../../archive/papers/2026-10-30-native-source-correction-delivery/native-r1-impl-c1/README.md)已独立核对，未合并或切默认 |
| [BASE-R1-FINAL-C1](../../archive/papers/2026-10-30-native-source-task-release-08/base-r1-final-c1.md) | P0 | delivered | accepted_for_audit_scope（组合补充，2026-11-02） | 审计材料接受；BASE-R1整体changes_requested，十项缺口开放 |
| [EVAL-R1-DESIGN-C1](../../archive/papers/2026-10-30-native-source-task-release-08/eval-r1-design-c1.md) | P1 | incomplete；未交付 | pending | 按原任务直接续办定义/接口；NATIVE修后契约已可读取，无须等待重新派发 |

补正交`docs/archive/papers/2026-10-30-native-source-correction-delivery/<task-id>/`。这是原任务续办，不新建WP或重复计算完成度。三次NATIVE未完成尝试原记录保留，当前结论见页首独立验收；交付不自动提升接受状态。原三包封条和已接受历史均保持原字节。

## 发布07交付状态

[发布07](../../archive/papers/2026-10-29-native-source-task-release-07/README.md)的三项均已交付。2026-10-30独立验收结果如下；封条/测试通过的限定范围不等于整体内容接受。

| 任务 | 优先级 | 执行状态 | 验收状态 | 首个动作 |
|---|---|---|---|---|
| [NATIVE-R1-IMPL](../../archive/papers/2026-10-29-native-source-task-release-07/native-r1-impl.md) | P0 | delivered | changes_requested | NATIVE-R1-IMPL-C1；原包123项封条通过，3项独立反例待修 |
| [BASE-R1-FINAL](../../archive/papers/2026-10-29-native-source-task-release-07/base-r1-final.md) | P0 | delivered | changes_requested | BASE-R1-FINAL-C1；当前审计视图同步、误引撤回、G0准备度 |
| [EVAL-R1-DESIGN](../../archive/papers/2026-10-29-native-source-task-release-07/eval-r1-design.md) | P1 | delivered | changes_requested | EVAL-R1-DESIGN-C1；指标/接口/比较与来源单位 |

原交付保留于`docs/archive/papers/2026-10-29-native-source-delivery/<task-id>/`，task-id分别为`native-r1-impl`、`base-r1-final`、`eval-r1-design`。后续补正使用发布08新目录，任务结果经协调方内容验收后才改累计状态。

## 发布06父任务

| 任务 | 执行状态 | 验收状态 | 下一动作 |
|---|---|---|---|
| [NATIVE-R1：原文事实链离线适配](../../archive/papers/2026-10-29-native-source-task-release-06/native-r1.md) | in-progress；实现已交 | C1离线实现范围已接受 | 已独立复核，未合并或切默认；真实试运行待外部输入 |
| [EVAL-R1：新路线评价与协议设计](../../archive/papers/2026-10-29-native-source-task-release-06/eval-r1.md) | in-progress；设计已交 | c5设计范围已接受 | 主比较与正式统计目标尚未批准；历史正文恢复另列开放 |

两项已交范围的接受见页首；接口联调以NATIVE-C1契约为输入。外部缺证独立记录，父任务状态不因子任务已交付而标完成。

## 既有任务如何继续

[发布 05 执行单](../2026-10-23-native-v3-next-stage-tasks.md)继续跟踪 WP12-R3、BASE-R1、WP11-R2、G1-R1；具体范围调整见[22 包对照](../../archive/papers/2026-10-29-native-source-task-release-06/wp-scope-map.csv)。BASE-R1 完成原 16 条款实质映射，并区分保留、适配和仅历史适用的要求；不用为新路线补建已取消的译文抽取。WP11-R2 可以交适用性/不可行报告；BIO 不是当前主方法必需节点。

[原工作包表](../../planned/2026-09-25-native-evidence-experiments/work-packages.csv)保留累计状态与原范围；本页只跟踪新任务，不创建另一套 WP 验收结论。旧 00–03、方法矩阵及冻结模板是历史审计输入；新路线不能直接执行它们。主比较、主终点、阈值、样本量、重复数及预算待 EVAL-R1 与 WP13/WP14 审议，见[不可执行模板](../../archive/papers/2026-10-29-native-source-task-release-06/freeze-manifest.template.json)。

## 保留状态与边界

REV 本地修复已于 2026-10-22 接受，不重开。WP11-C2、WP06/WP10 原范围交付保留；WP11/WP12 整体仍 in-progress，BASE-R1 仍 changes_requested，G1/G2 Pending。30 个候选仍 not_admitted / frozen=false。旧 M/B2 结果只说明旧方法与旧参考的开发观察。

本批仅授权隔离的离线适配、合成/mock 检查与方案交付；不运行真实模型或 BIO，不下载数据库，不读取新候选摘要/正文，不准入或冻结 test。无新敏感性结果，本轮不触发 bootstrap。发布决定已完成并归档；本活动页随任务推进更新。
