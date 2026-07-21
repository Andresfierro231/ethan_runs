---
task: AGENT-437
date: 2026-07-15
role: Coordinator/Writer
type: operational_note
status: complete
tags: [tomorrow-start, handoff, scheduler, forward-model, mdot-temperature-audit]
related:
  - .agent/BOARD.md
  - .agent/BLOCKERS.md
  - work_products/2026-07/2026-07-15/2026-07-15_mdot_temperature_error_report_and_presentation/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_recirculation_policy_forward_hydraulic_unblock_plan/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_agent373_hydraulic_chain_node_verification/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_lead_closure_qoi_hydraulic_postprocess/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_downstream_pm5_final_state_refresh/README.md
---
# Tomorrow Start Here

## Purpose

This note preserves the end-of-day state for a new agent on 2026-07-16. It
summarizes what was finished, what is still blocked, what should be done next,
and which overnight sbatch actions are worth considering.

The current theme is no longer "write more summary text." The next useful work
is to turn the documented model-audit findings into executable scorecards and
postprocessing/admission packages while preserving the diagnostic versus
predictive boundary.

## Late Addendum At 2026-07-15T17:42:28-0500

This addendum was added after AGENT-438 completed and after AGENT-439/440 were
claimed. It supersedes only the parts of the lower plan that still say to build
the setup-only HX/cooler scorecard from scratch.

New facts:

- AGENT-438 completed the setup-only HX/cooler scorecard unlock:
  `work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock/`.
- Preferred lane `salt2_fit_constant_UA_bulk_drive` now passes the bounded
  candidate screen: Salt3 validation `2.869 W`, Salt4 holdout `7.503 W`, and
  runtime input violations `0`.
- This advances HX/cooler modeling as a setup-only final-scorecard input, not
  as final forward-v1 admission.
- Final forward-v1 is still blocked by hydraulic/F6 admission,
  internal-Nu/sign/heat-balance, recirculation policy, and mesh/GCI/UQ.
- AGENT-439 is active on the M3+TS / val_salt2 / matched-plane sbatch-submit
  lane. Do not submit duplicate jobs in that lane unless AGENT-439 completes or
  explicitly records failure.
- AGENT-440 is active on staged closure-QOI/pressure postprocessing sbatch. Do
  not submit duplicate closure-QOI/pressure jobs unless AGENT-440 completes or
  explicitly records failure.

Tomorrow's updated first actions:

1. Check active AGENT-439 and AGENT-440 status files/work products before
   launching any overnight postprocessing.
2. Check live jobs `3297384`, `3293924`, and `3295438`.
3. If AGENT-439/440 finished, harvest their job IDs/log paths and parse outputs.
4. If AGENT-439/440 are still active, do not duplicate them; instead work on
   CPU-only documentation/scorecard integration or the segment-equation
   contract.
5. Use AGENT-438 as the current HX/cooler scorecard input in any final
   forward-v1 rebuild.

## Live Scheduler State At Handoff

Checked at `2026-07-15T17:35:42-05:00` and refreshed at
`2026-07-15T17:37:30-05:00` before closeout.

| Job | Name | State | Meaning | Tomorrow action |
| --- | --- | --- | --- | --- |
| `3297384` | `ethan_box_upload` | `R` on `c318-011`, runtime about `4:27:04` at refresh | Existing Box/rclone upload submitted by AGENT-436. | Check `squeue -j 3297384`, then inspect AGENT-436 status/log paths if terminal. Do not submit a duplicate unless it failed and the log explains why. |
| `3293924` | `saltq_sel_cont` | `R` on `c318-016`, runtime about `2-00:33:34` at refresh | Corrected-Q selected continuation still running; all four `foamRun` steps were running. | Check terminal state first. If complete, proceed to dependent harvest/admission processing. |
| `3295438` | `saltq_s24_sel_harv` | `PD (Dependency)` | Corrected-Q Salt2/Salt4 selected harvest waits on dependency. | Do not cancel or duplicate. Once released and complete, harvest outputs into the corrected-Q admission chain. |
| `3295120` | `idv75667` | `R` on `c318-008`, NuclearEnergy-dev | Pre-existing live job outside this handoff's scope. | Do not touch unless the user identifies it as part of tomorrow's work. |

Additional `sacct` facts at closeout:

- `3295492` (`upc_nominal`) completed successfully on `c306-006` in
  `00:03:36` on 2026-07-14. Harvest or parse this completed nominal upcomer
  matched-plane output before launching duplicate nominal matched-plane work.
- `3295901` (`upc_pm5q`) was `CANCELLED by 890970` before running.
- `3295968` (`upc_pm5q`) was also `CANCELLED by 890970` before running.
  Neither cancelled PM5 job produced physics rows.
- `3295989`, `3295990`, and `3295991` (`hyd_stage`) were `CANCELLED by
  890970` before running. Do not wait on this hydraulic dependency chain.
- PM5/hydraulic recovery happened through the July 15 diagnostic packages
  instead: AGENT-404/406/409/421/425. Treat those outputs as diagnostic unless a
  later admission gate promotes a row.

Box upload log paths:

- Slurm stdout: `staging/upload_jobs/slurm-3297384.out`
- Slurm stderr: `staging/upload_jobs/slurm-3297384.err`
- rclone log: `tmp/2026-06-16_ethan_box_upload_probe/rclone_full_upload.log`

At closeout the Box upload stdout showed about `441 GiB / 603 GiB` copied
(`73%`) with retryable rclone errors still present. Let it finish or fail
normally; it is a backup/share task, not a science-admission dependency.

## Completed Work To Reuse

### Mdot versus temperature-probe audit

Open first:

- `work_products/2026-07/2026-07-15/2026-07-15_mdot_temperature_error_report_and_presentation/mdot_temperature_error_report.md`
- `work_products/2026-07/2026-07-15/2026-07-15_mdot_temperature_error_report_and_presentation/presentation_outline.md`
- `work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/report.md`

Key current numbers from AGENT-424:

| Mode | Runtime boundary information | Mean absolute mdot error | All-probe RMSE | Interpretation |
| --- | --- | ---: | ---: | --- |
| M1 | Full CFD segment heat ledger | `35.874%` | `159.168 K` | Diagnostic full-ledger replay, not predictive. Poor pressure/thermal compatibility in current 1D model. |
| M2 | CFD heater + test-section net + cooler | `10.397%` | `26.972 K` | Best current diagnostic balance among pressure-root modes. Uses realized CFD terms and is not final predictive. |
| M3 | CFD heater + cooler only | `16.826%` | `18.023 K` | Improves probe RMSE but worsens mdot. It is an ablation, not permission to delete the test section. |

Important interpretation:

- The current best diagnostic mode is M2 for mdot and M3 for probe RMSE.
- The model needs an explicit setup-only test-section heat-loss term, not a
  hidden deletion of the test section.
- Realized CFD `wallHeatFlux`, imposed cooler duty, realized test-section net
  heat, CFD mdot, and validation/holdout TP/TW temperatures are not allowed as
  final predictive runtime inputs.

### Forward-model decisions from today

Open these before editing forward-model logic:

- `operational_notes/07-26/15/2026-07-15_m3_successor_test_section_heat_loss_requirement.md`
- `operational_notes/07-26/15/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.md`
- `operational_notes/07-26/15/2026-07-15_sensor_and_sophisticated_modeling_decisions.md`
- `operational_notes/07-26/15/2026-07-15_branch_specific_model_forms_and_upcomer_omission_plan.md`

Decisions to preserve:

- The next M3-like model is `M3+TS`: heater + cooler/HX + explicit setup-only
  test-section heat-loss model.
- The loop model must be segment-resolved and thermally coupled. Buoyancy is a
  density/temperature/elevation integral, not a detached scalar.
- Different branches may use different pressure and thermal model forms.
- TP2 should be restored to 1D scoring once finite/projection gates pass. TP2
  remains validation-only and fit/runtime-input disallowed.
- TW10 remains excluded until an active-HX shell/wall state exists.
- Current recirculating upcomer rows are omitted from ordinary single-stream
  `Nu`, `f_D`, and `K` fits. Upcomer proceeds in a separate hybrid/onset lane.

### Recirculation, internal Nu, and hydraulic admission

Open first:

- `work_products/2026-07/2026-07-15/2026-07-15_recirculation_policy_forward_hydraulic_unblock_plan/README.md`
- `work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/README.md`
- `work_products/2026-07/2026-07-15/2026-07-15_agent373_hydraulic_chain_node_verification/README.md`
- `work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/README.md`
- `work_products/2026-07/2026-07-15/2026-07-15_downstream_pm5_final_state_refresh/README.md`
- `work_products/2026-07/2026-07-15/2026-07-15_lead_closure_qoi_hydraulic_postprocess/README.md`

Current status:

- AGENT-421 reran the AGENT-373 stage logic into AGENT-421 scratch:
  raw two-tap preflight `3` rows, F6 gate `4` rows, reset-K sweep `128` rows.
- AGENT-409 landed real staged-copy raw two-tap diagnostics for Salt2/Salt3/
  Salt4 test-section-complex planes. Lower-minus-upper `p_rgh` values were
  Salt2 `16.30560313 Pa`, Salt3 `13.12073641 Pa`, and Salt4 `11.8397775 Pa`.
- PM5 repaired wall-band evidence exists and is useful.
- PM5 rows with wallHeatFlux: `12/12`.
- AGENT-414 refreshed downstream PM5 state: PM5 rows are ready for review but
  not admitted; F6 fit candidates `0`; internal-Nu fit candidates `0`.
- Internal-Nu fit-admissible rows: `0`.
- F6 fit-admissible rows: `0`.
- Final forward-v1 remains `blocked_no_go_final_forward_v1_not_admitted`.
- Final hydraulic residual remains `blocked_not_final`.

Why final hydraulic residual attribution is still blocked:

- Raw two-tap rows are coarse, reduced-pressure/proxy rows with orientation and
  straight-loss/component-subtraction admission still unresolved.
- Reset-K sweep rows are component-separation diagnostics, not final admitted
  `K` fits.
- F6/PM5 rows remain recirculation/onset diagnostics under the current RAF/RMF
  policy.
- No current row jointly passes pressure definition, tap orientation, localized
  loss isolation, recirculation, mesh/GCI, time-window, and source-path gates.

Admission rules that matter tomorrow:

- True single-stream coefficient fitting requires low reverse-flow fractions.
- Default true `Nu`, `f_D`, or component `K` fit admission requires
  `RAF < 0.01` and `RMF < 0.01`, plus sign, pressure, boundary, mesh/GCI, and
  source-path gates.
- Rows with `RAF >= 0.20` or `RMF >= 0.20` are material recirculation rows and
  must be section-effective or diagnostic-only.
- `Nu_section_effective_upcomer_diagnostic` must stay separate from true fit
  Nu.
- CFD `rcExternalTemperature` wall heat flux already includes radiation; do
  not invent a separate exported `qr` term.

## Current Training And Testing Run State

This is the usable split as of the end-of-day coordination pass. Tomorrow's
scorecard agent should freeze the exact split inside its own package, because
older packages use slightly different Salt3/Salt4 validation and holdout roles.

### Training or calibration candidates

| Run or row | Current use | Caveat |
| --- | --- | --- |
| `salt1_nominal` | User-policy thermal training candidate | Salt1 lineage caveats apply; do not use for F6/internal-Nu/upcomer onset fits. |
| `salt1_lo10q` | User-policy thermal training candidate | Perturbed-Q label must remain explicit. |
| `salt1_hi10q` | User-policy thermal training candidate | Perturbed-Q label must remain explicit. |
| `salt2_jin_nominal` | Canonical forward-train row in AGENT-416 lane | Keep separate from validation/test rows. |
| `salt3_jin_nominal` | Training under the newer user-policy split, validation under older split | Freeze split before scoring; do not mix roles inside one scorecard. |
| `salt4_lo5q` | User-policy perturbed-Q thermal training candidate | Closure rows remain diagnostic. |
| `salt4_hi5q` | User-policy perturbed-Q thermal training candidate | Closure rows remain diagnostic. |

### Testing, validation, or holdout candidates

| Run or row | Current use | Caveat |
| --- | --- | --- |
| `salt2_lo5q` | Thermal holdout/testing candidate | Do not tune on it. |
| `salt2_hi5q` | Thermal holdout/testing candidate | Do not tune on it. |
| `val_salt_test_2_coarse_mesh` | External-test or validation candidate, unlocked by AGENT-422 | Do not fit/tune if kept blind; realized wallHeatFlux is diagnostic/scoring evidence, not predictive runtime input. |
| `salt3_jin_nominal` | Validation candidate under older split | Same split-freeze caution as above. |
| `salt4_jin_nominal` | Holdout under older Salt4 holdout policy | Check the scorecard's declared split before consuming. |

### Closest to becoming usable after postprocessing

| Run or row | Status | What unlocks it |
| --- | --- | --- |
| `salt2_lo10q` | Running in corrected-Q selected continuation chain | Terminal `3293924` plus successful `3295438` harvest and admission package. |
| `salt2_hi10q` | Running in corrected-Q selected continuation chain | Terminal `3293924` plus successful `3295438` harvest and admission package. |
| `salt4_lo10q` | Running in corrected-Q selected continuation chain | Terminal `3293924` plus successful `3295438` harvest and admission package. |
| `salt4_hi10q` | Running in corrected-Q selected continuation chain | Terminal `3293924` plus successful `3295438` harvest and admission package. |

### Not usable now

| Run or row | Reason |
| --- | --- |
| Salt3 low-Q corrected perturbation | Stopped or under-advanced; needs continuation/re-gate rather than scorecard consumption. |
| Salt3 high-Q corrected perturbation | Failed; do not use as training/testing evidence. |
| Legacy `hiins` style rows | Diagnostic or historical only unless a later admission package re-admits them. |

## Main Blockers

| Blocker | Current status | Why it blocks | Useful next progress |
| --- | --- | --- | --- |
| `closure-qoi-mesh-gci` | Open high-priority blocker | Closure/QOI and coefficient rows need mesh/GCI/time-window support before final admission. | Build a closure-QOI mesh/GCI readiness matrix from existing PM5/F6/two-tap rows; queue missing triplet extractions only in staged copies. |
| `thermal-cfd-1d-parity` | Open high-priority blocker | Current diagnostic heat-ledger modes reveal pressure/thermal incompatibility; final model cannot consume realized CFD heat fluxes. | Convert M2/M3 findings into setup-only `M3+TS` and HX/cooler scorecards. |
| `predictive-heater-cooler-wall-submodels` | Open high-priority blocker | Heater, cooler/HX, passive wall loss, wall storage, and radiation ownership are not yet admitted setup-only model terms. | Run setup-only model-form sweeps over Salt2 train, Salt3 validation, Salt4 holdout. |
| `upcomer-onset-data-sparsity` | Open medium blocker | Current rows show recirculation, but onset/transition is not calibrated. | Launch targeted onset/postprocessing plan around lower Re or weaker thermal-drive cases, with RAF/RMF/SVF/Ri/Gz metrics. |
| `f6-friction-re-correction` | Open medium blocker | F6/pressure evidence is still diagnostic due to recirculation, pressure definition/orientation, and straight-loss subtraction gates. | Build raw pressure admission package: static pressure definition, tap orientation, straight-loss subtraction, mesh/GCI. |

Do not re-open stale blockers: OF13 reconstruction works, mesh families exist,
and CFD `rcExternalTemperature` includes radiation.

## Tomorrow Execution Plan

### 1. Start with live jobs and harvested evidence

Commands:

```bash
squeue -u andresfierro231
squeue -j 3297384
squeue -j 3293924,3295438
sacct -j 3297384 --format=JobID,JobName%30,State,Elapsed,ExitCode
sacct -j 3293924,3295438 --format=JobID,JobName%30,State,Elapsed,ExitCode
sacct -j 3295492,3295901,3295968,3295989,3295990,3295991 --format=JobID,JobName%30,State,Elapsed,ExitCode
```

If `3293924` and `3295438` are terminal and successful, claim a cfd-pp/admission
row and harvest the corrected-Q outputs into the corrected-Q admission chain.
Do not duplicate the dependency-held harvest while it is pending.

Also inspect completed nominal upcomer job `3295492` before relaunching nominal
matched-plane work. Open:

- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_compute_extraction/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_compute_extraction/scripts/`
- `tools/extract/sample_upcomer_matched_plane_metrics.py`

Expected useful output: a harvest/parse/admission package with exact source
paths, time windows, field presence, reverse area/mass fractions, thermal
fields, wallHeatFlux status, and diagnostic/admission class. Recirculating
rows remain onset/section-effective evidence, not ordinary single-stream
coefficient fits.

### 2. Make the mdot/temperature audit actionable

Claim a new forward-predictive scorecard row. Build a setup-only scorecard that
compares:

- baseline current pressure-root model;
- M2 diagnostic replay, clearly labeled non-predictive;
- M3 diagnostic ablation, clearly labeled non-predictive;
- `M3+TS` candidate with setup-only test-section heat-loss model;
- HX/cooler setup-only variants using only configuration/setup inputs.

Required outputs:

- per-case Salt1/Salt2/Salt3/Salt4 mdot, TP RMSE, TW RMSE, all-probe RMSE,
  mean temperature error, and loop delta-T error;
- train/validation/holdout split labels;
- explicit boundary-condition and closure-term table for each mode;
- appendix copies of compact 1D configuration or exact configuration manifests;
- forbidden-input audit column showing no realized CFD runtime leakage in
  setup-only modes.

### 3. Freeze the segment-resolved model contract

Before writing more model code, claim `TODO-PREDICT-SEGMENT-EQUATION-CONTRACT`
or a replacement row and write the exact equations and data contract for:

- buoyancy/elevation density integral;
- segment-local friction and localized/reset/development losses;
- heater source model;
- cooler/HX removal model;
- test-section heat-loss model;
- passive external boundary loss model;
- sensor output mapping and scoring-only constraints.

This contract should separate predictive runtime inputs, train-only fitted
parameters, validation-only outputs, and diagnostic-only realized CFD quantities.

### 4. Open closure-QOI and hydraulic gates only through admission packages

Do not treat repaired PM5 or staged two-tap outputs as final coefficients.
Instead:

- build a closure-QOI mesh/GCI readiness table for each candidate coefficient
  and QOI;
- create a raw pressure admission package that replaces or converts `p_rgh`
  proxies to an admitted pressure definition;
- enforce upstream/downstream tap orientation;
- subtract straight/distributed loss before computing localized/component K;
- report both diagnostic section-effective labels and true coefficient labels.

### 5. Keep upcomer in the recirculation lane

Do not fit ordinary-pipe `Nu`, `f_D`, or `K` with current recirculating upcomer
rows. The upcomer work should build:

- onset evidence table with RAF/RMF/SVF/Re/Pr/Ri/Ra/Gr/Gz and wall-bulk
  temperature drive;
- a pipe-throughflow plus recirculation-cell model sketch;
- candidate CFD/postprocessing cases to bracket onset.

## Suggested Overnight sbatch Work

These are suggestions, not submissions by this note. Any agent launching them
must claim a scheduler/postprocessing row, avoid mutating native solver outputs,
and document job IDs.

| Priority | Candidate overnight job | Type | Why it helps | Launch condition | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | Monitor/finish existing Box upload `3297384` | Existing sbatch | Preserves and shares artifacts externally. | Already running. | Do not submit duplicate unless failed. Inspect AGENT-436 log/destination first. |
| 1 | Corrected-Q terminal harvest after `3293924` -> `3295438` | Existing dependency chain plus harvest processing | Unlocks +/-Q candidate rows for admission and scorecards. | Wait until both jobs are terminal and successful. | Do not cancel/relaunch dependency job while pending. |
| 1 | Nominal upcomer matched-plane harvest from `3295492` | Harvest/parse first, sbatch only if outputs missing | Converts completed nominal upcomer compute into onset/recirculation evidence. | Inspect completed job output and parser contract first. | If rows are recirculating, keep them diagnostic/onset only. |
| 2 | Setup-only `M3+TS` / HX-cooler scorecard sweep | CPU model sweep | Directly attacks mdot-vs-TP/TW audit and predictive boundary blocker. | Can run once a row claims scorecard scripts/config copies. | Use Salt2 as train, Salt3 validation, Salt4 holdout; keep M2/M3 as diagnostic references. |
| 2 | Closure-QOI mesh/GCI readiness extraction | CFD postprocessing on staged copies | Moves `closure-qoi-mesh-gci` toward admission. | Need exact candidate case matrix from AGENT-409/406/425. | Must not mutate native CFD outputs; write staged scratch outputs and classify diagnostic until admitted. |
| 2 | Raw pressure/two-tap admission package | CFD/postprocessing plus reduction | Needed for final hydraulic residual and component K. | Need pressure definition, tap orientation, and straight-loss subtraction contract. | Current AGENT-409 rows are diagnostic reduced-pressure proxies only. |
| 3 | Upcomer onset targeted postprocessing | CFD postprocessing or new CFD if cases absent | Addresses `upcomer-onset-data-sparsity`. | Prefer postprocess existing/candidate Re ladder first; launch new CFD only after row and case plan. | Extract RAF/RMF/SVF/Re/Pr/Ri/Ra/Gr/Gz at inlet/mid/outlet planes. |
| 3 | Branch-specific ordinary-pipe scorecard excluding upcomer | CPU analysis | Lets downcomer/heater/lower-leg progress without invalid upcomer coefficients. | Can run after segment branch masks are frozen. | Publish included/excluded branch masks and coefficient labels. |
| 3 | Sensor-map refresh for TP2/TW10 policy | CPU documentation/scorecard | Prevents scoring ambiguity in next model audit. | Can run immediately under a sensor-map row. | Restore TP2 only after finite/projection gates; keep TW10 excluded until active-HX shell state. |

Recommended overnight order if compute is available:

1. Leave existing `3297384`, `3293924`, and `3295438` alone and monitor.
2. Launch a CPU-only setup-scorecard sweep for `M3+TS` and HX/cooler variants.
3. Launch staged closure-QOI/pressure postprocessing only if a new row can
   clearly name copied working directories and output paths.
4. Defer new CFD onset cases until the postprocessing/onset table proves what
   regime anchors are missing.

## Literature-Derived Study TODOs

Open first:

- `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md`
- `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/research_pathways.csv`
- `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/untried_litrev_model_forms.csv`
- `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/litrev_to_current_evidence_crosswalk.csv`
- `operational_notes/maps/literature-synthesis-and-gates.md`

The literature review did produce concrete things to try. Tomorrow agents
should not treat these as vague background; they are the research backlog.
Use the gate discipline from the litrev map: source-envelope overlap before
using a source-bounded correlation, property sensitivity before fitting
residuals, reset/named-loss evidence before global friction calibration,
separated heat-loss calibration before internal Nu tuning, and invalid-
single-stream diagnostics before exporting section coefficients.

| Priority | Lit-review study | Tomorrow action | Current overlap / guardrail |
| --- | --- | --- | --- |
| 1 | Branchwise source-envelope table | Compute or refresh branch `Re/Pr/Gr/Gr_star/Ri/Ra/Gz/Bo/L/D/reset-distance` ranges and mark literature correlations inside/outside/unknown. | Needed before Chen 2017, forced-developing Nu, or inclination/nonuniform-heating forms become active closures. |
| 1 | Property-mode sensitivity | Keep Reis/Jadyn replication properties separate from Jin/updated-property modes in every scorecard. | Do not fit residuals until the active property lane is declared. |
| 1 | Reset/developing hydraulic map | Build branch reset-distance and developing-pressure-loss evidence, including no-reset/aggressive-reset sensitivity. | AGENT-442 already ran a branch ordinary-pipe scorecard; tomorrow should consume it before rebuilding. |
| 1 | Named CFD pressure reductions | Convert pressure evidence into named `f_D,Delta_p`, component `K`, cluster `K`, or section-apparent rows only when planes isolate those terms. | AGENT-440 already completed staged raw two-tap diagnostics; next step is admission, not duplicate extraction. |
| 1 | Heat-loss resistance network | Keep heater efficiency, cooler/HX removal, passive loss, radiation, wall/layer resistance, storage, and residual separate. | AGENT-438 produced a setup-only HX/cooler candidate; do not absorb leftover heat residual into internal Nu. |
| 2 | Internal HTC/Nu bakeoff | Compare fully developed reference, forced-developing Nu, Chen 2017 mixed candidate, and CFD diagnostic Nu only where gates allow. | Internal Nu has `0` fit-admissible rows today; use validation/diagnostic labels unless gates change. |
| 2 | Upcomer recirculation/onset | Use matched-plane RAF/RMF/SVF/Re/Pr/Ri/Ra/Gr/Gz and wall-bulk drive to bracket onset; then design Re 150/200/250 cases only if needed. | AGENT-439 submitted matched-plane/onset work behind `3295438`; wait for terminal output before launching new CFD. |
| 2 | Nonuniform heating and inclination metadata | Add branch heating-pattern, wall heat-flux reconstruction, `theta`, `g_parallel`, `g_perpendicular`, aided/opposed/transverse flags. | Diagnostic metadata first; do not promote square-tube/inclined-source formulas into TAMU closures without envelope match. |
| 2 | Radiation bound | Add setup-only emissivity/Tsur/view-factor or lumped Stefan-Boltzmann sensitivity and no-double-count checks. | CFD `rcExternalTemperature` wallHeatFlux already includes radiation; no separate exported `qr` term exists. |
| 3 | Pressure-tap experiment design | Draft tap placement, uncertainty, and expected extraction plan around quartz/fitting clusters. | Planning only unless user shifts into experimental design. |
| 3 | Thermal instrumentation design | Draft wall/surface/coolant temperature priorities for heat-loss and internal-HTC separation. | Planning only unless user shifts into instrumentation. |
| 3 | Transient/freezing/oscillation extension | Define storage states and transient validation metrics. | Future method; not part of current steady closure unless thesis scope expands. |
| 3 | ROM/POD archive design | Define closure-relevant state-vector and snapshot metadata after closure/admission rows stabilize. | Future method; no ROM prediction claim now. |

The highest-value tomorrow sequence from this backlog is:

1. Consume AGENT-438/439/440/442 results before rebuilding any study.
2. Refresh the source-envelope/property/reset tables into one branchwise
   closure-readiness matrix.
3. Advance pressure and heat-loss admission first; they gate F6, H1 faithful,
   internal Nu, and Chen/forced-developing Nu.
4. Keep upcomer in the hybrid/onset lane until non-recirculating or transition
   anchors exist.

## Assumptions For Tomorrow Agents

- Salt2 is the default training lane for fitted setup-only scalars unless a
  later split note says otherwise.
- Salt3 is validation and Salt4 is holdout for model-audit scorecards unless a
  later split note overrides that exact package.
- Salt1 can be reported for comparison, but check its lineage and admission
  notes before using it as a training row.
- M1/M2/M3 diagnostic modes may be plotted and compared, but they are not final
  predictive models when they consume realized CFD quantities.
- Friction in the presentation outline should be stated as default distributed
  friction plus default minor-loss `K` terms. The intended current branch
  baseline is `F3_shah_apparent`, but any executed run left at an older solver
  default `F1 = 64/Re` must be audited before describing that run as F3.
- Internal Nu remains closed to fitting today. Reopening requires at least one
  row with interpretable wallHeatFlux sign, wallHeatFlux/enthalpy heat-balance
  closure, low RAF/RMF, no residual absorption, and mesh/time-window admission.
- Radiation semantics: CFD `rcExternalTemperature` includes radiative exchange
  in the exported wall heat flux. No separate exported `qr` term exists in the
  current evidence.

## Recommended First Prompt Tomorrow

```text
You are one Codex session in the coordinated multi-agent workflow.
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs

First read AGENTS.md, .agent/BOARD.md, .agent/STATE.md, .agent/BLOCKERS.md,
operational_notes/07-26/15/2026-07-15_TOMORROW_START_HERE.md, and the
AGENT-420/424/419/425 README files cited in that note.

Claim a board row. First check live jobs 3297384, 3293924, and 3295438. Then
implement the highest-value available task: either harvest terminal corrected-Q
outputs if ready, or build the setup-only M3+TS/HX-cooler scorecard from the
mdot-vs-temperature audit without using realized CFD runtime quantities.
```

## Closeout

This note did not submit, cancel, or modify scheduler jobs. It did not mutate
native CFD outputs, registry/admission state, generated indexes, or external
`../cfd-modeling-tools/**`.
