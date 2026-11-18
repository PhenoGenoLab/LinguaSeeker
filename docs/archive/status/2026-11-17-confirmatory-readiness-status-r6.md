# 确认性准入状态 R6

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R6 接入 PMC HTML 恢复审计 R3。XML、超时重试和 PMC HTML 路线合计将英文未决比例降至 39.60%，但仍未达到预注册 B2 的 10% 上限。

机器可读状态：[confirmatory_readiness_status_r6.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_readiness_status_r6.json)。

| 门槛 | 状态 |
|---|---|
| 离线计划校验 | 通过 |
| 英文 500 题执行 | 通过 |
| XML / 超时恢复审计 | 通过（581 个 occurrence） |
| PMC HTML 恢复审计 | 通过（39 个 occurrence） |
| 英文 B2 / recovery B2 | 未通过（39.60% 未决） |
| 原始 HTTP payload | 未通过 |
| R13 历史源包字节绑定 | 通过（22/22） |
| 两名 reviewer + 独立仲裁 | 未完成 |
| 最终 protocol reseal | 未完成 |

`retrieval_authorized=false` 继续保持。访问恢复只改变 access 审计，不改变原始 500 题账本、探索性确认性端点或确认性分母。
