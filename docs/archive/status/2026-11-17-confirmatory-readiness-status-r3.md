# 确认性准入状态 R3

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R3 将历史来源绑定状态单独接入准入报告。R13 的 22 条 `pending_source_review` 行已经全部绑定到 R5 矩阵快照，但这不等于完成来源审阅、两名 reviewer、独立仲裁或确认性纳入。

机器可读状态：[confirmatory_readiness_status_r3.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_readiness_status_r3.json)。

| 门槛 | 状态 |
|---|---|
| 离线计划校验 | 通过 |
| 英文 500 题执行 | 通过 |
| 英文 B2 / recovery B2 | 未通过 |
| 原始 HTTP payload | 未通过 |
| R13 审阅队列生成 | 通过（36 条） |
| R13 历史来源快照绑定 | 通过（22 条，R5 SHA-256 已保存） |
| 两名 reviewer + 独立仲裁 | 未完成 |
| 最终 protocol reseal | 未完成 |

英文恢复后的未决比例仍为 69.46%，高于 B2 的 10% 上限；`retrieval_authorized=false`，所有探索性候选仍排除在确认性分母之外。
