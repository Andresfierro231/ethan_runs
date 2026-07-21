---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/resampled_pm5_matched_plane_metrics.csv
  - work_products/2026-07/2026-07-15/2026-07-15_blocker_resolution_wave_implementation/thermal_internal_nu_admission_review.csv
  - work_products/2026-07/2026-07-15/2026-07-15_downstream_pm5_final_state_refresh/f6_pm5_row_readiness.csv
  - work_products/2026-07/2026-07-15/2026-07-15_agent373_hydraulic_chain_node_verification/hydraulic_admission_final_decisions.csv
tags: [f6, internal-nu, hydraulic, forward-v1, admission, journal]
related:
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/README.md
  - .agent/status/2026-07-15_AGENT-425.md
task: AGENT-425
date: 2026-07-15
role: Coordinator/Hydraulics/Internal-Nu/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
---
# F6/Internal-Nu Admission Review And Forward Unblock

## Purpose

The user asked why final forward-v1 and final hydraulic residual remain blocked,
whether repaired wall-band `wallHeatFlux` can be used for
`h_proxy=q''/(Twall-Tbulk)`, and how to move past sign and recirculation without
promoting diagnostic rows into final closure evidence.

## Work Performed

Created AGENT-425 and built a reproducible review package from completed
evidence only. The package reads AGENT-406 PM5 repaired wall-band metrics,
AGENT-413 thermal/internal-Nu admission review, AGENT-414 downstream readiness,
and AGENT-421 hydraulic final-decision lanes.

The builder emits:

- `f6_onset_scorecard.csv`
- `f6_fit_candidate_table.csv`
- `internal_nu_h_proxy_review.csv`
- `thermal_sign_heat_balance_gate.csv`
- `internal_nu_admission_decision.csv`
- `final_forward_v1_unblock_requirements.csv`
- `source_manifest.csv`
- `summary.json`

## Findings

The repaired PM5 state resolves the extraction blocker but not the admission
blocker. All 12 PM5 rows have wallHeatFlux and Re/Pr/Ri/Gr/Ra fields, but all
12 are material-recirculation diagnostics for F6. They may support onset/regime
interpretation, not a single-stream F6 fit.

The `h_proxy` calculation is valid as a diagnostic screen. Eight rows have
positive `h_proxy` under the current local sign convention, while four require
sign review. The eight positive rows still fail single-stream internal-Nu
fitting because material reverse flow invalidates the coefficient label. They
must remain `Nu_section_effective_upcomer_diagnostic` style evidence unless a
separate section-effective/bidirectional closure is admitted.

The segment sign/heat-balance gate has zero pass rows from current evidence.
Current blockers include repaired sign-label conflicts, opposed wallHeatFlux
versus enthalpy direction, and downcomer policy restrictions.

## Current Unblock Path

Final forward-v1 remains blocked until it can be rebuilt from admitted rows
only. Final hydraulic residual remains blocked because there are no fit-admitted
raw pressure/F6 rows that separate straight friction, component K,
reset/development, cluster/branch-apparent loss, and recirculation/onset terms.

To continue progress:

1. Use current PM5 rows for pressure/onset and section-effective diagnostics.
2. Resolve thermal sign/heat-balance before Nu fitting.
3. Obtain non-recirculating or near-transition matched-plane/pressure rows, or
   define a separate bidirectional/section-effective closure path.
4. Rebuild final forward-v1 only after admission gates, not from diagnostic rows.

## Validation

- `python3.11 -m unittest tools.analyze.test_f6_internal_nu_admission_review_and_forward_unblock`
- `python3.11 -m py_compile tools/analyze/build_f6_internal_nu_admission_review_and_forward_unblock.py tools/analyze/test_f6_internal_nu_admission_review_and_forward_unblock.py`
- `python3.11 tools/analyze/build_f6_internal_nu_admission_review_and_forward_unblock.py`

No native CFD solver outputs, scheduler state, registry/admission state,
generated indexes, or external Fluid files were mutated.
