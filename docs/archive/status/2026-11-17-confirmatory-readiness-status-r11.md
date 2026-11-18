# 确认性准入状态 R11

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R11 接入英文 R5 病例矩阵和多语种/英文库存对比 R3。R5 新增 5 条源级病例记录；R3 仍明确为描述性、非优效比较。

机器可读状态：[confirmatory_readiness_status_r11.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_readiness_status_r11.json)。

| 门槛 | 状态 |
|---|---|
| 离线计划校验 | 通过 |
| 英文 500 题执行 | 通过 |
| XML / 超时 / HTML 恢复 | 通过 |
| 原始 JATS 抽取、triage、病例排序 | 通过 |
| 英文 R5 新增病例 | 通过（5 条，探索性手工抽取） |
| 多语种/英文库存对比 R3 | 通过（描述性、非优效检验） |
| 英文 B2 / recovery B2 | 未通过（39.60% 未决） |
| 原始 HTTP payload | 未通过 |
| 两名 reviewer + 独立仲裁 | 未完成 |
| 最终 protocol reseal | 未完成 |

`retrieval_authorized=false` 不变，探索性病例和库存比较均不进入确认性分母。
