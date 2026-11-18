# Native-v3：发布 05 执行跟踪

**Status:** in-progress
**Created:** 2026-10-23
**Updated:** 2026-10-31
**PR:** not created

[发布快照与剩余工作盘点](../archive/papers/2026-10-23-native-v3-task-release-05/README.md) · [工作包状态](../planned/2026-09-25-native-evidence-experiments/work-packages.csv) · [前期活动计划](2026-10-15-native-v3-bio-and-test-readiness.md)

## 2026-10-31 发布11：omp实现与独立验收分工（当前）

用户指定协调方只负责发布与独立验收，具体实现交omp。[EVAL-C3-OMP执行单](../archive/papers/2026-10-31-native-source-task-release-11/eval-c3-omp.md)续办原EVAL，发布快照保留issued。现omp以用户指定commandcode/deepseek/deepseek-v4.1-flash完成c4及新c5，[最终独立验收](../archive/papers/2026-10-31-omp-eval-final-review/README.md)为delivered / accepted_for_this_scope：c5封24/24、交接包7/7、23成果/17输入、28行回放/5探针及F01/F02声明同步通过，F01–F03本轮关闭，F04限定关闭保留。协调方未实现EVAL逻辑，不回写旧包。主比较/阈值/样本量/预算未批准，研究执行未授权、未冻结；BASE/十缺口、REV、G1/G2与候选状态不变，历史16正文恢复另列开放。

## 2026-10-31 EVAL c2独立复核（前轮裁定，尚未被后续接受取代）

[最新复核](../archive/papers/2026-10-31-eval-c1-resume-c2-review/README.md)仍为delivered / changes_requested：24封条/23必需文件/17输入hash/5链接通过，25案例回放一致，分臂桶21/21与2/2成立。M13b应分臂为6/7与1/1，M10b为14/21与1/2；当前汇总混臂且漏减S24。F01集合公式、F02已有preserved视图遇后续预算中止的处理与判定表、F03分臂结果生成仍需补正；F04限定关闭保留。后续只写新c3，原目录/c1/c2及旧审查420保护文件不变。根进度与复盘已追加。旧16正文仍本地未恢复，与内容审查分别跟踪；BASE/十缺口、REV、G1/G2及候选状态不变。

## 2026-10-31 EVAL补正版复核与覆盖处置（前轮记录）

[最新复核](../archive/papers/2026-10-31-eval-c1-resume-correction-review/README.md)仍为delivered / changes_requested：F04定义澄清限定关闭，F01–F03部分完成。协调方保全补正版到eval-c1-resume-c1（25文件相同、24项封条通过）；旧封条重建hash相同，8旧成员定位、16旧正文仍本地未恢复，不作不可恢复判断。原审查记录保留，后续补正只写c2。22例演算通过不等于穷尽；其他工作包、已接受REV、G1/G2及候选状态不变。

## 2026-10-31 EVAL续办交付与独立验收（首轮记录）

EVAL-C1-RESUME已交付；[独立验收](../archive/papers/2026-10-31-eval-c1-resume-independent-review/README.md)为changes_requested。24项封条、23必需文件、17输入hash及5条链接通过，17例回放与已有守恒算术成立；主体分母、partial分类、C1比较目标和正确交付含义仍须补正。原交付及已封包只读，NATIVE/BASE复核未在此裁定；BASE-R1与G1/G2、REV及候选状态不变。下段保留发布时状态，当前以此段和路线入口为准。

## 2026-10-30 发布10：EVAL原任务四节点续办（发布时记录）

[发布10](../archive/papers/2026-10-30-eval-c1-resume-reissue-10/README.md)只续发EVAL-C1-RESUME，P0 / issued / not_delivered / acceptance pending；指标判定、合成演算、接口与比较/来源、完整封包四节点全部pending，可直接从M1开始。输出目录已准备两份控制记录，不算设计成果。本轮只发布；两个复核已交付、用户核过32/32及9/9封条，内容接受仍pending，不阻塞EVAL。BASE/G1/G2/REV及候选状态不变。

## 2026-10-30 发布09：独立复核与设计续办（发布时记录）

[发布09](../archive/papers/2026-10-30-native-source-task-release-09/README.md)新增两个复核任务NATIVE-C1-REV、BASE-C1-REV（P0）及既有设计续办EVAL-C1-RESUME（P1），均issued / acceptance pending，可直接开始；本轮只发布，未开始执行或接受。NATIVE修复不重复实施，BASE审计不先要求修完八项功能缺口，EVAL使用已交修后契约继续定义/映射，不再等重新派发。新成果交独立目录，旧封包只读，最终接受由协调方裁定。下列日期记录保留历史范围，当前执行安排见[路线入口](2026-10-29-native-source-fact-translation/README.md)。

## 2026-10-30 发布07验收与发布08补正

本日续办：NATIVE-R1-IMPL-C1已在原隔离工作树直接修复并[交付](../archive/papers/2026-10-30-native-source-correction-delivery/native-r1-impl-c1/README.md)，当前链路41/研究套件115/Ruff通过、8份golden字节一致；验收pending，未合并或切默认。BASE-FINAL-C1已报交付、内容待独立复核；EVAL-C1未交付，旧副本不算补正。本轮不修改两包字节或重开REV；下述“均issued”是发布时状态，当前表以[路线入口](2026-10-29-native-source-fact-translation/README.md)为准。

[独立验收](../archive/papers/2026-10-30-release-07-independent-review/README.md)确认三项均delivered，三项均changes_requested：NATIVE当前96项研究测试/Ruff、123项封条通过，但三项独立反例待修；BASE13项封条/48绑定/83输入通过，当前表仍未完整吸收已核查结论且误归因L85，G0准备度待补；EVAL12项封条/37输入通过，指标/CSV/接口与来源/比较单位待补。

[发布08](../archive/papers/2026-10-30-native-source-task-release-08/README.md)已直接发布NATIVE-R1-IMPL-C1（P0）、BASE-R1-FINAL-C1（P0）、EVAL-R1-DESIGN-C1（P1），均issued / acceptance pending，执行方无需再请求选项确认。补正交新目录，原封包不改。BASE终版审计无须先关闭八项实现缺口；G1外部凭据独立保留，REV和原绑定同步接受范围不重开。详见[当前路线入口](2026-10-29-native-source-fact-translation/README.md)。

下列2026-10-29及之前的日期段落保留其发布时范围；当前执行状态以上段及当前任务表为准。

## 2026-10-29 路线修订与发布 06

用户已确认改为“原文抽取 → 原文核验 → 事实英译”，不再从全文译文独立抽取。新路线以[活动入口](2026-10-29-native-source-fact-translation/README.md)和[发布 06 协议修订](../archive/papers/2026-10-29-native-source-task-release-06/protocol-amendment.md)为准；NATIVE-R1、EVAL-R1 均 issued / acceptance pending，本轮未执行。

发布 05 四项继续授权。BASE-R1 仍完成历史 16 条款内容映射及终版同步，并附新路线 retain/adapt/legacy_only 判断；不为新路线补建已取消的译文提取。WP11-R2 改按新问题提供 BIO 适用性/不可行报告，独立 BIO 不能使用本方法已提取事实的英文作为输入。WP12-R3 和 G1-R1 保持来源/外部凭据任务。详见[22 包范围对照](../archive/papers/2026-10-29-native-source-task-release-06/wp-scope-map.csv)。

旧方法矩阵/冻结模板只作历史审计输入，新比较对象与统计目标仍待 EVAL-R1/WP13/WP14；BIO 可比性判断不等于必须先运行 BIO。下列既有验收状态保持，REV 不重开。后续日期记录保留其当时范围。

## 2026-10-29 发布07执行安排

[发布07](../archive/papers/2026-10-29-native-source-task-release-07/README.md)发布NATIVE-R1-IMPL（P0隔离实现）、BASE-R1-FINAL（P0原16条款终版整合）、EVAL-R1-DESIGN（P1评价方案）三项执行任务，均issued / acceptance pending，发布本身未开始执行。它们细化既有父任务，不创建新工作包、不重开REV/绑定验收；外部缺证不阻断离线实现或完整缺口审计。单人优先NATIVE契约/最小链路，再交BASE终版与EVAL设计；不同执行者可分别推进。

BASE新终版交`docs/archive/papers/2026-10-29-native-source-delivery/base-r1-final/`，原base-r1执行包保持只读。用户最新确认仅涉及16/16和11/11封条，不能写成已接受24项内容。八项功能缺口继续开放；完整审计接受与功能关闭分别裁定。

## 当前执行任务

| 任务 | 优先级 | 执行状态 | 协调方验收 | 下一动作 |
|---|---|---|---|---|
| [WP12-R3](../archive/papers/2026-10-23-native-v3-task-release-05/wp12-r3.md) | P0 | in-progress；F2补正已报 | changes_requested；补正待独立复核 | 依执行方新记录复核ref绑定与预期哈希；本轮未复核，不阻塞BASE-R1 |
| [BASE-R1](../archive/papers/2026-10-23-native-v3-task-release-05/base-r1.md) | P0（终版子任务） | in-progress；FINAL已交，C1 issued | changes_requested；8项本地开放、2项外部开放 | 按[终版C1补正](../archive/papers/2026-10-30-native-source-task-release-08/base-r1-final-c1.md)同步已有核查与所有当前表，撤回误引、补G0准备度 |
| [WP11-R2](../archive/papers/2026-10-23-native-v3-task-release-05/wp11-r2.md) | P1 | issued | pending | 沿 C2 形成原 A 路线可行性/不可行报告及下一步决定条件 |
| [G1-R1](../archive/papers/2026-10-23-native-v3-task-release-05/g1-r1.md) | P1 | issued | pending | 核查外部日志/Billing 可用证据，或提交具体导出需求 |

单人当前顺序以发布08为准；WP12-R3等原任务授权继续，各项独立提交。`issued` 表示任务已发布，不表示执行已开始。工作包表中 19 项未整体验收（9 in-progress、10 planned）；此计数包含已有实现和限定范围交付，不能当作全未开展。

## 后续队列

2026-10-29 [BASE-R1八项实质映射接收核查](../archive/papers/2026-10-29-base-r1-substantive-mapping-review/README.md)：新表8条8列及11项封条通过，todo完成仅写行；24项主张按执行方本轮/协调方直接/历史核查/仅转述拆分，9项G-02契约映射已读断言但未运行。保留参考迁移极性/分号拆分部分证据，normalize_value有reference调用；零指标/最大匹配实现存在，严格主体历史探针保留；517条历史off归属已关闭，不为新未核实小差重开。复用本次结果接回16条款和BASE终版，不要求先实现全部缺口；8项均开放，原绑定同步及REV不重开。

2026-10-29 [BASE-R1绑定同步限定验收通过](../archive/papers/2026-10-29-base-r1-binding-sync-acceptance/README.md)：46处哈希和24行物理范围通过；相对上版仅WP08-A L46-76→L46-72，主evidence-map原按函数名/L46引用且字节不变，无需为本次修正改写。README/response已登记绑定，G-07/G-08/WP08已读范围补充，10项封条覆盖全部真实文件；10个本地Markdown链接独立核对通过。执行日志已追加，标题空行与旧快照未找到说法为非阻断历史格式/更正项。协调方按现有archive/papers布局完成doc-organize并保存11份接受版本原字节；本次绑定同步关闭，直接继续G-01至G-08实质映射，外部G1独列；BASE仍changes_requested，REV关闭。

2026-10-29 [BASE-R1 46行证据绑定核查](../archive/papers/2026-10-29-base-r1-binding-review/README.md)：46行6列覆盖16条款/26文件，与上轮46处条款-路径-哈希完全一致，uv重核46/46通过。24行物理定位中23有效、WP08-A的L46-76超过文件72行，改L46-72；原协调方引用范围同并更正，旧封包不改。8个测试绑定当前断言已读，3行JSON定位/2账本筛选/1目录核对；16公开快照定位复用已验来源，不强制改引JSONL。旧BASE8项封条仍通过但未含新绑定，先接回主表/说明并同步F2/F3，再补日志/整理与新封条；整体仍changes_requested，REV关闭。

2026-10-29 [BASE-R1 16条款映射接收核查](../archive/papers/2026-10-29-base-r1-clause-mapping-review/README.md)：16行均9列、ID及4 retain/12 adapt分类通过；14行指向6个现存文件，但局部更正表7行不支持所有转述。复用G-03已落盘前缀更正、8份完整会话哈希/53条来源绑定与11条已读证据，不再列为待取回。WP04匹配/零指标实现、WP05导入边界、WP07标签/历史off产物、WP08本地恢复、WP09本地预检均需保留部分证据；源漂移归WP08，结算另列G1。按逐条核查补引用并同步BASE终版；新英文契约归NATIVE-R1。协调方本轮doc-organize/日志完成，执行方作业日志另补；BASE仍changes_requested，REV关闭。

2026-10-28 [BASE-R1局部条款观察核查](../archive/papers/2026-10-28-base-r1-clause-observations-review/README.md)：新增6条中第6物理行10列；评分/缓存证据误挂WP02-B，应归WP04-B/WP08-B。极性helper断言部分成立，空输入tp断言实际L85；多病例已有部分证据可复用。工作树catalog文件名检索零命中，主仓命中v1/v2，原报告需明确cwd；工作树../docs不存在。四篇选择理由已读但不证明结果前选样。原53条结构/来源及历史progress验收保持；继续16条款实质映射和执行包终版同步，本次doc-organize/日志已完成。

2026-10-28 [BASE-R1更正版与原审查来源绑定验收](../archive/papers/2026-10-28-base-r1-source-binding-review/README.md)：53条均8列，仅修复四处错列；八份JSONL的完整哈希/行数匹配，公开输出与消息/Pointer已核对。会话头确认cwd；progress前420行/151093字节与原G-05工具输出哈希完全匹配，历史版本问题关闭。53条来源关联已建立，仍不等于内容验收；原输出中译文坐标、最大匹配、实际off产物及历史关闭范围需纳入16条款判断。直接继续实质映射与BASE终版同步，本次doc-organize已完成。

2026-10-28 [BASE-R1原审查映射接收核查](../archive/papers/2026-10-28-base-r1-origin-map-review/README.md)：当前文件实际53条而非73条，4条因未引用逗号错成9列；G-03新前缀正确。history别名尚无可解析JSONL路径/完整哈希/原输出定位，取回报告未独立确认。G-06脚本在工作树，WP05/WP08条款在根docs可读；保留原审查搜索范围，区分prompt哈希变化与冻结版本拒绝。原任务内修结构→补来源→实质映射/同步BASE，doc-organize及相关链接检查由本次协调方完成。

2026-10-28 [BASE-R1汇总接收与REV状态核对](../archive/papers/2026-10-28-base-r1-local-results-review/README.md)：八行汇总均pending_local_review，已报不等于内容验收；原审查出处待提供，G-03的windowing.py哈希前缀不符。CSV为原协调方4项封条之外的后加文件，本次另存原字节快照，不重封旧目录。REV两项已于10月22日验收，四个关键文件仍与验收字节一致，当前60项封条通过；不因旧回顾重开修复。BASE继续原八项核查，F1/F3及引用登记已通过范围保留。

2026-10-27 [BASE-R1引用登记与F3同步验收](../archive/papers/2026-10-27-base-r1-sync-review/README.md)：8项封条、76输入、16条7/7/1/1及8包6/2、8本地/2外部统计通过。F3同步关闭，F2的11条引用登记通过；允许引用不等于豁免未覆盖行为，F2总体仍未完成。沿用G-01至G-08发布具体本地核查清单，完成实际读取/映射或引用其对应已核查范围后再交整体；不要求本轮把八个原包实现全部修完。G1外部项不阻塞本地核查。本批doc-organize已由协调方完成，不再单独为归档返工。

2026-10-26 [BASE-R1 F1–F3补正复核](../archive/papers/2026-10-26-base-r1-f1-f3-followup/README.md)：8项封条/76输入通过；16行9列、7/7/1/1计数及主哈希唯一定位通过，F1此范围关闭。两处参考约束旧句已修。F2仍有未读断言/未映射条款；11条located-evidence属于协调方核查，可明确引用其范围。F3的response仍4/12，包级建议/缺口未同步，G0理由仍混入WP07。8包6/2与16条7/7/1/1是不同层级，不能机械对齐；只完成F2→F3→最终封包，不重做F1、不等账单、不重开REV。

2026-10-26 [BASE-R1证据映射独立核查](../archive/papers/2026-10-26-base-r1-evidence-map-review/README.md)：8项封条、76输入哈希/大小通过，21源码/测试/脚本仍匹配recheck-34；evidence-map首行因逗号未引用有10列而表头9列。16条虽均有行，Step2仍多为未读取/未映射，提供11个已定位证据入口及覆盖限制。G0不依赖后续G1结算，WP08/09本地核对与外部输入须分开；Step4旧句尚未同步。原任务内三项补正连续执行，不要求笼统重跑测试或等待外部账单。共享组成员再次从JSON确认为rett_062/063。BASE验收changes_requested，其他状态不提升。

2026-10-26 [BASE-R1参考约束核对与分母边界续办](../archive/papers/2026-10-26-base-r1-reference-boundary-review/README.md)：5项封条通过，Step 4七条核心约束可保留；文本同步并入Step 3/最终交付。独立计数为20篇、现有19组、1177参考事实、493患者事实（491主体未定），两臂逐篇TP+FN与reference_count相符。审计§4第2点已有“六篇未新增TP”的解释，但尚未经独立验证，不能据模拟结果设WP13效应量。WP06/WP10是支持输入而非16条矩阵成员；审计分类不能直接更换冻结分母。剩余步骤连续执行，不重开REV、不修改工作包表。

2026-10-25 [BASE-R1条款核对与输入定位](../archive/papers/2026-10-25-base-r1-clause-and-input-review/README.md)：八包16条及4项封条通过，条款提取子项完成；整体验收pending。76项输入路径/哈希已给出，21个当前源码/测试/脚本哈希匹配recheck-34；已定位143字段目录为v2，完整v3目录本轮尚未定位。未核对不等于真实功能缺口。Step 4补入本表下方待办，全部剩余项pending，不使用choice 2 scope。R3新F2补正仅按执行方日志记录为已报待复核，本轮不提升其验收结论。

### BASE-R1 当前子项

| 子项 | 状态 |
|---|---|
| Step 1a：八包条款提取 | completed；限定范围核对通过 |
| Step 1b：逐条源码/产物版本哈希映射 | 16条主文件哈希、CSV/计数及11条已有证据引用登记通过；剩余内容映射随F2 |
| Step 2：逐条证据与剩余缺口核查 | 未完成；53条来源/46绑定验收保留，新8条表已审；复用24项逐主张核查与9项G-02断言映射完成16条款实质判定，不能据todo关闭8项 |
| Step 3：WP06/WP10输入与WP13分母边界 | README §2已提交；基础计数/限制保留，F3同步通过 |
| Step 4：参考可评估性与条件性修订约束 | 核心约束及两处旧句修正通过；冻结分母约束保留 |
| Step 5：状态建议、G0判定、response及封包 | F3本版同步通过；F2完成后按实质结论更新终版，BASE整体changes_requested |

以下保留早先阶段记录；当前执行安排以本表及最新核对记录为准。

2026-10-25 [18项封条与回链复核／BASE-R1开工决定](../archive/papers/2026-10-25-wp12-r3-backlink-review/README.md)：18项完整封条及修改脚本Ruff通过，F1实质标签和F3暂定分组数量边界已落实。F2新增194行中33行因取整个provenance第一个路径/哈希而错绑；14行未绑定已有预期哈希。旧68真实来源哈希全部成立，无需重取。保持R3 changes_requested，仅继续原F2；BASE-R1不依赖它，立即开工，执行者先补R3本轮进度/复盘记录。其余两项仍issued/not started，REV不重开。

2026-10-25 [部分交付独立验收](../archive/papers/2026-10-25-wp12-r3-partial-acceptance/README.md)：15项封条完整、30/150/8/6/29组30成员/4事件计数、四脚本Ruff及8份CSV临时重放通过；R3仍需三项内容补正。MED/38684295的冲突是PubMed列出DOI与RA否定载荷，而非RA与agency404；MED/24397181无候选DOI，不能称两者DOI不同。请求号清单不替代内容证据，29组是暂定分组而非已证实独立来源。无需读取候选正文，未知权利可保留。其余三项仍issued/not started，本轮未包含不构成blocked。

2026-10-25 [进度核对与继续执行决定](../archive/papers/2026-10-25-wp12-r3-progress-review/README.md)：继续原 WP12-R3，不重开 REV。R3 尚未找到独立基线文件；新派生标签中的 refuted 与派生用途权限继承需在 R3 修正。旧包当前仅 README、response、封条不同于10月22日快照，其余58文件一致，差异单独留档、旧包不再修改。其余三项任务仍 issued，授权有效，不整体暂停等外部输入。

[WP13–WP21](../archive/papers/2026-10-23-native-v3-task-release-05/deferred-queue.md)保持 `queued_pending_inputs`。先结合发布 06 明确新路线问题/比较、可用来源、参考可评估性及需要保留的 BIO 主张范围，再正式做功效/精度/预算规划、G2、协议冻结、测试参考、正式实验、匿名审计、统计、写作与人工交付。NATIVE-R1/EVAL-R1 的离线准备已发布；正式执行另发任务。

## 已关闭与保留状态

[2026-10-22 REV local acceptance](../archive/papers/2026-10-22-wp12-rev-local-acceptance/README.md)为 `accepted_for_this_scope`；R2-C1 原包不返工、不重封，非阻断旧句留下一版本。WP10 completed-offline；WP11-C2 交付保留；WP11/WP12 整体 in-progress；G1/G2 Pending。30 候选均 not_admitted / frozen=false。

Aron 采用已保存的用户未暴露更正声明，仍待团队范围核对和准入；MED/24750837 历史开发暴露与同文献排除沿用。无新的参考敏感性结果，不新增 bootstrap 重跑欠项。

## 执行边界与收尾

既有 API 授权适用于本任务的元数据/独立条款及只读凭据核验。新候选摘要/正文、付费模型、BIO 运行、大包下载、邮件、test 准入/冻结不在本批范围。执行方依据每项任务交付；协调方独立验收后才改工作包状态。

每个节点在根 progress.txt 记录，迭代排查记录 lesson.md；docs 变化运行 doc-organize。完成的交付快照归档，活动表保持真实状态。全部四项经裁定后再归档本活动执行单。
