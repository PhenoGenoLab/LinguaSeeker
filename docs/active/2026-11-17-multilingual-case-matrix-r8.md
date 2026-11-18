# 多语种多维病例矩阵 R8（统一）

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R8 以 R7 为父矩阵，加入葡语恢复矩阵 R3。合并时按 `candidate_id` 去重；R7 已经包含 PYCR2 和 ARSA 两条葡语记录，因此只新增 ROR2 学位论文，避免重复计数。

| 来源语言 | 候选数 |
|---|---:|
| 中文 | 15 |
| 西语 | 10 |
| 英语 | 3 |
| 葡语 | 3 |
| 合计 | **31** |

葡语新增 ROR2 论文观察到 11 名患者、4 个家系图上下文和 13 个变异事件；这些数字描述原文证据宽度，不能直接转化为 11 个患者或 13 个变异的语言增量。所有记录继续区分 `observed_units` 与 `confirmed_increment`，确认性文章、患者、家系、变异和语言独有事实端点均为 0。

机器可读工件：[R8 统一矩阵](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_multidimensional_case_matrix_r8_unified.json)。父工件 SHA-256 已写入矩阵，检索器可复用本地 `lit-acquisition` 固定 commit `14e3dbfd07f1a5e7fbc1257c7f9fea37e29dca40` 或 GitHub 同源仓库；复用检索代码不替代英文 readiness、全文可审阅性、两名独立 AI reviewer 和独立仲裁门禁。
