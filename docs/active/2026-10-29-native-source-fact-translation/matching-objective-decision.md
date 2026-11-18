# Matching objective decision record

**Status:** in-progress
**Created:** 2026-11-12

Decision owner: unassigned. User decision: pending. No new protocol is frozen.

Options:

| Objective | Scientific consequence | Required reporting |
| --- | --- | --- |
| Existing C5 overlap-first greedy | Preserves historical rule; cardinality and overlap can be suboptimal and ID-sensitive | Explicit policy version; optimal-matching sensitivity |
| Maximum cardinality, then total overlap (recommended candidate) | Prioritizes number of eligible matched facts; overlap breaks cardinality ties | Exact objective, independent oracle, residual tie policy, ambiguity reporting |
| Maximum total overlap | Prioritizes source coverage; may sacrifice matched fact count | Justification relative to primary endpoint; cardinality sensitivity |

For a revised policy: retain document/field/value/positive-overlap edge rules unless separately reviewed; do not introduce subject/polarity into edges to inflate downstream correctness. Freeze eligibility, matching objective, equal-optimum tie handling, semantic-assignment ambiguity, unmatched output denominator and policy version before held-out evaluation. Require permutation and identifier-renaming tests for objective values; distinguish stable objective values from stable assigned pairs. Maximum matching alone cannot resolve semantic ambiguity.

Required evidence: reviewed choice tied to primary estimand; tested implementation with independent cardinality/weighted oracle; paired old/new sensitivity on admissible reference data; explicit separation of development from held-out evidence; no silent historical score replacement.
