# Coordinator Daily Analysis Rollup And Presentation Agent Prompt

Date: `2026-07-08`
Task: `AGENT-212`
Role: Coordinator / Writer

## Purpose

This journal consolidates today's CFD/1D closure-analysis state for
coordination, tomorrow's presentation update, and thesis/journal planning. It is
based on the July 8 board rows, status files, journals, and dated work-product
READMEs available during inspection. It does not create new physics evidence.

## Files Inspected

- `.agent/BOARD.md`
- `.agent/status/2026-07-08_AGENT-202.md`
- `.agent/status/2026-07-08_AGENT-203.md`
- `.agent/status/2026-07-08_AGENT-204.md`
- `.agent/status/2026-07-08_AGENT-205.md`
- `.agent/status/2026-07-08_AGENT-206.md`
- `.agent/status/2026-07-08_AGENT-207.md`
- `.agent/status/2026-07-08_AGENT-208.md`
- `.agent/status/2026-07-08_AGENT-209.md`
- `.agent/status/2026-07-08_AGENT-210.md`
- `.agent/status/2026-07-08_TODO-OBSERVATION-TABLE-CONTRACT.md`
- `.agent/status/2026-07-08_TODO-PRESSURE-TERM-LEDGER.md`
- `.agent/status/2026-07-08_TODO-PATCHWISE-HEAT-LEDGER.md`
- `.agent/status/2026-07-08_TODO-POSTPROCESSOR-CHARTS.md`
- `.agent/status/2026-07-08_TODO-MINOR-LOSS-TWO-TAP.md`
- `.agent/status/2026-07-08_TODO-MODEL-FORM-BAKEOFF.md`
- `.agent/status/2026-07-08_TODO-UPCOMER-ONSET.md`
- `work_products/2026-07-08_postprocessor_summary_charts/README.md`
- `work_products/2026-07-08_postprocessor_summary_charts/presentation_story.md`
- selected July 8 work-product READMEs for pressure, heat, observations,
  minor loss, model bakeoff, upcomer onset, thermal boundary, and thermal
  mismatch.

No `.agent/status/2026-07-08_TODO-MESH-UNCERTAINTY.md` file was present during
inspection. No `.agent/status/2026-07-08_AGENT-211.md` file was present during
inspection, although `AGENT-211` was active on the board.

## Today's Analysis State

### Evidence Contracts And Admission

- `AGENT-202` built the July 8 CFD scenario contract and observation seed.
  Observed facts: the audited Salt CFD case roots have a `0.03556 m` wall or
  insulation layer, equal to `1.4 in`; prior `0.25/0.30 in` values are 1D
  temperature-matching sweep settings, not the CFD insulation. The CFD cases
  contain `rcExternalTemperature` with emissivity metadata, but no
  `constant/radiationProperties`, `qr`, or `G` volume radiation field. Salt 1
  evidence has window/version caveats, while Salt 2/3/4 Jin are the mainline
  admitted rows for the current ledgers.
- `TODO-OBSERVATION-TABLE-CONTRACT` completed a canonical observation table in
  `work_products/2026-07-08_closure_observation_table/**`. Observed facts:
  `423` Salt 2/3/4 rows, `342` pressure rows, `81` thermal rows, `45`
  fit-eligible rows, and all rows validation-eligible. Salt 1 and corrected-Q
  rows remain excluded from the fitting set.

Interpretation: the work is now organized around an admission contract, not
loose case-by-case interpretation. This is the right foundation for journal
claims, but it does not remove mesh/GCI and gate caveats.

### Pressure Decomposition

- `TODO-PRESSURE-TERM-LEDGER` completed
  `work_products/2026-07-08_pressure_term_ledger/**`. Observed facts: `18`
  Salt 2/3/4 span rows, `12` fit-eligible rows, and `6` recirculation-excluded
  rows. The ledger explicitly reports endpoint `p_rgh`, dynamic-head change,
  total-pressure proxy, density-gradient buoyancy, distributed loss,
  development/reset contribution, minor-loss upper-bound, recirculation flags,
  fit eligibility, and residual.
- This is 3D CFD postprocessing evidence. It is not a 1D solver result.

Interpretation: this is the main challenge to raw static-pressure claims. The
presentation should show that gross `p_rgh` changes are not being equated with
pipe friction; the ledger separates buoyancy, mechanical losses, feature losses,
development/reset terms, and residuals.

### Heat Accounting And Thermal State

- `AGENT-203` extracted span endpoint bulk temperatures. Observed facts:
  heater delta-T for Salt 2/3/4 is about `+15.35/+15.79/+16.44 K`; heater
  energy balance is within about `8.5%`; cooler endpoint coverage is partial;
  upcomer recirculation is high enough that mixing-cup quantities are
  diagnostic rather than ordinary pipe-flow closure values.
- `TODO-PATCHWISE-HEAT-LEDGER` completed
  `work_products/2026-07-08_patchwise_heat_ledger/**`. Observed facts: `24`
  rows with imposed heater/cooler duties, wallHeatFlux, enthalpy-flow changes,
  BC signs, wall/conduction/external-convection diagnostics, and explicit no
  `qr` caveat. Cooler imposed duty matches wallHeatFlux closely; heater imposed
  duty exceeds heater wallHeatFlux; the test section has imposed positive heat
  source but net wall-flux sink in the Salt 2/3/4 ledger.
- `AGENT-207` added `heat_enthalpy_residual_by_segment.svg` to
  `work_products/2026-07-08_postprocessor_summary_charts/**`. Non-junction
  absolute heat residuals span about `36.7 W` to `162.7 W`.
- `AGENT-208` built the thermal boundary contract in
  `work_products/2026-07-08_thermal_boundary_contract/**`. Observed facts: the
  prior 1D state is about `61.950-66.201 K` hotter than CFD and has a loop
  delta-T about `3.722-3.908 K` smaller.
- `AGENT-209` built
  `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/**`. Observed
  facts: the current prior 1D comparison removes only about `46-54 W` through
  the cooler, while the CFD cooler wallHeatFlux removes about `136-169 W`.
  Prescribing CFD cooler duty at fixed mdot reduces Salt 2/3/4 mean-temperature
  errors to `6.219`, `4.453`, and `2.697 K`.
- This lane bridges 3D CFD postprocessing and 1D thermal replay. The ledgers are
  3D evidence; the replay/remedy scoring is 1D diagnostic work.

Interpretation: the 1D thermal mismatch is not primarily solved by retuning a
friction closure. The current best-supported near-term remedy is to correct the
cooler/HX heat-removal path, then rerun hydraulic closure scoring with thermal
state separated from pressure-distribution scoring.

### Friction, Model Forms, And 1D Predictivity

- `AGENT-195` remains the key existing friction-form evidence used by the chart
  package. Observed facts in the July 8 chart package: F1 mdot errors are
  positive across Salt 2/3/4 (`9.7%` to `18.0%`), while F3 Shah apparent narrows
  the range to about `-0.9%` to `3.7%`; F4 leg-class is negative across Salt
  2/3/4 (`-24.7%` to `-23.2%`), consistent with over-stiffening.
- `AGENT-200` is the current F5/Ri screen. Observed facts: the admitted
  three-point dataset does not support active Ri multipliers; coefficients are
  zero/deactivated and F5 is effectively degenerate with F3 for the current
  admitted rows.
- `TODO-MODEL-FORM-BAKEOFF` completed a starter package in
  `work_products/2026-07-08_model_form_bakeoff/**`. Observed facts: it consumes
  `423` observation rows and emits `15` model/case score rows; best current mdot
  form is `F3_shah_apparent` with mean absolute mdot error `2.669%`. It is a
  starter bakeoff from existing outputs, not a fresh Fluid rerun.
- `AGENT-210` implemented F6 phi-vs-Re and self-consistent per-segment Ri in the
  external Fluid model. Observed facts from the status file: F6 is implemented
  and tested; corner bends explain only `8-12%` of span-level pressure drop for
  heater/cooler/downcomer; residual pipe-only phi remains about `1.34-1.90`
  after corner attribution. This means dominant excess is not from corner K
  values alone.
- This is mostly 1D model-form work, with CFD ledger outputs serving as
  validation/fit targets.

Interpretation: F3 remains the strongest present mdot baseline, but model-form
selection should be scored on separate axes: mdot, pressure distribution,
thermal state, recirculation validity, and residual. A single tuned friction
factor would hide the wrong physics.

### Minor Losses And Feature Terms

- `TODO-MINOR-LOSS-TWO-TAP` completed
  `work_products/2026-07-08_minor_loss_two_tap/**`. Observed facts: `15` rows,
  including `12` computed preserved corner rows and `3` test-section connector
  rows flagged as requiring raw extraction. Diagnostic `K_apparent` spans about
  `6.2247-16.5038`; corrected/local `K_local` after minimum adjacent
  straight-loss subtraction spans about `1.0661-8.7476`.
- This is 3D postprocessing evidence derived from preserved feature endpoints
  and the pressure ledger, not a 1D solver fit.

Interpretation: legacy bend/minor-loss values should be treated as apparent
upper bounds. The next closure-grade step is raw two-tap extraction with explicit
tap-to-tap lengths for bends, reducers, junctions, and the test-section complex.

### Upcomer Regime

- `AGENT-196` and `TODO-UPCOMER-ONSET` provide the current upcomer evidence.
  The July 8 starter package lives at
  `work_products/2026-07-08_upcomer_onset/**`. Observed facts: `3` admitted
  Salt 2/3/4 rows; all classify as `recirculation_cell_observed`; backflow
  fraction decreases with Re but remains nonzero at Salt 4. The July 8 chart
  package reports backflow fraction decreasing from about `27.8%` to `17.2%`.
- This is 3D CFD regime evidence and an exclusion/admission rule for 1D fits.

Interpretation: the upcomer should be presented as a recirculation-cell regime,
not a single-stream pipe-friction span. It should be validation-only or modeled
with a separate regime equation until onset is bounded by more operating points.

### Run Status, Gate Status, And Corrected Salt

- `AGENT-205` documented the CFD/1D geometry and BC contract plus current run
  plan. Observed facts: corrected Salt gate job status was tracked and Salt 1
  normal/base-continuation provenance was clarified.
- `AGENT-206` staged and submitted Salt 1 nominal continuation job `3282992`
  (`salt1_nom_cont`), pending priority at initial check.
- `TODO-POSTPROCESSOR-CHARTS` includes
  `corrected_salt_gate_status.svg` as status-only evidence. Corrected Salt rows
  are not closure-fit rows until formal gate requalification.

Interpretation: use corrected Salt only for tomorrow's "what is moving" slide,
not as closure evidence.

### Mesh And Time-Window Uncertainty

- `TODO-MESH-UNCERTAINTY` remains open on the board. No July 8 status file was
  present during inspection.
- Time-window uncertainty is specified in the July 7 coordinator/deep-dive
  notes but does not yet appear as a completed July 8 package.

Interpretation: these are the main uncertainty lanes still missing before
publication-grade coefficient claims. For tomorrow, use them as explicit caveats
and next work, not as hidden limitations.

## Presentation Update For Tomorrow

### Figures Already Created And Ready To Use

Use the chart package at
`work_products/2026-07-08_postprocessor_summary_charts/**`:

- `figures/pressure_decomposition_by_span.svg`: lead pressure-decomposition
  figure. Message: raw static/`p_rgh` change is not friction; the ledger
  separates buoyancy, distributed mechanical loss, development/reset,
  feature-loss upper bounds, recirculation flags, and residual.
- `figures/heat_source_sink_by_patch_group.svg`: lead heat-accounting figure.
  Message: thermal boundary accounting is first-order; the test section is a
  net sink in wall-flux accounting despite an imposed 1D positive source.
- `figures/heat_enthalpy_residual_by_segment.svg`: segment residual figure.
  Message: span endpoint temperatures expose thermal residuals; cooler and
  upcomer caveats remain important.
- `figures/friction_form_mdot_error.svg`: mdot model-form screen. Message: F3
  Shah apparent currently performs best on mdot, F1 overpredicts, F4 over-stiffens.
- `figures/friction_per_leg_pressure_drop.svg`: optional support figure for why
  F4 suppresses mdot.
- `figures/f5_ri_screen_coefficients.svg`: honesty slide for the failed current
  Ri-multiplier screen.
- `figures/upcomer_backflow_vs_re.svg`: regime slide showing upcomer backflow
  weakens with Re but is not gone.
- `figures/corrected_salt_gate_status.svg`: status-only gate slide, not closure
  evidence.

### Additional Figures Or Tables To Create Today If Time Allows

- Minor-loss two-tap chart from
  `work_products/2026-07-08_minor_loss_two_tap/minor_loss_two_tap.csv`: bar
  chart of `K_apparent` versus `K_local`, with test-section complex rows marked
  as raw-extraction-required.
- Minor-loss separation chart/table from
  `work_products/2026-07-08_minor_loss_separation/**`: show that corner bends
  explain only `8-12%` of span-level pressure drop and that pipe-only residual
  phi remains `1.34-1.90`.
- Thermal mismatch remedy chart from
  `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/**`: show cooler
  duty mismatch and fixed-mdot mean-temperature error reduction when CFD cooler
  duty is prescribed.
- T13 run campaign figure/table from
  `operational_notes/07-26/08/2026-07-08_t13_run_campaign_proposal.md`: show
  planned Q sweep and expected Re range for the missing upcomer/Ri/F6 domain.
- Mesh uncertainty placeholder slide: do not invent GCI. State the minimum
  evidence needed and leave coefficients caveated until the mesh package exists.

### Most Important Findings For Tomorrow

- The project has moved from raw postprocessor plots to term ledgers with
  admission status, provenance, residuals, and caveats.
- Pressure is now decomposed into gross static/`p_rgh`, dynamic/total-pressure
  proxy, buoyancy, distributed loss, development/reset, feature/minor loss,
  recirculation invalidity, and residual.
- The 1D thermal-state mismatch has a strong, quantified cooler/HX component:
  current prior 1D cooler removal is about `46-54 W`, while CFD cooler
  wallHeatFlux is about `136-169 W`.
- Current mdot evidence favors F3 Shah apparent over F1 and F4, but mdot alone
  is not a sufficient closure score.
- F5/Ri cannot be promoted on the current admitted three-point dataset.
- Upcomer evidence supports a separate recirculation-cell regime treatment.
- Minor losses are not yet closure-grade for all features; preserved corner
  values are apparent/upper-bound diagnostics.
- Mesh/GCI and time-window uncertainty remain the main publication-confidence
  gaps.

## Are There Templates Already?

Yes, but they are distributed rather than one standalone master template.

- `.agent/BOARD.md` planned rows are the operative task templates. They define
  role, allowed edit paths, inputs, outputs, and acceptance targets.
- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`
  contains board-ready briefs for pressure ledger, observation table, targeted
  literature forms, minor loss, model bakeoff, upcomer onset, and mesh
  uncertainty.
- `operational_notes/07-26/07/2026-07-07_coordinator_status_and_task_queue.md`
  contains minimum worker prompt requirements.
- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_workflow_docs.md`
  contains the worker handoff contract.
- `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/parallel_agent_prompts.md`
  contains ready helper prompts for thermal/fixed-mdot follow-ups.

The reusable prompt below consolidates those conventions into one launch prompt.

## Can One Agent Confidently And Thoroughly Do All Of This?

Not as one implementation task if "thoroughly" means extracting, validating,
plotting, and interpreting every lane. The requested scope spans 3D CFD
postprocessing, 1D model reruns, uncertainty quantification, literature-to-form
translation, and presentation synthesis. A single senior coordinator can
confidently audit and route the work, and a single agent can do a read-only
presentation rollup. Thorough execution should be split into lanes:

- Pressure/minor-loss ledger and raw two-tap extraction.
- Heat accounting, thermal replay, and cooler/HX model correction.
- Observation contract and common-schema model-form bakeoff.
- Upcomer/regime and targeted literature form translation.
- Time-window and mesh/GCI uncertainty.

That split reduces overlap risk and makes each package reviewable.

## Reusable Prompt For The Next Agent

```text
You are working in /scratch/09748/andresfierro231/projects_scratch/ethan_runs
on 2026-07-08 or later. Follow the repo startup protocol before touching files:
read root AGENTS.md, .agent/BOARD.md, .agent/FILE_OWNERSHIP.md, .agent/ROLES.md,
and any relevant subtree README/TODO/AGENTS.override.md. Identify your role and
task ID. Do not edit unless a board row exists and your allowed edit paths are
explicit. If the row does not exist, remain read-only and ask the coordinator to
open it.

Goal:
Build a rigorous closure-analysis and presentation-update package that advances
these lanes without overclaiming:

1. pressure_term_ledger
   Produce or audit per-segment pressure decomposition with:
   - gross static / p_rgh pressure change
   - dynamic head change and total-pressure proxy
   - hydrostatic / buoyancy contribution
   - distributed major friction
   - entrance/development/reset contribution
   - minor-loss contribution for bends/reducers/junctions
   - recirculation or invalid-single-stream flag
   - residual
   Required boundary: this is 3D CFD postprocessing evidence. Do not report raw
   p_rgh as friction.

2. patchwise_heat_ledger
   Reconcile imposed Q, wallHeatFlux, enthalpy change, cooler sink, passive
   losses, junction/other losses, sign conventions, and radiation/emissivity
   caveats. Distinguish wall-flux accounting from segment enthalpy residuals.

3. time_window_uncertainty
   Tag quasi-steady windows, drift, amplitude, early-stop flags, oscillation
   envelopes, block means, autocorrelation/effective sample size if available,
   and independence groups. Do not promote transient samples to independent
   closure rows without a stated transient model.

4. observation_table_contract
   Maintain one canonical CFD observation schema for 1D model fitting. Every
   row needs source paths, admission status, fit/validation/exclusion status,
   uncertainty fields or placeholders, and the reason for any exclusion.

5. targeted_litrev_forms
   Convert literature lessons into candidate equations/features, not prose.
   For each candidate form list source, variables, nondimensional groups,
   branch applicability, validity range, constants, exclusion criteria, and
   what data would validate or reject it. Do not implement unverified constants.

6. minor_loss_two_tap
   Extract bend/reducer/junction losses with local dynamic-pressure
   normalization. Separate diagnostic K_apparent from corrected/local K. Subtract
   adjacent straight distributed loss where the available evidence supports it.
   Flag recirculation-adjacent rows and rows requiring raw tap extraction.

7. model_form_bakeoff
   Compare closure families before committing to one. Score mdot, pressure
   distribution, thermal-state mismatch, regime validity, and residual as
   separate objective columns. Do not let mdot-only agreement hide thermal or
   pressure-distribution failures.

8. upcomer_onset
   Characterize when the upcomer becomes a recirculation-cell problem instead of
   a pipe-friction problem. Report Re/Pr/Gr/Ra/Ri when available, backflow
   fraction, reverse momentum fraction, wrong-sign area, pressure-recovery
   zones, monotonic total-pressure checks, onset uncertainty, and fit-admission
   status.

9. mesh_uncertainty
   Define and, if data are available, compute the minimum mesh evidence needed
   before publication claims. Inventory coarse/medium/fine sources, cell counts,
   BC consistency, latest times, QOI comparisons, and GCI only where defensible.
   Do not fabricate GCI for two-level, non-monotone, or unreadable data.

Presentation deliverables:
- Identify figures already created for tomorrow and exact paths to use.
- Identify figures/tables that can be created today from existing evidence.
- Identify figures that must wait for new extraction, reruns, gate completion,
  or mesh/GCI evidence.
- Provide the three to seven most important findings, each tied to exact files.
- Provide a conservative story for tomorrow and a longer thesis/journal story.

Closeout requirements for every lane:
- observed facts
- inferred interpretation
- blockers / work in progress
- exact files used
- exact files generated or changed
- commands run and tests passed/skipped
- recommended next action
- fit-eligible, validation-only, and excluded row boundaries

Do not mutate native solver outputs. Do not use corrected Salt perturbations as
closure evidence until the gate admits them. Do not claim publication-grade
coefficients without mesh/GCI and time-window uncertainty.
```

## Recommended Next Coordination Actions

- Launch `TODO-MESH-UNCERTAINTY` as a high-priority lane before any paper-grade
  coefficient language is written.
- Launch a bounded `time_window_uncertainty` row if it is not already present,
  using the July 7 quasi-steady schema as the acceptance contract.
- Open a small charting row for the minor-loss and thermal-remedy figures listed
  above if tomorrow's deck needs them.
- Keep `AGENT-211` fixed-mdot results separate from closure-fit evidence until
  its status/journal and generated outputs are available.
- Refresh the presentation from the existing chart package first; only add new
  figures that materially strengthen the pressure/thermal/regime decomposition
  story.
