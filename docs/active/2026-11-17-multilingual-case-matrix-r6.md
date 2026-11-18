# 多语种多维病例矩阵 R6（统一）

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R6 将统一矩阵 R5 与两条葡语原始全文病例合并：

| 来源语言 | 候选数 | 观察患者单位 |
|---|---:|---:|
| 中文 | 15 | 880 |
| 西语 | 9 | 13 |
| 葡语 | 2 | 2 |
| 英语 | 3 | 10 |
| 合计 | 29 | 905 |

葡语新增来源为 PYCR2 晚发低髓鞘白质营养不良和 ARSA juvenile metachromatic leukodystrophy。两条均有出版方原始 PDF、患者级临床/遗传/影像或实验室/治疗信息；ARSA 文章还包含两个精确 HGVS 和纵向随访。PYCR2 原文没有精确 HGVS，保留为未标准化状态。

机器可读工件：[R6 统一矩阵](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_multidimensional_case_matrix_r6_unified.json)。R6 的确认性文章、患者、家系、变异和语言独有事实增量全部为 0。样本是便利探索样本，语言来源访问层级和同记录英文暴露不均衡，因此不能据此证明多语种总体优于英文。
