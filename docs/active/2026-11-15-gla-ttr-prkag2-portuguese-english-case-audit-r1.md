# GLA/TTR/PRKAG2 Portuguese–English Case Audit R1

**Status:** in-progress  
**Created:** 2026-11-15  
**Completed:** —  
**Scope:** Exploratory bilingual source-identity, case-evidence, and translation-fidelity audit  
**PR:** N/A (research audit)

## Current disposition

This is a 2026 Brazilian case report of a 16-year-old male from Manaus with severe hypertrophic cardiomyopathy and three reported variants in `GLA`, `TTR`, and `PRKAG2`. It is a useful **multivariant, family-segregation, and biomarker case** for the genetic evidence set. It is not, however, an English-unavailable article: the publisher's Portuguese JATS package contains a complete English `sub-article` translation, and the publisher serves a separate four-page English PDF under DOI `10.36660/abc.20260122i`.

The Portuguese and English versions report the same proband, variants, family testing, and laboratory values. One clinically relevant translation discrepancy was verified: the Portuguese introduction gives the first-degree-relative HCM wall-thickness criterion as `≥13 mm`, while the English translation says only “or 13 mm.” That is a translation-fidelity correction, not a new patient, article, or variant. Because this is a general diagnostic criterion and I have not audited the cited English guidelines for the same statement, it is not counted as language-exclusive evidence.

The `GLA c.870G>A p.(Met290Ile)` allele was already reported in an English Fabry cohort. The article does not claim the `TTR c.289T>C` or `PRKAG2 c.969C>A` alleles are novel; bounded searches finding no other EPMC record do not establish novelty. The authors themselves say it is difficult to determine which variant caused the phenotype or whether a synergistic effect occurred. `PRKAG2` remains a VUS in the report, with no clearly reported family segregation.

## Source identity and provenance

- Portuguese record: PMID `42788550`; PMCID `PMC13718332`; DOI `10.36660/abc.20260122`; EPMC language `por`.
- Publisher English page: `https://abccardiol.org/en/article/hypertrophic-phenotype-in-an-adolescent-from-the-amazon-region-associated-with-combined-variants-in-the-gla-ttr-and-prkag2-genes/`; it declares `dc.language=en`, `dc.identifier=10.36660/abc.20260122i`, and links `PDF - English` and `PDF - Português`.
- English translation DOI: `10.36660/abc.20260122i`. The publisher page, JATS sub-article and English PDF identify the translation. Crossref `/works/` and doi.org returned 404, and Europe PMC returned zero records for this DOI; this is an index/identifier-resolution gap, not evidence that the English translation is unavailable.
- Publisher JATS package, retained as `benchmark/experiments/acmg_multilingual/candidate_audits/gla_ttr_prkag2_pt_en_r1/publisher_bilingual_jats.xml`, declares the root article `xml:lang="pt"` and includes a complete `<sub-article article-type="translation" id="TRen" xml:lang="en">` with the translated DOI, case report, discussion, conclusion, ethics, data, and funding sections.
- PMC OAI JATS SHA-256: `9bbba3d8ec722a523e967e55a9428b10f7d9a549e45ade76b82b9b0f04f8d38e`.
- Publisher JATS SHA-256: `1e0e5b3d9a065202b84b534ccfebe55aabedf1cf2f7c16cc2494e6f2c015fd75`.
- Publisher English page SHA-256: `531323b6c91944dbb67cf9302e5a3f1985437b53cbe6b1b2e60d36fe0ca99a17`.
- English PDF SHA-256: `3599686dde17e059b3620e3b198ecfe33da94a58893d319a541c20fbdd691dd9`; four pages; extracted text retained next to the PDF.
- The article is marked CC BY 4.0 in the JATS license record; the English PDF states that it is distributed under the Creative Commons Attribution License.

The complete source and query receipts are retained under `benchmark/experiments/acmg_multilingual/candidate_audits/gla_ttr_prkag2_pt_en_r1/`. Hashes bind retrieved files, not the truth of author interpretations.

## Case and genetic evidence

The Portuguese and English bodies describe the same patient. He was diagnosed with obstructive HCM at age 12 during hospitalization for bacterial meningitis. At age 16 he presented with palpitations, dyspnea, and chest pain; echocardiography showed marked wall thickening and a resting LVOT gradient of 141 mmHg, and Holter monitoring showed one episode of non-sustained ventricular tachycardia. CMR, bone-tracer cardiac scintigraphy, and myocardial biopsy were not performed because of logistical/resource limits. Metoprolol succinate 50 mg twice daily was started; after one month symptoms were partly improved and the LVOT gradient was 53 mmHg. The patient died suddenly while awaiting ICD implantation and authorization for heart transplantation.

| Gene / source HGVS | Transcript-aware report in article | Author classification | Family evidence in article |
|---|---|---|---|
| `GLA` | `NM_000169.3:c.870G>A p.(Met290Ile)` | Pathogenic, hemizygous in proband | Father had no reported variants; older brother had the same hemizygous `GLA` variant; mother and younger sister carried `GLA` plus `TTR`. |
| `TTR` | `NM_000371.4:c.289T>C p.(Ser97Pro)` | Probably pathogenic, heterozygous | Reported in proband, mother, and younger sister; no clear clinical segregation with cardiac disease is demonstrated. |
| `PRKAG2` | `NM_016203.4:c.969C>A p.(Phe323Leu)` | VUS, heterozygous | Family transmission is not clearly reported. |

Proband α-galactosidase activity was `0.66 mcmol/L/h` (reference `>1.68`); Lyso-Gb3 was `0.85 ng/mL` with the article giving `1.1 ng/mL` as a reference but no comparator sign. The older brother, mother, and younger sister had reported α-galactosidase activities of `0.75`, `1.82`, and `3.48 mcmol/L/h`, and Lyso-Gb3 values of `1.0`, `0.4`, and `0.4 ng/mL`, respectively. The article reports that family members were asymptomatic. Do not infer a Lyso-Gb3 threshold direction where the text omits it.

The 2023 English Fabry cohort `PMC10726653` independently lists `GLA c.870G>A p.(Met290Ile)` among reported pathogenic variants. Thus the GLA allele is not novel. Europe PMC exact searches for `TTR c.289T>C p.Ser97Pro` and `PRKAG2 c.969C>A p.Phe323Leu` returned only this 2026 record within the searched index; this bounded result is not a novelty claim.

The article states that the combination makes it difficult to assign which variant caused the HCM or whether there was synergy. Its suggestion that `PRKAG2` may be the main determinant is an author hypothesis, not a proven causal result; the reported variant remains a VUS and lacks clear segregation.

## Portuguese/English content comparison

| Topic | Portuguese source | English translation | Disposition |
|---|---|---|---|
| HCM wall-thickness criterion | “... espessura da parede `≥ 15 mm` ... ou `≥ 13 mm` em parentes de primeiro grau...” | “... wall thickness `≥ 15 mm` ... or `13 mm` in first-grade relatives...” | The English translation omits the inequality sign before 13 mm. This changes precision and should be reported as a translation-fidelity discrepancy. It is a general diagnostic threshold, not a new case observation. |
| Three HGVS variants | Same accessions, coding changes, protein changes, and author classifications | Same accessions, coding changes, protein changes, and author classifications | No variant-information increment between the versions. |
| Family segregation and enzyme values | Father negative; brother GLA only; mother/sister GLA+TTR; matching enzyme/biomarker values | Same details and values | No patient/family/segregation increment between versions. The relative Lyso-Gb3 reference lacks a direction sign in both. |
| Family asymptomatic sentence | Appears once | Appears twice in the English version | Editorial duplication, not a data difference. |
| Ethics approvals | Introduction: `7.108.530 / CAAE 55200322.5.3009.516`; ethics section: `7.106.271 / CAAE 55200322.5.3009.5016` | Same conflicting pair appears in the translated English text | Internal source inconsistency shared by both versions; not a translation effect and not resolved here. |

## Retrieval and endpoint accounting

| Query/arm | Result | What it does and does not show |
|---|---|---|
| Europe PMC `DOI:"10.36660/abc.20260122"` | One record, `PMC13718332`, language `por`, no `abstractText`. | Article is indexed under the Portuguese DOI/record. |
| Europe PMC English-title search without `LANG` | One result, still the Portuguese-language PMC record. | An English title query can retrieve the source record. |
| Europe PMC `LANG:eng AND TITLE:"Hypertrophic Phenotype ..."` | Zero results. | Language filter excludes the source record, even though the publisher has a full English translation. |
| Europe PMC `DOI:"10.36660/abc.20260122i"` | Zero results. Crossref and doi.org also returned 404 for the translation DOI. | The separate English DOI is visible on the publisher page but not resolved in these metadata services at retrieval. Do not call it globally unavailable. |

This article is a **bilingual full-text control**. It adds one verified translation-fidelity correction (the missing `≥`) but no language-exclusive article, patient, or variant increment. Any acquisition difference caused by EPMC's language label or DOI indexing is a retrieval/index effect, not proof that the clinical evidence exists only in Portuguese.

## Current review state

- PMC JATS, publisher JATS, publisher English page, and English PDF all retrieved and hash-checked.
- Independent blind review compared the two versions and checked the source/translation DOI, license, segregation, biomarker values, and the inequality discrepancy.
- GLA `c.870G>A` prior English evidence verified through the 2023 English cohort `PMC10726653`.
- TTR/PRKAG2 prior-variant novelty remains unresolved beyond the bounded EPMC exact queries; no novelty claim is made.
- No patient, article, or variant increment is counted in the primary endpoint; this case is a negative control for language-exclusive evidence and a translation-fidelity example.

## Procedural reference (not clinical evidence)

Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. arXiv:2609.00065. https://doi.org/10.48550/arXiv.2609.00065. This procedural reference informed database-response verification only; it contributes no case or variant evidence.
