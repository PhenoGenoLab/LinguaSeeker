# 确认性实验门禁审计 R1

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:** —  
**PR:** N/A（检索前门禁）

## 已固定输入

- Orphadata 2026-06-23 已评估胚系关联/HPO 问题框：1,933 个问题。
- 主终点阈值：每题 `δ=0.25` 个有界英文审计独有事实单位。
- 抽样：固定种子简单随机无放回；60 题 manifest 仍是草案，不是功效样本量。
- 探索性候选全部排除于确认性分母。

机器可读门禁回执：[confirmatory_gate_audit_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_gate_audit_r1.json)。

## 已登记的范围选择

| 选项 | 已选 |
|---|---|
| 语言范围 | `1-1`：英、西、葡、中文 |
| 英文臂正文暴露 | `2-1`：英文查询命中的非英语全文可读，但作为同源暴露，不计语言独有 |
| 中文术语回退 | `3-1`：语言中性 ORPHA/HPO 标识符/语义槽回退，不冒充中文术语覆盖 |

## 其他未冻结门禁

1. 来源库、日期截点和两臂相同的查询/全文访问流程。
2. 每题查询模板、返回候选上限、全文获取预算和停止规则。
3. 最大未决/仅摘要比例、分层缺失上限和 MNAR 敏感性界间隔。
4. 单侧 α、多重性调整、优效下界、无效上界和中期观察次数。
5. 方差保护情景、最终功效样本量和未决样本膨胀规则。
6. 英文基线资格门：候选守恒、身份核验、来源哈希、双审与仲裁绑定。

现有 `α=0.0125` 和 60 题只是规划敏感性输入，尚未成为注册选择。确认性检索未启动；有界 no-match、同文英文摘要、译文和 ClinVar 记录均不能替代英文基线闭合。

## 查询语言可执行性审计

当前问题框的 1,933 行均有英文、西文和葡文疾病名，以及 HPO ID；没有中文疾病名字段。中文是否纳入不能只改 `query_languages` 数组，否则会产生系统性查询不对称。

- [query_language_readiness_audit_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/query_language_readiness_audit_r1.json)
- 中文 Orphadata URL 有界探针：[probe_summary.json](../../benchmark/experiments/acmg_multilingual/overall_design/candidate_frames/orphanet_hpo_product4_20260623/chinese_terminology_probe_20261116/probe_summary.json)；四个猜测路径最终均 HTTP 404，仅排除这些路径，不证明全球没有中文术语源。
- 选择 `1-1` 后已登记 `3-1` 语言中性回退契约：[chinese_query_fallback_contract_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/chinese_query_fallback_contract_r1.json)。
- 1,933 行无检索干跑已通过：[manifest](../../benchmark/experiments/acmg_multilingual/overall_design/chinese_query_fallback_dry_run_manifest_r1.json) 与 [receipt](../../benchmark/experiments/acmg_multilingual/overall_design/chinese_query_fallback_dry_run_receipt_r1.json)；所有行通过，未使用语言特定字段，且 `no_retrieval_performed=true`。
- 四语种模板干跑也已通过：[manifest](../../benchmark/experiments/acmg_multilingual/overall_design/multilingual_query_template_dry_run_manifest_r1.json) 与 [receipt](../../benchmark/experiments/acmg_multilingual/overall_design/multilingual_query_template_dry_run_receipt_r1.json)；1,933 行生成 7,732 个模板，中文臂未使用语言特定字段，未发生检索。
- 英文臂和多语种臂必须使用相同语义槽、来源库和预算；语言过滤只能作诊断分层。

该审计已完成范围选择和中文回退干跑，但未执行确认性检索。
