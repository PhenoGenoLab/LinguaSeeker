# SMPX Chinese full-text family audit R1

**Status:** in-progress  
**Created:** 2026-11-15  
**Completed:** —  
**PR:** N/A (research audit)

## Result

The SMPX article's English abstract already includes the reported `NM_014332.3:c.133-2A>C` variant, the proband and two affected maternal relatives, and Sanger confirmation that all three carry the variant. The Chinese body provides more granular pedigree, audiology, imaging, and author ACMG-code details than that abstract. A bounded English-source search found prior English SMPX-family reports with related maternal pedigrees, audiology, and splice-site variants, but no verified identity link or exact `c.133-2A>C` match. Those 2025 body details remain candidates; the English search was not exhaustive.

Therefore, this case contributes **zero confirmed language-exclusive patients, variants, or facts**. It is an exploratory source-detail candidate only. It cannot support an overall superiority claim.

## Source and review boundary

The source package is `benchmark/experiments/acmg_multilingual/candidate_audits/smpx_chinese_r1/`. The primary source is the PMC article page for PMID 40443382 / PMCID PMC12527658, DOI `10.13201/j.issn.2096-7993.2025.06.013`. Its body is Chinese; the same record includes an English abstract. The blind review was performed in an isolated review context (`smpx_blind_audit`) and then adjudicated against the retained source HTML and Europe PMC record. The package contains `source_acquisition_receipt.json` and `independent_review.md`.

The independent review compared only the Chinese full text with the same-record English abstract. It did not claim that an English full text or all English sources had been exhausted. An English abstract omitting a body detail is not a valid English-literature negative.

## Evidence comparison

| Evidence unit | Chinese full text | Same-record English abstract | Disposition |
|---|---|---|---|
| Disease/inheritance | X-linked dominant nonsyndromic sensorineural hearing loss | Present | Shared |
| Variant | `NM_014332.3:c.133-2A>C` | Present | Shared; transcript/variant novelty not independently established |
| Family carriers | Proband, mother, maternal grandmother; Sanger segregation | All three carriers and Sanger confirmation stated | Shared; no new family unit |
| Pedigree and onset | Three generations/nine relatives; proband reported as 18-year-old male with onset at 7; relative onset histories | Not detailed | Candidate detail only |
| Audiology | Individual pure-tone descriptions, ABR thresholds, DPOAE and tympanometry | Modalities are named, individual values/results are not | Candidate detail only |
| Imaging | Proband temporal-bone CT and inner-ear MRI reported normal | Not stated | Candidate detail only |
| ACMG reasoning | Author gives `PVS1 + PM2_supporting + PP1` | Evidence codes not listed | Author-reported classification detail, not independent reclassification |

### Conflicts and novelty boundary

The body identifies the proband as `III-1`, but Figure 2's caption lists `III-3`, `II-3`, and `I-2` as carriers (PMC HTML §2.1 and Figure 2 caption, lines 1495 and 1504). The discrepancy is unresolved. The discussion's “first splice variant” wording is contradicted if intended as the first reported SMPX splice variant: the same article's Table 1 includes `c.132+1G>A` and `c.133-1G>A` splice-site-style entries, and an English 2019 paper reported `NM_014332.2:c.132+1G>A` in a Chinese family. A 2024 English cohort also summarizes SMPX splice-altering variants. The exact-site assertion that `c.133-2A>C` was first reported remains unresolved; no exhaustive search or transcript/genome normalization was completed.

The local ClinVar gene result contains 279 SMPX summaries. An XML parse searched decoded text across all 279 records for the exact `c.133-2A>C` string and found zero exact-record matches. This is only a snapshot/database-query result. It does not establish absence from all ClinVar submissions, other variant databases, or literature, and it does not establish pathogenicity or novelty.

### Bounded English correspondence search

Three complete first-page Europe PMC result sets were reviewed (`pageSize=100`): `SMPX AND (grandmother OR "maternal grandmother") AND (hearing OR deafness)` returned 10/10; `SMPX AND ("auditory brainstem response" OR ABR) AND (hearing OR deafness) AND LANG:eng` returned 55/55; and `SMPX AND "70 dB" AND (hearing OR deafness)` returned 27/27. A language-filtered exact HGVS query without a gene constraint returned two unrelated POMC papers, so those were excluded. The gene-constrained query for `SMPX AND "c.133-2A>C" AND LANG:eng` returned HTTP 500 and cannot be interpreted as zero hits.

The English 2019 full text (PMID 31478598 / PMCID PMC6825843) reports a donor splice-site SMPX variant `NM_014332.2:c.132+1G>A`, a male neonate in a three-generation Han Chinese family, a mother described as hearing normally at the time, and a maternal grandmother with mild hearing loss since age 50. The paper also describes RT-PCR, qPCR, aberrant transcripts, a predicted frameshift, and nonsense-mediated decay. It explicitly calls this the first SMPX splicing-variant report in a Chinese family. The 2024 English cohort (PMID 39272213 / PMCID PMC11396341) Table 1 includes `NM_014332.3:c.29insA` in a female with family history and newborn onset and `NM_014332.3:c.132+1G>T` in a male without family history and onset at eight years; its text summarizes three SMPX splice-altering variants. The 2025 Chinese paper's own Table 1 also lists `c.132+1G>A` and `c.133-1G>A` splice-site-style SMPX entries as rows classified as frameshift, creating an internal terminology/novelty conflict. A 2021 English family report (PMID 33708524 / PMCID PMC7944167) describes a four-generation Chinese family and `SMPX c.262C>G`; it shares an author with the 2025 report, so potential data-source linkage remains unresolved.

These are related cases and variant context, not confirmed identity matches for the 2025 family. The 2025 paper's own Table 1 plus the 2019 and 2024 English reports rebut an unqualified claim that 2025 was the first SMPX splice-variant report; they do not disprove the narrower claim that the exact `c.133-2A>C` site was previously unreported. The query set is bounded and the specific gene-plus-HGVS English query failed, so global variant novelty remains unresolved. The independent English correspondence memo and all query/source route artifacts are recorded in the raw package.

## Adjudication and count

- Same-record English abstract already reports the core patient-family-variant facts.
- Chinese-body detail beyond the abstract is eligible only as a fact-level candidate pending the frozen English correspondence protocol.
- No exact patient/family identity link to prior English reports is documented; a full English-source search for every detail unit is not exhaustive.
- Confirmed patient increment: **0**.
- Confirmed family increment: **0**.
- Confirmed variant increment: **0**.
- Confirmed language-exclusive fact increment: **0** under the completed bounded comparison; detail candidates remain unresolved for global English correspondence.

This audit distinguishes an English retrieval workflow's coverage from language-exclusive evidence. It does not contribute a positive observation to the confirmatory population estimate.

## Reproducibility artifacts

The source receipt binds the retained PMC HTML, Europe PMC metadata, RefSeq record, PubMed prior-record response, ClinVar query/summary bytes, English comparison articles, search responses, and access-route errors by size and SHA-256. For the ClinVar gene snapshot, the exact-string scan was run using `uv run --no-sync python` with Python's XML standard library; all 279 records were parsed and searched. The independent review memos distinguish text similarity from patient identity and record the search limits. HTTP errors, timeouts, challenge pages, and failed downloads are retained as access outcomes, not evidence of absence.

## Procedural reference (not clinical evidence)

Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. arXiv:2609.00065. https://arxiv.org/abs/2609.00065. Cited only for reproducible scholarly search and evidence-bound reporting; it contributes no clinical or multilingual-increment evidence. The arXiv Atom record was checked on 2026-11-15; no journal reference or publisher DOI was listed.
