# 英文恢复遗传病例候选排序 R2

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

基于 887 条原始 JATS 文本和固定英文查询计划，生成病例级候选排序。排序结合病例报告信号、HGVS 标签、患者/家系/测序/临床/影像/随访模式，用于安排后续原文审阅；不判断变异真实性、英文对应关系或确认性端点。

机器可读工件：[case rank R2](../../benchmark/experiments/acmg_multilingual/overall_design/english_adapter_recovery_case_rank_r2.json)。

| 项目 | 状态 |
|---|---|
| 输入文本 | 887 条，原始 JATS，未翻译 |
| 候选排序 | 887 条 |
| 审阅状态 | 全部 `candidate_queue_not_adjudicated` |
| 确认性纳入 | 全部 false |

查询标签仅表示候选由哪些固定问题召回；同一文章可能关联多个问题，不能据此推断病例属于某个 Orphadata 题框。
