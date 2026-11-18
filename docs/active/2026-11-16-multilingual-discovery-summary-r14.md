# 多语种发现汇总 R14

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:**  
**PR:** 未合并

R14 追加 R4 的两个西语线索到探索性总账：

- PMID 29333833 的肾-眼结肠综合征出版方 PDF 已完成全文提取、英文对应、双 AI 审阅和独立仲裁。由于英文臂允许读取同一非英语全文，仲裁排除该候选，文章、患者、家系、变异和语言独有事实增量均为 0。
- PMID 7940052 的先天性角化不良记录只有摘要，没有 PMCID、DOI 或开放全文路由；标记为 `abstract_only_access_unresolved`，不启动全文双审，不作英文阴性判断。

R14 不改变此前 R3 语言独有正文事实簇 1 的历史记录；R4 新增端点增量为 0。当前探索性总账的文章、患者、家系、变异增量仍为 0，确认性门禁仍未通过。

机器可读汇总：[discovery_summary_r14.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/discovery_summary_r14.json)

来源包：

- [R4 汇总](../../benchmark/experiments/acmg_multilingual/candidate_audits/orphanet_exploratory_round4_20261116/round4_summary_r1.json)
- [肾-眼结肠综合征审计](../../benchmark/experiments/acmg_multilingual/candidate_audits/orphanet_exploratory_round4_20261116/renal_coloboma_pmid29333833/candidate_audit.json)
- [肾-眼结肠综合征双审/仲裁](../../benchmark/experiments/acmg_multilingual/candidate_audits/orphanet_exploratory_round4_20261116/renal_coloboma_pmid29333833/ai_review_r1.json)
- [先天性角化不良访问收据](../../benchmark/experiments/acmg_multilingual/candidate_audits/orphanet_exploratory_round4_20261116/congenital_dyskeratosis_pmid7940052/abstract_only_access_receipt.json)
