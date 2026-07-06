# Salt Hydraulic Evidence Subset

Generated: `2026-06-22T09:47:35-05:00`

## Purpose

This package defines a conservative Salt-family hydraulic evidence subset
using only existing June 15 and June 18 transport outputs. It does not
reopen extraction, rebuild campaign figures, or loosen the cross-family
closure gate. Its job is to identify which Salt branches are clean enough
for Salt-family branch-pressure interpretation and which of those branches
overlap with the current Water candidate subset without overclaiming
cross-family readiness.

## Inputs Used

- Salt case packages under `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family` and `tmp/2026-06-15_live_case_analysis/contract_fix_salt2`
- Water hydraulic subset `reports/2026-06-18_ethan_water_hydraulic_evidence_subset/README.md`
- Interpretation closure package `reports/2026-06-18_ethan_transport_interpretation_closure/README.md`

## Candidate Salt Hydraulic Branches

- `left_lower_leg, left_upper_leg, lower_leg, right_leg, test_section_span, upper_leg`

These branches keep positive shear/direct branch means, positive branch-end
cumulative direct `p_rgh` drop, and stable per-case alignment signatures
through the current Salt retained windows.

## Shared Salt/Water Candidate Overlap

- `right_leg, test_section_span, upper_leg`

These overlap branches are clean in both family screens, but they remain
guarded from direct cross-family hydraulic fitting by the June 18 closure
package.

## Contextual-Only Salt Hydraulic Branches

- none

## Excluded Salt Hydraulic Branches

- none

## Cross-Family Boundary

No branch in this package is promoted directly to cross-family hydraulic use.
The overlap screen is meant to show where future cross-family work could start
once the closure gate changes, not to claim that it already has.
