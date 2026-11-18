# Multilingual Genetic-Case Candidate Synthesis R2

**Status:** completed
**Created:** 2026-11-15
**Completed:** 2026-11-15
**Scope:** Addendum for new multilingual case leads and source/translation adjudications
**PR:** N/A (research synthesis)

> Archived as the R2 synthesis snapshot and superseded by the active R3 synthesis. The overall experiment remains in progress.

## Current conclusion

Three newly audited reports broaden the exploratory case set across EIF2B5 leukodystrophy, FZD2-related omodysplasia, and a Brazilian three-gene cardiomyopathy report. They add useful dimensions for evaluating source-language access—clinical course, imaging, family segregation, enzyme biomarkers, and translation fidelity—but none currently supports a confirmed multilingual-only patient or variant increment. The EIF2B5 genotype is unresolved against current RefSeq transcripts. The FZD2 and GLA/TTR/PRKAG2 cases have English abstracts or full translations for the same patient.

These are convenience-discovered exploratory cases. They do not estimate an overall average, and they cannot prove that multilingual retrieval always adds more evidence. Keep article, patient, variant, fact-detail, indexing, and translation-quality outcomes separate.

## New candidate matrix

| Report | Original-language/source structure | Multidimensional evidence | English correspondence and variant status | Current endpoint disposition |
|---|---|---|---|---|
| EIF2B5 / vanishing-white-matter report, 2024, Spain | Spanish full text, no abstract element in the inspected JATS; Europe PMC's English-translated title finds the same record. | Febrile-triggered decline, serial MRI, biochemical findings, two reported variants, treatment timeline, and follow-up. | Two independent source reviewers confirmed the proceedings false hit. However, the report omits transcript accessions. Both reported cDNA reference bases mismatch all 7 current human RefSeq mRNAs returned for EIF2B5; the ClinVar gene-level snapshot contains a different `c.338G>A p.Arg113His` allele. The reported genotype is not validated. | Clinical-source lead only; zero article/patient/variant count in the primary endpoint. Broader English correspondence and source transcript/test report unresolved. See [EIF2B5 audit](2026-11-15-eif2b5-spanish-fulltext-candidate-r1.md) and its retained package `benchmark/experiments/acmg_multilingual/candidate_audits/eif2b5_spanish_r1/`. |
| FZD2 / type 2 omodysplasia, 2026, Latin America | Spanish article body, Spanish and English abstracts in one PMC record; no separate English full text located. | Birth history, development, surgeries, examination, anthropometry, radiographs, a prior Japanese case comparison, and the reported `FZD2 c.1640C>A p.(Ser547*)` variant. | Same current patient appears in the English abstract; the same allele was reported in a different Japanese male in 2018 English literature. English abstract calls the stop notation “missense,” contradicting Spanish “nonsense” and `p.(Ser547*)`. | Fact-detail/translation-fidelity candidate; zero article, patient, or variant acquisition increment. See [FZD2 audit](2026-11-15-fzd2-omodysplasia-spanish-abstract-audit-r1.md). |
| GLA/TTR/PRKAG2 / hypertrophic cardiomyopathy, 2026, Brazil | Portuguese primary article plus complete publisher English `sub-article` and separate English PDF/translation DOI. The English DOI is visible at the publisher but did not resolve in Crossref/doi.org or Europe PMC. | Three transcript-anchored variants, family segregation, echo/Holter, enzyme activity, Lyso-Gb3, treatment, and outcome. | Portuguese and English full texts carry the same case and genotype. `GLA c.870G>A p.(Met290Ile)` appears in a 2023 English Fabry cohort. The English translation omits the `≥` before the first-degree-relative 13-mm HCM threshold; both versions share conflicting ethics identifiers. | Bilingual negative control plus translation-fidelity candidate; zero language-exclusive article, patient, or variant increment. TTR/PRKAG2 novelty is unproven. See [Portuguese-English audit](2026-11-15-gla-ttr-prkag2-portuguese-english-case-audit-r1.md) and retained package `benchmark/experiments/acmg_multilingual/candidate_audits/gla_ttr_prkag2_pt_en_r1/`. |

## Evidence dimensions retained

The cases should be reviewed across separate evidence dimensions rather than counted as raw article or variant rows:

- **Variant identity:** transcript accession/version, HGVS reference-base consistency, genomic normalization, and independent classification.
- **Inheritance and family structure:** genotyped relatives, segregation, phase, and explicit test-negative relatives.
- **Phenotype and time course:** age at onset, system-specific findings, imaging, biomarkers, treatment timing, and outcomes.
- **Source coverage:** whether each fact is present in the original-language body, same-record English abstract, separate English full text, or another English paper.
- **Translation fidelity and indexing:** mistranslated/omitted operators, language labels, parallel DOI relations, and whether English pages are independently indexed.
- **Causal uncertainty:** separate author interpretation from measured findings; a complex genotype or post-treatment improvement does not establish causality.

For the current three reports, detailed facts may improve source-level reconstruction, but they do not yet establish that those facts are absent from all English literature. The Portuguese `≥13 mm` discrepancy is known to be absent from its own English translation; it remains a translation correction, not a new patient observation. The EIF2B5 variants cannot be used in a variant novelty denominator until their transcript identity is resolved.

## Accounting boundary

The exploratory packages have no common probability-sampled denominator. Do not pool the three reports with earlier Chinese, French, Russian, Spanish, or Rett/MECP2 observations. Current confirmed primary endpoint remains **0 validated multilingual-only patient or variant increments**; this is a status of the current evidence gate, not proof that the population-wide increment is zero.

The EPMC English-language filter is not a complete operational definition of “English evidence.” One record can have `language=por` while its publisher provides a complete English translation. Conversely, a translated title or English abstract does not guarantee that the full English body is indexed. The frozen English baseline must state whether it searches publisher-hosted translations and unfiltered mixed-language records.

## Next work

1. Resolve EIF2B5's transcript/test-report identity before treating the c.338T>A and c.713G>A labels as variants.
2. Keep FZD2 and GLA/TTR/PRKAG2 as bilingual/detail controls, not positive article/patient/variant increments.
3. Continue discovery in additional disease groups and languages, but retain all zero-yield and bilingual controls.
4. Freeze a language-independent target-question sampling frame, the primary fact unit, English baseline, effect threshold, and sample size before confirmatory retrieval.

## Procedural reference (not clinical evidence)

Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. arXiv:2609.00065. https://doi.org/10.48550/arXiv.2609.00065. This is cited only as a workflow resource and contributes no clinical or multilingual-increment evidence.
