---
provenance:
  - .agent/STATE.md
  - .agent/BLOCKERS.md
  - .agent/status/2026-07-17_AGENT-519.md
  - .agent/status/2026-07-17_AGENT-532.md
  - operational_notes/07-26/17/2026-07-17_WEEKEND_NEXT_MODEL_HANDOFF_PLAN.md
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/mentor_thesis_outline.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/cfd-runs-and-admission.md
tags: [handoff, monday-start, fresh-agent, next-steps, scheduler, thesis-dossier, forward-model]
related:
  - operational_notes/START_HERE_FOR_AGENTS.md
  - operational_notes/07-26/17/2026-07-17_WEEKEND_NEXT_MODEL_HANDOFF_PLAN.md
  - work_products/2026-07/2026-07-17/2026-07-17_post_terminal_cfd_harvest_watch/README.md
  - reports/thesis_dossier/README.md
task: AGENT-534
date: 2026-07-17
role: Coordinator/Scheduler/Writer
type: operational_note
status: current
supersedes: []
superseded_by:
---
# Monday Morning Fresh-Agent Handoff

This note is the start-here context for a fresh agent on Monday,
2026-07-20. It captures the working context at the end of Friday,
2026-07-17, with special emphasis on what to do next.

Scheduler state below is a read-only snapshot from `2026-07-17T17:28:12-0500`.
Refresh it Monday before making any harvest, submission, or admission decision.

## Open First Monday

1. `AGENTS.md`
2. `.agent/BOARD.md`
3. `.agent/STATE.md`
4. `.agent/BLOCKERS.md`
5. `operational_notes/07-26/17/2026-07-17_MONDAY_MORNING_FRESH_AGENT_HANDOFF.md`
6. `work_products/2026-07/2026-07-17/2026-07-17_post_terminal_cfd_harvest_watch/README.md`
7. `operational_notes/07-26/17/2026-07-17_WEEKEND_NEXT_MODEL_HANDOFF_PLAN.md`
8. `reports/thesis_dossier/README.md`
9. `reports/thesis_dossier/mentor_thesis_outline.md`
10. `operational_notes/maps/forward-predictive-model.md`
11. `operational_notes/maps/cfd-runs-and-admission.md`

Before editing, claim or confirm a non-overlapping board row and run:

```bash
python3.11 tools/agent/preflight_task.py --task-id <TASK_ID>
```

## Current Big Picture

The repository is organized around a defensible CFD-to-1D reduction thesis for
the TAMU molten-salt natural-circulation loop. The current thesis claim is that
a predictive 1D model cannot be built from one global correction factor; it
needs branch/component-local pressure and heat ledgers, evidence roles, local
closure admission, uncertainty, and explicit handling of junctions,
recirculation, walls, and external heat transfer.

The final predictive target is steady `fluid+walls`: each region has fluid
state, wall/material stack, pressure model, thermal circuit, source/sink role,
boundary-layer/development state, recirculation/admission flags, and uncertainty
status.

The mentor-facing thesis outline was saved as:

- `reports/thesis_dossier/mentor_thesis_outline.md`

The internal thesis execution roadmap remains:

- `reports/thesis_dossier/Outline.md`

Do not replace one with the other. The mentor outline is for advisor discussion;
`Outline.md` is the technical build plan.

## Thesis Dossier State

The thesis dossier is now cleanly structured:

- `reports/thesis_dossier/README.md`
- `reports/thesis_dossier/Outline.md`
- `reports/thesis_dossier/mentor_thesis_outline.md`
- `reports/thesis_dossier/Chapters_and_sections/current/`
- `reports/thesis_dossier/Chapters_and_sections/dated/`
- `reports/thesis_dossier/figures/`

Current copy-ready/current thesis sections include:

- `01_modeling_approach.md`
- `02_model_form_fluid_walls.md`
- `03_split_policy_and_evidence_classes.md`
- `04_upcomer_recirculation_modeling.md`
- `05_junction_aware_ledgers.md`
- `06_intermediate_model_forms_and_endpoint_strategy.md`
- `07_wall_test_section_coupled_score_and_physics_plan.md`
- `08_thesis_claim_ledger.md`
- `09_fluid_walls_segment_atlas.md`
- `10_uncertainty_chapter_package.md`
- `11_sam_facing_interpretation.md`
- `12_thesis_figures_and_diagrams_plan.md`

Initial editable SVG figures were created under:

- `reports/thesis_dossier/figures/`

These include segment atlas, segment-local ledger inset, upcomer hybrid
schematic, junction-aware comparison, model-form ladder, and SAM-facing
flowchart. They should be polished after mentor feedback or final scorecard
changes, not treated as final quantitative figures yet.

## Canonical Split And Evidence Roles

Use the July 17 canonical final predictive split, not older Salt2/Salt3/Salt4
development split language.

| Role | Rows |
| --- | --- |
| final training | `salt1_nominal`, `salt2_jin_nominal`, `salt3_jin_nominal`, `salt4_nominal` |
| training support | `salt1_lo10q`, `salt1_hi10q`, `salt4_lo5q`, `salt4_hi5q` |
| holdout/testing | `salt2_lo5q`, `salt2_hi5q` |
| external test | `val_salt2` |
| future holdout candidates | selected Salt2/Salt4 +/-10Q after `3293924` and `3295438` terminal admission; new Salt3 Q x insulation matrix after run/admission |

Do not use Salt3, Salt2 +/-5Q, `val_salt2`, selected +/-10Q, or new CFD rows
to choose model form, coefficients, root fallbacks, sensor exclusions, or
admission thresholds unless a later policy explicitly changes their role.

Forbidden predictive runtime inputs remain:

- CFD `mdot`
- realized CFD `wallHeatFlux`
- imposed CFD cooler duty
- realized test-section heat
- validation, holdout, or external-test temperatures

Replay/diagnostic analyses may use these only when clearly labeled.

## Open Blockers

Trust `.agent/BLOCKERS.md` over stale prose. As of the generated July 17 index,
the open blockers are:

1. `predictive-wall-test-section-submodels` / high
   - Evidence: `work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/README.md`
   - Current meaning: heater and cooler/HX setup models have usable evidence,
     but passive wall/test-section/thermal-shape physics still has no admitted
     predictive candidate.

2. `upcomer-onset-data-sparsity` / medium
   - Evidence: `work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard/README.md`
   - Current meaning: current upcomer evidence is recirculation-dominated and
     lacks ordinary single-stream anchors.

3. `f6-friction-re-correction` / medium
   - Evidence: `work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/README.md`
   - Current meaning: current PM5 rows are all recirculation diagnostics; use
     `F3_shah_apparent` as production until non-recirculating or explicitly
     recirculation-modeled pressure evidence exists.

Do not reopen resolved blockers such as broad heater/cooler/wall submodels,
thermal parity, radiation parity, OF12 reconstruct segfault, or no-mesh-for-GCI
unless a later dated package explicitly reopens them.

## Forward Model State

Recent candidate attempts narrowed the problem:

- AGENT-529 heater-source leave-Salt3-out score completed `67/67` rows but
  admitted `0` candidates. Salt4 train rows had rejected roots, and the
  diagnostic finite-row lambda failed Salt3 versus M3 by mdot, TP, TW, and
  all-probe gates.
- AGENT-531 blocker audit found `0` admitted wall/source candidates and `0`
  scoreable source-segment mismatches. It points next toward axial
  mixing/upcomer stratification.
- AGENT-526 explicit test-section bulk-to-ambient series-resistance fallback
  completed `6/6` rows but admitted `0` candidates. It improved mdot but made
  TP/TW/all-probe errors worse.

The stable failure pattern is: many candidates improve mdot while putting the
thermal field in the wrong place, especially heated-incline/upcomer/test-section
TW/TP residuals. Do not call mdot improvement success if TP/TW/all-probe errors
worsen.

## Why The TP/TW Gates Failed

The current evidence points to spatial thermal-shape error rather than runtime
failure. The candidates move integrated flow in the right direction but do not
move heat through the loop in the same way as the CFD/M3 comparator. In practice,
mdot improves while the local TP/TW probes get worse.

Do not blame TP2 or TW10 as the primary explanation. AGENT-531 records those as
known policy exclusions: TP2 is validation-only junction/restore target context,
and TW10 is an active-HX shell state excluded from scoreable closure admission.
The scoreable failures persist without relying on either sensor.

Open `work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/invariant_failure_modes.csv`.
The highest-signal rows are:

- `TW_heated_incline_TW5`: `30/30` fail rows, worst delta `78.64861796 K`.
- `TW_heated_incline_TW6`: `30/30` fail rows, worst delta `71.05938137 K`.
- `TW_heated_incline_role_rmse`: `30/30` fail rows, worst delta
  `67.22153272 K`.
- `TP_left_upper_vertical_TP6`: `30/30` fail rows, worst delta `49.86332527 K`.
- `TP_test_section_TP5`: `28/30` fail rows, worst delta `41.48064787 K`.

AGENT-526 gives a compact numerical example. The lumped-cooler
test-section wall/fluid candidate:

- Salt3: mdot delta `-15.8500613 pct`, but TP delta `+11.5769804 K`, TW delta
  `+42.37730593 K`, and all-probe delta `+35.38684985 K`.
- Salt4: mdot delta `-13.09023967 pct`, but TP delta `+26.19173439 K`, TW delta
  `+48.6052515 K`, and all-probe delta `+42.93410155 K`.

The failed model families include passive wall/test-section distribution,
wall-temperature drive, heater-source redistribution, wall thermal circuits,
and a one-node test-section wall/fluid series resistance. That means the next
model should not be another passive hA retune or wall-state selector retread.
It needs a mechanism that changes axial/branch thermal transport:
upcomer/test-section mixing, stratification/recirculation exchange, or a richer
distributed wall/fluid model with energy ledgers.

Monday's first scientific task should therefore be a no-solver TP/TW
failure-forensics package. It should turn the current residual evidence into a
physics-requirement matrix before anyone launches another coupled grid.

Minimum outputs for that package:

- `candidate_family_gate_matrix.csv`
- `sensor_failure_rank.csv`
- `role_segment_failure_rank.csv`
- `physics_requirement_matrix.csv`
- `model_form_exclusion_table.csv`
- `next_model_contract.csv`
- `README.md`, `summary.json`, status, journal, and import manifest

## Scheduler Snapshot To Refresh Monday

Friday `squeue`/`sacct` snapshot:

| Job | Name | Friday state | Monday action |
| --- | --- | --- | --- |
| `3293924` | `saltq_sel_cont` | `RUNNING`, elapsed `4-00:24:06` | Refresh status. If terminal, wait for dependent `3295438`; do not harvest directly under monitor row. |
| `3295438` | `saltq_s24_sel_harv` | `PENDING`, dependency-held | Do not submit a duplicate selected Salt2/Salt4 corrected-Q harvester while this job exists. |
| `3299610` | `salt4_q3x_probe` | `RUNNING`, elapsed `23:48:41` | If terminal successful Monday, claim a separate high-heat harvest/admission row before parsing or scoring. |
| `3299620` | `salt4_heat_pack` | `RUNNING`, elapsed `23:33:52` | If terminal successful Monday, claim a separate high-heat harvest/admission row before parsing or scoring. |

Use read-only checks first:

```bash
squeue -j 3293924,3295438,3299610,3299620
sacct -j 3293924,3295438,3299610,3299620 --format=JobID,JobName%24,State,ExitCode,Elapsed,Start,End
```

If any watched job is terminal successful, AGENT-519 or the Monday monitor
should stop at a handoff and create/claim a separate cfd-pp/admission row. Do
not harvest, parse, admit, cancel, requeue, or resubmit from a read-only monitor
row.

## Weekend Sbatch Submission Decision

Submit immediately: nothing new. The critical weekend CFD work is already
running or dependency-held, and the next Fluid model run is not submit-ready
until the UMX1 API and dry-contract gates pass.

| Candidate job | Weekend status | Required gate before sbatch |
| --- | --- | --- |
| Corrected-Q selected continuation | Already running as `3293924` | Do not duplicate. Monitor until terminal. |
| Corrected-Q selected harvester | Already dependency-held as `3295438` | Let dependency release; do not submit a second harvester. |
| Salt4 high-heat no-recirculation probe | Already running as `3299610` | Do not duplicate. Harvest only from a fresh cfd-pp/admission row after terminal success. |
| Salt4 high-heat bracket pack | Already running as `3299620` | Do not duplicate. Harvest only from a fresh cfd-pp/admission row after terminal success. |
| UMX1 tiny Fluid smoke | Prepare only | Submit only after Fluid hook audit, dry contract, runtime-input audit, and split contract pass. |
| UMX1 full grid | Not ready | Submit only after tiny smoke gives accepted train roots with no split leakage. |

Useful non-sbatch weekend work is the TP/TW failure-forensics package, the
read-only Fluid API audit, and the UMX1 dry contract/tests.

## Monday Priority Sequence

### 1. Refresh Coordination State

- Open `.agent/BOARD.md` and `.agent/STATE.md`.
- Confirm whether `AGENT-519` is still the only active task.
- Refresh the four watched scheduler jobs above.
- If a generated index refresh happened after this note, trust the newer
  `.agent/STATE.md`/`.agent/BLOCKERS.md`.
- Claim a specific board row before any edit or harvest.

### 2. Do Not Duplicate Running/Dependency-Held Jobs

Do not submit another corrected-Q selected harvester while `3295438` exists or
is dependency-held. Do not submit duplicate high-heat jobs until `3299610` and
`3299620` are terminal and their outputs/logs are inspected.

### 3. If Terminal Jobs Finished, Harvest With Separate Rows

Corrected-Q chain:

- Required trigger: `3293924` terminal, then `3295438` released, runs, and
  completes with usable harvest logs/outputs.
- Next row: corrected-Q selected Salt2/Salt4 +/-10Q terminal
  harvest/admission.
- Output should classify selected +/-10Q rows as future holdout/testing
  candidates only, not fit rows by default.

High-heat chain:

- Required trigger: `3299610` or `3299620` terminal success plus readable
  staged outputs/logs.
- Next row: high-heat no-recirculation/onset harvest/admission.
- Use these to test no-recirculation/upcomer-onset/F6 anchor gates, not to
  force an ordinary-pipe closure onto recirculating rows.

### 4. If No Harvest Is Ready, Start The Next Model Lane

Primary next model lane: `UMX1` energy-conserving upcomer
mixing/stratification.

Start by auditing Fluid for a real hook:

```bash
rg -n "upcomer|mixing|stratification|recirculation|exchange|ScenarioConfig" ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2
```

If an updated Fluid API exists, build a repo-local scorer around it. If it does
not exist, write a no-solver API contract package and stop before launching
jobs. Do not fake mixing with posthoc sensor correction.

UMX1 model intent:

- Split the upcomer/test-section path into a throughflow stream and an exchange
  or recirculation reservoir.
- Couple them with an energy-conserving exchange term such as
  `Q_mix = C_mix * mdot * cp * (T_reservoir - T_main)`, or the equivalent
  Fluid API parameter.
- Fit at most one scalar first.
- Use Salt1/Salt2/Salt4 nominal rows for selection only if roots are accepted.
- Use Salt3 as nominal holdout.
- Treat Salt2 +/-5Q and `val_salt2` as blind score-only rows when executable
  adapters exist.

Minimum outputs:

- `case_split_contract.csv`
- `candidate_definitions.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `training_objective_by_parameter.csv`
- `nominal_coupled_scorecard.csv`
- `salt3_holdout_delta_vs_m3.csv`
- `probe_error_localization.csv`
- `blind_perturbation_external_scorecard.csv`
- `candidate_admission_review.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
- `README.md`

Admission requires runtime legality, accepted train roots, Salt3 mdot/TP/TW/all
probe no worse than M3 and best prior wall/source candidate, plus either blind
score pass or explicit non-admitted release gate.

### 5. Secondary Model Lane

Secondary lane: `TSWFC2` distributed test-section wall/fluid nodes.

Do this after UMX1, or only if UMX1 is blocked by missing Fluid API. Do not
repeat AGENT-526's single bulk-to-ambient series-resistance fallback. The next
wall/fluid candidate should be distributed and energy-conserving, with explicit
fluid, inner-wall, and outer-wall states by axial node and a small number of
setup-legal parameters.

### 6. Thesis Work Monday

The thesis dossier is in good shape for mentor discussion. Monday thesis tasks
should be scoped separately from model scoring:

- Send or review `reports/thesis_dossier/mentor_thesis_outline.md` with
  mentors.
- Use `reports/thesis_dossier/Outline.md` for internal planning.
- Keep current sections under `Chapters_and_sections/current/`; avoid
  proliferating new dated sections unless recording provenance or a changed
  result.
- Update `08_thesis_claim_ledger.md` only when a claim's evidence, split role,
  blocker, figure/table source, or caveat changes.
- Refresh `05_junction_aware_ledgers.md` only after stronger junction/stub or
  pressure corner-K evidence lands.
- Polish thesis figures after mentor feedback or final scorecards; do not add
  quantitative overlays before the corresponding evidence is admitted.

## Research Lines Not To Lose

- Junction-aware versus segment-only model forms: `val_salt2` currently has
  about `40.9260865692 W` of junction/stub loss across four buckets, while
  pressure corner-K remains diagnostic because centerline-subtracted local K is
  negative. This supports local role ledgers, not a global correction factor.
- Upcomer recirculation: ordinary single-stream `Nu`, `f_D`, and `K` fits are
  invalid for current recirculating upcomer evidence. Keep the hybrid
  throughflow-plus-exchange lane separate.
- Uncertainty chapter package: time-window, mesh/GCI disposition, property
  lane, sensor-map, split, and model-form uncertainty are already assembled as
  thesis source material.
- SAM-facing interpretation: explain branchwise losses, heat ledgers,
  recirculation flags, and admission metadata as future SAM guidance without
  claiming SAM validation.

## Hard Guardrails

- No native CFD/OpenFOAM output mutation.
- No registry/admission mutation without an explicit row.
- No scheduler submission/cancel/requeue/dependency edit without an explicit
  scheduler row.
- No solver/postprocessing launch on login nodes.
- No external Fluid source edit unless a row explicitly claims it.
- No fitting or model selection on holdout/external-test rows.
- No use of CFD mdot, realized CFD wall heat flux, imposed CFD cooler duty, or
  validation temperatures as predictive runtime inputs.
- No duplicate submissions for running/dependency-held jobs.
- No global multiplier presented as a thesis-strength closure.

## Acceptance Signal For Monday

A good Monday start produces one of these clean outcomes:

- Scheduler terminal states are refreshed and any completed chain is handed to a
  separate harvest/admission row without duplicate submissions.
- UMX1 produces a dry API/contract package if Fluid lacks a mixing hook.
- UMX1 produces accepted-root, split-legal scorecards if the Fluid hook exists.
- If UMX1 is blocked, the blocker is precise enough that TSWFC2 can start
  without guessing.
- Thesis work remains cleanly separated from model scoring and uses the mentor
  outline for communication, not as a source of new scientific claims.
