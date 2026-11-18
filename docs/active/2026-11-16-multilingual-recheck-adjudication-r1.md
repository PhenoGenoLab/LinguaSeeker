# 多语种四条全文候选复核与仲裁 R1

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:** —  
**PR:** N/A（探索性证据包）

## 范围

本轮完成此前四条已取得全文但英文对应未闭合的候选：MUSK、CHD7、SSUH2 和 SLC25A20。审阅对象是已保存的中文 PMC 原文及英文对应查询收据；本轮不启动确认性检索，所有候选继续排除于确认性分母。

## 结果

| 候选 | 原文单位 | 英文对应边界 | 仲裁结论 |
|---|---:|---|---|
| MUSK（PMCID PMC13684089） | 1 名婴儿、1 个家系、2 个分相变异 | 两个英文精确查询均为 0；同文英文摘要覆盖核心；ClinVar 仅确认 c.2300G>A 为 VUS | 文章/患者/家系/变异/语言独有事实增量 0 |
| CHD7（PMCID PMC13481339） | 7 名新生儿、5 个报道的 CHD7/缺失事件；家系单位未单独定义 | c.481C>T 英文命中为无关语境；c.3378G>C 已在 ClinVar；同文英文摘要覆盖核心 | 增量 0；不接受“5 个新变异”的全球新颖性推断 |
| SSUH2（PMCID PMC13458854） | 1 个三代家系、4 名患者、1 个变异 | 同文英文摘要覆盖核心；2017 英文论文报告同一等位基因，但与本家系身份未闭合 | 增量 0；不把两个家系强行合并 |
| SLC25A20（PMCID PMC13273518） | 1 名新生儿、1 个家系、2 个分相变异 | DOI 匹配的同文英文全文译本可读；c.199-10T>G 有英文复现，c.823C>T 已入 ClinVar | 增量 0；译文不是独立英文文章 |

## 证据边界

- 同一记录的英文摘要或出版方译文不算独立英文病例来源。
- ClinVar 等位基因记录不等同于患者、家系或文章对应。
- `LANG:eng` 精确查询的 0 命中是有界诊断，不是全球英文缺失证明。
- 正文相对摘要的细节保留为候选事实，不能直接称为语言独有事实。
- CHD7 七名新生儿有亲本检测，但原文没有可安全计数的七个家系单位，因此家系终点不计数。

## 可复现工件

- [batch_manifest.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/batch_recheck_20261116_r1/batch_manifest.json)
- [primary_review.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/batch_recheck_20261116_r1/primary_review.json)
- [independent_review.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/batch_recheck_20261116_r1/independent_review.json)
- [adjudication.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/batch_recheck_20261116_r1/adjudication.json)
- [discovery_summary_r2.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/discovery_summary_r2.json)

四条候选均完成主审、隔离独立复核和第三方仲裁；探索性累计确认增量仍为 0。这一结果不能证明多语种在总体上必然增加更多证据，只能说明这些候选在当前有界对应审计中没有形成确认增量。
