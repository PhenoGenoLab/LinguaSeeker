# 确认性准入状态 R7

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R7 将 887 条英文恢复原始 JATS 文本抽取和 triage 队列接入准入报告。抽取与排序门槛已通过，但它们仍属于探索性准备工作，不等于两名 reviewer 或仲裁完成。

机器可读状态：[confirmatory_readiness_status_r7.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_readiness_status_r7.json)。

| 门槛 | 状态 |
|---|---|
| 离线计划校验 | 通过 |
| 英文 500 题执行 | 通过 |
| XML / 超时 / HTML 恢复 | 通过 |
| 原始 JATS 文本抽取 | 通过（887 条） |
| 规则 triage 队列 | 通过（887 条，未审阅） |
| 英文 B2 / recovery B2 | 未通过（39.60% 未决） |
| 原始 HTTP payload | 未通过 |
| 两名 reviewer + 独立仲裁 | 未完成 |
| 最终 protocol reseal | 未完成 |

`retrieval_authorized=false` 继续保持；抽取、triage 和历史源包绑定均不改变确认性分母。
