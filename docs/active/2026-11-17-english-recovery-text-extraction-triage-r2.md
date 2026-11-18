# 英文恢复原文抽取与 triage R2

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

将 Europe PMC XML、PMCID 解析和超时重试 sidecar 中的身份核验通过记录合并去重，得到 887 条原始 JATS 文本。抽取使用标准库 XML 遍历，排除 `ref/ref-list`，未使用翻译；随后用规则计数生成同规模 triage 队列。

机器可读工件：

- [原文抽取 manifest R2](../../benchmark/experiments/acmg_multilingual/overall_design/english_adapter_recovery_text_manifest_r2.json)
- [triage 队列 R2](../../benchmark/experiments/acmg_multilingual/overall_design/english_adapter_recovery_fulltext_triage_r2.json)

| 项目 | 数量/状态 |
|---|---|
| 原始 XML 文本记录 | 887 |
| triage 记录 | 887 |
| 翻译使用 | false |
| AI/人工端点审阅 | 未完成；全部 `triage_only_not_adjudicated` |
| 确认性纳入 | false |

规则 triage 只用于排序后续审阅，不证明病例、变异或语言独有事实，也不改变英文阴性状态和确认性分母。
