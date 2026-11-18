# EIF2B5 Spanish full-text evidence candidate R1

**Status:** in-progress
**Created:** 2026-11-15
**Completed:** —
**Scope:** Exploratory candidate audit for non-English full-text evidence beyond English abstracts
**PR:** N/A (research audit)

## Current finding

The Spanish full text reports a 4-year-old boy with previously normal neurologic development, febrile-triggered rapid decline, serial MRI changes, and two reported compound-heterozygous `EIF2B5` variants (`c.338T>A` and `c.713G>A`). Europe PMC records the article as Spanish and has no abstract text; the PMC XML body and figure legend are in Spanish. Its bibliographic record has an English-translated title, so an English title search can retrieve the record. The variant and clinical details are available in the Spanish body; no English abstract was found in the inspected record.

This is an exploratory **case-report lead**, not a validated variant increment. The independent source review is complete for the article and proceedings hit, but transcript-aware checks now show that both reported HGVS strings conflict with the reference bases of the current NCBI RefSeq mRNAs returned for `EIF2B5`. No transcript or test report is supplied in the article, so neither reported consequence nor novelty can be accepted. No patient or variant is counted in a primary numerator.

## Source and provenance

- Article: [Imágenes de resonancia magnética de inicio y evolución de un niño con nueva variante genética de leucodistrofia evanescente](https://europepmc.org/articles/PMC11064962)
- PMID `38289247`; PMCID `PMC11064962`; DOI `10.33588/rn.7803.2023349`; *Revista de Neurología* 78(3), 2024, pages 91–92.
- Europe PMC source language: `spa`; EPMC abstract field empty. The JATS full-text XML contains Spanish article body text and figure legend.
- Full-text XML SHA-256 at retrieval from Europe PMC: `10d9cbed2a7d2c5ce5f4331e2ca5c40d1afeb6c678c90d674236190e25536ab5`.
- Independent PMC OAI JATS retrieval SHA-256: `f37da5e281a20f2c437c47bd2b9b2f8a1ba14284f94e937edb2941ebc93c7d2a`; retained with the RefSeq and ClinVar response records under the paper workspace candidate-audit package.
- Crossref metadata SHA-256: `d62040b51fe0361ca99757b2a6f194fdcbc8bc8581507b414e128ac21d3e8713`; Crossref records the Spanish title and language `es`.

Hashes bind the retrieved bytes only. They do not certify the clinical interpretation, variant classification, or completeness of English correspondence searching.

## Original-text fact candidates

Locators below refer to the Spanish JATS body paragraph or MRI figure legend. The article has no English abstract, so the immediate comparison is against English-language records and bounded English searches, not a same-article abstract comparison.

| Dimension | Original Spanish quotation | Normalized fact for review | Evidence status |
|---|---|---|---|
| Pre-event development and onset | `un niño de 4 años con desarrollo neurológico normal que durante un proceso infeccioso febril inició clínica de vómitos persistentes, cefalea con foto- y sonofobia, irritabilidad y somnolencia` — body paragraph 1 | A 4-year-old boy reportedly had normal neurologic development before a febrile illness followed by vomiting, headache with photo/phonophobia, irritability, and somnolence. | Source-grounded candidate; independent review confirms extraction; English-equivalence audit pending. |
| Acute progression | `Durante los siguientes 20 días presentó un deterioro neurológico progresivo con clínica de encefalopatía subaguda, tetraparesia espástica, imposibilidad para la bipedestación y sedestación, hipertonía, rigidez, hiperreflexia, dificultades graves de visión, midriasis bilateral y dislalia/disartria con alimentación por sonda` — body paragraph 1 | Over 20 days, the article reports progressive encephalopathy, spastic tetraparesis, inability to stand or sit, hypertonia, rigidity, hyperreflexia, severe visual difficulty, bilateral mydriasis, dysarthria, and tube feeding. | Candidate multi-system/temporal detail; not an independent patient count. |
| Biochemistry | `La analítica sanguínea y del líquido cefalorraquídeo destaca en ambas por aumento del ácido láctico` — body paragraph 1 | Elevated lactate was reported in both blood and cerebrospinal fluid. | Candidate laboratory observation; values and collection details are not given in this passage. |
| Molecular findings | `heterocigosis compuesta heredada de ambos progenitores del gen EIF2B5: una variante patógena nonsense (c.338T>A) y otra variante missense (c.713G>A), no descritas previamente. Ambas probablemente son patógenas in silico` — body paragraph 1 | The authors report compound heterozygosity in `EIF2B5`, with a nonsense `c.338T>A` and missense `c.713G>A`, said to derive from both parents and not to have been previously described; their predicted pathogenicity is in silico. | **Unresolved variant annotation:** the article gives no transcript, genomic coordinate, protein consequence, or parent-to-allele phase. Current NCBI RefSeq reference checks do not validate either raw HGVS string as written; do not accept the author's consequence or novelty labels. |
| MRI study dates | `Las imágenes de la fila superior corresponden a una resonancia magnética de cráneo de 2019. Las de la fila de inferior, a una resonancia magnética de cráneo de 2021` — figure legend / body paragraph 2 | The figure compares brain MRI from 2019 and 2021. | Candidate longitudinal imaging evidence. |
| MRI distribution and progression | `afectación extensa de la sustancia blanca supratentorial ... de forma bilateral y simétrica` and `progresión de la afectación de la sustancia blanca con desarrollo de cavitación ... dilatación del sistema ventricular ... lesión del esplenio del cuerpo calloso con progresión hacia atrofia` — figure legend / body paragraph 2 | The legend describes bilateral symmetric supratentorial white-matter disease and progression between scans, including cavitation, ventricular dilation, splenial involvement/atrophy, and later symmetric cerebellar changes. | Candidate radiologic detail; any derived severity score would require a prespecified scheme. |
| Treatment and follow-up | `se inició medicación de estimulación mitocondrial (L-carnitina, tiamina, riboflavina, biotina, coenzima Q y vitamina E), y presentó una evolución clínica favorable tras 15 días de tratamiento` — body paragraph 1 | A mitochondrial cofactor regimen was followed by reported clinical improvement after 15 days. | Temporal association only; this single case cannot establish treatment efficacy. |
| Three-month status | `A los tres meses del alta presentaba mejoría de la motilidad global y la deglución, recuperación incompleta del habla, sedestación y bipedestación, y realizaba deambulación con ayuda, con escasa afectación cognitiva` — body paragraph 1 | At three months after discharge, the report describes improved gross movement and swallowing, incomplete speech recovery, regained sitting/standing, walking with assistance, and little cognitive involvement. | Candidate follow-up detail; exact assessment scales are not supplied here. |

These rows are source-extraction candidates, not a prespecified count of independent facts. They may be collapsed or subdivided only under a frozen fact-unit ontology before confirmatory review.

## Bounded English correspondence checks

Search date: 2026-11-15. These checks are exploratory and do not replace a frozen English baseline.

| Query | Result | Interpretation |
|---|---|---|
| Europe PMC: `EIF2B5 AND "c.713G>A"` | One result: this Spanish record (`PMC11064962`, language `spa`). Response SHA-256 `5f055ccbb4f37adf43defd2b7e68ab6565dfa00ec9d007a22b7b8f3dfeaf73c0`. | No separate English-language article appeared in this exact-query result. It does not prove English-wide absence. |
| Europe PMC: `LANG:eng AND EIF2B5 AND "c.713G>A"` | Zero results. Response SHA-256 `a6a50f5bcbaf14daa191fd958f32374bc27fd77c433ef0ee38283d2698ce6ab3`. | Bounded English-record check only; alternative notation/transcript normalization remains unsearched. |
| Europe PMC: `"c.338T>A" AND EIF2B5` | Two records: the Spanish report and an English 2019 ESHG conference-proceedings compilation (`PMC6778823`). | Independent review of the proceedings confirmed a document-level co-occurrence only: `EIF2B5` occurs in a separate rapid-WES cohort abstract, while the `c.338` tokens are in other-gene posters. No target allele or matching patient was found in that volume. It is not an English counterpart. |
| Europe PMC: `TITLE:"vanishing white matter" AND EIF2B5 AND variant` | 43 records, including `PMC11064962` as language `spa` with an English-translated catalog title. | An English title/concept query can retrieve the bibliographic record. This is not an article-acquisition miss in this provider; it still exposes no English abstract/body evidence for extraction. |

## Review gates and current disposition

- Original Spanish body extraction: completed at candidate level; source hash recorded.
- English title/metadata discovery: confirmed for this provider; no article-acquisition increment claimed.
- English abstract: absent in the inspected record/source.
- English full-text equivalence for the patient-specific facts: pending.
- Variant transcript normalization and database classification: pending; the article does not specify transcript accessions and describes predicted pathogenicity, not a functional assay.
- Parent-specific phase for `c.338T>A` versus `c.713G>A`: the text says inheritance from both parents but the inspected passage does not assign each allele to a named parent.
- Independent source review and proceedings-hit adjudication: complete for this bounded scope; broader English-source correspondence remains pending.
- Transcript reference validation: **unresolved / incompatible as written** against the current NCBI RefSeq mRNA set returned below; the article does not identify its transcript or supply the laboratory report.
- Confirmatory sample inclusion and primary-endpoint count: no; no probability sample or frozen frame is in place.

## Independent review disposition (2026-11-15)

Two independent source reviews agree that this is a Spanish full-text article with no abstract element in the article XML and no indexed English abstract text. Its English-translated catalog title makes the record discoverable through English title/concept searches, so this is not an article-acquisition increment in Europe PMC. The body and figure caption are the source of the case-specific clinical course, MRI, treatment/follow-up, and genotype details above.

The reviewers independently checked the apparent English proceedings hit. The omnibus ESHG record `PMC6778823` is not an English counterpart: the inspected `EIF2B5` mention occurs in a separate rapid-WES abstract without the target alleles or a matching patient; the exact-looking `c.338` token occurs in other-gene records (including a Colombian `MECP2 c.338C>G` case). This resolves that record-level co-occurrence as a false correspondence for the Spanish case. The bounded Europe PMC searches still do not establish that no English source exists globally.

The two reviewers agree that the paper describes one boy and reports `EIF2B5 c.338T>A` plus `c.713G>A` as compound heterozygous and inherited from both parents, but it does not assign each allele to a named parent or specify transcript/protein/genomic coordinates. The paper's “not previously described” and pathogenicity language are author claims, not independent variant classification evidence. No sibling, additional patient, or independent segregation assay can be inferred from this short report.

| Endpoint | Current disposition |
|---|---|
| Article found by English-indexed search | No increment; English-translated title retrieves the same record. |
| Spanish-body clinical/imaging facts absent from an English abstract | Candidate fact-level content availability; no English abstract exists in the inspected record. |
| Patient/family increment | Not established; one reported patient, with no independent English patient-level correspondence audit complete. |
| Variant increment or novelty | Not established; transcript-aware normalization and independent database/literature assessment remain pending. |
| Primary confirmatory endpoint | Excluded from the inferential denominator; exploratory convenience case. |

The independent reviews are qualitative source checks only. They do not replace the frozen English correspondence protocol, transcript normalization, or probability-sampled confirmation.

## Transcript-reference and ClinVar cross-check (2026-11-15)

The article reports only `c.338T>A` and `c.713G>A`; it does not identify a transcript accession/version or provide genomic coordinates. To avoid guessing a transcript, the bounded NCBI RefSeq search used `EIF2B5[Gene Name] AND Homo sapiens[Organism] AND mRNA[filter] AND RefSeq[filter]` and reconciled all 7 returned records. Their GenBank records were retrieved and the CDS reference bases were read at the stated cDNA positions:

| RefSeq transcript | Ref at c.338 | Ref at c.713 | Both source HGVS reference bases match? |
|---|---:|---:|---|
| `NM_003907.3` (curated) | G | T | No |
| `XM_054348282.1` | A | T | No |
| `XM_054348281.1` | G | T | No |
| `XM_054348280.1` | G | T | No |
| `XM_011513266.4` | A | T | No |
| `XM_047449148.1` | G | T | No |
| `XM_011513265.1` | G | T | No |

This comparison does **not** prove that the authors' strings are impossible on every historical or non-RefSeq transcript. It shows that they cannot be normalized or assigned the reported nonsense/missense consequences on the current RefSeq set checked. Because the source does not name its transcript, the genotype cannot yet serve as a validated variant-level observation.

ClinVar ESearch for `EIF2B5[gene]` returned 926 gene-associated records. The 926 IDs were retrieved in two ESummary batches (500 + 426; JSON batch cap 500), and all returned text fields were inspected locally for the source strings. This bounded ClinVar snapshot did not contain exact `c.338T>A` or `c.713G>A` entries. It did contain `NM_003907.3(EIF2B5):c.338G>A (p.Arg113His)` (`VCV000005945.86`), classified pathogenic with multiple submitters and no conflicts. That is a different alternate allele and consequence; it is not a match and must not be merged with the paper's `c.338T>A`.

NCBI's exact ClinVar text queries for the source spellings returned zero, but EUtils rewrote punctuation in the echoed query (`c.` became `c0x2e`); those zero-query results are not used as standalone negative evidence. The full gene-level ESummary scan is the basis for the bounded statement above. It still does not establish global absence, especially while the article's transcript is unknown.

| Endpoint | Updated disposition |
|---|---|
| Article retrieval | Same Spanish record is discoverable by its translated English catalog title; no article retrieval increment claimed. |
| Clinical and MRI detail | Source-grounded one-patient report; English abstract absent in the inspected record, but wider English-source correspondence remains bounded. |
| Variant identity | Unresolved: both reported HGVS strings mismatch reference bases in all 7 current RefSeq mRNAs checked. |
| Variant novelty/pathogenicity | Not established. ClinVar c.338G>A p.Arg113His is not the same allele; c.713G>A has no matching name in the bounded 926-record ClinVar scan. |
| Patient/variant primary numerator | Zero; exploratory lead excluded until transcript/test-report identity and English correspondence are resolved. |

This remains an exploratory source candidate for **case-detail availability in a non-English body without an English abstract**. Its reported genotype is not currently normalized against the RefSeq set checked, so it is not valid variant-level evidence yet; neither it nor the bounded English searches support an overall multilingual advantage or global absence claim.
