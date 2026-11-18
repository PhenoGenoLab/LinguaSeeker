# Multilingual overall experiment plan R1

**Status:** in-progress  
**Created:** 2026-11-14
**Completed:** —
**PR:** N/A (research protocol)

## 2026-11-16 用户选择状态

用户选择了 Orphadata 2026-06-23 的 1,933 个已评估胚系关联/HPO 问题框、主要阈值 `δ=0.25`，以及简单随机无放回抽样。目标估计量因此采用该有限问题框的总体平均。早期候选六层和每层 10 个/总计 60 个簇仅作为历史覆盖草案，不再是所选抽样方案。用户选择和哈希绑定见 [selection receipt](../../benchmark/experiments/acmg_multilingual/overall_design/user_selected_confirmatory_inputs_r1.json)。全协议尚未冻结，功效模拟仅为敏感性；确认性检索仍未启动。

## Objective

Estimate two non-equivalent outcomes in a bounded target population: (1) additional validated evidence retrieved relative to the frozen English procedure, and (2) evidence units supplied only by verified non-English full text after a bounded English-equivalence audit. The second is the primary outcome for a claim that multilingual source coverage extends evidence beyond English sources. This plan cannot test or establish the universal claim that multilingual retrieval is always superior.

## Sampling frame

The user-selected confirmatory frame is the bounded Orphadata 2026-06-23 frame of 1,933 disorder/HPO questions with an assessed disease-causing germline association. Stable ORPHA/HPO identifiers and the frame SHA-256 are recorded in the [selection receipt](../../benchmark/experiments/acmg_multilingual/overall_design/user_selected_confirmatory_inputs_r1.json). The selected allocation is a fixed-seed simple random sample without replacement; the 60-question file is a draft manifest only and has not authorized retrieval.

Source language is an observed outcome of the retrieval arms, not a sampling stratum: sampling known Chinese/Spanish articles would condition inclusion on the outcome and inflate the apparent multilingual yield. If a separate language-stratified descriptive sample is used, report it separately; it cannot replace the question sample for the primary overall estimate. The prior six convenience strata and 60-question coverage floor are historical design drafts and are superseded for the selected allocation.

Use two distinct sampling frames if the claim includes both richer evidence for known variants and discovery of variants/relations absent from the English arm:

- **Variant-conditioned frame:** independently sample canonical variant/evidence-family questions from a registry or other frame fixed before multilingual searching. This estimates additional facts, patients and families for specified events; it cannot estimate discovery of events absent from that frame.
- **Question-conditioned frame:** independently sample gene/disease/phenotype questions, without selecting them from known non-English candidate articles. Treat variants and relations found by either arm as nested outcomes. This is needed to estimate newly discovered gene–variant–phenotype relations.

Articles, table rows, variants within one sampled question and translated abstracts are not independent units. Claims must be limited to the frozen represented target population. For broader ACMG/genetic-disorder generalization, draw genes and target questions from an independent, enumerable frame before multilingual candidates are inspected. The 60-question draft is a coverage artifact only, not a power-justified sample size; the confirmatory sample size must be calculated from the frozen primary endpoint, δ, target power and a defensible question-level variance estimate. The question-conditioned contract is now represented by `question_cluster_schema.json` and the `cluster_validator.py` `cluster_kind="question_conditioned"` branch. It validates ORPHA/HPO target metadata while retaining the existing receipt, source-hash, dual-review and fact-grounding gates. The frame preserves raw HPO association lists; duplicate HPO IDs are allowed when one concept has multiple frequency associations, and `hpo_count` must equal the raw list length. This schema change does not freeze the study manifest or authorize retrieval; query scope, arm exposure, budgets, missingness and inference rules remain open.

## Paired arms

For every sampled question, freeze the same date range, inclusion criteria, query/search limits, source database universe, identity rules and review workflow. The user-selected language contrast is:

- **English arm:** English-language query forms against the shared source universe;
- **multilingual arm:** the complete English arm plus pre-registered Spanish- and Portuguese-language query forms against the same source universe.

Do not apply a source-language filter to either arm. Record the body language found during source review as an outcome. Query counts and retrieval budgets remain to be frozen.

The English query arm can still retrieve a record with an English abstract and non-English body. Before retrieval, freeze whether the English arm may use that non-English full text. Also align the primary outcome with the intended contrast: language-exclusive facts present in the multilingual evidence set, or facts additionally acquired by the multilingual query arm after accounting for what the English query arm retrieved. Source language alone does not establish query-arm increment.

The multilingual evidence set must retain every verified English-arm unit. This guarantees non-decrease by construction, not strict increase. Preserve query-session receipts separately from evidence adjudication: a completed zero-candidate query is a valid zero-yield sampled cluster, while a failed/unrun query is unresolved. For an efficiency claim, add a separate equal-resource randomized arm with fixed and equal query, access, model and review budgets. The additive multilingual arm alone estimates retrieval expansion, not cost efficiency.

## Primary endpoint

After original-text extraction, patient/family deduplication and independent adjudication, record endpoint-specific differences for each cluster. Store a dual-reviewed disposition for every candidate returned in each query (include, irrelevant, duplicate, or unresolved); no returned candidate may disappear from the ledger. Unresolved candidates remain missing and put the cluster into sensitivity-only/excluded handling under the frozen rule. Store a fact-level ledger with source IDs, verified body-language provenance, English and multilingual arm presence, bounded English-equivalence status, original-text grounding, and independent adjudication. Derive aggregate counts from that ledger; do not enter the primary language-exclusive count as an unaudited manual total. Separate retrieval-workflow increment from bounded English-audit-exclusive increment:

\[
D_i=Y_{M,i}-Y_{E,i}
\]

Here `Y` is evaluated separately for four endpoints: fact units, independently ascertained patient/proband units, family units, and gene–variant–phenotype relations. Patient and family units are nested but distinct; do not merge them or sum endpoints into one evidence count. The primary language-exclusive endpoint is a fact unit that is (a) grounded by a typed `grounding_source_id` in verified non-English full text, (b) independently adjudicated by distinct primary and independent reviewers (with a recorded arbitrator when they disagree), (c) deduplicated, and (d) not equivalent to any source found in the frozen English correspondence protocol. The source hash, original quotation and locator, query-form hash, provider, timestamp, and response receipt hash must remain linked in the fact/source ledger. Also record all units newly retrieved relative to the English procedure, since some may be English sources missed by that procedure; these measure retrieval expansion but not language-exclusive contribution. A query/access failure is unresolved, not a zero.

## Pre-registration gates

Before opening candidate results, freeze:

1. the final sample size and hash-bound simple-random manifest for the selected 1,933-question frame;
2. the source universe, date cutoff, query ladder, per-question budgets, response parsers and candidate limits;
3. the primary endpoint exposure/arm definition and user-selected minimum meaningful increment `δ_language_fact=0.25`; patient, family and relation counts remain descriptive until their thresholds and data contracts are separately reviewed;
4. transcript normalization, structural-variant and same-patient rules;
5. access-failure and abstract-only handling;
6. blinded adjudication roles and disagreement resolution;
7. cluster bootstrap or hierarchical-model specification;
8. one-sided confidence level, multiplicity handling and stopping boundaries.

After retrieval, reconcile every record against the frozen cluster manifest with `validate_study_cluster_set`. Every sampled ID must appear exactly once as a zero-hit, primary-eligible, sensitivity-only, or explicitly excluded outcome; do not compute the denominator from a filtered list of eligible rows.

An English access failure is unresolved, not English-negative. A translated abstract is not a second source. A repeated allele is not a new patient or a new variant without the relevant unit-level evidence.

## Decision rule

For the primary endpoint, test `H0: μ_language_fact ≤ δ_language_fact` against `H1: μ_language_fact > δ_language_fact` in the frozen target population. Report a one-sided 95% lower confidence bound using pre-registered nesting-aware cluster resampling and multiplicity control for any additional confirmatory endpoints. Claim bounded superiority only if the primary adjusted lower bound exceeds its threshold, the English query-and-identity procedure gate is complete, and pre-specified missingness and heterogeneity checks pass. If the lower bound remains below the threshold at the maximum sample, report “not demonstrated.” If a pre-registered upper bound falls below the threshold at the futility boundary, report “not supported for this endpoint in this target population.”

One positive case cannot establish a population-average effect. Report prespecified subgroup heterogeneity, but a subgroup with no gain does not by itself negate the finite-frame mean if the primary lower confidence bound exceeds `δ`. A true negative result and an unresolved observation are different states: unresolved cases remain missing and enter the pre-registered sensitivity analysis, rather than being set to zero or treated as an automatic veto. The final manuscript must state the target population, sampling frame, independent question unit, endpoint-specific `δ`, missingness assumptions and confidence bound.

## Current gate status

The existing case packages are exploratory convenience samples. They establish source-grounded extraction and correspondence risks, but they do not satisfy the selected confirmatory manifest, English query-procedure/missingness gate or inferential gates above. Their confirmed patient and variant increments remain zero. No overall effect has been estimated.

The machine-readable v3 schema continues to validate sampled variant-conditioned targets with zero candidates. The new question-level schema/validator branch validates ORPHA/HPO targets without inventing a canonical variant event; discovered events remain nested outcomes. The updated contract retains the existing receipt, source-hash, dual-review, arbitration and original-text grounding checks. Patient, family and relation outcomes remain descriptive under the currently selected primary endpoint.

## Design clarifications required before data collection

### Cluster identity and nesting

Assign each sampled question a stable `cluster_id` before retrieval. In the selected question-conditioned frame, the independent unit is the preregistered ORPHA/HPO question; discovered alleles, relations, articles, families, patients and facts are nested outcomes, not new independent clusters. Multiple rows in one article, multiple relatives in one family, variants within one question and repeated reports of one patient do not create independent clusters. The old minimum of 10 per convenience stratum and 60 overall is not a confirmatory sample-size rule. Variant-conditioned event records may be stored as nested outcomes only after transcript-aware normalization; an unresolved event remains `pending` and is excluded from inference until normalized.

### Endpoint-specific estimands

Pre-register separate units and thresholds:

- fact endpoint: valid fact units per cluster, with its own `δ_fact`;
- patient endpoint: independently ascertained, deduplicated patient/proband units per cluster, with `δ_patient`;
- family endpoint: independently ascertained family units per cluster, with `δ_family`;
- relation endpoint: unique gene–variant–phenotype relations per cluster, with `δ_relation`.

The endpoint thresholds have different units and must not be pooled. A multilingual evidence set is designed to retain every verified English-arm unit, so it cannot decrease by construction; strict increase is an empirical question. Query/access failures are missing/unresolved, never zero. If comparing independently executed search sessions rather than nested final evidence sets, their raw observed difference may be negative due to retrieval stochasticity and must be analyzed as a paired workflow comparison.

### Sampling estimand and missingness

The selected simple-random design targets the population mean over the finite 1,933-question frame; the earlier equal-stratum estimand is superseded. Define the English-baseline gate operationally before retrieval: all pre-registered queries, identity checks and access routes must be attempted and logged for every question. This procedure-complete status is distinct from full-text availability. Freeze an overall maximum unresolved/abstract-only proportion and report it across pre-specified access-relevant subgroups. Unresolved cases remain missing and enter a missing-not-at-random sensitivity analysis bounded using the pre-registered candidate limit per question; they are never silently coded as zero or English-negative. If the missingness ceiling is exceeded, no superiority claim is allowed until the access gate is repaired. If missingness is within the ceiling, report the primary estimate plus conservative, endpoint-specific sensitivity bounds; a superiority claim is allowed only if the lower confidence bound remains above `δ` under those bounds. Missingness is neither an automatic veto nor presumed ignorable.

### Inference and stopping

Specify the finite-population inference procedure and resampling levels before retrieval. For success, use a one-sided lower bound with the frozen multiplicity rule for the primary endpoint and pre-specified subgroup sensitivity checks. For futility, specify a separate one-sided upper-bound confidence level and alpha-spending rule; do not invoke an undefined “upper bound.” The final sample size, futility boundary and success boundary must be fixed before observing outcomes.

### Equal-resource arm and blinding

Randomize at the `cluster_id` query-session level for an efficiency arm; freeze total query count, retrieval time, full-text requests, token budget and reviewer time per arm. Prevent leakage by running arms in isolated sessions and withholding candidate lists and source identities until extraction is complete. Reviewers may see the original text needed for grounding, but language/arm labels, search provenance and the competing arm's candidates are masked where technically possible; unmask only for the adjudication step.

## Machine-readable design inputs

The pre-retrieval target strata, cluster schema and endpoint-specific threshold placeholders are stored in `benchmark/experiments/acmg_multilingual/overall_design/`. These files are design inputs only: they contain no retrieved clusters and explicitly exclude the existing convenience packages from the inferential denominator until the query-and-identity procedure gate, missingness ceiling and independent adjudication rules are frozen and complete.
