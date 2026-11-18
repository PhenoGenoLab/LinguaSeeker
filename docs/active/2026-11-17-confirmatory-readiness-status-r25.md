# 确认性准入状态 R25

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**   
**PR:** 未合并

R25 将 Orphadata 多语种探索 R5 的扫描、候选排序、全文恢复、原文提取、triage 和多维矩阵接入 readiness。Round5 工件均通过哈希和不变量检查，但仍属于探索性发现。

机器可读状态：[confirmatory_readiness_status_r25.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_readiness_status_r25.json)。

| 门槛 | 状态 |
|---|---|
| Round5 多语种筛选 | 已完成（10 题、40 查询、原始响应保留） |
| Round5 全文恢复 | 已完成（16/20；4 条 PMID-only 未决） |
| Round5 多维矩阵 | 已完成（14 条、72 条原文引文） |
| 英文 B2 | 未通过（822/2,076 条未决，至少还需恢复 615 条） |
| 原始 HTTP payload | 未完成 |
| 两名 reviewer + 独立仲裁 | 未完成 |
| C3 主置信下限 | 尚不可检验 |
| 最终 protocol reseal | 未完成 |

Round5 的观察患者、家系和变异事件不等于确认性增量；所有确认性端点为 0，`retrieval_authorized=false`、`overall_superiority_proven=false` 和 `confirmatory_admission=false` 继续保持。
