# GIM pipeline and data correction, 2026-09-06

**Status:** completed
**Created:** 2026-09-06
**Completed:** 2026-09-06
**PR:** not merged; isolated branch awaiting human review

The iteration corrects two source-visibility labels, repairs the model-panel
diagnostic and makes the audit wrapper select the invoked paper worktree.
Implementation is in branch `iteration/gim-pipeline-20260906`. The original
paper worktree's existing changes were preserved as the starting point.

## Data correction

`rett_078` cites `p.Pro302Leu`; `rett_088` cites `D156E`. Both are protein
names. The former ledger recorded each as both `A.variant_hgvs_p` and
`A.variant_hgvs_c`, although the product catalog defines the latter as an HGVS
coding variant. Coverage revision `v1.2-protein-only-visibility-correction`
removes only these two coding-field records and their derived increment entries.
The source bytes, comparator membership, direct-inference events and independent
field-bridge ledger are unchanged.

| Measure | Before | Corrected |
|---|---:|---:|
| Verified field-anchor checks | 211/211 | 209/209 |
| Unique source anchors | 130 | 130 |
| Native-layer field records | 106 | 104 |
| On-disk events | 32 | 32 |
| Comparator families with an increment | 8/13 | 8/13 |
| Full-text-only observations | 21 | 19 |
| Field categories | 7 | 7 |
| Coding-name observations | 6 | 4 |
| Protein-name observations | 6 | 6 |
| Median observations per comparator family | 2 | 1 |
| Leave-one-family-out observation range | 15–21 | 13–19 |
| Variant-name share | 12/21 (57%) | 10/19 (53%) |
| `rett_007` contribution | 6/21 (29%) | 6/19 (32%) |

The [audit artifacts](../../../benchmark/experiments/acmg_multilingual/audit/2026-09-06/)
contain separately regenerated baseline and corrected receipts, plus
`revision_provenance.json` binding ledger, receipts, unchanged sources and
dependency files by SHA-256. Corrected facts SHA-256:

```text
c3bde5c9c08ede2c2e1b6cfa66ec8c68ab760e6f67dd5018c565c10e6e5ab651
```

## Diagnostic pipeline correction

The former overall Fleiss' kappa treated four different criteria as additional
raters of one event. Three models agreeing on every criterion could produce
kappa −0.090909. Version 2 instead uses event × criterion as the item, models
as raters, and complete-panel events for kappa. A hand-calculated disagreement
case with balanced 2:1 splits gives the expected −1/3.

Other repaired failures were dictionary-to-BaseModel serialization, a report
validator that could not reload its own JSON, incomplete responses silently
becoming negative votes, duplicate/empty model IDs, ignored unknown event IDs,
single-model consensus and zero similarity for two identical empty code sets.
The CLI now uses the configured reasoning endpoint, credentials and parameters.

Version 2 retains prompts, raw responses, request parameters and explicit failed
votes. Consensus requires at least two valid respondents and a strict majority
of them. The report records unavailable events and all statistical denominators.
This is a diagnostic contract revision; no historical model report was relabelled
as a v2 run and no live model calls were made during this iteration.

## Reproduction and validation

The shell wrapper formerly resolved the shared scripts directory to another
checkout and embedded the report path in Python source. It now preserves the
invoked worktree, resolves relative output before uv changes directory and passes
the path through `sys.argv`. Python execution stays inside the locked uv runtime.
Tests cover ordinary and symlinked script directories, outside working
directories, quoted paths and relative output paths.

The source-field regression was run before correction and failed for both
protein-only examples. Panel counterexamples initially had 19 failures and
3 passes. The final local experiment suite has 46 passing tests, including
28 model-panel cases; Ruff and shell syntax checks pass. The offline audit
verifies 209/209 checks and 32/32 on-disk events. Both manuscript sources are
compiled (main: 27 pages; supplementary: 21 pages), with no undefined
references or citations. The updated figure/table counts are checked against
the receipts; both PDFs contain no raster images. Table S3 now paginates with
all 18 source rows visible, the author block wraps inside the page, and the
obsolete author-placeholder statement is corrected. Six pre-existing minor
overfull-box warnings remain in long command/field/declaration text.

Independent agent review found no blocking code or ledger defects. This review
does not replace the project's required human review before merging. The paper
worktree uses `master`, which project rules reserve for manual merges.

## Remaining study boundaries

The two-entry positive pilot still has zero main-study-ready entries. No new
translation-equivalence review, clinical adjudication or three-arm experiment
was fabricated. The local bridge ledger contains normalized variant mappings;
its hash/quote checks do not establish that a coding variant name occurs in the
source. The [current developer guide](../../gim/reproducibility/README.md)
describes the commands and the v2 reporting contract.

Documentation lifecycle review retains `docs/gim/` and its reproduction guide
as active reference material and archives this completed iteration record here.
`docs/archive/` is a shared symlink to the application repository, so this new
record is stored in that shared archive; implementation, manuscripts and audit
artifacts are in the isolated paper worktree. Unrelated plans were not moved.
