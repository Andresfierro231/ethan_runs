# Water Hydraulic Evidence Subset

Generated: `2026-06-22T09:47:35-05:00`

## Purpose

This package defines a conservative Water-family hydraulic evidence subset
using only existing June 15 and June 18 transport outputs. It does not reopen
extraction, rebuild campaign figures, or try to rescue excluded left-lower-leg
rows. Its job is to identify which non-excluded Water branches are stable
enough for future family-specific branch-pressure interpretation.

## Inputs Used

- Water case packages under `tmp/2026-06-15_live_case_analysis/contract_fix_water_family`
- Interpretation closure package `reports/2026-06-18_ethan_transport_interpretation_closure`

## Candidate Water Hydraulic Branches

- `right_leg, test_section_span, upper_leg`

These branches keep positive shear/direct branch means, positive branch-end
cumulative direct `p_rgh` drop, and stable per-case alignment signatures
through the current Water retained windows.

## Contextual-Only Water Hydraulic Branches

- `left_upper_leg, lower_leg`

These branches are not excluded because of the same failure mode as
`left_lower_leg`, but they are still not stable enough for Water-family branch
pressure dependencies.

## Excluded Water Hydraulic Branches

- `left_lower_leg`

`left_lower_leg` remains excluded by the June 18 interpretation closure.

## Cross-Family Boundary

No branch in this package is promoted directly to cross-family hydraulic use.
The point of this subset is to move future Water-family hydraulic work off the
excluded `left_lower_leg` branch and onto a cleaner Water-only evidence set.

## Reproduction Commands

- `python -m py_compile tools/analyze/build_ethan_water_hydraulic_evidence_subset.py`
- `python tools/analyze/build_ethan_water_hydraulic_evidence_subset.py --output-dir tmp/2026-06-18_ethan_water_hydraulic_evidence_subset_smoke`
- `python tools/analyze/build_ethan_water_hydraulic_evidence_subset.py --output-dir reports/2026-06-18_ethan_water_hydraulic_evidence_subset`
