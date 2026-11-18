# 确认性准入状态 R10

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R10 接入英文恢复矩阵 R4 的 5 条新病例、多语种相对英文库存对比 R2，以及此前的源包、恢复、抽取和 triage 工件。R4 新增病例仍为探索性手工抽取，R2 对比仍明确不是总体优效检验。

机器可读状态：[confirmatory_readiness_status_r10.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_readiness_status_r10.json)。

| 门槛 | 状态 |
|---|---|
| 离线计划校验 | 通过 |
| 英文 500 题执行 | 通过 |
| XML / 超时 / HTML 恢复 | 通过 |
| 原始 JATS 抽取、triage、病例排序 | 通过 |
| 英文 R4 新增病例 | 通过（5 条，探索性手工抽取） |
| 多语种/英文库存对比 R2 | 通过（描述性、非优效检验） |
| 英文 B2 / recovery B2 | 未通过（39.60% 未决） |
| 原始 HTTP payload | 未通过 |
| 两名 reviewer + 独立仲裁 | 未完成 |
| 最终 protocol reseal | 未完成 |

所有探索性新增仍排除在确认性分母之外，`retrieval_authorized=false` 不变。
