# 英文适配器全文恢复与原文提取 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

## 目的

英文 provider-native readiness 运行有 2,076 条访问记录，其中 1,996 条为 `no_access`。本批次只尝试恢复可验证全文路线，不修改已封存的英文 readiness ledger，不把访问失败、未决或摘要-only 编码为英文阴性。

检索层继续复用本地/GitHub `lit-acquisition`，本地路径为 `/data/yangzs/Projects/01_Platform/05_lit-acquisition`，commit 为 `14e3dbfd07f1a5e7fbc1257c7f9fea37e29dca40`。新增路线使用其 SSRF URL 校验和显式代理配置。

## 恢复路线与结果

### PMCID → Europe PMC XML

对 972 个唯一未决 PMCID 请求 `https://www.ebi.ac.uk/europepmc/webservices/rest/{PMCID}/fullTextXML`。只有 HTTP 200、JATS 根节点为 `article` 且 `<article-id pub-id-type="pmcid">` 与请求一致时才记为 `full_text`。

- 420/972 个唯一 PMCID 通过身份核验；
- 映射回原始访问记录后恢复 533/1,248 次 PMCID 访问；
- 其余超时或 HTTP 500 保留为未决。

### PMID/DOI → PMCID → Europe PMC XML

使用 NCBI PMC ID 转换接口分批解析 657 个 PMID 和 74 个 DOI：

- PMID 映射出 63 个 PMCID；
- DOI 映射出 11 个 PMCID；
- 21 个映射 PMCID 获得身份核验全文；
- 回映射时使用 `query_id + baseline_candidate_id`，因为原始 `access_records` 没有稳定 `occurrence_id` 字段。

合并两条 sidecar 后，恢复 554/1,996 次未决访问，剩余 1,442 次，未决比例为 `0.6946050096339114`，仍高于 B2 预注册的 0.10 门槛。

## 原文提取边界

恢复的 439 份 XML 被保存后，使用 `xml.etree.ElementTree` 从原始 JATS XML 提取文本；不读取翻译、不调用摘要替代正文。提取器排除 `<ref>` 与 `<ref-list>`，保留正文、表格和文章元数据。后续正则 triage 只用于排序，未作患者、变异或语言增量判定，也未进入确认性分母。

## 机器可读工件

- [PMCID XML 恢复脚本](../../scripts/recover_english_adapter_europepmc_xml_r1.py)
- [PMID/DOI ID 转换脚本](../../scripts/resolve_english_adapter_identifier_routes_r1.py)
- [映射 PMCID 恢复脚本](../../scripts/recover_english_adapter_resolved_pmcids_r1.py)
- [恢复覆盖审计](../../benchmark/experiments/acmg_multilingual/overall_design/english_adapter_recovery_audit_r1.json)
- [原始 XML 提取清单](../../benchmark/experiments/acmg_multilingual/overall_design/english_adapter_recovery_text_manifest_r1.json)
- [探索性全文 triage](../../benchmark/experiments/acmg_multilingual/overall_design/english_adapter_recovery_fulltext_triage_r1.json)

所有 sidecar receipt 都标记 `baseline_ledger_unchanged=true`、`english_negative_claim_allowed=false` 和 `confirmatory_admission=false`。当前 readiness 仍为 `not_ready`，双 reviewer、独立仲裁和确认性主检索均未由本批次自动准入。
