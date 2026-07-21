---
provenance:
  - reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_todo_campaign_index/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope/source_overlap_flags.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity/property_sensitivity_summary.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/named_pressure_loss_table.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration/heat_closure_admission.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_cfd_validity_diagnostics/coefficient_naming_limits.csv
tags: [journal, litrev-synthesis, heat-loss, radiation, property-sensitivity]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md
  - .agent/status/2026-07-14_AGENT-314.md
  - imports/2026-07-14_boundary_hx_wall_radiation_model_form_decision.json
task: AGENT-314
date: 2026-07-14
role: Coordinator/Writer
type: journal
status: complete
---
# Boundary / HX / Wall-Layer / Radiation Model-Form Decision

## Observed

The July 13 lit-review campaign already contains the necessary gate evidence:
source-envelope flags, property-mode sensitivity, reset/named-loss rows,
heat-loss admission rows, and CFD coefficient naming limits. The requested
`operational_notes/maps/13/2026-07-13_litrev_lessons_and_research_pathways/README.md`
path was not present; the equivalent package is
`reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md`.

## Interpretation

The usable model-form boundary is narrower than the source list. VDI/Reis
heat-path sources are admitted as architecture. Property sources are lanes.
Named-loss and CFD-validity sources are method gates. Chen 2017 and Tian 2024
must not be promoted for current Salt2/3/4 active closure rows. Current CFD
radiation is embedded in `rcExternalTemperature` realized `wallHeatFlux`, so
replay models must not add a separate radiation term on top.

## Output

Created:

- `work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/decision_table.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/source_status.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/summary.json`

Also added a discoverability link to
`operational_notes/maps/literature-synthesis-and-gates.md`.

## Guardrails

- Do not fit friction, K, Nu, UA, HX, or radiation residuals until property
  mode is declared.
- Do not use imposed CFD cooler duty as a predictive runtime input outside
  explicitly labeled imposed-cooler replay.
- Do not double-count radiation in realized-wallHeatFlux replay.
- Do not use repaired/smoke thermal outputs as fit-admitted closure data.

## Validation

CSV/JSON parse check passed. Repository generated index refresh was skipped
because active `AGENT-309` owns generated index files.
