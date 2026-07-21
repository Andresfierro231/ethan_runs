---
date: 2026-07-14
task: AGENT-374
tags:
  - forward-model
  - forward-v1
  - overnight
  - handoff
  - compute-node
status: complete
related:
  - work_products/2026-07/2026-07-14/2026-07-14_tomorrow_forward_v1_full_context_and_overnight_plan/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_forward_v1_gate_refresh_after_fluid_api_and_audits/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_forward_v1_blocker_documentation_audit/README.md
---
# Tomorrow Forward-v1 Full Context And Overnight Plan

## Workspace

```bash
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
```

This note is the 2026-07-14 evening start-here for continuing forward-v1
tomorrow. It consolidates the forward-pred, hydraulics, cfd-pp, boundary/HX,
heater/source, blocker-documentation, and overnight-compute state.

## Current Compute / Scheduler Snapshot

Observed from current node `c318-008.ls6.tacc.utexas.edu`:

- Interactive/dev allocation: `3295120` `idv75667`, running on `c318-008`.
- Corrected-Q continuation: `3293924` `saltq_sel_cont`, running on `c318-016`.
- Dependent selected Salt2/Salt4 +/-10Q harvester: `3295438`, pending on
  dependency.
- Nominal upcomer matched-plane extraction: `3295492`, completed `0:0`.
- PM5 matched pressure/upcomer job: `3295901`, cancelled before running.

Do not rely on older notes that say `3295901` is merely pending. Current
accounting says it was `CANCELLED by 890970` with `Elapsed=00:00:00`.

## What We Finished

Forward-v1 gate and scorecard readiness:

- AGENT-362 integrated +/-5Q corrected-Q terminal-harvest evidence and hydraulic
  tap-length refresh.
- AGENT-366 refreshed the forward-v1 gate after Fluid reset/development API,
  mdot/temperature audit, Salt1 BC conflict resolution, and the +/-5Q/hydraulic
  delta.
- AGENT-371 audited blocker documentation sufficiency. All 7 forward-v1
  blockers have primary docs, supporting evidence chains, proof numbers,
  plain-language why-blocked explanations, and next unblock artifacts.

Hydraulics:

- AGENT-361 implemented `MinorLosses.reset_development_k_by_segment` in external
  Fluid.
- API support is real, but H1 remains not launchable because admitted
  reset/development pressure evidence and fit-admissible component/cluster K rows
  are still missing.
- AGENT-349 resolved 12 hydraulic tap-length rows with mesh-centerline evidence;
  3 connector rows still need raw two-tap extraction.

Boundary/HX/thermal:

- AGENT-365 produced the external-BC/source-contract and thermal-profile parity
  package for Salt2-4.
- AGENT-370 produced the heater/source-contract screen. Heater-only is the next
  unfitted source contract; Salt2-only `eta_heater=0.989703` improves held-out
  Tmean MAE to `3.199 K`, but does not admit final forward-v1 because setup-only
  cooler/HX and hydraulic gates remain blocked.

CFD admission/split:

- AGENT-369 documented Salt training/testing evidence changes.
- Salt1 hi10q conflict is resolved for perturbed-Q training use.
- Salt4 nominal and Salt4 +/-5Q are training evidence under the latest cfd-pp
  rollup; Salt2 +/-5Q are holdout/testing evidence.
- Do not silently treat Q perturbations as independent nominal baselines.

## Current Final Forward-v1 State

Final forward-v1 remains:

`blocked_no_go_final_forward_v1_not_admitted`

Current split for the final scorecard remains:

`salt_2=train; salt_3=validation; salt_4=holdout`

Do not change the split after looking at validation/holdout residuals unless a
new dated split policy supersedes it.

## Why It Is Still Blocked

Open AGENT-371 first for the detailed evidence chain:

`work_products/2026-07/2026-07-14/2026-07-14_forward_v1_blocker_documentation_audit/blocker_reading_guide.md`

Short version:

- Fluid reset/development API exists, but pressure evidence is not admitted.
- H1/F6 hydraulic closure is blocked by zero fit-admissible K rows and missing
  admitted Re-variation pressure rows.
- PM5 matched pressure/upcomer metrics are absent because `3295901` was
  cancelled before running.
- +/-5Q rows cannot expand training rows without a dated perturbation split
  policy.
- Internal-Nu fitting remains blocked; diagnostic upcomer Nu is validation-only.
- Boundary/HX still lacks setup-only outputs replacing imposed cooler duty.
- Sensor residuals are post-solve targets only; complete sensor scoring needs
  exclusion/coordinate policy.

## Open First Tomorrow

1. `work_products/2026-07/2026-07-14/2026-07-14_tomorrow_forward_v1_full_context_and_overnight_plan/README.md`
2. `work_products/2026-07/2026-07-14/2026-07-14_tomorrow_forward_v1_full_context_and_overnight_plan/tomorrow_progress_context_table.csv`
3. `work_products/2026-07/2026-07-14/2026-07-14_tomorrow_forward_v1_full_context_and_overnight_plan/overnight_study_recommendations.csv`
4. `work_products/2026-07/2026-07-14/2026-07-14_forward_v1_gate_refresh_after_fluid_api_and_audits/README.md`
5. `work_products/2026-07/2026-07-14/2026-07-14_forward_v1_blocker_documentation_audit/README.md`
6. `operational_notes/07-26/14/2026-07-14_SALT_TRAINING_TESTING_EVIDENCE_ROLLOUT.md`
7. `operational_notes/07-26/14/2026-07-14_TOMORROW_THERMAL_PARITY_AND_OVERNIGHT_STUDY_HANDOFF.md`
8. `operational_notes/07-26/14/2026-07-14_TOMORROW_HYDRAULICS_AND_OVERNIGHT_COMPUTE_HANDOFF.md`
9. `.agent/BOARD.md`
10. `.agent/BLOCKERS.md`

## Recommended Overnight Studies

Use the current compute node for lightweight 1D/repo-local analyses. Do not
launch heavy OpenFOAM or mutate native CFD outputs from this handoff.

Highest value:

1. **External-boundary Fluid table rerun**
   - Compare bulk-drive, wall-shell-drive, and one Salt2-trained mixed-drive
     factor.
   - Source inputs: AGENT-365 external-BC segment equivalents and thermal-profile
     tables.
   - Score Salt2 train / Salt3 validation / Salt4 holdout.
   - Keep diagnostic until setup-only runtime guardrails pass.

2. **Setup-only cooler/HX replacement screen**
   - Replace imposed cooler duty with a setup-only UA or epsilon-NTU candidate.
   - Score against heat residuals without using realized CFD `wallHeatFlux` or
     CFD cooler duty as runtime inputs.
   - This is the biggest remaining thermal shortcut.

3. **Sensor-map policy refresh**
   - Convert AGENT-360 sensor residual evidence into an explicit exclusion /
     coordinate-upgrade policy.
   - Lightweight and useful for final scorecard readiness.

4. **Corrected-Q terminal watcher/harvest**
   - Only after `3293924` reaches terminal state.
   - Let or inspect dependency job `3295438`.
   - Do not submit duplicate corrected-Q solver jobs.

5. **PM5 matched pressure/upcomer relaunch decision**
   - First diagnose why `3295901` was cancelled.
   - Relaunch only under a new board row if cancellation was administrative.
   - Needed for F6/onset and internal-Nu reopen evidence.

Already active or claimed:

- AGENT-373 has claimed a hydraulics overnight dependent chain after `3295120`;
  do not duplicate it.
- AGENT-372 is documenting the mdot/temperature audit handoff; do not overwrite
  that package.

## Do Not Do Overnight

- Do not mutate native CFD solver outputs.
- Do not run heavy OpenFOAM on the login node.
- Do not duplicate `3293924`, `3295438`, or the AGENT-373 hydraulics chain.
- Do not call diagnostic Fluid reset-K sweeps H1 admission.
- Do not call imposed cooler duty final predictive HX.
- Do not use realized CFD `wallHeatFlux`, CFD mdot, or validation/holdout
  temperatures as runtime inputs.
- Do not fit internal Nu from recirculating diagnostic upcomer rows.
- Do not reopen stale blockers: OF13 reconstruction works, mesh families exist,
  and CFD `rcExternalTemperature` includes radiation.

## Tomorrow Pickup Order

1. Check `.agent/BOARD.md` for active rows first.
2. Check scheduler state for `3293924`, `3295438`, `3295492`, `3295901`, and any
   AGENT-373 submitted jobs.
3. If `3293924` is terminal, process corrected-Q harvest/admission before
   changing split policy.
4. If staying in forward-pred, start from AGENT-366 and AGENT-371 packages.
5. If staying in thermal/boundary, run the external-boundary Fluid table rerun
   or setup-only cooler/HX screen.
6. If staying in hydraulics, consume AGENT-373 outputs and any admitted
   pressure evidence before attempting F6/H1 scoring.
