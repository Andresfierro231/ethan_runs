---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/all_streamwise_pressure_1d_map.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state/scientific_review.md
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/patch_role_area_heat_summary.csv
  - work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/val_salt2_section_heat_loss_ledger.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_loop_plot_and_cfd_heat_audit/heat_audit_and_modeling_recommendations.md
tags: [pressure-map, heat-audit, junction-heat-loss, one-d-model]
related:
  - .agent/status/2026-07-16_AGENT-462.md
  - imports/2026-07-16_pressure_loop_plot_and_cfd_heat_audit.json
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_loop_plot_and_cfd_heat_audit/summary.json
task: AGENT-462
date: 2026-07-16
role: Writer/Tester
type: journal
status: complete
supersedes: []
superseded_by:
---

# Pressure Loop Plot And CFD Heat Audit

Created a reusable script, `tools/analyze/build_pressure_loop_plot_and_cfd_heat_audit.py`, to turn the completed station-pressure maps and heat ledgers into a reproducible report package under `work_products/2026-07/2026-07-16/2026-07-16_pressure_loop_plot_and_cfd_heat_audit/`.

The pressure-map plots use AGENT-457 `loop_order_index` and branch labels, so the loop-axis labeling maps to 1D regions: heated incline, lower upcomer, test section, upper upcomer, cooled upper leg, and right downcomer. The plots are diagnostic because the upstream pressure rows remain blocked by orientation, straight-loss subtraction, and recirculation-mask admission.

The heat audit found comparable realized CFD heat accounting for Salt2, Salt3, Salt4 mainline and val_salt2. Salt1 nominal/perturbation cases and Salt2/Salt4 perturbation cases have pressure maps but no comparable heat ledger in the current artifacts, so the output records them as coverage gaps rather than inferring heat trends.

Observed trend: Salt2-4 aggregate junction/stub heat loss rises 39.128 W -> 43.235 W -> 48.485 W as imposed heater power rises 265.7 W -> 297.5 W -> 337.6 W. The loss fraction is nearly flat at 14.7%, 14.5%, and 14.4% of imposed heater power, which makes the junction/stub pathway look structural rather than anomalous. Junction/stub loss is about one third of passive non-cooler loss in the same role table.

Interpretation: the loss is large because `junction_other` is not a single corner. It aggregates 29 exposed connector/stub patches with about 0.04248 m2 of area and mixed `rcExternalTemperature`, `externalTemperature`, and `zeroGradient` boundary roles. The realized `wallHeatFlux` includes the total external heat pathway, including radiation where present. That is sufficient for an aggregate heat audit, but not for fitting four separate junction thermal nodes.

1D-model implication: add explicit localized junction/stub thermal nodes, fit or assign area/resistance/ambient/emissivity/convection parameters per node, couple loss to local fluid temperature, and split future CFD postprocessing by physical junction before calibrating local terms. Runtime prediction should use setup-derived parameters, not realized CFD `wallHeatFlux`.

Validation completed:
- `python3.11 -m unittest tools.analyze.test_pressure_loop_plot_and_cfd_heat_audit`
- `python3.11 tools/analyze/build_pressure_loop_plot_and_cfd_heat_audit.py`
