# RPS6KA3 Chinese full-text versus English-abstract fact screen R1

**Status:** completed
**Created:** 2026-11-15
**Completed:** 2026-11-15
**Scope:** Exploratory, source-specific fact screen; no confirmatory increment adjudication
**PR:** N/A (research note)

## Question and result

Does the Chinese body of this Coffin–Lowry syndrome family report contain patient-level facts omitted from its English abstract?

**Yes, as a source-specific comparison.** The full text reports developmental scores, imaging, ancillary tests, parental findings, and more differentiated half-sibling histories that are absent or compressed in the publisher's English abstract. The abstract already contains the headline variant, mother/proband segregation, broad sibling description, follow-up, and literature-summary totals.

This does **not** establish an article-, patient-, family-, or variant-level increment beyond English retrieval. The article has an English title and publisher English abstract, and the English abstract itself contains `RPS6KA3 c.1603-2A>G`. The candidate body-level details are not yet searched against a frozen English full-text correspondence protocol, independently dual-reviewed, or arbitrated. None is counted in the primary numerator.

## Source identity and provenance

- Article: [Case Report of One Family With Coffin-Lowry Syndrome and Literature Review of 28 Cases in China](https://jsu-mse.com/index.php/journal/article/view/1218)
- PMID: `41536659`; PMCID: `PMC12796916`; DOI: `10.12182/20251160204`
- Body language: Chinese, verified in the PMC full-text XML and publisher page.
- English comparator: publisher page's English abstract; it is a discovery/summary layer, not an English full-text copy.
- PMC full-text XML SHA-256 at retrieval: `31043b51aa43279df230d22be7c75de9b7a10827a51b58f3667ec6a33f67c8db`
- Publisher HTML SHA-256 at retrieval: `d1fe0db5a5b26408d9842ea69993fd8c01c1a63fa96afa2b7b9653e0e7345997`
- Europe PMC record response SHA-256: `c0d7ea6d2110baf77a657c5ffa2f9ffc566460422c5bbd93f1cede00bc16a303`
- Exploratory English-correspondence query `RPS6KA3 AND "c.1603-2A>G"` returned the same indexed article (response SHA-256 `16510d117b1b1d590c0f833c34071c6f7abe0de96b912961784367cf76036620`). OpenAlex full-text search for `RPS6KA3 "c.1603-2A>G"` also returned the article (response SHA-256 `93e36bc25cbc5c1236d43b3c02dec23073619f85626e87228690a3e1010f5045`). These are exploratory provider checks, not the frozen English baseline.

Hashes bind the retrieved bytes only. They do not certify the accuracy of the paper's clinical interpretation, variant classification, or the completeness of English correspondence searching.

## Fact-level candidates

The locator format is JATS section ID/title plus paragraph order: `s01` is 病例资料; `s02` is 文献复习. English-abstract coverage describes only the same article's publisher abstract. Whole-English-literature equivalence remains pending for every candidate. Row groupings below are for review and are not a prespecified counting ontology.

| Candidate | Original Chinese quote and locator | Normalized fact for review | Same-article English abstract | Current disposition |
|---|---|---|---|---|
| F01 presentation/birth | `患儿，男，1岁8天，以“语言及运动发育落后”就诊。患儿为G 3 P 3 ，足月出生，出生体质量3200 g，无出生窒息史` — `s01/p[2]` | Male proband presented at 1 year 8 days; term birth, birth weight 3,200 g, no birth asphyxia. | **Partial:** says “1-year-old boy”; omits exact age and birth history. | Source-supported; independent review agrees. Not a new patient or increment. |
| F02 developmental chronology | `6个月前当地儿保发现运动落后……该患儿5月龄开始抬头，1岁翻身，不会独坐……不能扶物站立……无抽搐病史` — `s01/p[2]` | Motor delay noted before 6 months; head control at 5 months; at 1 year could roll but not sit independently or stand holding an object; no seizures reported. | **Partial:** broad developmental delay/hypotonia only. | Source-supported timeline; whole-English equivalence pending; not counted. |
| F03 feeding and anthropometry | `母乳喂养，按时添加辅食，喂养困难。体格检查：体质量7.72 kg，身高69.2 cm（<P3），头围45.2 cm` — `s01/p[2]` | Feeding difficulty; at examination weight 7.72 kg, height 69.2 cm (<3rd percentile), head circumference 45.2 cm. | **Partial:** growth retardation, without measurements or feeding detail. | Source-supported; age/measurement interpretation retained as reported; not counted. |
| F04 detailed physical findings | `前额突出，前囟宽大，眼裂下斜，眼距宽，鼻头大、鼻孔前倾，大嘴，唇厚；耳大、耳位低……手掌肉厚，手指关节过伸，手指短且呈椎体样` — `s01/p[2]` | Detailed craniofacial, ear, and hand findings. | **Partial:** broad facial and tapered-finger descriptors. | Body provides granularity beyond the abstract; not a new patient/fact until the prespecified unit is applied. |
| F05 spine radiograph | `脊柱正侧位片显示腰5隐形脊柱裂，余未见异常` — `s01/p[2]` | Spine radiographs reported L5 spina bifida occulta and no other abnormality. | Not stated in the English abstract. | Source-supported candidate detail; English-literature search pending. |
| F06 echocardiogram and EEG | `超声心动图：卵圆孔未闭，左向右分流；脑电图未见异常` — `s01/p[2]` | Echocardiography reported a patent foramen ovale with left-to-right shunt; EEG was unremarkable. | Not stated in the English abstract. | Distinct test observations; remain tied to the proband; not counted. |
| F07 MRI | `头部磁共振成像（MRI）提示：双侧大脑半球白质容积偏少，胼胝体偏薄` — `s01/p[2]` | MRI showed reduced bilateral cerebral white-matter volume and a thin corpus callosum. | Not stated in the English abstract. | Source-supported candidate detail; English-literature search pending. |
| F08 hearing and hand X-ray | `耳声发射：双耳未通过；X线片双手末端指骨短、簇状` — `s01/p[2]` | Both ears failed otoacoustic-emission testing; hand radiographs showed short, tufted distal phalanges. | Not stated in the English abstract. | Keep hearing and skeletal observations separately linked to the proband; not counted. |
| F09 initial GESELL scores | `GESELL发育测评：适应性DQ52；大运动DQ30；精细动作DQ57；语言DQ61；个人社会DQ61` — `s01/p[2]` | Initial GESELL scores: adaptive 52, gross motor 30, fine motor 57, language 61, personal-social 61. | Not stated in the English abstract. | Source-supported assessment vector; do not count each score as an independent unit. |
| F10 age-2 scores and follow-up | `2岁GESELL测评：适应性DQ27；大运动DQ25；精细动作 DQ15；语言DQ21；个人社会DQ10。3岁时随访患儿仍不能独走，无任何有意义语言` — `s01/p[2]` | At age 2, GESELL scores were adaptive 27, gross motor 25, fine motor 15, language 21, personal-social 10; at age 3 the child could not walk independently or use meaningful language. | **Partial:** broad developmental outcome but no domain scores. | Source-supported; scores remain a grouped time-point vector; not counted. |
| F11 independent walking at 3y8m | `3岁8月随访……患儿可独走数米，但不稳，仍不会说话` — `s01/p[2]` | At 3 years 8 months, the child could walk independently several meters, unsteadily, and still could not speak. | **Ambiguous/partial:** English abstract says “not capable of walking steadily independently or speech”; body clarifies independent walking was possible but unsteady. | Independent review flagged an ambiguity; root adjudication accepts the Chinese wording. Do not rewrite as “unable to walk independently.” |
| F12 mother and father | `母亲智力正常，身高150 cm，鼻塌，嘴大，唇厚，前额突出，手厚而软、锥形手指` — `s01/p[3]`; `父亲未检测到该突变` — `s01/p[4]` | Mother is reported as cognitively normal with specified features; paternal testing did not detect the variant. | **Partial:** mother carrier is reported, but her clinical details and paternal result are omitted. | Source-supported; do not infer maternal Coffin–Lowry diagnosis from this passage. |
| F13 maternal half-brother | `同母异父的哥哥，9岁，4岁开始走路，6岁开始说话，能说单词表达需求，现走路不稳，易发作性跌倒，重度智力低下` — `s01/p[3]` | Maternal half-brother, age 9, walked from age 4 and spoke from age 6; unstable gait, episodic falls, severe intellectual disability. | **Partial:** abstract says he had similar clinical manifestations, without this trajectory. | Source-supported; no sibling genotype is reported; not a confirmed variant-positive patient. |
| F14 maternal half-sister | `同母异父的姐姐，7岁，语言运动发育无异常，成绩差，当地曾诊断轻度智力低下` — `s01/p[3]` | Maternal half-sister, age 7, no reported language/motor abnormality, poor school performance, and prior local mild-ID diagnosis. | **Partial/ambiguous:** abstract groups her with siblings as having similar manifestations and omits this distinction. | Local diagnosis is attributed, not independently established; no sibling genotype reported. |
| F15 assay methods | `对患儿及其父母进行全外显子基因组检测，最后用Sanger测序方法验证` — `s01/p[4]` | Whole-exome testing was performed on the proband and both parents; Sanger sequencing was used for validation. | **Partial:** abstract only says genetic analysis. | Methods as reported; sibling testing is not specified and should not be inferred. |
| F16 variant and segregation | `RPS6KA3基因17号内含子上发生 c.1603-2A > G 半合子突变，母亲发生杂合突变，父亲未检测到该突变` — `s01/p[4]` | Proband hemizygous for intron-17 `c.1603-2A>G`; mother heterozygous; father result negative. | **Partial:** abstract reports proband and mother, not paternal result or validation method. | Variant/parent result is already abstract-visible; transcript accession is not given; no increment. |
| F17 author classification/database search | `查阅ClinVar、DGV、HGMD及PubMed此变异未收录……参照ACMG指南将……判断为致病性变异（PVS1+PM2+PP4）` — `s01/p[4]` | Authors report database/literature searches and classify the variant using PVS1+PM2+PP4. | **Partial:** abstract calls the variant previously unreported, without search details or criteria. | Author interpretation only; not independently validated, not a pathogenicity conclusion by this audit. |
| F18 review search frame and denominator | `在中国知网、万方数据库、PubMed数据库以……检索自建库至2025年7月……中文文献6篇，英文文献5篇，加上该家系4人，共有28例患者` — `s02/p[1]` | Authors report searches of CNKI, Wanfang, and PubMed through July 2025; their synthesis totals 28 patients including four from this family. | **Partial:** abstract gives 28 total, not search sources/cutoff/article counts. | Secondary synthesis, not 28 new observations; independent deduplication not performed here. |
| F19 review phenotype frequencies | `认知及语言运动发育迟滞（92.6%，25/27）、肌张力低（95.2%，20/21）、锥形手指（88.5%，23/26）……听力异常（40.9%，9/22）……头颅MRI异常（62.5%，5/8）……` — `s02/p[2]` | The review reports feature frequencies with feature-specific denominators that vary by data availability. | **Partial:** abstract includes selected frequencies but not all features/denominators. | Secondary literature synthesis; cannot be pooled as newly observed patient facts. |

### Control facts already present in the English abstract

The English abstract includes the reported `c.1603-2A>G` variant, a hemizygous proband, a heterozygous mother, broad half-sibling findings, follow-up through age 3 years 8 months, the 28-person Chinese literature summary, and selected cohort feature frequencies. Those items are not counted as details newly supplied beyond that abstract. The 28-person summary is secondary synthesis and is not a count of new independent patients.

## Independent review and root adjudication

A separate blind AI reviewer independently re-opened the publisher English abstract and Chinese JATS full text without seeing the initial candidate table. The review agreed with the source identity/language, the abstract-visible variant and maternal carrier, and the warning that siblings were not genotyped. It identified additional reportable details: exact presentation/birth history, L5 spina bifida occulta, hand radiographs, two GESELL time points, literature-review search frame/frequencies, and a potentially misleading compression of walking status in the English abstract.

The root adjudication checked these disagreements against the retrieved JATS paragraphs and publisher abstract. The Chinese text says the child **could walk independently for several meters, but unsteadily**, at 3 years 8 months; it should not be coded as “unable to walk independently.” The abstract's wording is ambiguous and less precise. The sister's normal reported language/motor development is also a qualification to the abstract's broad phrase “similar manifestations.” These are accepted as source-to-abstract coverage differences, not as evidence absent from the entire English literature.

## Review and counting gates

- Primary extraction: completed from the Chinese original text above.
- Independent blind source/abstract review: completed.
- Root source-comparison adjudication: completed for the abstract/body discrepancies described above.
- English full-text correspondence for F01–F19: pending. “Not stated in this abstract” is not equivalent to “absent from English sources.”
- Patient/family deduplication against earlier RPS6KA3 reports: pending.
- Variant normalization: pending; the inspected article record does not specify a transcript accession for `c.1603-2A>G`.
- Confirmatory sample inclusion: no; this is an exploration-informed example, not a probability-sampled target.

The present result is therefore limited to a direct demonstration that a Chinese full-text body contains finer-grained observations than its same-article English abstract. It does not establish that multilingual retrieval yields more evidence overall.
