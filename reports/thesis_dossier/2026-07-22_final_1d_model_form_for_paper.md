---
provenance:
  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md
  - reports/thesis_dossier/Chapters_and_sections/current/17_ch5_csem_fluid_walls_model.md
  - reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md
  - reports/thesis_dossier/Chapters_and_sections/current/13_two_tap_recirc_section_effective_pressure_model.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_draft_model_form_admission_thorough_analysis/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_outer_insulation_radiation_runtime_implementation/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_model_form_bakeoff/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_mesh_uncertainty/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_upcomer_onset/summary.json
tags: [thesis-dossier, paper, final-1d-model-form, fluid-walls, no-admission]
related:
  - .agent/status/2026-07-22_TODO-PAPER-FINAL-1D-MODEL-FORM-DOCS.md
  - .agent/journal/2026-07-22/paper-final-1d-model-form-docs.md
task: TODO-PAPER-FINAL-1D-MODEL-FORM-DOCS
date: 2026-07-22
role: Writer / Reviewer / Forward-pred / Thermal-modeling / Hydraulics
type: report
status: complete
---
# Final 1D Model Form For Paper Use

## Position

The current paper-facing 1D model form is a steady `fluid+walls` network. It is
not a fluid-only heat balance, not a transient/storage model, not a single
global pressure multiplier, and not an admitted final predictive closure. The
scientific product is the model architecture and admission discipline: each
branch or local region carries pressure, thermal, source, property,
recirculation, uncertainty, and split-role labels.

The final score state remains blocked: current admitted final candidates are
`0`, final score values are `0`, and source/property release-ready rows are
`0` in the July 22 model-form admission packet.

## Segment State

Each segment record should carry:

| Field | Paper-facing definition | Current status |
| --- | --- | --- |
| Geometry | Length, diameter, area, elevation, orientation, branch and station map. | Architecture ready; exact admission still row-specific. |
| Material stack | Steel, insulation, quartz, connector, junction, or local feature. | Partial/source-backed by heat-loss packets; no broad source/property release. |
| Fluid property lane | Density, viscosity, heat capacity, conductivity, and property-mode label. | Required before freeze; release-ready rows remain `0`. |
| Pressure slot | Straight/developing, local feature, junction/stub, section-effective, recirculation, or residual. | Diagnostic/non-admitted for current corner/F6 rows. |
| Thermal slot | Heater, cooler/HX, passive wall, test section, junction/stub, external radiation/convection, or residual. | Contract-ready in places; wall/test-section closure remains blocked. |
| Recirculation flag | RAF/RMF/topology state that prevents ordinary one-stream labels. | Current upcomer rows are `recirculation_cell_observed`. |
| UQ/admission state | Time/mesh/source/split status tied to the same QOI. | Formal S13 GCI-ready rows remain `0`. |

The test section is the middle upcomer span. It is retained as a physical
bare-quartz/electrically heated segment, not deleted when a diagnostic
temperature ablation improves a score.

## Governing Balances

For a steady segment `i`,

```text
d/ds[mdot cp(T) T] =
    q'_heater_to_fluid,i
  - q'_cooler_removed,i
  - q'_wall_loss,i
  + q'_other_source_to_fluid,i
```

In finite-volume form,

```text
mdot * cp_bar_i * (T_out,i - T_in,i)
  = Q_heater,i
  - Q_cooler,i
  - Q_wall_loss,i
  - Q_junction_stub_loss,i
  + Q_test_section,i
  + Q_residual,i
```

`Q_residual` is an owner lane. It must not be silently absorbed into internal
`Nu`, branch `UA`, friction factor, component `K`, or a hidden multiplier.

For ordinary wall-covered regions,

```text
Q_wall_loss,i =
  (T_drive,i - T_env,i)
  / (R_internal,i + R_wall,i + R_layer,i + R_external,i)
```

Radiation belongs in the external boundary network. The PASSIVE-H2 runtime
contract gives a legal train-only target for the corrected outer-insulation
radiation contribution: `22.4052516482` to `25.6530978934 W`, with the full
passive operator spanning `38.6073163603` to `44.6770586908 W`. That is a
contract for a future Fluid patch; the current external runtime still had
`radiation_on` as a no-op in all three checked train cases.

## Pressure Form

The loop pressure model balances buoyancy drive against distributed and local
loss slots:

```text
Delta_p_drive = integral rho(T,p,property_lane) g dz

Delta_p_loss =
  sum_i [ f_i * (L_i / D_i) * q_i ]
  + sum_j [ K_j * q_j ]
  + Delta_p_junction_stub
  + Delta_p_recirc_section
  + Delta_p_residual
```

The coefficient symbols are placeholders until admitted. Current two-tap
`corner_lower_right` evidence remains diagnostic: component isolation,
reverse-flow, and same-QOI UQ gates do not pass, so component `K`, F6, clipped
K, and global hidden multipliers remain forbidden.

The pressure model direction is therefore section-effective for current
recirculating pressure evidence and ordinary-anchor seeking for future F6.
The July 22 low-reverse anchor design still has `0` replacement-ready rows,
`0` same-QOI UQ-ready rows, and `0` component-K/F6 release rows.

## Upcomer Treatment

The upcomer is not an ordinary single-stream pipe when reverse flow is
material. The current upcomer onset refresh emits `3` Salt train rows, all
classified as `recirculation_cell_observed`; ordinary upcomer pipe admission
rows and exchange-coefficient admission rows are both `0`.

The model-form target is:

```text
net loop throughflow
  + recirculation-cell exchange / mixing / residence-time lane
  + residual-complete open-CV energy balance
```

The July 22 reverse-flow switching design is complete as a design artifact:
`6` switching states, `8` calibration metrics, and `6` activation gates. It
does not fit or admit a switching coefficient.

## Score And Split Discipline

The July 22 model-form bakeoff remains diagnostic. It consumed `1032`
observation rows and emitted `15` case/model score rows across `5` model forms;
the current mdot comparator is `F3_shah_apparent`, but mdot alone is not a
thermal prediction. No validation, holdout, or external-test scoring was newly
executed.

The paper can state:

- the final architecture is ready to describe;
- diagnostic rows explain the missing physics and why residual ownership must
  be explicit;
- the candidate-freeze gate is not passed;
- protected rows remain protected until a separate frozen runtime-legal
  candidate exists.

The paper must not claim:

- final predictive validation;
- admitted source/property release;
- admitted passive wall/test-section closure;
- admitted ordinary upcomer `Nu/f_D/K`;
- admitted component `K` or F6;
- any score that uses held-out or external rows for tuning or model selection.

## Current Next Work

1. Patch the external Fluid runtime under a separate owned row to realize the
   PASSIVE-H2 heat-ledger contract.
2. Derive same-window throughflow enthalpy endpoint masks for the S13 open-CV
   residual path.
3. Wait for the CAND001 pressure endpoint gate before deciding whether any
   ordinary pressure anchor is available.
4. Keep S11/S15 closed until exactly one runtime-legal candidate exists.
