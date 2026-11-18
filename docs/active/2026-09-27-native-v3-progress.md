# 原生多语言 v3 实施进度

**Status:** in-progress
**Created:** 2026-09-27

**Updated:** 2026-10-29

2026-10-29 路线已修订为[原文事实抽取与英文呈现](2026-10-29-native-source-fact-translation/README.md)；[发布 06](../archive/papers/2026-10-29-native-source-task-release-06/README.md)已发布两项离线任务，尚未执行/验收。下方 M/B2、费用、参考和复验数字仍属于旧方法的开发历史，不作为新路线效果；新主比较与统计目标未定。旧代码、参考、账本和封包不改，G1/G2 保持 Pending。

当前任务入口：[发布 05 活动执行单](2026-10-23-native-v3-next-stage-tasks.md)。2026-10-22 WP12 REV 局部修复已限定范围验收关闭；WP11/WP12 整体 in-progress，G1/G2 Pending。Aron 以[用户未暴露更正声明](../archive/papers/2026-10-16-aron-exposure-correction/README.md)为准，仍待准入；下文旧 B 答复及旧核查状态仅保留历史时间范围。

当前核查：[第三十四次当前 DAG 预算预恢复闭环复验](../archive/papers/2026-09-27-plan-progress-audit/recheck-34.md)与[完整证据](../archive/papers/2026-09-27-plan-progress-audit/recheck-34-evidence.json)。74 项测试及全量 Ruff 通过；40 个父臂、140 组结果和 5,726 次请求匹配零调用缓存重放通过，原入口五份 CSV、报告、分组与账本副本逐字节一致。

第33次唯一剩余P1已关闭：首轮失败/次轮成功后，重启在首节点前恢复全部$0.011100，两次重启均零新增调用并保持原消费。40/40文献方法预恢复金额与当前DAG全部既有事件的独立费率计算一致，总规划$38.851835；重复恢复、缓存查询计数与全局增量均为零。五类跨窗口失败续跑及充足预算正对照通过，未发现新的阻断项。**WP10 当前开发产物与离线纠正复验记为 completed-offline；G1/G2 不提升。**

严格计数保持 M 71/495/1106、B2 81/655/1096；pooled ΔF1=-0.00321501，19组CI[-0.01195335,+0.01300326]，文献加权宏平均组CI[-0.01590671,+0.01881391]。主方法1981事件规划$18.43307250/刊例估算$3.39833938；额外审核3750事件$20.41876250/$2.74412002，联合与历史分区保持。原报告披露历史仅有$150全局预算，当前联合重放为$10文献方法上限，不追认历史逐篇预算。

范围与限制：WP06原四篇离线验收保持completed-offline；20篇参考/seal与上一轮字节相同，491/493患者参考主体仍未定。当前纠正通过不证明M优于B2或专家参考已验收。G0未在本轮整体验收；G1旧缺失/逐次凭据与正式结算仍待补，G2另有来源、样本量和冻结条件。1598个独立输入文件、三个HEAD和暂存区保持，无真实API调用或实现改动。以下保留历史时点记录。

设计完成，工程框架已开始，尚未通过 G0 或真实模型预检。

- [2026-09-27 核查报告](../archive/papers/2026-09-27-plan-progress-audit/README.md)
- [详细设计与执行计划](../planned/2026-09-25-native-evidence-experiments/01-design.md)
- [工作包状态](../planned/2026-09-25-native-evidence-experiments/work-packages.csv)

下一节点：[BIO 开发可行性与 Rett 测试来源准备](2026-10-15-native-v3-bio-and-test-readiness.md)。WP11/WP12初步盘点报告和两份暴露清单已[归档](../archive/papers/2026-10-15-wp11-wp12-offline-inventory/README.md)，工作包准入仍为in-progress。后续检索维持Rett；ABC单列域外，不因同刊同领域强制合组；Aron于2026-10-16经用户B项自述确认已暴露，归calibration并排除Test-v3；[事件记录](../archive/papers/2026-10-16-aron-exposure-attestation/README.md)已归档，当前五条intake无可继续按未暴露Rett来源推进的条目，需补充新来源。可准备tmVar3已暴露开发集小样本测试，先固定版本、资源、条款和输入；本轮未运行BIO或付费模型。已纠正G1四篇56次翻译与WP10累计258次的范围混淆、西班牙语开发集遗漏；25行账本须与55行历史清单统一核验。WP10 completed-offline、G1/G2待验收状态保持。

最新：[二次核查](../archive/papers/2026-09-27-plan-progress-audit/recheck.md)。HEAD cfc623b，7 测试及 Ruff 通过；G0 未完整验收、G1 未完成，WP10 仍待执行。

最新：[第三次核查](../archive/papers/2026-09-27-plan-progress-audit/recheck-3.md)。模拟编排有所推进；参考语义与真实预检未通过，G1 仍未完成。

最新：[第四次核查](../archive/papers/2026-09-27-plan-progress-audit/recheck-4.md)。多数票筛选、窗口传递等已改进；真实模型、来源定位、预算阻断、参考身份和选文验收仍欠缺。

2026-09-28 最新：[第五次核查](../archive/papers/2026-09-27-plan-progress-audit/recheck-5.md)。bec8136 的修复已确认；来源版本统一、预算上界、full gate 和主体身份仍待修，G1 未完成。

最新：[第六次核查](../archive/papers/2026-09-27-plan-progress-audit/recheck-6.md)。16 测试通过，源文/样本修复确认；预算和病例绑定仍待解决，WP10待执行。

最新：[第七次核查](../archive/papers/2026-09-27-plan-progress-audit/recheck-7.md)。07bcc2a定向验证通过，三项集成反例未通过，G1/WP10状态不变。

2026-09-29 最新：[第八次核查](../archive/papers/2026-09-27-plan-progress-audit/recheck-8.md)。上轮三项修复确认；19测试通过，坐标有效性/原译映射仍未验收，G1未完成。

最新：[第九次核查](../archive/papers/2026-09-27-plan-progress-audit/recheck-9.md)。21测试通过；原译坐标基础检查改善，同事实重复与主体归属仍未验收。

最新：[第十次核查](../archive/papers/2026-09-27-plan-progress-audit/recheck-10.md)。23测试通过，文献级去重和各轨主体核验仍待闭环，G1未完成。

最新：[第十一次核查](../archive/papers/2026-09-27-plan-progress-audit/recheck-11.md)。25测试通过；跨窗口全轨主体一致性仍待修，G1未完成。

最新：[第十二次核查](../archive/papers/2026-09-27-plan-progress-audit/recheck-12.md)。26测试通过，跨路径不一致关闭；无编号队列被默认patient_1仍待修，G1未完成。

最新：[第十三次核查](../archive/papers/2026-09-27-plan-progress-audit/recheck-13.md)。27测试通过，主体证据推断与未知接纳仍未验收，G1未完成。

2026-09-30 最新：[第十四次核查](../archive/papers/2026-09-27-plan-progress-audit/recheck-14.md)。29测试通过；上轮四项关闭，参考共识/原文冲突仍未验收，G1未完成。
