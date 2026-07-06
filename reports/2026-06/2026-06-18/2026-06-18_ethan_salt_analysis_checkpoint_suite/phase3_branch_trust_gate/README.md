# Phase 3 Branch Trust Gate

Generated: `2026-06-18`

This checkpoint turns the Salt branch thermal support logic into a durable
promotion gate for later correlation fitting.

## Main findings

- Candidate branch rows: `36` of `63`
- Screening branch rows: `14`
- Blocked branch rows: `13`
- Candidate branch names: `left_lower_leg, left_upper_leg, test_section_span, upcomer`

## Key outputs

- `branch_promotion_gate.csv`
- `branch_candidate_subset.csv`
- `branch_screening_remainder.csv`
- `branch_reason_summary.csv`
- `branch_status_summary.csv`

## Interpretation checkpoint

This phase formalizes the Salt thermal subset that can move into the final
fit-ready package. It also preserves blocked and marginal branches explicitly so
they remain documented evidence rather than disappearing from view.
