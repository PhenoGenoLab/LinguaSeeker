# SH2B3 中文病例访问与英文对应审计 R1

**Status:** in-progress
**Created:** 2026-11-15
**Completed:** —
**Scope:** 记录 SH2B3 中文病例候选的摘要证据、全文访问状态与变异对应边界
**PR:** N/A (access audit)

## 当前状态

候选为 PMID 42161666 / PMCID PMC13195548 / DOI `10.3760/cma.j.cn121090-20251019-00472`，题名为 “Myeloproliferative neoplasm with a homozygous germline SH2B3 mutation: a case report and literature review”。EPMC 探索性中文查询的首屏记录标注 `language=chi`，摘要层报告一名59岁女性、纯合胚系 `SH2B3 c.1481C>A (p.S494*)`、VAF 100%、子女均为杂合携带且表型正常、MPN 表型及芦可替尼治疗反应。

这不是正文审计结果。PMC HTML 路线返回 Google reCAPTCHA 页面；EPMC landing/PDF 路线返回 HTTP 403；EPMC `fullTextXML` 返回 HTTP 500；DOI resolver 路线返回 HTTP 404；PubMed landing 返回 203。因而无法核实正文中的家系人数、检测方法、转录本、骨髓病理细节、变异分类、英文全文或同一患者的英文对应。

## 变异与计数边界

- 摘要给出的 `c.1481C>A p.S494*` 只能作为候选标签，尚未核对 transcript accession、参考基因组、ClinVar/gnomAD 或独立英文文献。
- 摘要说“first reported case in China”，这是作者主张，不是独立新颖性证据。
- 由于没有可核验原文正文，当前不计新增患者、家系、变异或事实单元；访问状态为 `unresolved`，不是英文阴性。
- EPMC 记录中显示的英文摘要属于同一记录的英文元数据层，不等同于完整英文正文。不能据此断言中文正文事实被英文覆盖或未被覆盖。

## 原始工件

所有响应保存在 `benchmark/experiments/acmg_multilingual/candidate_audits/sh2b3_chinese_r1/`。`source_acquisition_receipt.json` 绑定11个源/派生工件的大小与 SHA-256；`epmc_chinese_search_first_page.json` 保留原始探索性检索响应（654条命中，只检查25条首屏）。

这些错误页和摘要记录证明的是访问路径状态与候选存在，不证明原文内容缺失或英文没有对应。下一步需要取得可读正文或出版社正式英文页面后，才能做双重抽取、独立仲裁和事实级增量判断。
