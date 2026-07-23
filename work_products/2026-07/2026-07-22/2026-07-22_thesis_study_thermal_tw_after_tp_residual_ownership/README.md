---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate/tp_same_qoi_projection_uq.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf15_runtime_wall_profile_basis_gate/wall_profile_release_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf17_same_qoi_wall_core_exchange_uq_execution/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate/tp_tw_residual_separation.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d3_wall_shape_axial_mixing_gate/candidate_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d4_segment_source_placement_evidence_gate/source_bounded_candidate_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight/field_release_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_thermal_accounting_traceability_evidence_packet/thermal_accounting_traceability_ledger.csv
tags: [thermal, tp-tw, residual-ownership, heat-loss, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-THESIS-STUDY-THERMAL-TW-AFTER-TP-RESIDUAL-OWNERSHIP-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-study-thermal-tw-after-tp-residual-ownership.md
  - imports/2026-07-22_thesis_study_thermal_tw_after_tp_residual_ownership.json
task: TODO-THESIS-STUDY-THERMAL-TW-AFTER-TP-RESIDUAL-OWNERSHIP-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Sensor-map / Forward-pred / Writer / Reviewer / Tester
type: work_product
status: complete
---
# Thermal TW-After-TP Residual Ownership Study

Decision: `fail_closed_no_single_runtime_legal_tw_after_tp_owner`.

This study separates the bulk-to-TP projection problem from the remaining TW
thermal residual. The observed evidence supports several physical mechanisms:
wall/core exchange shape, axial mixing, source placement, passive boundary
loss, and sensor/QoI projection uncertainty. None is currently a runtime-legal
single owner, because source/property release, runtime temperature release,
same-QOI production/UQ, and independent coefficient/source-bounded gates do not
all pass.

## Key Results

- D2 TP projection reduces transfer TP RMSE from `13.5673279702 K` to
  `4.38159298515 K`.
- D2 leaves transfer TW RMSE at `12.5130610954 K`, so TW-after-TP residual is a
  remaining owner problem rather than solved bulk projection alone.
- MF15 wall/profile release-ready rows are `0`.
- MF17 executes temporal same-QOI UQ for 4 QOI labels, but releases no Qwall,
  production harvest, mesh/GCI result, source/property fields, or coefficient.
- MF13/source-property release rows are `0`; `cp_J_kg_K` remains unreleased.
- N4 runtime temperature allowed rows are `0` for TP and TW sensors.
- S12 candidate-reviewable rows are `0`, validation/holdout/external scored
  rows are `0`, and final score values are `0`.

## Package Files

- `tw_after_tp_residual_owner_table.csv`
- `tp_subtracted_tw_residual_evidence.csv`
- `source_property_runtime_audit.csv`
- `same_qoi_uq_status.csv`
- `s11_s12_s15_consequence_table.csv`
- `figure_table_targets.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
- `figures/svg/tw_after_tp_owner_gate_waterfall.svg`

## Interpretation

After the TP projection is separated, the remaining TW residual should be
treated as a named unresolved residual with candidate owners. The strongest
current candidates are wall/core exchange and axial mixing, followed by
source-placement and passive-boundary explanations. They are scientifically
useful for thesis discussion and next-run design. They are not admissible as
runtime closures today.

The heat-loss accounting guardrail remains active: missing heat residual is not
assigned to internal Nu. Internal Nu is the salt-side internal convection lane.
Wall conduction, insulation/quartz, external convection, radiation,
jacket/cooler, source/sink, storage, wall/core exchange, sensor projection, and
residual ownership stay separated until a setup-known source/property and
same-QOI uncertainty gate admits a candidate.

## Next Gate

The next rigorous unlock is not another residual fit. It is a source/property
and same-QOI production gate that can prove one candidate owner independently:

- release row-specific `cp_J_kg_K`, viscosity/property mode, setup-known
  source/sink ownership, and pressure/heat-path labels;
- finish S13 same-label medium/fine sampler repair and post-sampler mesh/GCI;
- decide whether Qwall/exchange/wall-core QOIs can be production harvested;
- only then evaluate S11/S12/S15/S6 consequences.

## Validation

`python3.11 work_products/2026-07/2026-07-22/2026-07-22_thesis_study_thermal_tw_after_tp_residual_ownership/check_thermal_tw_after_tp_packet.py` passes with:

`PASS thermal TW-after-TP packet: 6 residual rows, 9 owner rows, D2_TP_RMSE=4.38159 K, D2_TW_RMSE=12.5131 K`.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state,
Fluid/external repository, thesis LaTeX/body file, blocker register,
source/property release, Qwall release, coefficient admission, protected score,
or final score was changed. No validation temperatures, realized `wallHeatFlux`,
CFD `mdot`, imposed cooler duty, or residual-fitted multiplier was used as a
runtime input.
