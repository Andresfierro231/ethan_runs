---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit
  - operational_notes/07-26/17/2026-07-17_WEEKEND_NEXT_MODEL_HANDOFF_PLAN.md
  - work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/coupled_delta_vs_m3.csv
tags: [forward-model, wall-test-section, tp-tw, failure-forensics, physics-requirements]
related:
  - .agent/status/2026-07-18_AGENT-536.md
  - .agent/journal/2026-07-18/tp-tw-failure-forensics.md
  - imports/2026-07-18_tp_tw_failure_forensics.json
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-536
date: 2026-07-18
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# TP/TW Failure Forensics

## Result

Decision for `predictive-wall-test-section-submodels`: `contract_first_no_grid`.

The package turns the wall/test-section failure evidence into a physics
requirement matrix before another Fluid grid is launched. It performs no
solver, scheduler, Fluid, fitting, tuning, registry, or scientific-admission
action.

## Counts

- Sensor failure rows: `15`.
- Role/segment failure rows: `10`.
- Candidate family gate rows: `10`.
- Physics requirements: `5`.
- Next-model contract rows: `4`.
- Admitted candidate families: `0`.

## Interpretation

The dominant scoreable failures are thermal-shape failures, not sensor-policy
artifacts. TP2 and TW10 remain policy/extraction exclusions, but TW5/TW6 and
heated-incline role RMSE are scoreable failures that persist across passive
wall redistribution, wall-temperature drive, wall-circuit, heater-source
redistribution, and the AGENT-526 single-node wall/fluid series fallback.

The next Fluid work should start with the `UMX1` static API/root/scenario
contract. A full grid is blocked until that contract shows accepted roots,
runtime legality, split discipline, and no mdot-only admission path. `TSWFC2`
distributed wall/fluid nodes are secondary and must not duplicate AGENT-526's
single bulk-to-ambient series-resistance model.

## Files

- `sensor_failure_rank.csv`
- `role_segment_failure_rank.csv`
- `candidate_family_gate_matrix.csv`
- `physics_requirement_matrix.csv`
- `next_model_contract.csv`
- `runtime_request_audit.csv`
- `source_manifest.csv`
- `summary.json`
