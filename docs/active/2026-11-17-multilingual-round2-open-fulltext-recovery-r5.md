# 多语种 R2 开放全文恢复 R5

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

从 q_0488 葡语候选补充 3 条 SciELO/开放期刊路线：

| 候选 | 结果 | 矩阵处理 |
|---|---|---|
| `10.34024/rnc.2013.v21.8152` 葡语 MLD 双兄弟 | 原始 PDF 恢复 | 纳入葡语 R4；2 名患者、1 个家系、临床/康复证据，无患者级变异 |
| `10.1590/S0004-282X1986000400016` 葡语 MLD 双胞胎题名记录 | 原始 PDF 恢复 | 排除；实际文件是一页作者更正说明，不是病例正文 |
| `10.1590/S0074-02761972000300006` 葡语 Krabbe | 当前 SciELO PDF 路线 502 | access-unresolved，不编码证据 |

当前恢复汇总为 13 条路线。双胞胎更正说明保留 `triage_exclusion.json` 和 OCR 哈希，确保不把题名误当作病例正文。机器可读汇总：[全文恢复汇总](../../benchmark/experiments/acmg_multilingual/candidate_audits/multilingual_round2_open_fulltexts_20261117/summary.json)。
