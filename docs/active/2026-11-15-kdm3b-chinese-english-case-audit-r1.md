# KDM3B Diets-Jongmans 中英全文病例审计 R1

**Status:** in-progress
**Created:** 2026-11-15
**Completed:** —
**Scope:** 核实一篇中文病例的原文、出版方英文全文、转录本坐标、事实差异与变异记录
**PR:** N/A (research audit)

## 结论

PMC13037267 / PMID 41914422 / DOI `10.7499/j.issn.1008-8830.2508138` 是同一篇中英双语发表的 KDM3B 相关 Diets-Jongmans 综合征病例报告。PMC 可读中文全文，并在正文链接至出版方英文完整译文。英文译文保留同一名患者、相同表型、相同检测、相同 HGVS、相同亲代 Sanger 结果、相同 ACMG 作者分类及相同的未做功能验证限制。因此，病例、患者和变异均**不构成语言独占增量**。

盲态独立审阅确认一个精度差异：中文记胎龄 `38+5` 周，英语写 `38 weeks`，漏掉 5 天。这个差异改进孕周精度，却不增加患者或变异。两版还共享至少两项需要源数据核对的不一致：按 `NM_016604.4` 的 CDS 坐标，`c.5147` 对应转录本第 5258 位，而两版结构预测段落都把核苷酸写成“第 5174 位”；另有“检测到 17 个变异”与亚型数量 13+6+1+1=21 不相符。两项均不是翻译差异。

变异 `NM_016604.4:c.5147T>C (p.Leu1716Pro)` 的 HGVS 与 RefSeq 序列参考碱基一致；ClinVar 当前 KDM3B 基因记录快照中没有该 c.5147 或 p.Leu1716Pro 记录，Europe PMC 的精确文本检索只返回这篇原始病例。作者“未曾报道/ClinVar 未收录”的陈述与本次有限快照相容，但不等于临床意义已独立验证，也不能据此宣称全局新颖。应将 variant status 记为“作者报告 likely pathogenic；独立重分类与全局新颖性未确证”。

## 来源与检索工件

原始工件在 `benchmark/experiments/acmg_multilingual/candidate_audits/kdm3b_chinese_r1/`：

| 工件 | 用途 |
|---|---|
| `pmc_landing.html` | PMC 中文全文页面，包含 `article lang="zh"`、英文摘要与作者引用的出版方英文全文 URL |
| `publisher_english_fulltext_page.html` | 按 PMC 正文所列 URL 获取的出版方英文完整译文页面 |
| `epmc_record_retry.json` | PMID/PMCID/DOI/语言字段及全文链接目录记录 |
| `epmc_exact_variant_search_r2.json` | Europe PMC 对 `c.5147T>C` / `p.Leu1716Pro` 的精确文字检索原始响应 |
| `clinvar_gene_search_full.json` 与 `clinvar_gene_esummary_batch_*.xml` | ClinVar gene query 与 549 个 KDM3B UID 的完整 ESummary 分批快照 |
| `clinvar_transcript_search_full.json` 与 `clinvar_transcript_esummary_batch_*.xml` | ClinVar `KDM3B AND NM_016604.4` 查询与 529 个 UID 的完整 ESummary 分批快照 |
| `clinvar_gene_variant_scan.txt` | 两个完整 ClinVar 结果集合对 `c.5147` / `Leu1716Pro` 的精确标记扫描 |
| `refseq_nm_016604_4.gb` | NCBI RefSeq `NM_016604.4` GenBank 记录 |
| `source_acquisition_receipt.json` | 15 个源/派生工件的大小、HTTP 状态、来源 URL 和 SHA-256 绑定 |
| `clinvar_variant_search.json`、`clinvar_protein_search.json`、`clinvar_coordinate_search.json`、`clinvar_transcript_search.json` | 精确数据库探索查询及其 query translation / 结果边界 |
| `epmc_fulltext_error_500.json`、`ncbi_bioc_error_404.html` | 接口访问错误证据；不代表来源阴性 |

PMC 页面提供完整文章页面；标题、DOI、刊名、卷期页与 EPMC 条目一致。英文完整页面的主体含病例、辅助检查、讨论、图题与结论，不限于摘要。PMC 内容同时嵌入中文原文、英文摘要及作者列出的英文译文页面 URL。出版方翻译页使用脚本驱动，因此保留原始页面与 PMC 内嵌的完整英文翻译表示；关键句已逐段核查。

## 独立核查的事实维度

| 维度 | 中文原文与英文译文 | 审计判断 |
|---|---|---|
| 患者/病史 | 5岁3个月男童；语言发育迟缓；同一胎次、出生及家族史 | 同一患者；英文摘要和正文均有对应 |
| 临床表型 | 智力障碍、ASD、矮身材、长耳/大耳廓、宽鼻尖、尖下巴、漏斗胸、双侧隐睾 | 两版病例内容对应；无额外患者 |
| 孕周/出生情况 | 中文 `胎龄38+5周`；英文 `born at 38 weeks of gestation`；2.45 kg，出生身长不详 | 已由独立审阅确认漏译 5 天；译文精度差异，不是新增病例事实 |
| 体格/量表 | 身高 101.7 cm、体重 11 kg、BMI 10.6 kg/m²、韦氏总分 <45、语言 48、操作 49、CARS 35、社会生活能力量表 9 | 两版数字对应；量表“总分 <45 但子分 48/49”是共同源文问题，需查原始量表，不可擅改 |
| 神经检查/影像 | EEG 边界性；头颅 MRI 未见明显异常 | 两版一致 |
| 分子检测 | `NM_016604.4` exon 23，`c.5147T>C (p.Leu1716Pro)`；父母 Sanger 为野生型 | 两版一致；支持作者报告 de novo，不能替代实验室原始报告 |
| ACMG 分类 | 作者报 likely pathogenic，PS2+PM1+PM2_Supporting+PP2+PP3 | 两版一致；此处只记录作者判断，不作独立致病性重分类 |
| 功能证据 | 结构预测、氢键推断与跨物种保守性分析 | 两版一致；属于计算/预测证据，文章明确未做变异—表型功能验证 |
| 新表型主张 | 作者称首次描述 KDM3B 相关漏斗胸 | 中英文均有；它是同文主张，病例层仍不独占，因果关系仍未验证 |

## 变异规范化与数据库核验

NCBI RefSeq GenBank 记录给出 `NM_016604.4` 的 CDS 起始于 mRNA 第 112 位（1-based）。所以 `c.5147` 的转录本位置为 `112 + 5147 - 1 = 5258`；序列第 5258 位参考碱基为 T，与文章 `c.5147T>C` 相符。转录本第 5174 位是 C，不是文章说的 T；其对应 cDNA 位置为 c.5063。故正文结构段中“第 5 174 位核苷酸由 T 变 C”与该变异描述冲突。英文译文逐字保留同一数字，问题来自共同源文。

NCBI ClinVar `KDM3B[gene]` 查询返回 549 个 UID，按 500+49 分批下载；`KDM3B AND NM_016604.4` 返回 529 个 UID，按 500+29 分批下载。两组完整 ESummary 都未发现 `c.5147` 或 `Leu1716Pro`。Europe PMC 精确检索返回 1 个记录，即原病例本身，不能视为独立重复。当前证据仅界定为本次检索快照的范围，不支持“全球首次/绝对新变异”声明。正式评估还需基于规范化基因组 HGVS、组装版本、ClinVar/gnomAD/文献的日期化审查，以及对 ACMG 每条证据代码前提的独立复核。

## 翻译/源文差异的计数边界

本病例确认 1 项待纳入翻译保真汇总的事实精度差（孕周 5 天漏译）；共同源文坐标错误和共同的变异总数/亚型总数不匹配单列为源文质量问题。当前完成的对照不计新增文章、患者、家系或变异，也不能推断更广英文文献不存在相同临床信息。它说明双语获取有助于找出翻译损失，并不证明多语种在总体上平均增加了变异证据。

## 限制与后续

- 这是一例便利发现的同文双语案例，不进入总体效果分母。
- 独立审阅的是中英版本事实对应，不是对临床诊断、量表正确性或 ACMG 分类的独立临床验证。
- “首个漏斗胸表型”需用引用链和病例去重单独核查；不由语言差异推导。
- SOX10 中文候选仍在其单独目录，当前无可审计全文；访问失败不是英语阴性。
- 若总体问题是“多语种是否增加新变异/关系”，仍须使用预先抽样的疾病问题框架并将事件作为嵌套结果，而非先按已知变异或非英文候选文章筛样。

## 来源

- PMC / Europe PMC: PMID 41914422, PMCID PMC13037267, DOI `10.7499/j.issn.1008-8830.2508138`.
- PMC 页面中作者提供的出版方英文全文链接：`https://www.zgddek.com/fileup/1008-8830/HTML_EN/2026-3-353.html`.
- NCBI RefSeq: `NM_016604.4`，GenBank artifact retained above.
- NCBI ClinVar gene query: `KDM3B[gene]`，本次返回 549 UID；精确变异判断限于该日期化快照。
