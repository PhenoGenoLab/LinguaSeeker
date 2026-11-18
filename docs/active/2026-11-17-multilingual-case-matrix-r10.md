# 多语种多维病例矩阵 R10（统一）

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R10 以 R9 为父矩阵，加入西语恢复矩阵 R3；R3 中 ARSA 与 GLUT1 已存在，因此按 `candidate_id` 去重后只新增 Joubert 谱系表型记录。

| 来源语言 | 候选数 |
|---|---:|
| 中文 | 15 |
| 西语 | 12 |
| 英语 | 3 |
| 葡语 | 3 |
| 合计 | **33** |

Joubert 记录提供临床、家系和影像/病理多维观察，但没有患者遗传检测或报告变异；R10 将其明确编码为 `variant_event=0`、`molecular_variant=false`。这扩展了证据维度库存，却不能支持多语种相对英文的变异增量或总体优效结论。

机器可读工件：[R10 统一矩阵](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_multidimensional_case_matrix_r10_unified.json)。确认性文章、患者、家系、变异和语言独有事实端点均为 0。
