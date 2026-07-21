# Pressure Decomposition Buoyancy Sign Audit

Date: 2026-07-09  
Task: AGENT-230  
Role: Coordinator / Implementer / Writer  
Owner: codex

## Trigger

The user challenged the explanation of the pressure-decomposition chart,
specifically the lower-leg/heater density-gradient buoyancy sign. The user was
right that the heater should lower density along actual flow, and asked whether
the figure ignored height effects or contained a real mistake.

## Findings

- The lower-leg source stations show density increasing in station order, but
  the lower-leg flow direction is opposite station order (`flow_orientation_sigma
  = -1`). Therefore density decreases along actual flow, consistent with heating.
- The existing summary chart used `buoyancy_contribution_pa` directly. That is
  station-order bookkeeping from the pressure ledger, not the along-flow signed
  density-gradient term a slide reader expects.
- The pressure ledger already contains the flow-projected quantity
  `gh_drho_dxi_pa_m`. The chart should use `gh_drho_dxi_pa_m * L_m`.

## Correction

Updated `tools/analyze/build_postprocessor_summary_charts.py`:

- `density_gradient_buoyancy_pa = gh_drho_dxi_pa_m * L_m`
- retained old value as `station_order_buoyancy_pa`
- added `density_gradient_buoyancy_basis = flow_projected_gh_drho_dxi_times_L`
- updated figure subtitle to state that the density-gradient term is flow-projected
- updated moved `work_products/YYYY-MM/YYYY-MM-DD/...` input paths so the builder
  is reproducible after the July 8 cleanup

Regenerated:

- `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/**`

Added presentation note:

- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/pressure_decomposition_buoyancy_sign_audit.md`

Updated:

- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/slide_outline_with_speaker_notes.md`

## Corrected Values

For lower/upper legs after regeneration:

```text
Salt 2 lower_leg: density_gradient_buoyancy_pa = -5.218 Pa
Salt 2 upper_leg: density_gradient_buoyancy_pa = -39.274 Pa
Salt 3 lower_leg: density_gradient_buoyancy_pa = -5.437 Pa
Salt 3 upper_leg: density_gradient_buoyancy_pa = -38.022 Pa
Salt 4 lower_leg: density_gradient_buoyancy_pa = -5.238 Pa
Salt 4 upper_leg: density_gradient_buoyancy_pa = -36.448 Pa
```

The old station-order lower-leg values are retained in the summary table as
positive `station_order_buoyancy_pa` for traceability only.

## Validation Commands

```bash
python3.11 tools/analyze/build_postprocessor_summary_charts.py --output-dir work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts
python3.11 -m py_compile tools/analyze/build_postprocessor_summary_charts.py
python3.11 -c 'import json; json.load(open("imports/2026-07-09_pressure_decomposition_buoyancy_sign_audit.json")); print("json ok")'
git diff --check -- tools/analyze/build_postprocessor_summary_charts.py work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/slide_outline_with_speaker_notes.md work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/pressure_decomposition_buoyancy_sign_audit.md imports/2026-07-09_pressure_decomposition_buoyancy_sign_audit.json .agent/status/2026-07-09_AGENT-230.md .agent/journal/2026-07-09/pressure-decomposition-buoyancy-sign-audit.md
```

## Boundary

No native OpenFOAM outputs, external solver code, or source pressure ledger rows
were modified.
