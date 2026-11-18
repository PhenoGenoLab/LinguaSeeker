# 英文 PMC HTML 恢复 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

对 XML、超时重试和 identifier-resolution 后仍未决的 PMCID，新增 PMC HTML 路线探测。共处理 147 个候选，25 个页面通过 PMCID 身份核验，带回 39 个 access occurrence；响应原文与 SHA-256 保存在独立 sidecar。

机器可读工件：

- [PMC HTML receipt](../../benchmark/experiments/acmg_multilingual/overall_design/executions/english_adapter_pmc_html_recovery_20261117_r1/receipt.json)
- [merged recovery audit R3](../../benchmark/experiments/acmg_multilingual/overall_design/english_adapter_recovery_audit_r3.json)

合并后英文恢复未决比例为 39.60%，仍高于 B2 10% 门槛。HTML 访问成功不等于正文抽取或审阅完成；剩余失败仍保持未决，不编码为英文阴性。
