# 多语种遗传变异候选综合 R6

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:** —  
**PR:** N/A（探索性研究）

本轮在 R5 的 8 条候选之外，又完成 3 条高信息量病例/队列的原文提取、英文对应筛查、独立复核和仲裁：中文 ALPL 低磷酸酯酶血症队列、西语 GJB1/CMTX1 病例，以及西语 OTC 代谢-肝病病例。机器可读汇总见 [discovery_summary_r3.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/discovery_summary_r3.json)。

## 新增候选

| 候选 | 多维证据 | 英文对应/分子边界 | 处置 |
|---|---|---|---|
| ALPL/HPP，中文队列（PMCID PMC13684095） | 12 名患儿、3 个亚型；乳牙早失、骨骼/生长/运动表现、ALP、WES、亲本分相、ERT 与随访；19 个变异事件/18 个不同事件 | 同文英文摘要覆盖核心；出版方英文全文路线在本轮不可读；`c.191T>A` 英文命中仅为 ESHG 汇编，ClinVar 只确认部分其他等位基因 | 多维队列候选；文章/患者/家系/变异/语言独有事实增量均 0 |
| GJB1/CMTX1，西语病例（PMCID PMC13439794） | 13 岁男孩、母系家族、`c.20A>G (p.Tyr7Cys)`；黄蜂蜇伤后卒中样发作、双侧白质 MRI、血管影像阴性、24 小时恢复 | 英文精确命中为无关 UTR/基因面板语境；ClinVar 为 VUS；英语 CMTX1 病例为不同患者/变异 | 多维病例候选；增量 0 |
| OTC，西语病例（PMCID PMC13068355） | 37 岁男性、酒精相关肝病/胆管炎、肾损伤、低钾、显著高氨血症、综合治疗 | 原文只写“杂合致病 OTC 变异”，无转录本或 HGVS；同文英文摘要可检索 | 分子未解析负对照；不计变异或语言独有事实增量 |

## 共同边界

- 三条均有同文英文摘要或英文元数据，不能据此主张独立英文病例缺失。
- ClinVar 的已知等位基因只证明数据库记录，不证明患者或家系对应。
- 英文精确查询的有界命中/未命中不构成全球英文存在性或不存在性证明。
- OTC 缺少 HGVS，不能把作者的“致病变异”转成可去重的变异单位。
- 三条均排除于确认性分母；当前 11 条探索性候选的确认性文章、患者、家系、变异和语言独有事实增量仍为 0。

## 可复现工件

- [new case batch manifest](../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/new_multilingual_cases_20261116_r1/batch_manifest.json)
- [primary review](../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/new_multilingual_cases_20261116_r1/primary_review.json)
- [independent review](../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/new_multilingual_cases_20261116_r1/independent_review.json)
- [adjudication](../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/new_multilingual_cases_20261116_r1/adjudication.json)

这批材料扩展了多维证据覆盖，但仍不能证明多语种在总体上必然增加更多证据；总体估计必须等待确认性样本、英文基线和缺失门禁冻结。
