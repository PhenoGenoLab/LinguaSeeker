# 多语种发现汇总 R13

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:**  
**PR:** 未合并

R13 在 R12 的 25 条已审计候选基础上，新增西语 PMCID `PMC11469105` 的哥伦比亚遗传性远端肌病系列。原文包含 12 名患者和 12 个 HGVS 事件；同记录英文摘要已覆盖患者系列和基因列表，精确等位基因也有有限英文/数据库命中。

两个独立 commandcode 模型和一个独立仲裁模型均同意保留该来源。按协议去重后的端点为：

| 端点 | 增量 |
|---|---:|
| 文章 | 0 |
| 患者 | 0 |
| 家系 | 0 |
| 独立变异 | 0 |
| 语言独有正文事实簇 | 1 |

12 个 HGVS 表格事件被保留为一个语言独有的正文事实簇，避免把同一文章的表格误写成 12 个新的独立变异。该候选仍排除确认性分母。

机器可读汇总：[discovery_summary_r13.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/discovery_summary_r13.json)
