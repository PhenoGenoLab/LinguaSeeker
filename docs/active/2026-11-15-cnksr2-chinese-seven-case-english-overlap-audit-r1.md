# CNKSR2 Chinese seven-case series and English overlap audit R1

**Status:** in-progress  
**Created:** 2026-11-15  
**Completed:** —  
**Scope:** Audit the 2026 Chinese CNKSR2 series against same-record English abstract and bounded prior English variant/family sources  
**PR:** N/A (research audit)

## Result

The Chinese paper reports seven local patients, five distinct reported CNKSR2 variants, and a 42-patient literature review. Its English abstract already reports the seven local cases, aggregate clinical frequencies, and four center patients with short stature and/or malnutrition, but it does not give the local HGVS list or per-patient evidence table.

A bounded English audit found strong evidence that two local rows repeat the two probands in a 2025 English full-text paper from Xiangya Hospital. Case 3 / English Proband I share `NM_014927.5:c.1658-3_1676del`, age nine at diagnosis, epilepsy onset at three, and an uncommon matching MRI description. Case 2 / English Proband II share `c.1102G>T (p.Gly368*)`, age about six, epilepsy onset at four, and normal MRI. The second match is somewhat less specific because the family-history summaries differ. No unique medical-record or sample identifiers were available, so these are adjudicated as **very likely repeat reports**, not identity proved beyond doubt.

The five local variant strings are not five new variants. `c.1102G>T` and `c.1658-3_1676del` were in the prior English Xiangya report; `c.2134C>T (p.Arg712*)` has prior English records; and ClinVar already lists `c.1684C>T` as Pathogenic (VCV003370477.1, evaluated 2024-02-26). The apparent ESHG `c.1684C>T` match is a separate cross-poster false positive. `c.1557dupA` was the only variant without an exact English or ClinVar match in the bounded searches. It remains a novelty candidate, not a confirmed language-exclusive variant.

This article adds no confirmed language-exclusive patient or family unit. It is a useful exploratory example of why records must be reconciled across languages before case counts are pooled.

## Source records

The Chinese source is PMID 42244324 / PMCID PMC13229662 / DOI `10.11817/j.issn.1672-7347.2026.240640`. The same record contains a Chinese full text and English abstract. Its raw source and search package is `benchmark/experiments/acmg_multilingual/candidate_audits/cnksr2_chinese_r1/` with per-artifact SHA-256 values in `source_acquisition_receipt.json`.

English comparison sources reviewed:

- PMID 39920708 / PMCID PMC11806549 / DOI `10.1186/s13052-025-01877-0`, a 2025 English full-text report of two Xiangya families with `c.1658-3_1676del` and `c.1102G>T`.
- PMID 40873128 / DOI `10.1111/cge.70054`, a 2025 English abstract reporting `c.2134C>T, p.(Arg712Ter)` in a girl as de novo, with X-inactivation skewing of 85:15.
- PMID 28098945 / DOI `10.1111/epi.13666`, a 2017 English abstract reporting three affected siblings and a maternally transmitted `p.Arg712*` variant printed as `c.2314C>T`.
- PMCID PMC10858311 / PMID 38337158, a 2024 English full text that summarizes earlier CNKSR2 variant families and reports a different splice variant `c.1657+1G>A`.
- PMCID PMC6777611, the ESHG 2018 poster proceedings volume returned by the broad `c.1684C>T` search. The matching `c.1684C>T (p.Arg562Term)` text is in a SPAST/ATL1 hereditary spastic paraplegia table, not the CNKSR2 poster. Its CNKSR2 poster P09.050B reports a 10-kb deletion instead.

## Case and variant accounting

| Chinese series row(s) | Reported variant | English correspondence | Counting disposition |
|---|---|---|---|
| Case 1 | `NM_014927.5:c.1684C>T (p.Arg562*)` | EPMC returned the ESHG 2018 proceedings, but the matching HGVS belongs to a SPAST table in another poster. ClinVar lists `VCV003370477.1`, Pathogenic, single submitter, evaluated 2024-02-26. | Variant already represented in an English-accessible database before the Chinese article; no new variant increment. Patient identity with prior ClinVar evidence is unknown. |
| Case 2 | `NM_014927.5:c.1102G>T (p.Gly368*)` | Exact variant in 2025 English Proband II; age, epilepsy onset, and normal MRI also align. Same center. | Likely repeat patient; do not add again to a combined English/multilingual patient count. |
| Case 3 | `NM_014927.5:c.1658-3_1676del` | Exact variant in 2025 English Proband I; age, seizure onset, MRI, and maternal phenotype closely align. English article reports minigene validation; Chinese table labels it not validated. | Very likely repeat patient; keep identity status short of definitive. English full text already has the variant and functional evidence. |
| Case 4 | `NM_014927.5:c.1557dupA (p.Leu520Thrfs*53)` | Exact Europe PMC and ClinVar gene-snapshot scans returned no exact match; the title/abstract searches found only the Chinese paper. | One variant-level novelty candidate in this bounded audit; not a confirmed global novelty or language-exclusive unit. |
| Cases 5–7 | `NM_014927.5:c.2134C>T (p.Arg712*)` | Exact HGVS appears in a 2025 English report; ClinVar lists `VCV000446716.6`, Pathogenic, multiple submitters/no conflicts, last evaluated 2025-07-18. The 2017 English abstract prints `c.2314C>T; p.Arg712*`. The Chinese article identifies cases 5–7 as brothers in one family with maternal transmission. | Three patients, one Chinese family, one known allele. English families have no cross-paper IDs; do not merge by variant alone. |

There are **seven reported local patients**, **five local allele strings**, and **one explicitly shared local pedigree (cases 5–7)**. Do not count seven independent families or count the `c.2134C>T` variant three times. The two probable English overlaps (cases 2 and 3) should be handled as a duplicate-risk sensitivity branch until a unique identifier resolves them. Only `c.1557dupA` remains an unmatched allele candidate in this bounded English/ClinVar review.

The 2025 Chinese paper says four variants were previously unreported, while its own text identifies `c.2134C>T` as known. The bounded audit confirms prior English publication for `c.1102G>T` and `c.1658-3_1676del`, and a pre-article ClinVar record for `c.1684C>T`; the ESHG `c.1684C>T` paper hit is a cross-poster false positive. Only `c.1557dupA` remained unmatched in the scanned ClinVar and Europe PMC results. Thus the paper's novelty claim for at least three of the four “unreported” variants is contradicted by the checked sources.

The PubMed record for PMID 28098945 reports `c.2314C>T; p.Arg712*`, whereas the Chinese article and 2025 English Clinical Genetics abstract report `c.2134C>T; p.Arg712Ter`. No transcript or genomic normalization was performed for the 2017 HGVS. Preserve the original strings and do not silently correct the coordinate.

## Same-record English abstract versus Chinese body

The English abstract of the 2026 paper already contains the 7-patient local sample, the 42-case literature review and 49-case total, pooled phenotype frequencies, and the report that four center patients had short stature and/or malnutrition. These high-level findings are not missing from English.

The Chinese body adds the per-patient HGVS, inheritance/source, ACMG codes, EEG/MRI findings, treatments, age-specific follow-up, and the family relationship among cases 5–7. For cases 2 and 3, a prior English full-text paper has already reported matching variants and several of those patient-level dimensions. The body details for other cases are candidates for a frozen English-source correspondence check; no detail count is promoted to a confirmed language-exclusive increment here.

## Bounded retrieval and limits

Europe PMC exact-text queries returned these first-page totals (`pageSize=100`): `c.1684C>T` 2 records, `c.1102G>T` 2, `c.1658-3_1676del` 2, `c.1557dupA` 1, and `c.2134C>T` 4. All records returned for those queries were retained. The 2018 proceedings result demonstrates an important failure mode: full-text co-occurrence within a compiled conference volume is not proof that the variant belongs to the gene-specific poster. The PubMed abstract for PMID 28098945 likewise has a reported transcript coordinate different from the current paper.

The search does not establish global English absence, complete ClinVar status, or family identity across articles. The two likely repeat reports were adjudicated from variant, phenotype, age, and center matches, not patient identifiers. A pooled multilingual superiority estimate cannot be inferred from this convenience-discovered candidate.

## Transcript reference and ClinVar snapshot

NCBI RefSeq `NM_014927.5` GenBank records CDS positions 481–3585. Mapping coding position `c.n` to the transcript sequence at `480+n` confirms the reference bases for the four single-nucleotide variants in this series: `c.1102G`, `c.1684C`, and `c.2134C`; the base at `c.1557` is `A` for the reported duplication. The codons for `c.1102G>T`, `c.1684C>T`, and `c.2134C>T` are consistent with the reported Gly368Ter, Arg562Ter, and Arg712Ter effects. This is a transcript-reference check, not genomic-coordinate normalization; the intronic deletion `c.1658-3_1676del` was not mapped to the genome here.

A ClinVar `CNKSR2[gene]` ESearch returned 610 UIDs. Both ESummary batches were parsed (500 + 110 records; 610/610 retrieved). An exact decoded-text scan found `c.1684C>T` as VCV003370477.1 (Pathogenic, single submitter, evaluation date 2024-02-26), `c.2134C>T` as VCV000446716.6 (Pathogenic, multiple submitters/no conflicts, last evaluated 2025-07-18), and a different variant `c.1657+1G>A`. It found no exact record-text matches for `c.1102G>T`, `c.1557dupA`, or `c.1658-3_1676del`. This is a database snapshot, not a literature-wide absence test or patient-identity proof.

## Procedural reference (not clinical evidence)

Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. arXiv:2609.00065. https://arxiv.org/abs/2609.00065. Cited for reproducible scholarly search and evidence-bound reporting only; it contributes no clinical or multilingual-increment evidence. The arXiv Atom record was checked on 2026-11-15; it listed no journal reference or publisher DOI.
