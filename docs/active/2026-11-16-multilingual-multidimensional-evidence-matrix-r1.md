# 多语种多维证据矩阵 R5（R1–R4 快照保留）

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:** —  
**PR:** N/A（探索性研究）

## 目的与范围

本矩阵把已完成双审和独立仲裁的中文、西语探索候选按证据维度编码，用于检查“正文是否提供多维病例/队列信息”这一机制问题。它不是确认性样本，也不估计多语种相对英文的总体增量。

当前机器可读工件：[multidimensional_evidence_matrix_r5.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multidimensional_evidence_matrix_r5.json)。R1–R4 保留为历史快照；R5 引用 [discovery_summary_r12.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/discovery_summary_r12.json)，其 SHA-256 在 JSON 工件中登记。

## 编码结果

| 指标 | 结果 |
|---|---:|
| 中文候选 | 15 |
| 西语候选 | 7 |
| 葡语候选 | 3 |
| 报告患者单位（嵌套计数，不跨文献合并） | 898 |
| 临床/发育证据 | 25/25 |
| 分子事件 | 24/25 |
| 遗传检测 | 25/25 |
| 家系/遗传模式 | 22/25 |
| 影像/病理 | 21/25 |
| 实验室/生化 | 21/25 |
| 治疗/随访 | 23/25 |
| 生殖/子代结局 | 3/25 |
| 确认性文章、患者、家系、变异、语言独有事实增量 | 均为 0 |

“分子事件”按原文可稳定识别的 HGVS 或结构事件编码；OTC 候选缺少可标准化 HGVS，因此不补造变异单位。ADGB 的 781 是一篇文章内的筛查队列人数，另有 1 名深度表型患者；队列中的患者、家系和变异事件保持嵌套关系，不能把报告患者数直接相加作为独立总体样本量。

## 解释边界

正文存在而同文英文摘要缺失，只能说明摘要覆盖不足；同文英文摘要、译文、ClinVar 等位基因记录或有界英文未命中不能证明全球英文不存在对应证据。所有候选继续排除确认性分母。该矩阵也不支持“多语种获取在总体上一定比英文增加更多证据”的结论；这一结论只能由冻结问题框、同源来源库、预设缺失处理、独立审阅和正式总体估计支持。

确认性方案当前已记录 `1-1`（纳入中文）、`2-1`（英文查询命中的非英语全文可读但不计语言独有）和 `3-1`（语言中性 ORPHA/HPO 回退）。回退契约见 [chinese_query_fallback_contract_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/chinese_query_fallback_contract_r1.json)；1,933 行无检索干跑全部通过。预算、缺失/MNAR、功效和英文基线门仍未冻结，确认性检索未启动。
