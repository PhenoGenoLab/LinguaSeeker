# Native-v3：BIO 开发可行性与 Rett 测试来源准备

**Status:** in-progress
**Created:** 2026-10-15
**Updated:** 2026-10-29
**PR:** not created

[初步盘点归档](../archive/papers/2026-10-15-wp11-wp12-offline-inventory/README.md) · [设计](../planned/2026-09-25-native-evidence-experiments/01-design.md) · [工作包](../planned/2026-09-25-native-evidence-experiments/work-packages.csv)

## 2026-10-29 当前路线入口

用户已批准[原文抽取、核验后事实英译](2026-10-29-native-source-fact-translation/README.md)。[发布 06](../archive/papers/2026-10-29-native-source-task-release-06/README.md)新增 NATIVE-R1/EVAL-R1 离线任务；WP11-R2 的 BIO 适用性按新研究问题解释，允许有依据的不可行报告，不要求先跑 BIO。WP12 来源、权利、暴露和分组要求保持。旧设计与下方记录用于历史审计，不能直接启动旧 M/B2 主矩阵。发布 05 的四项任务继续跟踪，原验收状态不提升。

## 2026-10-23 新任务发布（发布 05 执行入口）

[发布 05](../archive/papers/2026-10-23-native-v3-task-release-05/README.md)已发布 WP12-R3 来源准入证据、BASE-R1 早期工作包与参考可评估性对照、WP11-R2 BIO 路线决策、G1-R1 外部凭据对账四项；执行与验收分别在[新活动执行单](2026-10-23-native-v3-next-stage-tasks.md)跟踪。WP13–WP21 按依赖进入后续队列，未启动正式实验。

2026-10-22 的 REV 局部修复验收保持关闭，R2-C1 不再返工/重封。WP11-C2 保留，WP11/WP12 整体 in-progress，G1/G2 Pending；候选均未准入/冻结。以下各日期记录按当时范围保留，旧 changes_requested、待封包或 Aron 旧暴露答复不得覆盖最新裁定。

## 2026-10-22 REV 本地修复验收通过

[协调方验收](../archive/papers/2026-10-22-wp12-rev-local-acceptance/README.md)：WP12-R2-C1本地修复accepted_for_this_scope，REV local acceptance=passed。60项封条完整；30行CSV全部34列；150主张64/70/16/0；194引用/69不同引用守恒；68真实来源定位及原日志核对通过。由保留快照重放两项纠正后register与提交件逐字节一致；逗号回归临时探针在写入前退出1、原字节保持；五份派生产物逐字节复现，候选9 changed/21 unchanged。

MED/24750837历史开发暴露supported已落实，保留same_document排除和未准入/未冻结。本轮本地补正关闭，不再重复封包；一处unresolved_items旧短语记为非阻断说明遗留，由当前已纠正身份/排除裁定覆盖，后续版本清理即可。原包submitted/changes_requested为提交时快照，当前结论以上述独立验收为准。

30候选仍全部not_admitted/frozen=false；文章权利、Aron全团队暴露/准入、注册分歧、八条DOI、俄语关联等继续留待来源准入。WP11-C2本地交付保留，WP11/WP12整体in-progress，G1/G2 Pending；没有发布BIO、盲测或正式冻结。以下记录保留此前时间范围。

## 2026-10-21 来源定位验收与最终本地剩余项（当前）

[本轮独立验收与明确裁定](../archive/papers/2026-10-21-wp12-final-local-review/README.md)：上轮报告5项封条核实；新提交59项全包封条通过，68个实际引用source_path/哈希及14个JSON定位均有效（另1个none），来源定位修正关闭。150主张63/71/16/0、候选8变更/22未变、三份派生逐字节重放均通过；req11/108与req12状态标签已纠正。完整链后的Aron声明无来源缺口，团队暴露和准入未决保留。

REV本地范围只剩MED/24750837历史暴露裁定未落实。原源文题名、8名作者顺序及DOI字符串与已保存PubMed元数据对应；DOI字符串存于pii字段，源文件哈希与C1-001一致，历史exposed_dev排除成立。执行方应在最终生成器落实该行supported（限历史开发暴露）并保留排除/未准入，不能只改措辞仍写unresolved；同步派生计数和当前说明后最后封包。无需用户重新裁定或新API。外部许可/八条DOI等未知不阻塞此项；WP11-C2本地项关闭，WP11/WP12整体in-progress，G1/G2 Pending。以下记录保留此前时间范围。

## 2026-10-21 重封包与门禁验收（当前）

[本轮复验](../archive/papers/2026-10-21-wp12-reseal-review/README.md)：58项封条与完整非缓存集合一致，嵌套历史封条补齐；supported/unresolved引用缺失、哈希错误、字节数错误、无效指针五个单一缺陷探针均正确阻断，正常对照通过。这些技术门禁和封条项关闭。五步派生的三份输出逐字节复现，150主张63/71/16/0，30候选未准入/未冻结。

REV仍changes_requested，仅继续原A/B的本地剩余义务：rett_006源路径/哈希再次核实存在，新backlink脚本却写回source path not located并降级历史排除；69个manifest entry仍缺明确来源路径/请求元数据定位。补正现有生成器与当前说明并最后封包，不因外部许可等待。req11/108实际HTTP200且载荷为DOI does not exist，req12才是HTTP404。WP11-C2本地项保持关闭，两个WP整体in-progress，G1/G2 Pending。以下段落为先前阶段记录。

## 2026-10-21 A/B 补正复验（最新协调方结论）

[本轮独立验收](../archive/papers/2026-10-21-wp12-ab-reacceptance/README.md)：12个C1 works与Aron声明回链通过，150主张计数63/71/16/0、30候选守恒，六份隔离派生逐字节复现；52份R2响应、12份refetch与14个本地指针核验通过。supported引用缺失、原日志哈希错误、单一无效指针分别以1项对应问题阻断，关闭这些分支。

REV仍changes_requested。原A剩余rett_006历史暴露排除在claim层被错误降级；原B对unresolved行引用缺失及日志字节数错误仍退出0，须依原任务统一文件完整性门禁及来源路径。56项现有封条均通过，但58个非缓存文件中漏列两份嵌套历史SHA256SUMS，既有封条生成器可枚举全部58项。只补这些剩余项并同步说明；不重开本轮已通过的works/Aron回链或既有F2/F3，不需新API或候选正文。WP11-C2本地项保留关闭，WP11/WP12整体仍in-progress，G1/G2 Pending。下方记录保留其历史时间范围。

## 2026-10-21 R1–R3 独立验收（当前）

[独立验收与限定续办](../archive/papers/2026-10-21-wp12-r1-r3-independent-acceptance/README.md)：56项全包封条、52份当前R2响应的原日志哈希/字节数、30候选守恒、8/22候选变更及六份隔离派生重建均通过。REV仍changes_requested，执行方“R1–R3全部完成”尚未成立：12个已有C1 works记录未进入最终claim map，Aron更正事件仍被当作外部无来源，rett_006已验收历史排除仍被claim层降级；外部清单在响应缺失的隔离探针中仍返回0/problems=[]。

只执行[两项限定补正](../archive/papers/2026-10-21-wp12-r1-r3-independent-acceptance/continuation.md)：接回已有内容证据，以及让清单依原始日志核验并对缺失/篡改/指针失效阻断；随后一次同步说明与封条。真实许可、八条DOI搜索与准入未知不阻止本次本地验收。F2/F3及WP11-C2本地项不重开，WP11/WP12工作包仍in-progress，G1/G2 Pending。以下复验收尾段保留为执行方提交时记录，以本段协调方验收为准。

## 2026-10-21 WP12 REV 复验收尾

[REV 复验记录](../archive/papers/2026-10-20-wp12-r2-c1-rev-followup/README.md)确认当前150条主张的51/83/16/0计数、10项当前封条及5项pre-F1快照通过；匹配器隔离输出重放的4份产物逐字节一致，固定规则下0 strict、1 author+year、120/120合成控制。F2失败记录分离与F3计算可复现性通过，REV仍changes_requested。

三项本地收尾已完成（[REV follow-up 记录](../archive/papers/2026-10-20-wp12-r2-c1-rev-followup/continuation.md)）：R1 claim map的provenance/locator在完整重建后保留，150行非空；R2 外部清单对R2请求与C1文件逐一磁盘回读哈希（0问题），整包封条覆盖56个非缓存文件并回读通过；R3 response、候选变更表、README与本计划已同步。C1-001已定位到rett_006源文件及哈希；PubMed DOI字符串在pii字段，保留MED/24750837历史暴露排除。C1已有12个精确DOI的Crossref works记录，不能因新包未引用而全部降为无证据。Aron更正事件作为用户自述有据，准入仍pending；其余真实未知继续保留。REV未通过，等待协调方验收。

本目录为共享符号链接，须跟随扫描；“docs/active无WP12引用”已由本轮纠正。本次不新增网络或BIO操作，无修订敏感性结果则19组bootstrap条件未触发。WP11-C2既有交付保留，WP11/WP12仍in-progress，G1/G2 pending。上述检查始于10月20日，10月21日完成索引、进度与封包收尾。

## 2026-10-20 WP12 修复表验收与剩余任务

[独立核查](../archive/papers/2026-10-20-wp12-r2-c1-register-review/README.md)确认30候选ID守恒、全部not_admitted/frozen=false，92个当前引用响应的字节/哈希及28响应130书目项分母成立；claim map实际30行，26行evidenced只是hash-only。WP12-R2-C1判changes_requested：缺逐主张文本/内容定位，req74空响应哈希仍在3行许可凭据字段，匹配0/20未交可复现过程，SHA256SUMS仅3项且response-to-acceptance缺失。

执行[同编号补正任务](../archive/papers/2026-10-20-wp12-r2-c1-register-review/continuation.md)：先补完整内容证据与封包。WP11-C2现有50项封条通过，状态submitted_with_external_blockers；三条规则在10月15日WP12 §6及10月20日离线说明已有记录，纠正“未开始/未写入”表述，不重做已完成本地项。MED/32820509注册机构已有req7/23/104，req8失败保留历史，不阻断已有结论；req74可沿既有API授权限定补取，真实许可未知可保留。未修订敏感性结果时不要求立即重算bootstrap。WP11/WP12仍in-progress，G1/G2 pending。

## 2026-10-20 G1 对账修复收尾

[G1 本地账本重建与勘误](../archive/papers/2026-10-20-g1-reconciliation-ledger-repair/README.md)已完成：按当前合并账本重建 13 行分层及 15,049 行追溯，独立 Decimal 复算与报告逐行比对通过。当前 CSV 与报告更新，修复开始时的版本保留为 as_found；最初 CSV 字节未找回，不宣称原件恢复。1b/1c/3a/3b、总 token 及重试次数已勘误，910 条多次尝试推得 1,266 次前序尝试。规划总额 $101.21298875（含模拟/未计量预算），刊例估算 $15.11169653；历史缺证仅称本地未留存，云侧/Billing 未核验，G1/G2 仍 pending。

本次收尾的 53 份非审计输入哈希保持，包括账本、参考/seal 及 WP10 产物。WP11 保持 submitted_with_external_blockers，WP12 保持 in-progress；本次未推进新 BIO 或来源任务。后续沿原 WP12-R2-C1 交付清单继续权利表、claim map、更正事件与封包，原 API 授权有效，无需重复请求。

## 本轮决策

用户委托决定下一步疾病范围、Aron 暴露处置与 tmVar3 开发测试范围。本轮安排如下；尚未冻结测试名单或正式实验协议。

| 事项 | 决策 | 当前状态 |
|---|---|---|
| Test-v3 疾病范围 | 后续检索维持 Rett；扩充独立 Rett 来源 | 现有5条intake中4条ABC域外，Aron经用户更正恢复为待准入候选；需补充新独立Rett来源 |
| ABC 四篇心脏文献 | 单列域外候选，不用于补足 Rett 样本 | 同刊同领域不足以合为一个 publication group；团队/系列关系待核验 |
| Aron 2019 | `unexposed_by_user_attestation`、`candidate`、`pending_admission_review` | 2026-10-16用户明确更正误选B；尚未准入或冻结 |
| tmVar3 | A 路线分阶段验收：保留原版完整路径，先补正资源/许可/输入方案 | 2026-10-18 R1 退回补正；未发布大包下载或样本运行任务 |

Aron 当前以2026-10-16[用户更正声明](../archive/papers/2026-10-16-aron-exposure-correction/README.md)为准：用户明确说明此前B选错，实际未读正文，也未用于提示词、规则、标注或输出调试。记录为用户自述未暴露，恢复待准入候选；旧B记录保留并由新事件取代当前处置。此声明尚不独立证明团队全部人员或系统无历史暴露；不替代来源组、权利和冻结审查。

## WP11：限定的开发试验

1. 固定 tmVar3 的 commit/release、运行依赖、模型及字典资源，保存取得时间、官方出处、内容哈希和各自条款。现有材料只报告读到 COPYING，尚未完成这些版本级记录。未核实工具的 403/404 不代表整体服务不可用，也不证明许可不存在。
2. 预先选择 2–3 篇已经用于 Dev-v3 的文献，以语言、篇幅和输入格式覆盖为准，不根据模型成绩挑样本；记录选择理由。只使用既有原文、已缓存译文和本地工具，不新增付费翻译或提取调用。
3. 本次 tmVar3 子任务只检查变异提及与规范化输出。GNormPlus/GNorm2 的基因能力需另行核验；tmVar3 成功不等于 gene+variant 对照或完整原子事实 schema 已可行。
4. 运行前固定输入格式、offset 单位、译文到原文映射规则和无法映射时的表示。原生能力、适配器行为与语义审核分别留痕；不得凭实体提及赋病例、极性或支持标签。
5. 交付版本/输入清单、运行命令与日志、原始输出、格式/坐标有效性、失败记录，以及耗时、内存和依赖资源占用。任何准确率或召回率估计须有事先定义的对应参考和分母；未建立时仅报告兼容性与可定位性。

复用已有译文的本次新增模型费用可为零；独立部署的 MT 成本必须保留。56 次 translate、规划 $1.011777 / 刊例 $0.220633 来自 G1 四篇预检。WP10 批次累计为258次、$4.317680 / $0.941686，包含历史探索。后续按当前依赖哈希和文献/窗口拆分，不能直接用任一批次平均数外推新 test 成本。

完整事实 schema 的 BIO 对照目前未形成可行实现。是否将 gene/variant 子任务作为次要对照，须在正式冻结前写明比较范围、映射和分母；主要 M/B2 比较暂不改变。

## WP12：来源与暴露准入

1. 合并核验[25行开发/候选清单](../archive/papers/2026-10-15-wp11-wp12-offline-inventory/05-wp12-exposure-ledger.csv)和[55行历史材料清单](../archive/papers/2026-10-15-wp11-wp12-offline-inventory/exposure-ledger.csv)，建立规范来源 ID、别名、DOI/哈希、暴露类型及证据路径。不能只与20篇开发集查重。
2. 对 rett_004/080、006/082、007/083、011/087 的别名关系保留原记录并指向规范 ID；按来源去重后才统计文献数量。团队/系列关联与文档身份分别记录，不用不同 PDF 哈希证明独立。
3. 对新的 Rett 候选先做题录层盘点，记录作者、机构、项目/病例系列、语言、获取路径和权利状态，并与上述暴露集合检查关联。研究团队的正文阅读或开发使用继续写入暴露账本。
4. Aron 已依据2026-10-16用户明确更正恢复为待准入候选；合并账本时同时保留原B和更正事件，以更正事件为当前声明。不得将它作为已暴露tmVar3开发样本；已有西班牙语开发文献rett_035，Aron不构成新语言层。
5. 产出可追溯的候选纳入/排除/待核验理由；疑似关联可保守处理，但不得据同刊同领域断言共享病例或强行合组。

## 2026-10-16 准备进展

[本次核查与输入准备归档](../archive/papers/2026-10-16-wp11-wp12-readiness-update/README.md)：

- 两份暴露表的80行原始证据已派生归并：60个ID经5组既有别名映射为55个规范来源条目。补发现rett_036→rett_035的Stage-1映射；未另做原刊身份复核。新表保留原始行、文件和哈希，尚未验收为完整准入主账本。
- Aron采用用户明确更正后的未暴露声明，恢复待准入候选；不纳入开发测试。
- tmVar3与GNorm2提交已固定，官方条款与资源证据已保存；GNormPlus官方包目录和免责声明已检查。除tmVar3的已留存公有领域声明外，相关许可/资源条款仍有缺口，不能提升为全栈许可验收。
- tmVar3开发预选rett_007/078/071，按文字系统与篇幅下中位数选样；16个已有译文窗口已导出并核对原文覆盖，尚未运行。下一步需固定兼容资源、输入格式和供应商坐标单位；译文跨度到原文映射未建立。
- 首批30条Rett题录已保存（143条命中的第一页）；其中Aron命中旧intake，其余29条仍待完整历史身份/暴露核对。机构、病例系列、权利与准入待补，未读候选正文。

## 2026-10-16 tmVar3 启动探针

[代码资源与启动失败记录](../archive/papers/2026-10-16-tmvar-runtime-probe/README.md)：已取得并固定368,594,869字节代码包（SHA256 `526d173cfdd72792df723e80c537d15283c6369651aba80cf36367e103f73b63`）。原版JAR在空输入探针中因缺`Database/rs.rank.txt`退出1；源码证实输入遍历前依赖4个Database文本文件，Test分支后续进入SQLite归一化。没有处理3篇开发样本，也没有输出提及结果。

下一步先固定兼容数据库及条款、解决基因前处理依赖，再落实输入封装、坐标验证和16窗口运行。当前不通过填空数据库或修改供应商分支宣称原版可运行。启动探针不代表BIO性能测量。

## 2026-10-17 任务发布与验收分工

用户指定本协调助手负责发布下一步任务和独立验收成果。[发布01任务书](../archive/papers/2026-10-17-native-v3-task-release-01/README.md)及输入封条已归档。R1 两项已提交，2026-10-18 独立验收结果如下；原任务书中的 issued/pending 为发布时快照。

| 任务 | 执行状态 | 验收状态 | 下一交付 |
|---|---|---|---|
| WP12-R1 候选来源核验 | submitted | changes_requested | 漏查来源、身份字段、多语匹配和获取/权利证据补正 |
| WP11-R1 运行资源决策 | submitted；运行仍有资源/许可阻塞 | changes_requested | 纠正资源事实，补齐 A 路线可执行计划和固定输入契约 |

执行方自检记录保留；[协调方独立验收](../archive/papers/2026-10-18-native-v3-r1-independent-acceptance/acceptance.md)另存，不覆盖原提交。工作包完成、test准入/冻结与G1/G2状态分别判断。

## 2026-10-18 独立验收与补正任务

66份原始产物、8份发布输入及两份交付封条通过；候选30/shortlist9/关系35、五组别名和合成坐标检查复核通过。WP11包内实际含libcrfpp.so.0，免责声明相同哈希来自相同原文，不能当复制错误；原16窗口与两模型封条已复核。WP12漏查了registry已指向的rett_088/089，55条历史作者均留空、49条题名留空；rett_006与PMID24750837同文献发现经独立核对成立。

[发布02任务书](../archive/papers/2026-10-18-native-v3-task-release-02/README.md)明确采用A的分阶段路线，保留原版提及/规范化可行性路径，先验收资源和许可方案；本次不发布约99GB下载或BIO运行，也不修改正式方法定义。

| 任务 | 执行状态 | 验收状态 | 下一交付 |
|---|---|---|---|
| WP12-R1-C1 | in-progress；收到俄语关系部分进展说明，未见完整 C1 交付 | pending | 完整历史覆盖/书目字段、候选关系与获取/权利核验补正包 |
| WP11-R1-C1 | in-progress；已有 7 份部分草稿 | changes_requested（部分草稿）；完整 C1 未验收 | 纠正资源不可定位判断，完成精确依赖/条款/容量与16窗口契约 |

单一执行者优先WP12补正；两项可独立提交。外部缺证允许如实保留unresolved，但已有证据遗漏和错误判断须纠正。补正范围验收通过不等于工作包完成；下一次资源取得/有限运行由协调方另行发布。Aron声明已解决，不重复询问；所有候选继续not_admitted/frozen=false。

## 2026-10-19 C1 阻塞核查与续办

[续办指令及当日资源证据](../archive/papers/2026-10-19-native-v3-c1-continuation/README.md)：在验收主机重新找到固定代码包并核对完整SHA256，CRF库、模型及源码均为可读取的包成员；16个开发译文窗口及其历史费用字段存在，rett_088/089的reviewed_source存在。未取得的Database资源与未明确的许可保留，不据此暂停本地静态检查、书目补全或合成测试。

继续执行原C1，不另等下一轮。公开官方条款、题录和独立权利信息的联网核验已在发布02授权，再次确认无需重复申请；不读取新候选摘要/正文。Route A保持分阶段方案，本轮仍不发布大包下载或BIO运行。俄语两条保留possible_link，不合并身份、不计为两个已证实独立来源。进展按子节点写progress，不等待整个工作包完成。

## 2026-10-19 C1 部分成果与 rett_085 准据

[本次独立验收与资源决定](../archive/papers/2026-10-19-native-v3-c1-source-and-resource-decision/README.md)：314个解包普通文件与原包逐项哈希一致；本地覆盖为50/55，16组双路径中15组一致、rett_085不同。CRF静态观察仅部分接受，依赖矩阵仍需补齐分片、实际入口和组件条款；根COPYING应为NCBI公有领域声明，非BSD。

rett_085冻结实验准据为v2/v3共同绑定的source.txt（SHA256 bb46f0c100a4a70529a94086337cdf2dcb7fad4c9bc3cc75789921911fbc060a）；两份Markdown保留各自历史用途。WP12书目优先引用冻结文本、查重对三版分别执行并取命中并集，保留exposed_dev，不用副本差异暂停其余来源核验。原registry的2023年题录需在新派生版本以纠正事件处理，旧证据不改。

本次不发布数据库下载或来源未指定的GNormPlus输出取得任务。执行方先完成精确资源/容量峰值/兼容检查方案、实际本地使用条款、固定16窗口输入与gene输出来源契约；再分发条件单列，不能单凭缺再分发许可断定本地使用不可行。其余C1本地和已授权元数据工作继续，完整交付仍待验收。

## 状态与完成条件

### 2026-10-20 离线说明补充核查（当前）

[本轮独立核查](../archive/papers/2026-10-20-wp11-wp12-offline-prep-review/README.md)确认R2原始证据93匹配/8不符/4缺失/11无保存体及MED/24608581误命中拒绝有依据。补取16份部分文件与前次快照一致，12响应字节及映射核验结论沿用。新说明尚未交付30行权利表、claim map、更正事件、README/response与封条；继续优先完成原WP12-R2-C1离线封包，8条无DOI可如实unresolved，不因尚未全部识别而暂停提交。

G1新措辞的方向接受，但报告总表/原CSV仍有8处irrecoverable_historical_gap，§2.2仍有“无法事后恢复精确输出token”的无范围限定表达；须用带版本勘误/分类覆盖表统一，不覆盖原CSV。报告哈希已由ed5a4cf7…变为b509729b…，变更及旧新完整哈希已留痕，仍须配套修订说明；其余65项保护原件未变。G1/G2保持pending。

WP11当前依据为C2路线与成本交付，旧planned/04含已纠正静态结论，不能据此重开已关闭项。16窗口已留存成功收据规划$0.2426475/刊例估算$0.0527595/复用新增$0保持；未来BIO运行成本未测。WP11 submitted_with_external_blockers，两个WP均in-progress。

### 2026-10-20 补取核验及离线封包续办（阶段记录）

[协调方阶段核验及续办要求](../archive/papers/2026-10-20-wp12-r2-c1-refetch-review/README.md)：12个Crossref请求已完成，13次尝试中12份响应的磁盘字节/哈希与日志一致；035第1次SSL EOF有日志但没有响应文件，不能称13份响应哈希通过。12行旧新映射核验通过，旧提交141份文件未变；24–31各5项、32有20项、33–35为0项，无abstract字段。阶段结论仅为补取字节及请求映射已核实。

WP12-R2-C1剩余工作继续执行：30行rights-register、逐主张claim-evidence-map、更正事件、README/response、脚本诊断整理及最终SHA256SUMS。默认Ruff已通过；Optional类型警告需明确工具与诊断后最小修正，保留真实执行版本，离线验证不重跑fetch。交付编制in-progress，整体验收pending；不将子阶段核验算作14/14全部完成。

用户已明确授权任务中可以调用API，当前任务所需公开书目及独立许可信息接口可直接使用，不再等待API授权。现有本地响应足以开展表格重建；继续按已定任务范围与证据要求执行。WP11保持submitted_with_external_blockers，两个工作包均in-progress，G1/G2待验收。

### 2026-10-19 权利证据定向补取与发布04（历史快照）

用户已将待办核对为13/14完成、1项blocked；WP11-C2为submitted_with_external_blockers，保留外部资源/条款与运行前置。协调方本轮复核WP11-C2的50份封条文件、WP12-R2的89份封条文件通过，不重开用户已关闭的其他本地项。

WP12剩余项为30候选权利核验。原C1历史盘点的范围验收保留；R2已路由30行，但原始证据验收未通过。105条记有保存路径的请求中，93条与日志哈希匹配、24–31共8条不匹配、32–35共4条缺失。整包SHA256SUMS通过不能代替逐请求证据核验。

[发布04：WP12-R2-C1定向补证](../archive/papers/2026-10-19-wp12-r2-evidence-repair-release-04/README.md)已批准重取12个原URL，执行方可直接继续，沿用既有元数据/独立条款授权。24–35实际全部是Crossref限定字段查询，不涉及文章页。本轮仅发布任务、未执行网络补取。新请求/响应使用独立编号和不可覆盖路径；原缺陷保留，新证据不冒充旧响应复原。

8条缺DOI、MED/38684295 DOI矛盾和7条无license字段仍分别unresolved。补取后以新日志/文件哈希、30行派生权利表及逐项证据映射重新验收；所有候选仍not_admitted/frozen=false。WP11/WP12均in-progress，G1/G2保持pending。

### 2026-10-19 C1 范围验收与发布03（历史快照）

[独立验收与发布03](../archive/papers/2026-10-19-native-v3-c1-acceptance-and-release-03/README.md)记录本轮决定。WP12-R1-C1 accepted_for_this_scope：17封条文件/86证据哈希通过，30候选、80原始行、25 shortlist、40 links、50/55本地覆盖均复核一致；全部not_admitted/frozen=false。权利和独立来源准入尚未完成，MED/29213044与29359720保持possible_link。

WP11资源运行保持blocked_with_evidence，C1决策包changes_requested：条款CSV四行错列，Route A误写排除GNormPlus，窗口/换行契约与固定16输入不符，历史MT费用误记unknown，资源峰值及命令需补正。22封条文件和27项有哈希证据通过，11项合成检查通过；这些不替代实际运行验收。

| 当前任务 | 发布状态 | 验收条件 |
|---|---|---|
| [WP11-R1-C2](../archive/papers/2026-10-19-native-v3-c1-acceptance-and-release-03/wp11-r1-c2.md) | issued | 修正条款/路线/16窗口封装/费用/资源分阶段方案；外部未决证据独立列示 |
| [WP12-R2](../archive/papers/2026-10-19-native-v3-c1-acceptance-and-release-03/wp12-r2.md) | issued | 30行权利跟进：8缺DOI、1已可回填、9已知DOI未命中、7缺许可字段、5许可链接范围核验 |
| [NCBI询证](../archive/papers/2026-10-19-native-v3-c1-acceptance-and-release-03/ncbi-inquiry-draft.md) | draft ready; not sent | 由项目联系人以真实署名发送限定技术询证，分别保留发送/回复证据；不阻断本地补正 |

只读数据库大小查询已完成：压缩包106,570,426,433字节；解压大小/兼容性仍未验证，本轮未下载数据库。固定16窗口成功翻译收据的规划归因成本$0.2426475、现有费率刊例估算$0.0527595；本次复用新增模型费$0。未留存尝试及实际Billing边界仍保留，不整体记unknown，也不宣称完整结算。

公开元数据/独立条款页核验继续沿既有授权；本轮未执行候选后续联网队列或发送邮件。WP11/WP12均in-progress，不启动BIO、付费调用、测试材料读取或准入/冻结。

状态权威：[work-packages.csv](../planned/2026-09-25-native-evidence-experiments/work-packages.csv)记录工作包状态，本文件记录未完成任务。归档报告的 `Status: completed` 仅指文档快照完成，其独立字段 `Work package status: in-progress` 表示工作包未验收。

账本权威：C1历史身份登记与80行追溯已在盘点范围验收；完整测试准入主账本尚未验收。Aron当前处置以2026-10-16用户更正事件为准，原始盘点快照保留。25行开发/候选表与55行历史表是互补证据快照，均须保留；它们共同20个来源ID，各自另有5个候选和35个历史条目。后续统一账本的准入依据仍需逐项核验。

- 已完成：初步离线盘点报告归档、已知文字及费用范围纠正、索引/工作包/进度同步、下一步范围明确；2026-10-16 Aron误选B的更正声明已记录，恢复待准入候选。
- WP11 `in-progress`：C2本地补正按用户核验关闭，submitted_with_external_blockers；资源条款、兼容数据库和开发样本运行尚待完成，尚无样本输出。
- WP12 `in-progress`：C1历史盘点范围验收保留；R2-C1的12份补取响应及映射已核实，30行权利表/逐主张证据/封包待提交，整体验收pending；独立来源认定与准入尚待完成。
- WP10 保持 `completed-offline`。参考主体审计中的建议修订及其19组敏感性区间尚未在本轮验证；原参考、seal、账本和 WP10 产物保持不变。
- G1/G2 保持待验收。WP13 可准备分析方法与假设表，正式样本量和功效/精度目标须结合可评估参考与新来源；WP14 待这些输入齐备后冻结。

归档的是已完成的初步盘点文档，不代表整个 WP11/WP12 已验收。未完成计划保留原位置，通过上述链接连接归档证据，归档不以断链为理由延期。

## 2026-10-21 WP12 当前计数更正

- 上文 2026-10-21 REV 复验段所引 51/83/16/0 为当时计数，已被后续 works 回链取代。当前150行：`supported` 63、`unresolved` 71、`not_applicable` 16、`refuted` 0。
- 外部清单以 request-log.jsonl 的记录哈希核验，不再使用重读列；负向探针（缺失原始文件、哈希不符、指针失效）各返回 exit 1，记录于 `wp12-r2-c1-delivery/negative-probes-2026-10-21.md`。真实输入 problems=0。
- 封条重算为56个非缓存文件，`sha256sum -c` 通过。WP11/WP12仍分别为 submitted_with_external_blockers / in-progress；G1/G2 Pending；REV 未通过。
