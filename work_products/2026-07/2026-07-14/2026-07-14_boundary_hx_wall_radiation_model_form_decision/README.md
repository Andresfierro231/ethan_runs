---
provenance:
  - reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md
  - reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/research_pathways.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_todo_campaign_index/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope/source_overlap_flags.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity/property_sensitivity_summary.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/named_pressure_loss_table.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration/heat_closure_admission.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_cfd_validity_diagnostics/coefficient_naming_limits.csv
tags: [litrev-synthesis, forward-model, heat-loss, radiation, property-sensitivity]
related:
  - operational_notes/maps/literature-synthesis-and-gates.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-314
date: 2026-07-14
role: Coordinator/Writer
type: work_product
status: complete
---
# Boundary / HX / Wall-Layer / Radiation Model-Form Decision

Purpose: give downstream agents a compact table for choosing what can be used
in the boundary/HX/wall-layer/radiation path without rereading the full
literature packages.

## Files

- `decision_table.csv` is the main acceptance artifact. Columns are:
  `lane`, `source_status`, `source_author_title`, `equation_or_form`,
  `valid_range_or_source_limit`, `tamu_overlap`, `allowed_use`,
  `excluded_use`, and `primary_evidence`.
- `source_status.csv` is a shorter source-to-status index.
- `summary.json` records the package contract and highest-signal decisions.

## Decision Rules

1. Property decisions are a separate lane. Declare the property mode before
   fitting any friction, K, Nu, UA, HX, or radiation residual.
2. Admitted means admitted for a specific role: architecture, method gate,
   diagnostic boundary fact, or property lane. It does not mean calibrated
   closure unless the row says so.
3. Current Chen 2017 low-Re molten-salt mixed-convection Nu is rejected for
   active Salt2/3/4 promotion because audited TAMU rows are outside or unknown.
4. VDI Heat Atlas and Reis solidification/failure evidence are admitted as
   heat-path architecture: jacket/cooler, passive convection, radiation
   metadata, heater input, wall/storage, and residual stay separate.
5. Current CFD `rcExternalTemperature` radiation is embedded in realized
   `wallHeatFlux`; replay modes must not add a separate radiation term on top
   of that realized heat-flux evidence.
6. Named pressure losses can be used as method-gated component/cluster/branch
   diagnostics, but universal `K`, `f_D`, or `Nu` names are rejected wherever
   validity diagnostics mark the span as section-effective or recirculating.

## Property Lane Separation

Use `replication_reis_jadyn` for replication. Use Sohal/Janz, Jin, Parida/Basu,
Santini, Hoffman/Cohen, or Shen-derived property combinations only as declared
reference/sensitivity lanes until a full rerun and gate decision says
otherwise. The property package reports that updated viscosity modes move mean
Re by roughly 1.25-1.30x and Pr/Gz by roughly 0.43-0.61x versus replication in
Salt2/3/4. That is large enough to block friction/thermal fitting before the
lane is explicit.

## Boundary / HX / Radiation Split

Use imposed-cooler replay only when the task explicitly says replay. For
predictive modeling, cooler/HX removal must be modeled separately from passive
external loss, heater realization, wall/storage, and residual. Radiation may be
bounded or represented in a first-class external-boundary model, but current CFD
`wallHeatFlux` already includes `rcExternalTemperature` emissivity/Tsur effects,
so a separate radiation term would double count in realized-wallHeatFlux replay.

## Downstream Use

The next boundary/HX/wall-layer task can consume `decision_table.csv` directly.
It should filter `source_status` rather than relying on citation numbers:
`admitted_*` rows define architecture/gates, `sensitivity_only` rows may run
bounded studies, `reference_only` rows can be reported but not fit, and
`rejected_current_closure` rows must not be promoted for current Salt2/3/4.
