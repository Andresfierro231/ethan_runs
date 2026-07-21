# 2026-07-09 Ethan Runs Journal

This entry is the restart recap requested after the interactive session drop on
July 9. It summarizes the recent multi-agent CFD/1D closure work from this week,
where the previous session left off, and the next actions. It is compiled from
the July 4, July 6, July 7, and July 8 raw agent journals, status files,
operational notes, and work-product READMEs. It does not create new physics
evidence.

## Where We Left Off

The previous interactive allocation ended at `2026-07-09 06:07:17 CDT`
(`3282230`, `idv78867`, Slurm state `CANCELLED+`). The current allocation
started at `2026-07-09 07:28:35 CDT` (`3285548`, `idv43192`), and tmux was
created at `07:29:00 CDT`.

At `2026-07-09 07:34:40 CDT`, the live scheduler state was:

- `3275448` `corr_saltq_g1`: running.
- `3275449` `corr_saltq_g2`: running.
- `3275560` `corr_saltq_salt4_all`: running.
- `3280969` `saltq_gate_after`: pending on dependency.
- `3282992` `salt1_nom_cont`: running.
- `3285548` `idv43192`: current interactive session.

The practical handoff from July 8 was:

1. The presentation package is ready as a decomposed-evidence story:
   `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/**`.
2. Corrected Salt Q perturbations are still status-only until the gate admits
   rows.
3. Salt1 nominal continuation is running but not yet evidence.
4. Do not claim final closure coefficients. The current state supports pressure,
   heat, regime, and model-form decomposition with caveats.

## This Week's Arc

### Corrected Salt Relaunch And Gate Discipline

July 4 established why the historical Salt Q perturbation rows were invalid:
restart fields did not reliably contain the intended Q perturbations, and some
root `0/T` files changed only part of the heater patch group. Those rows are
quarantined as workflow-failure provenance, not closure data.

The corrected workflow staged 14 Salt Q perturbation cases under
`jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/`, patched
both root and restart-time `T` fields, preserved collated `decomposedBlockData`
frames, and required `preflight_patch_audit_<job>.csv` before any result could
be trusted. Current viable corrected-Salt production jobs are `3275448`,
`3275449`, and `3275560`; gate job `3280969` is waiting on them.

Source journals:

- `.agent/journal/2026-07-04/salt-perturbation-quarantine-and-corrected-relaunch.md`
- `.agent/journal/2026-07-06/overnight-postprocess-submissions.md`
- `.agent/journal/2026-07-07/tomorrow-handoff-f4-corrected-salt-postprocessing.md`

Boundary: corrected Salt rows cannot enter closure fitting, ROM fitting, or
model-form validation until the gate marks operating points requalified and any
special-scrutiny row receives coordinator review.

### Workflow And Documentation Alignment

July 6 aligned Claude and Codex output conventions: status files, raw journals,
`work_products/YYYY-MM-DD_slug` naming, import manifests, and report-package
`summary.json` files. This reduced coordination risk for the July 7-8 parallel
agent work.

Source journal:

- `.agent/journal/2026-07-06/coordinator-claude-codex-structure-alignment.md`

### July 7: From Friction Fits To Physical Decomposition

July 7 produced the first broad closure-decomposition wave:

- Pressure term ledger: `work_products/2026-07-07_pressure_term_ledger/**`.
- Heat source/sink ledger: `work_products/2026-07-07_heat_source_sink_ledger/**`.
- Friction-form mdot comparison:
  `work_products/2026-07-07_friction_forms_comparison/**`.
- Upcomer recirculation correlation:
  `work_products/2026-07-07_upcomer_correlation_v2/**`.
- F4/Ri and F5 candidate screens:
  `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/**` and
  `work_products/2026-07-07_f5_ri_corrected/**`.
- Time-window quasi-steady UQ tooling:
  `work_products/2026-07-07_time_window_quasi_steady_uq/**`.

Key findings:

- The mdot gap is not cleanly a scalar friction problem. Applying per-leg CFD
  friction can reverse the mdot error sign.
- `F3_shah_apparent` is the strongest current diagnostic mdot baseline, with
  Salt 2/3/4 errors around `-0.93%`, `+3.33%`, and `+3.75%` in the July 7
  comparison.
- `F4_leg_class` over-stiffens the loop by roughly `23-25%` mdot error.
- `F5_ri_corrected` is framework plumbing and a negative screen for the current
  admitted set: active coefficients are zero, so F5 behaves like F3.
- Upcomer rows are not ordinary single-stream pipe-friction rows. The current
  three-point fit is `bf = 0.0539 + 15.93/Re`, with backflow still nonzero at
  Salt 4.
- The July 7 pressure and heat ledgers were useful but still needed stronger
  admission/schema handling, station/feature refinement, and physical-interface
  thermal residuals.

Source journals:

- `.agent/journal/2026-07-07/coordinator-end-of-day-handoff.md`
- `.agent/journal/2026-07-07/codex-end-of-day-cfd-handoff.md`
- `.agent/journal/2026-07-07/coordinator-writer-end-of-day-handoff.md`

### July 8: Contract, Ledgers, Thermal Diagnosis, Presentation Package

July 8 consolidated the work into a more defensible evidence stack.

CFD and observation contract:

- `work_products/2026-07-08_cfd_scenario_contract/**`
- `work_products/2026-07-08_closure_observation_table/**`

Observed: the audited Salt CFD roots use a `0.03556 m` wall/insulation layer
(`1.4 in`). The `0.25/0.30 in` values are 1D temperature-matching settings, not
the CFD insulation. The audited CFD cases include emissivity metadata but no
separate `constant/radiationProperties`, `qr`, or `G` radiation field. The
canonical observation table seeded `423` Salt 2/3/4 observations.

Pressure and minor-loss ledgers:

- `work_products/2026-07-08_pressure_term_ledger/**`
- `work_products/2026-07-08_minor_loss_two_tap/**`
- `work_products/2026-07/2026-07-08/2026-07-08_hydraulic_closure_rigor_audit/**`

Observed: pressure accounting now separates endpoint `p_rgh`, dynamic/total
pressure proxy, density-gradient buoyancy, distributed mechanical loss,
development/reset, minor-loss upper bounds, recirculation invalidity, fit
eligibility, and residual. Two-tap minor-loss rows report diagnostic
`K_apparent` and corrected/local `K_local`, but test-section connector rows and
some raw tap geometry remain blockers.

Heat and thermal-boundary ledgers:

- `work_products/2026-07-08_patchwise_heat_ledger/**`
- `work_products/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/**`
- `work_products/2026-07-08_span_endpoint_temperatures/**`
- `work_products/2026-07-08_thermal_boundary_contract/**`

Observed: heater imposed duty exceeds heater wallHeatFlux into the fluid, cooler
wallHeatFlux is the relevant CFD sink, the test section can be a net heat sink
in wall-flux accounting, and no separate `qr` radiation term exists in the
current CFD evidence.

Thermal mismatch and fixed-mdot replay:

- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/**`
- `work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs/**`
- `operational_notes/07-26/08/2026-07-08_thermal_interface_power_policy.md`

Observed: prior 1D thermal state is `61.950-66.201 K` hotter than CFD and has
loop Delta T `3.722-3.908 K` too small. Current 1D cooler removes only about
`46-54 W`, while CFD cooler heat removal is about `136-169 W`. The best current
fixed-mdot thermal path is `P1_cfd_cooler_duty_only`, with mean absolute Tmean
error `4.456 K`; no path passes the strict thermal gate.

Model-form and regime context:

- `work_products/2026-07-08_model_form_bakeoff/**`
- `work_products/2026-07-08_upcomer_onset/**`
- `work_products/2026-07-08_minor_loss_separation/**`
- `reference/geometry_reference.md`

Observed: the model-form bakeoff is a starter screen from existing outputs, not
a fresh fully predictive Fluid rerun. F3 remains the strongest current mdot
baseline. F5 remains degenerate. F6 was implemented as a diagnostic/prototype
phi-vs-Re closure, but it is trained on three Salt points and should not be used
as publication-grade evidence. Upcomer remains a recirculation-cell regime in
all admitted Salt rows.

Presentation and closeout:

- `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/**`
- `.agent/journal/2026-07-08/final-user-closeout-and-tomorrow-pickup.md`
- `journals/2026-07/2026-07-08_ethan_runs.md`

The presentation package includes a 12-slide outline with speaker notes, figure
manifest, source inventory, missing/nice-to-have figures, and four support
figures. It is ready for a decomposed-evidence presentation, not a final
closure-law announcement.

## Current Claim Boundaries

Use these boundaries in any presentation or thesis/paper draft:

- Do not claim publication-grade closure coefficients yet.
- Do not use corrected Salt Q perturbations until the gate admits them.
- Do not use Salt1 as closure evidence until the nominal continuation is
  complete and formally qualified.
- Do not describe the fixed-mdot replay as a predictive hydraulic solution; it
  is a thermal-boundary diagnostic.
- Do not treat `F5_ri_corrected` as an improvement; it is currently degenerate
  with F3.
- Do not present F6 as validated beyond a diagnostic/prototype screen.
- Do not promote current minor-loss `K_local` values as final truth until raw
  tap/control-volume issues are resolved.
- Do not infer radiation losses from emissivity metadata. Current CFD evidence
  has no separate `qr` term.
- Do not hide the missing mesh/GCI and time-window uncertainty.

## What To Do Next

Immediate restart steps:

1. Check scheduler state for `3275448`, `3275449`, `3275560`, `3280969`, and
   `3282992`.
2. If the corrected-Salt jobs finish and `3280969` fires, inspect its stdout,
   stderr, and generated gate outputs before admitting any row.
3. Use the July 8 presentation package for the near-term deck:
   `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/slide_outline_with_speaker_notes.md`.

High-priority technical follow-ups already on the board:

- `TODO-THERMAL-OPENFOAM-INTERFACE-SAMPLING`: run bounded compute-node sampling
  to add physical cut planes for paper-grade heat closure.
- `TODO-OBSERVATION-TABLE-THERMAL-REFRESH`: refresh the canonical observation
  table with physical-interface thermal residual status and no-`qr` semantics.
- `TODO-PREDICT-COOLER-REMOVAL`: build a predictive cooler-removal model rather
  than prescribing CFD cooler wallHeatFlux.
- `TODO-PREDICT-HEATER-FLUID-FRACTION`: model what fraction of electrical heater
  power enters the fluid.
- `TODO-1D-RADIATION-CAPABILITY`: add/report 1D radiation separately without
  double-counting CFD wallHeatFlux.
- `TODO-MESH-UNCERTAINTY`: intake readable mesh levels and compute GCI only
  where defensible.
- A time-window UQ/admission refresh remains needed if not already represented
  by a complete board row.

Good order of operations:

1. Gate and scheduler review.
2. Presentation from existing July 8 package.
3. Thermal interface sampling and observation-table refresh.
4. Predictive cooler/heater boundary models.
5. Mesh/GCI and time-window UQ.
6. Only then revisit closure-law coefficients and model-form validation.

## Validation For This Recap

This July 9 entry is documentation-only. It was validated by reading the recent
source journals/statuses and checking current scheduler state. No numerical
scripts, model runs, or tests were executed for this recap task.
