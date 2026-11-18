# 确认性准入状态 R5

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R5 接入延长超时的 Europe PMC 恢复审计。新增重试回收 581 个英文 access occurrence，恢复后未决比例为 41.47%，仍高于预注册 B2 的 10% 上限。

机器可读状态：[confirmatory_readiness_status_r5.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_readiness_status_r5.json)。

| 门槛 | 状态 |
|---|---|
| 离线计划校验 | 通过 |
| 英文 500 题执行 | 通过 |
| Europe PMC 超时恢复审计 | 通过（新增 581 个 occurrence） |
| 英文 B2 / recovery B2 | 未通过（41.47% 未决） |
| 原始 HTTP payload | 未通过 |
| R13 历史源包字节绑定 | 通过（22/22） |
| 两名 reviewer + 独立仲裁 | 未完成 |
| 最终 protocol reseal | 未完成 |

访问重试没有改变原始账本，也没有把失败记录转成英文阴性或确认性证据；`retrieval_authorized=false` 继续保持。
