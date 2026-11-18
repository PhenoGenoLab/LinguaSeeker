# Multilingual case candidate triage R1

**Status:** completed
**Created:** 2026-11-15
**Completed:** 2026-11-15
**Scope:** Cross-language genetic case discovery and original-text versus English-abstract comparison
**Work type:** Exploratory triage only
**PR:** N/A (research note)
**Confirmatory status:** Not enrolled; no confirmatory sampling frame is frozen

## Finding

This bounded screen identified seven full-text case/family reports across Chinese, Spanish, French, and Russian. All seven have English titles or English abstracts in bibliographic sources, so this screen does **not** establish that multilingual retrieval found an article missing from English-indexed discovery. It does identify candidate patient-level details in the non-English full texts that are not stated in their English abstracts. Those details remain exploratory until independently screened against a frozen English correspondence protocol.

No additional patient, family, or variant unit is counted as a validated multilingual increment here. The candidate records were not sampled from a frozen probability frame, and no full English correspondence audit was run.

## Search and screening

On 2026-11-15, Europe PMC was queried with `LANG:<code> AND FIRST_PDATE:[2020-01-01 TO 2025-12-31] AND IN_EPMC:Y AND (mutation OR variant) AND (genetic OR syndrome) AND (case OR family)`. The 2020–2025 open-full-text queries returned 196 Chinese-, 43 Spanish-, 28 Portuguese-, 78 French-, and 33 Russian-tagged records, respectively. The corresponding Japanese query returned zero records. These are search-result counts, not eligible-paper counts or an exhaustive review; title/abstract relevance screening and source-language confirmation were required before a paper entered the candidate table.

The candidate table below was cross-checked against Europe PMC/PMC records and, for the RPS6KA3 paper, the publisher landing page. Full-text language was checked directly in the article body. An English abstract was treated as a discovery route and comparator, not as an independent source or a second patient.

## Candidate evidence matrix

| Source and body language | Genetic and family evidence in the original full text | Candidate detail beyond the English abstract | English-discovery and increment status |
|---|---|---|---|
| [Coffin–Lowry family, RPS6KA3](https://europepmc.org/articles/PMC12796916), Chinese body, PMID 41536659, DOI 10.12182/20251160204 | The authors report a hemizygous `c.1603-2A>G` variant in the proband and a heterozygous maternal carrier; the father tested negative. A transcript accession is not specified in the inspected article record. The two maternal half-siblings had reported clinical features but were not reported as variant-tested. The paper assigns ACMG criteria, which have not been independently re-evaluated here. | The full text gives staged developmental and GESELL scores, birth and growth measurements, MRI findings (reduced white-matter volume and a thin corpus callosum), hearing and echocardiography results, and separate half-sibling histories. See the [19-row fact-level screen](../2026-11-15-rps6ka3-abstract-body-fact-screen-r1/README.md). The English abstract already reports the variant, maternal segregation, siblings' broad phenotype, follow-up, and the 28-patient literature summary. | The publisher provides an English abstract and OpenAlex indexes an English title/abstract; English search retrieves the same paper. **No article, patient, or variant retrieval increment is established.** Body-only details are fact-level candidates; English-equivalence review is pending. The siblings must not be counted as genotype-confirmed carriers. |
| [X-linked intellectual developmental disorder-105, USP27X](https://europepmc.org/articles/PMC11469094), Spanish body, PMID 39007861, DOI 10.33588/rn.7903.2024097 | The report describes `NM_001145073.3:c.692delT` (`p.Leu231Trpfs*13`) and maternal segregation involving the index boy, his maternal uncle, and mother; a healthy maternal aunt is reported as a non-carrier. | The Spanish body adds detailed developmental chronology, examination findings, negative work-up, and finer distinctions between the index case and maternal uncle. | The English abstract already reports the variant, segregation, both male cases, and several phenotypic details. **No article, patient, or variant retrieval increment is established.** Remaining body-level details need fact-by-fact English correspondence review. |
| [Congenital fibrosis of extraocular muscles, TUBB3](https://europepmc.org/articles/PMC12554870), Chinese body, PMID 41184125, DOI 10.11817/j.issn.1672-7347.2025.240596 | A proband and her mother are reported with `NM_006086.4:c.904G>A` (`p.Ala302Thr`); the mother has ptosis and the father tested negative. The paper cites earlier reports of this variant, so it is not a new variant candidate. | The Chinese body includes detailed ocular measurements, a prior operation, imaging, and a more granular examination than the English abstract. | The English abstract already gives the variant, proband, maternal carrier/ptosis, and surgical outcome. **No article, patient, or variant retrieval increment is established.** Candidate only for detailed fact extraction. |
| [Aicardi–Goutières syndrome, RNASEH2B](https://europepmc.org/articles/PMC12535594), French body, PMID 41116827, DOI 10.11604/pamj.2025.51.102.48730 | The article reports a homozygous RNASEH2B mutation in a 14-month-old infant, but neither the English abstract nor inspected full text gives a transcript-level HGVS variant. | The French body describes regression chronology, feeding difficulty and stridor, neurologic examination, and absence of several typical findings. These are clinical-detail candidates, not a new allele. | The English abstract already reports the age, regression, absent microcephaly/calcifications, MRI finding, and homozygous RNASEH2B result. **No variant-level increment is supported.** |
| [Thyroid hormone resistance, THRA](https://europepmc.org/articles/PMC12319631), Russian body, PMID 40734302, DOI 10.14341/probl13541 | A heterozygous de novo `c.1198C>G` (`p.Leu400Val`) variant is reported in a boy. The full text classifies the variant as uncertain clinical significance; it is not treated here as a confirmed pathogenic allele. | The body gives hormone/lipid/creatine-kinase measurements, clinical findings, and the trade-off between lipid response and thyrotoxic symptoms under supraphysiological levothyroxine. | The English abstract already reports the variant, de novo status, clinical context, and treatment response. **No article or variant retrieval increment is established.** The VUS classification must be retained. |
| [Von Hippel–Lindau family](https://europepmc.org/articles/PMC12954419), Russian body, PMID 41640149, DOI 10.14341/probl13510 | The report identifies heterozygous `VHL c.500G>A` (`p.Arg167Gln`) in a family. The mother and older son had pheochromocytoma; a younger brother was reported as a carrier. The variant is discussed with prior functional literature and is not novel. | The Russian body gives tumor histology, treatment and recurrence chronology, family testing, and follow-up details. | The English abstract already reports the variant, affected mother/older son, and younger brother testing. **No article or variant retrieval increment is established.** The younger brother is not counted as an affected patient without a reported phenotype. |
| [Congenital isolated ACTH deficiency, TBX19](https://europepmc.org/articles/PMC12319635), Russian body, PMID 40734300, DOI 10.14341/probl13519 | Two cases are reported with homozygous `c.82C>T` (`p.Gln28Ter`) and `c.469-1G>A` variants, respectively. The authors call the second variant previously undescribed. | The full text describes neonatal hypoglycemia, delayed diagnosis, cholestatic/hepatic findings in one infant, and response to hydrocortisone. | The English abstract already states both case-level genotypes and clinical courses. **No article, patient, or variant retrieval increment is established.** |

## Interpretation by evidence dimension

- **Variant discovery:** RPS6KA3 `c.1603-2A>G` is described by the authors as previously unreported, but it is also present in the paper's English abstract. This screen cannot count it as a variant absent from English retrieval. Transcript-aware normalization and independent database review remain outstanding.
- **Segregation:** The RPS6KA3 family includes a tested proband, mother, and father. The maternal half-siblings are clinically described but are not shown as variant-tested in the inspected methods/results; they are not counted as confirmed variant-positive patients.
- **Phenotype depth:** The Chinese, Spanish, and French bodies contain patient-level measurements, temporal detail, examination findings, and negative results beyond their English abstracts. These may support a fine-grained extraction-quality endpoint if their absence from the frozen English correspondence audit is confirmed.
- **Function and classification:** The screen found no direct functional experiment for the RPS6KA3 variant. The variant classifications in the case reports are author assessments, not independent adjudications. The TUBB3 variant is cited as previously reported; it is retained as a recurrence/family-detail example, not as a novel allele.
- **Endocrine and tumor-predisposition dimensions:** Russian full texts add THRA-associated thyroid hormone resistance, VHL family segregation/tumor chronology, and TBX19-associated ACTH deficiency. Their English abstracts already surface the variants and core cases; the THRA full text explicitly retains a VUS interpretation.
- **Cohort summaries:** The RPS6KA3 paper's 28-person review is a secondary synthesis of earlier Chinese and English reports. Its denominator is not a set of 28 newly acquired independent patients and was not added to any increment count.

## Protocol implication

This screen separates two questions that must stay distinct:

1. **Acquisition increment:** did the multilingual arm retrieve an eligible article, patient, family, or variant that the frozen English arm did not retrieve?
2. **Original-text detail increment:** did the non-English body support a deduplicated fact absent from both the English abstract and the bounded English-source correspondence audit?

These seven records currently support only candidate detail-level comparisons. They do not establish an overall multilingual advantage, and they do not enter the confirmatory denominator. A confirmatory analysis still requires a pre-retrieval target-question sampling frame, a completed English baseline, endpoint-specific `δ`, missingness rules, power-based sample size, and the independent review/arbitration workflow.

## Search workflow reference

The research-lookup skill guided search logging and source verification. This is a workflow reference, not scientific evidence for the case claims:

Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. arXiv:2609.00065. https://doi.org/10.48550/arXiv.2609.00065
