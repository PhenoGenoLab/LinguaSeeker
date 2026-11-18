# 多语种多维病例矩阵 R12（统一）

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R12 以 R11 为父矩阵，加入葡语恢复矩阵 R4；R4 中的 PYCR2、ARSA 和 ROR2 已存在，因此按 `candidate_id` 去重后只新增葡语 MLD 双兄弟记录。

| 来源语言 | 候选数 |
|---|---:|
| 中文 | 15 |
| 西语 | 13 |
| 英语 | 3 |
| 葡语 | 4 |
| 合计 | **35** |

新增记录提供 2 名患者、近亲家系、病程、康复和呼吸照护等证据，但没有患者级变异或遗传检测；因此不会被解读为多语种变异增量。确认性文章、患者、家系、变异和语言独有事实端点仍全部为 0。

机器可读工件：[R12 统一矩阵](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_multidimensional_case_matrix_r12_unified.json)。
