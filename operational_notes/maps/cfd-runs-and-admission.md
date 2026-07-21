---
task: AGENT-294
date: 2026-07-13
role: Writer
type: map
status: reference
tags: [salt-q-perturbation, admission, steady-state]
related:
  - operational_notes/maps/README.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
---
# CFD Runs & Admission — Map of Content

Tags: #salt-q-perturbation #admission #steady-state

## What this covers

The CFD run inventory that feeds closure fits and 1D validation: the trusted
mainline Salt Jin continuations, the Salt-Q perturbation campaigns (original
false-steady set vs. corrected relaunch), the run-classification policy, and the
admission / steady-state gating rules that decide whether a row is closure-fit
usable. This is the hub for "which CFD rows are real data and why".

## Current status

Mainline Salt1/2/3/4 Jin continuations are now the intended final predictive
training envelope, but not all rows have equal postprocessing depth yet. Salt2-4
have the strongest common schema coverage; Salt1 nominal/lo10q/hi10q are admitted
primary closure evidence and still need promotion into the Salt2-4 schema before
final model training consumes them. The original 14-case Q/insulation perturbation
campaign was all false-steady (mdot pinned at nominal, insulation knob never
applied) and is quarantined. A corrected campaign was relaunched on 2026-07-04
with patched restart fields, all thermal patches, and staged `dynamicCode/`. On
2026-07-13 the admission policy was user-corrected: a converged/stationary Salt-Q
row is closure-fit admissible even if the old `too_short` post-restart gate would
reject it, and the `corrected` suffix was dropped from display names (short names
`salt2_lo10q`, `salt2_hi10q`, `salt4_lo10q`). Every approved sbatch stop must now
leave numeric final-window drift evidence.

2026-07-14 superseding training/testing update: Salt1 nominal, Salt1 lo10q,
Salt1 hi10q, Salt4 nominal, and Salt4 +/-5Q are now usable thermal training
rows under the documented split policy; Salt2 +/-5Q are holdout/testing rows.
Salt1 hi10q's older failed/not-admissible inventory label is superseded by the
terminal harvest plus patch-complete terminal BC table. Pressure/upcomer metrics
for Salt2/Salt4 +/-5Q are still blocked: Slurm job `3295901` was cancelled
before running, so do not admit those hydraulic/upcomer metrics until a
replacement job produces parsed matched-plane files.
Start with
`operational_notes/07-26/14/2026-07-14_SALT_TRAINING_TESTING_EVIDENCE_ROLLOUT.md`
and
`work_products/2026-07/2026-07-14/2026-07-14_salt_training_testing_evidence_rollup/`.

2026-07-17 final predictive split update: AGENT-481 makes Salt1-4 nominal rows
the final training/calibration envelope. Testing/holdout comes from
perturbation, external, and new-CFD rows: Salt2 +/-5Q are holdout/testing after
PM5 matched-plane extraction repair; `val_salt2` is external-test only after a
matching heat-loss/admission package; Salt2/Salt4 +/-10Q remain blocked until
`3293924` and `3295438` finish and terminal admission lands; the AGENT-478
Salt3 Q x insulation matrix is the new-CFD holdout/onset design. Source:
`work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/`.

## CFD-to-1D Postprocessing Schema Contract

Every case promoted into predictive training, training support, holdout/testing,
or external-test scoring should publish the same schema lanes before use:

- BC/source/material role table with physical role, source/sink role, and
  runtime legality.
- Geometry/material mapping rows for branch, segment, station, wall stack, and
  sensor locations.
- Patchwise heat ledger separating heater, cooler/HX, passive wall,
  test-section, junction/other, enthalpy-flow change, and residual.
- Pressure ladder / streamwise pressure rows with sign convention and branch or
  station provenance.
- Thermal score rows with source/sign status and segment heat-loss ownership.
- Sensor target rows for TP/TW/mdot targets with runtime-forbidden flags.
- PM5/F6/internal-Nu rows where applicable, including upcomer recirculation or
  matched-plane caveats.
- Runtime-input audit proving no CFD `mdot`, realized `wallHeatFlux`, imposed
  CFD cooler duty, validation temperatures, or holdout temperatures are used as
  predictive runtime inputs.
- Admission table that labels each row as training, training support,
  holdout/testing, external-test, diagnostic-only, blocked, or superseded.

Use `python3.11 tools/agent/case_schema_lint.py <package>` as an advisory
coverage check. The linter is intentionally conservative; passing it does not
replace scientific admission, and failing it means the missing schema lane must
be documented before the row is used.

## Trusted results

- **Mainline baseline** — Salt2/3/4 Jin continuations stationary in flow and gross
  duty (coarse mesh). Salt1 weakly converged; use with caution.
  `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt{1..4}_jin/`
- **Run-classification policy** — mainline vs. sensitivity groups; Kirst runs are
  NOT mainline; perturbations stay in their own sensitivity group (per AGENTS.md).
  `operational_notes/06-26/30/2026-06-30_run_classification_policy.md`
- **Steady-state stop evidence (2026-07-13)** — `salt1_nominal`, `salt1_lo10q`,
  `salt1_hi10q` steady (max mdot rel drift `8.0e-8` / `3.3e-7` / `2.0e-6`;
  `total_Q` drift `0 W`). `salt4_hi10q` NOT steady (mdot rel drift `6.3e-3`,
  `total_Q` drift `-1.59 W`) → repacked into job `3293441`.
  `operational_notes/07-26/13/2026-07-13_stopped_sbatch_steady_state_decisions.md`
- **Salt training/testing rollout (2026-07-14)** — Future agents should consume
  the case-use table before fitting or scoring closure models. Training thermal
  rows now include Salt1 nominal/lo10q/hi10q, Salt4 nominal, and Salt4 +/-5Q.
  Salt2 +/-5Q are holdout/testing rows. Pressure/upcomer metrics remain blocked
  because job `3295901` was cancelled before running.
  `operational_notes/07-26/14/2026-07-14_SALT_TRAINING_TESTING_EVIDENCE_ROLLOUT.md`
  `work_products/2026-07/2026-07-14/2026-07-14_salt_training_testing_evidence_rollup/salt_training_testing_case_use_table.csv`
- **Canonical final predictive split (2026-07-17)** — Final training spans
  Salt1-4 nominal rows. Holdout/testing is supplied by Salt2 +/-5Q, external
  val_salt2, selected +/-10Q after terminal admission, and new CFD rows after
  run/admission. This supersedes old final-score language that reserved Salt4
  nominal as the untouched holdout.
  `work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/`

## Open / in-progress / blocked

- **Gate job `3293441` steps** — track the repacked continuation (includes the
  still-drifting `salt4_hi10q`); needs steady final-window before admission.
- **Matched pressure/upcomer job `3295901`** — cancelled before running; inspect
  AGENT-357 package and relaunch or document a replacement path before any
  pressure/upcomer admission claim.
- **Still-drifting salt3 rows** — diagnose `salt3` hi5q / hi10q (reported ~24% /
  ~45% drift); not yet admissible.
- **Deferred terminal harvest** — run post-exit terminal harvest for the cancelled
  Salt1 rows to recover any usable final window.
- **Requalification gate** — `--require-moved-from` exposed the 14 false-steady
  runs; keep applying it before admitting any perturbation.

## Research avenues tried (outcome + provenance)

- **Original Q/insulation perturbation sweep** (hiq/loq/hi5q/lo5q/hiins/loins/
  optins, 14 cases) — FALSE-STEADY: mdot pinned at nominal; the perturbation was
  not reliably in the restart `T` field read by `foamRun`, and insulation labels
  (`hiins`/`loins`) never changed the live BC (all baseline `insulated.h = 5.964`).
  Quarantined; do not use for friction/HTC/regression/validation.
  MASTER TODO T3; `operational_notes/07-26/04/2026-07-04_salt_perturbation_quarantine_and_relaunch.md`
- **Corrected Q-perturbation relaunch** — patch root `0/T`, copied
  `processors64/<latest>/T` immediately before `foamRun`, all three lower heater
  patches, and balanced upper cooling patches; stage into a clean dated dir with
  parent `dynamicCode/`; require launch-time `preflight_patch_audit_<job>.csv`.
  Earlier attempts `3275388`–`3275436` all failed (launcher bootstrap, Slurm array
  splitting, broken post-OF python patcher, corrupted collated `decomposedBlockData`
  framing, missing `dynamicCode/`); `3275448`–`3275451` is the current corrected
  submission.
  `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/`
- **Old invalid staged roots deleted (2026-07-13)** — June 19 and June 25 invalid
  Salt perturbation roots removed after path-specific destructive approval; `find`
  verification confirmed no matching old names remain and July 4 repaired roots are
  present.
  `.agent/journal/2026-07-13/salt-q-admission-policy-and-short-names.md`
- **Admission-policy correction (2026-07-13)** — converged/stationary Salt-Q rows
  are closure-fit admissible; `too_short` retained only as context; short display
  names replace `*_corrected`; status-table / F4-gate / upcomer-onset / presentation
  builders no longer categorically exclude Salt-Q rows.
  `operational_notes/07-26/13/2026-07-13_salt_q_admission_policy_and_short_names.md`
- **Steady-state stop evidence rule (DECISIONS 2026-07-13)** — every user-approved
  sbatch stop must leave numeric final-window evidence in the same status/journal/
  op-note as the action; no reliance on chat context.
  `.agent/DECISIONS.md`;
  `operational_notes/07-26/13/2026-07-13_stopped_sbatch_steady_state_decisions.md`

## Key artifacts (canonical)

- Mainline runs: `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt{1..4}_jin/`
- Corrected Q campaign: `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/`
- Run-classification policy: `operational_notes/06-26/30/2026-06-30_run_classification_policy.md`
- Quarantine + relaunch: `operational_notes/07-26/04/2026-07-04_salt_perturbation_quarantine_and_relaunch.md`
- Admission policy + short names: `operational_notes/07-26/13/2026-07-13_salt_q_admission_policy_and_short_names.md`
- Stopped-sbatch steady-state decisions: `operational_notes/07-26/13/2026-07-13_stopped_sbatch_steady_state_decisions.md`
- Final-window metrics CSV: `work_products/2026-07/2026-07-13/2026-07-13_stopped_sbatch_steady_state_decisions/final_window_metrics.csv`
- Corrected-Q live terminal-admission check:
  `work_products/2026-07/2026-07-14/2026-07-14_corrected_q_terminal_admission_gate/`
- Salt training/testing rollout:
  `operational_notes/07-26/14/2026-07-14_SALT_TRAINING_TESTING_EVIDENCE_ROLLOUT.md`
- Salt training/testing case-use table:
  `work_products/2026-07/2026-07-14/2026-07-14_salt_training_testing_evidence_rollup/salt_training_testing_case_use_table.csv`
- Canonical final predictive split policy:
  `work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv`
- Salt1 patch-complete BC and hi10q conflict resolution:
  `work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/`

## Operational gotchas

- sbatch from compute nodes via `ssh login3.ls6.tacc.utexas.edu`; no long jobs on
  login nodes.
- OF13 env required for `T` reconstruction (custom BC segfaults under OF12).

## Related

- `operational_notes/maps/README.md`
- `operational_notes/maps/mesh-gci-and-uncertainty.md`
- `operational_notes/maps/thermal-closures-and-internal-nu.md`
