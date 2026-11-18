# 多语种总体候选综合 R4

**Status:** in-progress  
**Created:** 2026-11-15  
**Completed:** —  
**Scope:** Exploration-only synthesis before question-conditioned confirmatory sampling  
**PR:** N/A (research synthesis)

## Current conclusion

The expanded exploration includes Chinese, Spanish, and Portuguese genetic-case leads, bilingual controls, a negative access control, and the independently adjudicated Nasu–Hakola Spanish reverse control. Confirmed multilingual-only article, patient, family, variant, and fact increments remain **0**. Some non-English bodies contain details absent from same-record English abstracts, but those are convenience-sample body-only candidates until a frozen English correspondence audit establishes that the facts are unavailable in the defined English procedure.

The exploration cannot establish a population average or a universal claim. The Orphadata question-conditioned candidate frame is bounded to 1,933 rare disorders with an assessed germline disease-causing association and HPO annotation; it is not the whole genetic-variant domain. The 10-target query pilot is feasibility-only, with incomplete requests and nonspecific redacted terms.

The machine-readable [exploratory endpoint ledger R2](../../benchmark/experiments/acmg_multilingual/overall_design/ledgers/exploratory_endpoint_ledger_r2.json) keeps article, patient, family, tested-member, variant, and body-only-fact units separate and marks all five current leads, including the reverse control, as excluded from the confirmatory denominator.

## Candidate accounting

| Lead or control | Source and evidence structure | English correspondence | Current accounting |
|---|---|---|---|
| FGG hypodysfibrinogenemia family, China, 2025 | One family; one proband, two variant-positive members, three tested members; two FGG missense variants; coagulation, thrombosis, segregation, structural and functional assays | English trans-abstract covers headline case, thrombosis, broad lab pattern and both HGVS; no independent English full text; expanded exact English searches found no independent record | 13 body-only fact candidates relative to the translated abstract; patient/family/variant/confirmed language-exclusive increments 0. Independent adjudication complete. |
| BBS2 Bardet-Biedl case, Argentina, 2022 | Spanish full text; one 13-year-old proband; two reported BBS2 variants; clinical, ophthalmic, metabolic and follow-up details | Same-paper English abstract covers patient and broad phenotype. `c.613-1G>C` appears in two English full texts and ClinVar. `c.1990_1991insTA` remains transcript-unresolved; conditional NM_031885.5 consequence is p.(Asn664IlefsTer13) | Article/patient/known-variant increments 0; insertion is an unresolved candidate. Independent adjudication complete. |
| ALG13 CDG case, Colombia, 2021 | Spanish article record; abstract reports one boy, `c.428C>T (p.Pro143Leu)`, maternal carrier and phenotype | 2026 English full text lists the same variant and cites the Spanish article; publisher full text was inaccessible in this audit | Not a valid MGAT2 pilot-target hit; no language-exclusive increment. |
| Glanzmann thrombasthenia case, Spanish, 2025 | Spanish index hit without abstract; subscription-only full text; no accessible variant/family evidence | English correspondence not auditable; second English congress hit not shown to be same case | Negative/access control; no endpoint count. |
| Nasu–Hakola, Bolivia, 2003 | Spanish full text with English and Portuguese summaries; two affected brothers; clinical, imaging and pathology detail | Same article is returned by the English query (rank 509/854). No patient-level molecular test or HGVS. Spanish manifest rank 1/1 conflicts with retained exact-query `hitCount=0` and is unresolved | Reverse control; body-only clinical detail candidate only; article/patient/family/variant/language-exclusive increments 0. |
| KDM3B, SOX10, SMPX, CNKSR2 and earlier R3 leads | Non-English bodies with same-record English abstracts or complete translations; several prior English allele or duplicate-report matches | Body details are not globally English-negative; duplicate and phenotype conflicts retained | Translation/detail candidates only; no confirmed patient/variant/fact increment. |
| Portuguese GLA/TTR/PRKAG2 bilingual article | Complete Portuguese and publisher English translation of the same case | Same case/genotypes in both full texts; one threshold symbol omitted in translation; GLA allele in English cohort | Bilingual negative control and translation-fidelity event; no endpoint count. |

## What can be counted now

- **Confirmed article increment:** 0.
- **Confirmed patient/proband increment:** 0.
- **Confirmed family increment:** 0.
- **Confirmed variant increment:** 0.
- **Confirmed language-exclusive fact increment:** 0.
- **Bounded body-only fact candidates:** 13 in the independently adjudicated FGG case, plus unpooled detail candidates in prior audits. These are not a population estimate.
- **Nasu–Hakola body-only detail candidates:** qualitative, unpooled clinical/imaging/pathology details relative to the same-record English summary; not counted as a global language-exclusive increment.
- **Translation-fidelity events:** recorded separately; they are not language-exclusive evidence.

The FGG case is the strongest current body-detail candidate because its English trans-abstract omits many numeric and mechanistic details while the Chinese body reports them. It still cannot support the claim that English literature lacks those facts globally. The BBS2 case demonstrates the opposite safeguard: a non-English case can contain a variant that is already documented in English sources, while a second unnormalized insertion remains unresolved.

## Corrected search interpretation

The English and multilingual arms must search the same source universe. A `LANG:eng` filter is a diagnostic result stratifier, not a valid English baseline, because it can exclude a Spanish or Chinese article that has an English abstract or English metadata. In the corrected 10-target pilot, English query terms found the BBS2 Spanish article at rank 679 of 6,081 results; the Spanish query found it at rank 2 of 8. This is a ranking/recall feasibility observation, not a treatment effect estimate, because query budgets and ranking cutoffs were not frozen.

## Generalization boundary and next gate

No convenience case may enter the confirmatory denominator. Before confirmation, freeze the question-conditioned frame, language-neutral query construction, source universe, query budget, primary fact unit, δ, missingness bounds, multiplicity, stopping rule, and power-based cluster count. The current 60-cluster floor is not powered; the sensitivity analysis shows required analyzed clusters ranging from 10 to 1,369 across illustrative δ and variance values.

