# 多语种遗传变异候选综合 R8

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:** —  
**PR:** N/A（探索性研究）

本轮新增两篇西语遗传病例全文：BCL11B 相关发育障碍病例和 USP27X 相关 X 连锁智力发育障碍家系。机器可读汇总见 [discovery_summary_r5.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/discovery_summary_r5.json)。

## 新增候选

| 候选 | 多维证据 | 分子/英文对应边界 | 仲裁结论 |
|---|---|---|---|
| BCL11B，墨西哥西语病例 | 4 岁男孩；发育/语言迟缓、行为、微头畸形、面容、牙齿、免疫球蛋白、CT、心超；WES 与 NMD assay | `c.363dup (p.Asp122ArgfsTer4)`；英文精确查询 0；ClinVar 已有 `c.363dup (p.Asp122fs)` likely pathogenic，反驳原文“未入 ClinVar” | 患者/变异/语言独有增量 0 |
| USP27X，西语母系家系 | 2 名男性病例；微头、语言/智力发育、行为、面容和指端异常；母亲及舅舅携带，姨母阴性 | `c.692delT (p.Leu231Trpfs*13)`；英文精确查询无同病例，蛋白写法命中无关机制论文；ClinVar bounded no-match | 家系/患者/变异/语言独有增量 0 |

两篇同一记录均带英文摘要，不能当作独立英文病例；原文细节保留为候选事实，不等同于英语全局缺失。

## 当前状态

累计 15 条探索性候选均完成相应来源审计或访问边界登记；确认性文章、患者、家系、变异和语言独有事实增量仍为 0。候选全部排除于确认性分母，不能据此证明多语种总体必然增加更多证据。

工件：[new Spanish cases batch](../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/new_spanish_cases_20261116_r1)。
