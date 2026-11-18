# 多语种探索批次 R6：ADGB 与 TUBB3 中文全文

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:** —  
**PR:** N/A（探索性研究）

本批次新增两条已完成原文提取、英文对应边界、ClinVar 边界和双审/仲裁的中文全文候选。机器可读汇总见 [discovery_summary_r9.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/discovery_summary_r9.json)，批次工件见 [round6_adjudication_r1](../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/round6_adjudication_r1)。

同轮还登记了一条女性低促性腺功能不全队列访问线索（`PMC13077325`）；Europe PMC/NCBI 正文路线未提供可读正文，已标为 `access_unresolved_not_counted`，不进入候选矩阵，也不作为英文阴性。

## ADGB 少弱畸精子症队列

PMCID `PMC12979990` 报告 781 名原发不育男性的 ADGB WES 筛查，识别 148 个变异位点；其中一名深度表型患者携带复合杂合 `NM_024694.4:c.4859G>A (p.Arg1620Gln)` 与 `c.4981A>G (p.Lys1661Glu)`。该患者有严重 OAT、ADGB 蛋白缺失、精子顶体/鞭毛和 9+2 轴丝异常，研究还包括小鼠/人表达、免疫荧光、Co-IP 和 ICSI 妊娠结局。

同文英文摘要覆盖核心队列和病例。精确英文变异查询在本批次为零命中；`c.4981A>G` 在 ClinVar 有单提交者 VUS 记录，不能建立同一患者对应。该候选提供强多维生殖遗传学证据，但确认性文章、患者、家系、变异和语言独有事实增量均为 0。

## TUBB3 CFEOM 家系

PMCID `PMC12554870` 报告一个 CFEOM3 家系：10 岁女性先证者与母亲均受累，父亲和姐姐正常；WES/家系检测发现 `NM_006086.4:c.904G>A (p.Ala302Thr)`，并记录眼球运动、上睑下垂、动眼神经 MRI、家系分离、斜视手术和额肌瓣悬吊术后改善。

同文英文摘要覆盖核心家系。独立英文 CFEOM 队列 `PMC11325808` 报告 62 名患者，其中 8 名携带 TUBB3 变异，包含同一 `c.904G>A` 等位基因；ClinVar 为多提交者致病记录。等位基因复现不等于同一家庭或新增语言独有变异，因此确认性增量仍为 0。

## 统一边界

两条候选均保留为探索性多维证据，不进入确认性分母。矩阵更新见 [multidimensional_evidence_matrix_r2.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multidimensional_evidence_matrix_r2.json)。新增来源使描述性候选数达到 20，但不能据此推出多语种在总体上必然比英文获取更多证据。
