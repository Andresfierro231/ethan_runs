---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert/source_manifest.csv
tags: [journal, thesis, negative-k, section-effective-pressure]
related:
  - .agent/status/2026-07-21_TODO-THESIS-CH6-CH7-NEGATIVE-K-SECTION-EFFECTIVE-INSERT-2026-07-21.md
  - imports/2026-07-21_thesis_ch6_ch7_negative_k_section_effective_insert.json
task: TODO-THESIS-CH6-CH7-NEGATIVE-K-SECTION-EFFECTIVE-INSERT-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: journal
status: complete
---
# Thesis Ch6/Ch7 Negative-K Section-Effective Insert

## Attempted

Reviewed the negative-K dispatch package, no-fit hybrid pressure bakeoff, and
current Chapter 6/Chapter 7 pressure sections. Added thesis-current language
that turns the lower-right pressure result into a rigorous negative contribution
instead of an unresolved coefficient temptation.

## Observed

The existing thesis dossier already had pressure gate language. The insertion
needed to make the claim boundary explicit: current lower-right rows are
section-effective pressure evidence, not component-K/F6 evidence. The supporting
packages provide Salt2/Salt3/Salt4 residuals of `-1.25366731683 Pa`,
`-1.84957005859 Pa`, and `-1.67833900273 Pa`, with Salt2-frozen diagnostic
transfer maximum error `0.47046606946166093438399 Pa`.

## Inferred

The thesis can use this as evidence that the admission workflow rejects an
attractive but invalid ordinary coefficient form while preserving measured
pressure information in a better-named residual ledger. The right reduced-model
claim is model-form motivation and residual ownership, not admission.

## Contradictions Or Caveats

The Salt2-frozen transfer is numerically small on train-context rows, but it is
not candidate-reviewable because no protected split was consumed and no
ordinary admissible F6 row exists for comparison. Any statement that the hybrid
route beats F3/Shah, repairs F6, or admits component `K` would contradict the
source packages.

## Next Useful Actions

1. Carry `pressure_claim_boundary_table.csv` and `caption_bank.md` into the
   LaTeX thesis when the Chapter 6/7 sync row owns the papers repository.
2. Keep ordinary component-K/F6 work closed for these lower-right rows unless a
   future nonrecirculating or low-reverse-flow anchor with same-QOI UQ is
   released.
3. Use the no-fit bakeoff only as model-form motivation unless a future row
   explicitly performs split-safe candidate review.
