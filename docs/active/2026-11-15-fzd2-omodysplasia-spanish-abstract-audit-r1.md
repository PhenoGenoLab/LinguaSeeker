# Spanish/English Abstract Audit: FZD2 Omodysplasia R1

**Status:** in-progress  
**Created:** 2026-11-15  
**Completed:** —  
**Scope:** Exploratory comparison of one Spanish full text and its same-record English abstract  
**PR:** N/A (research audit)

## Question and current result

Does the Spanish article body expose case-level information not preserved in its English abstract, and does that information establish a new variant or patient?

The article reports an 11-year-old boy with FZD2-related type 2 omodysplasia. The same PMC record contains a Spanish abstract and an English abstract, while the article body is Spanish. The English abstract captures the central phenotype and the reported `FZD2 c.1640C>A p.(Ser547*)` allele. The Spanish body supplies more detailed birth, developmental, surgical, physical-examination, anthropometric, radiographic, and prior-literature comparison details. The paper explicitly says the same allele was previously reported in a Japanese male patient. Therefore this is **not a new-variant case**. It is a same-record abstract/body coverage candidate and, at most, a candidate for richer case facts than the abstract.

The body and English abstract also disagree on variant consequence: both show `c.1640C>A p.(Ser547*)`, but the Spanish text calls it `variante sin sentido` (nonsense), while the English abstract says `missense`. The original allele and stop-gain consequence should be checked against a transcript-aware variant representation and the cited 2018 report before this is presented as an English abstract error. This is a source/translation consistency issue, not proof of multilingual retrieval superiority.

## Source identity and provenance

- Article: Cammarata-Scalisi F, et al. *Hallazgos clínicos, radiológicos y moleculares de la omodisplasia de tipo 2*. Biomédica. DOI: `10.7705/biomedica.7922`.
- Europe PMC/PMC record: PMCID `PMC13743072`, index language `spa`; record title contains both Spanish and English title forms.
- Europe PMC core result for `DOI:"10.7705/biomedica.7922"`: one result; the record has no PubMed abstract field (`abstractText` absent) though the PMC full-text HTML contains both Spanish and English abstract sections.
- Retrieved PMC HTML and OAI JATS are retained in the paper workspace under `benchmark/experiments/acmg_multilingual/candidate_audits/fzd2_omodysplasia_r1/`. The HTML SHA-256 is `818262b2d2a3d02d2f2272c9bfb1e1c0af6acd44b261ecd39d1279d31899d377`; the OAI JATS SHA-256 is `70ef4205543eafec5459d54a2fdd0d9b78070bb3b22782ec2c73bfae1cc3f762`.
- Europe PMC record JSON: retained as `epmc_record.json`; SHA-256 `c3b9fbe14c2832c969de178adcc3900477e8279654966c987b1f8a506f1d7c50`.
- Crossref JSON: retained as `crossref_record.json`; SHA-256 `818ed0b29e189b8ba6e2eb2beae56706d082527ed035757ae65ae54ab1c02577`.
- Crossref metadata includes an English abstract matching the PMC English abstract and a Spanish title, but no separate English DOI/translation relation. Thus article discovery and evidence-language access are distinct here.

Hashes bind the retrieved bytes, not the correctness of the clinical or variant interpretation. Temporary raw responses are in `/tmp`; the retained record is this audit and its exact quoted source snippets.

## Candidate body facts versus the same-record English abstract

Source locators are section names from the PMC full-text HTML (`Resumen`, `Abstract`, `Presentación del caso`, `Cuadro 1`, `Cuadro 2`, and `Discusión`). Quotations retain source wording; candidate normalized facts are not independent endpoint units until the fact ontology and equivalence audit are frozen.

| Source locator / Spanish text | Normalized fact candidate | English abstract coverage | Status |
|---|---|---|---|
| `Presentación del caso`: `de 11 años, el tercero de una prole de cuatro hermanos, caso único en la familia y producto de padres no consanguíneos, procedentes de Bolivia`; born at 39 weeks, 3,100 g and 48 cm | The male proband was 11, third of four siblings, only affected family member as reported, parents nonconsanguineous and from Bolivia; term birth measurements recorded. | Absent, except generic “male adolescent.” | Body detail candidate, one patient only. |
| `Presentación del caso`: `El desarrollo psicomotor y el desempeño escolar del paciente fueron adecuados.` | Psychomotor development and school performance were reported as adequate. | Absent. | Body detail candidate. |
| `Presentación del caso`: surgeries at 6 months and 7 years for bilateral cleft lip; hospitalization at 1 year for UTI; umbilical hernia repair at 8 years | Medical/surgical timeline: cleft repairs at two ages, UTI admission, and umbilical hernioplasty. | Absent. | Body detail candidate; not additional patients. |
| `Presentación del caso`: detailed facial, dental, ear, pectus, genital, and limb findings | Specific exam includes frontal prominence, sparse broad eyebrows, ptosis, broad nasal bridge, anteverted nares, short columella, low-set posteriorly rotated ears, dental anomalies, pectus excavatum, micropenis/ascending testis history, and rhizomelic shortening. | Only broad limb shortening, cleft lip, micropenis, and retractile testicle are in English abstract. | Body detail candidate; clinical labels need faithful translation. |
| `Cuadro 1`: arm 16.1 cm (<5th percentile), forearm 17.1 cm (<5th), hand 14.5 cm (<3rd), thigh 32 cm (<3rd), leg 29 cm (<5th), foot 21 cm (reported percentile band) | Segmental anthropometry with low percentile measurements. | Absent. | Body detail candidate; preserve source table and unclear foot percentile exactly. |
| `Presentación del caso`/`Figura 1`: radiographs showed short humerus, altered radius and short first metacarpal | Detailed skeletal imaging findings. | First-metacarpal shortening is in abstract; humerus/radius details are not. | Partial body detail candidate. |
| `Discusión`: `La variante descrita en este informe fue reportada en un paciente de sexo masculino por Nagasaki et al., en Japón.` | Authors state that the same variant had already been reported in a Japanese male. | Absent; English abstract reports the allele but not its prior occurrence. | Important novelty counterevidence; not a new variant. The cited source must be checked directly before treating as independently verified. |

The two abstracts are not separate patients or sources. The Spanish body, same-record English abstract, Crossref English abstract, and PMC record belong to one publication identity. Body facts absent from the abstract can be counted only under a predeclared fact-level availability endpoint, not as article or patient acquisition increments.

## Variant representation and English correspondence search

The Spanish abstract/body says “variante sin sentido … FZD2 c.1640C>A p.(Ser547*)”; the English abstract says “missense variant … FZD2 c.1640C>A p.(Ser547*).” A premature stop symbol `*` is inconsistent with “missense” under standard protein consequence terminology; the authors' Spanish “nonsense” wording matches the displayed protein consequence. Independent transcript/sequence normalization has not been completed.

The article's own discussion says this same `c.1640C>A p.(Ser547*)` allele was previously reported in a Japanese male by Nagasaki et al., citing *Nonsense mutations in FZD2 cause autosomal-dominant omodysplasia: Robinow syndrome-like phenotypes* (2018; DOI `10.1002/ajmg.a.38623`; PMID `29383834`). This establishes recurrence according to the source authors and makes “novel variant” an invalid interpretation of the 2026 case.

Bounded Europe PMC searches performed 2026-11-15:

| Query | Result | Interpretation |
|---|---|---|
| `DOI:"10.7705/biomedica.7922"` | One PMC record, `PMC13743072`, language `spa`. | Same publication is indexed with mixed-language title metadata. |
| `TITLE:"Clinical, radiological and molecular findings of type 2 omodysplasia"` | One record: `PMC13743072`, indexed `spa`; response SHA-256 `c20a0e385c990080257b3283d20b000eacdd763c179a059bb9c29782a0337a0d`. | The bilingual title retrieves the same Spanish-body record; no separate English full text is implied. |
| `LANG:eng AND TITLE:"Clinical, radiological and molecular findings of type 2 omodysplasia"` | Zero records; response SHA-256 `d08fbe5b1c7f34f07de092f7b58519f4e0c930bcbe29c3fe5ed2a23eaa12d610`. | A language-restricted English query excludes this record despite its translated English title and abstract. This is a database-filter effect, not proof that English readers cannot access the abstract. |
| `LANG:eng AND FZD2 AND "c.1640C>A"` | Three English records: PMIDs `35937024`, `29383834`, `30455931`; response SHA-256 `49d0902ab28c50ceb4b14002bac4c25a8b4b43db5b9fa751ee5fdcba36f14ba1`. | English-indexed prior omodysplasia literature contains records matching the allele query. The 2018 Nagasaki record explicitly reports a 16-year-old Japanese boy with the same nonsense allele `c.1640C>A, p.S547*`; this is a different patient. |
| `FZD2 AND "c.1640C>A"` | Four records: the Spanish PMC item plus the three English MED records above; response SHA-256 `2579e6124e65f5ee29accf7abe72a7d6bc9693788c74e511749890bf63d9d605`. | The allele has English-literature correspondence; it is not a novel-variant increment. |

The English abstract's consequence label appears discordant with the Spanish text and protein notation, but final correction requires transcript-aware normalization and source citation review. Do not classify the allele as pathogenic solely from the article's “likely pathogenic” wording.

## Review and adjudication state

- Source identity, article language, mixed abstract availability, and record provenance: verified from PMC OAI JATS, PMC HTML, Europe PMC, and Crossref metadata. OAI JATS declares `xml:lang="es"`, `article-type="case-report"`, and contains both `trans-title-group xml:lang="en"` and `trans-abstract xml:lang="en"`; this is one bilingual record, not a separate English full text.
- Spanish-body fact extraction: primary screen complete; exact passages are retained above.
- English abstract comparison: primary screen complete; broad details are distinguished from absent measurements/history.
- Prior same-allele English report: independently checked against the 2018 English abstract (PMID `29383834`), which reports a 16-year-old Japanese boy with de novo heterozygous nonsense `FZD2 c.1640C>A, p.S547*`; this is a different person from the 11-year-old in the 2026 report.
- Independent blind review: complete. The reviewer independently confirmed the bilingual-record structure, body-versus-abstract omissions, same-allele prior English case, and consequence-wording inconsistency.
- Patient-level English correspondence: the same 11-year-old is already described in the English abstract in the same bilingual record, so no patient acquisition increment is supported by this case.
- Transcript-aware HGVS normalization: pending. The displayed `p.(Ser547*)` and Spanish `sin sentido` indicate stop-gain/nonsense; the English abstract's “missense” wording is internally inconsistent and is adjudicated as an abstract wording error, not as a validated biological consequence beyond the reported notation.
- Parental segregation: not reported; do not infer inheritance or phase from this article.
- Confirmatory sample: no; this is a convenience-discovered exploratory source, excluded from the inferential denominator.

## Current disposition

This case shows that a same-record English abstract may compress or omit original-body clinical detail and may use a consequence label inconsistent with both the Spanish wording and displayed protein stop notation. The independent review confirms the article's prior English report describes a different Japanese boy with the same allele; the English abstract in the 2026 bilingual record already describes the current patient. The defensible status is **exploratory body-detail/fidelity candidate; zero article, patient, or variant acquisition increment; primary endpoint not evaluated**. No evidence from this single case can establish an overall multilingual advantage.

## Independent blind-review disposition (2026-11-15)

The independent reviewer retrieved the PMC OAI JATS record and confirmed that it declares `xml:lang="es"` and `article-type="case-report"`, with an English `trans-title-group` and `trans-abstract`, while the body remains Spanish. This is one bilingual record, not an English full-text translation. The reviewer confirmed the reported age (11 years), family position, birth history, surgeries, development, physical findings, anthropometry, radiology, prior-case comparison, and consent details against the Spanish body. The English abstract does not include those granular facts; it does summarize the current male adolescent and the headline phenotype/allele.

The English 2018 Nagasaki abstract independently reports a 16-year-old Japanese boy with de novo heterozygous nonsense `FZD2 c.1640C>A, p.S547*`. That is prior same-allele evidence but a different patient. The current 2026 English abstract already describes the 11-year-old in the Spanish body, so this cannot count as a patient-acquisition increment relative to an English-abstract baseline. The paper reports no parental testing/segregation, and it gives no patient-specific post-diagnosis outcome. Its statement that this is the first Latin American case remains an author claim and was not independently verified.

The reviewer agrees that “missense” in the English abstract conflicts with both Spanish `sin sentido` and `p.(Ser547*)`. This is adjudicated as an English-abstract wording inconsistency; transcript-aware HGVS normalization remains pending. The table's foot-length percentile is printed as `25-3`; preserve the literal value rather than normalizing it. The independent review was limited to this article and its cited English abstract and does not complete a global English correspondence search.

## Procedural reference (not clinical evidence)

Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. arXiv:2609.00065. https://doi.org/10.48550/arXiv.2609.00065. The latest arXiv record was checked on 2026-11-15; this paper describes procedural documentation and reports no task-level evaluation, so it is cited only as a workflow resource and contributes no evidence to the case or multilingual-increment claim.
