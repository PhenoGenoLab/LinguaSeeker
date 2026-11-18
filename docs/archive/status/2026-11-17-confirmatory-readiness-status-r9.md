# 确认性准入状态 R9

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R9 接入 30 条英文病例候选清单。候选均有原始全文指针，但尚未完成逐篇源级提取、AI 双审或独立仲裁，患者/家系/变异单位保持未知。

机器可读状态：[confirmatory_readiness_status_r9.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_readiness_status_r9.json)。

| 门槛 | 状态 |
|---|---|
| 离线计划校验 | 通过 |
| 英文 500 题执行 | 通过 |
| XML / 超时 / HTML 恢复 | 通过 |
| 原始 JATS 抽取、triage、病例排序 | 通过 |
| 新英文病例候选清单 | 通过（30 条，观察单位未审阅） |
| 英文 B2 / recovery B2 | 未通过（39.60% 未决） |
| 原始 HTTP payload | 未通过 |
| 两名 reviewer + 独立仲裁 | 未完成 |
| 最终 protocol reseal | 未完成 |

候选清单保持探索性，`retrieval_authorized=false` 不变。
