# 确认性准入状态 R18

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R18 接入 PMID 路线元数据探针。首批 10 条去重 PMID 均返回元数据，但未暴露 PMCID；该探针支持路线优先级判断，不改变未决状态或确认性门禁。

机器可读状态：[confirmatory_readiness_status_r18.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_readiness_status_r18.json)。

| 门槛 | 状态 |
|---|---|
| PMID 路线优先级 | 已完成 |
| PMID 元数据探针 | 已完成（10 条，0 条 PMCID） |
| 英文 B2 | 未通过（822 条未决） |
| 双审/仲裁 | 未完成 |
| C3 主置信下限 | 尚不可检验 |
| 最终 protocol reseal | 未完成 |

`retrieval_authorized=false` 继续保持。
