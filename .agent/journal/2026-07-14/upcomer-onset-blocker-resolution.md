---
provenance:
  - work_products/2026-07/2026-07-07/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv
  - work_products/2026-07/2026-07-07/2026-07-07_upcomer_correlation_v2/upcomer_correlation_fit.csv
  - work_products/2026-07/2026-07-08/2026-07-08_upcomer_onset/upcomer_onset_regime_table.csv
  - reports/2026-06/2026-06-29/2026-06-29_ethan_upcomer_recirculation_evidence/upcomer_recirculation_case_summary.csv
tags: [journal, upcomer-onset, recirculation, blocker-resolution, thermal-closure]
related:
  - .agent/status/2026-07-14_AGENT-324.md
  - imports/2026-07-14_upcomer_onset_blocker_resolution.json
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/README.md
task: AGENT-324
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Upcomer Onset Blocker Resolution

## Observed

The current admitted upcomer onset dataset contains 3 rows: Salt2/3/4 Jin.
Their Re range is `71.125` to `134.883`. All three rows classify as
`recirculation_cell_observed`. The minimum backflow fraction is `0.171875`, and
the minimum `Ri_median` is `1.497987`.

The prior onset fit records Route A midpoint Re `250.0` and Route B midpoint Re
`167.5`. Both midpoints are above the maximum current admitted Re; Route A is
well outside the admitted range, and Route B midpoint is still extrapolated.

## Interpretation

The blocker is narrowed but not resolved. The thesis-safe claim is that admitted
Salt2/3/4 upcomer rows are mixed-convection recirculation-cell diagnostics. The
current evidence does not support a calibrated onset threshold, a production 1D
regime switch, or a universal upcomer `f_D`, `K`, or `Nu` closure.

## Work Product

Created:

- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/upcomer_onset_evidence_status.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/math_and_theory.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/next_evidence_requirements.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/blocker_status.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/results_interpretation.md`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/source_manifest.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/summary.json`

## Next Evidence

Minimum blocker-resolution evidence:

- terminal corrected Salt-Q points near Re `150`, `200`, and `250` if admitted;
- at least one non-recirculating anchor or transition pair;
- mesh/time uncertainty for backflow fraction, `Ri_median`, and `Nu_upcomer`;
- wall-core or wall-bulk Delta T on the same retained windows.

## Validation

`python3.11 -m unittest tools.analyze.test_upcomer_onset_blocker_resolution`
passed 4 tests.

No native CFD solver outputs were modified.
