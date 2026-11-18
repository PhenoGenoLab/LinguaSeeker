# 多语种多维病例矩阵 R9（统一）

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R9 以 R8 为父矩阵，加入西语恢复矩阵 R2。R2 中的 ARSA 记录已存在于 R8，因此按 `candidate_id` 去重后只新增西语 GLUT1 病例。

| 来源语言 | 候选数 |
|---|---:|
| 中文 | 15 |
| 西语 | 11 |
| 英语 | 3 |
| 葡语 | 3 |
| 合计 | **32** |

新增 GLUT1 原文病例包含 `SLC2A1 c.972+1G>T` de novo 变异、父母阴性、三人外显子组、MRI、临床和照护信息；同篇英文摘要已暴露，独立英文对应和 AI 仲裁未完成。所有确认性文章、患者、家系、变异和语言独有事实端点均为 0。

机器可读工件：[R9 统一矩阵](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_multidimensional_case_matrix_r9_unified.json)。检索器仍可复用本地/GitHub `lit-acquisition` 固定 commit；复用不解除全文、英文 readiness、双审和独立仲裁门禁。
