# End-of-Day Coordinator Handoff

Date: 2026-07-07
Prepared by: codex
Role: Coordinator / Writer

## Purpose

This is the fresh-session handoff for tomorrow. It consolidates the context from
today's coordination, documentation, board cleanup, corrected-Salt monitoring,
worker outputs, and remaining scientific/operational decisions.

Tomorrow's agent should start here, then read the files listed below before
touching the board or any active run artifacts.

## Required Startup Reads For Tomorrow

Read these first:

1. `AGENTS.md`
2. `.agent/BOARD.md`
3. `.agent/FILE_OWNERSHIP.md`
4. `.agent/ROLES.md`
5. This handoff:
   `.agent/journal/2026-07-07/coordinator-end-of-day-handoff.md`

Then read the task-specific context:

- Corrected Salt / Water gate:
  - `.agent/status/2026-07-07_AGENT-181.md`
  - `.agent/journal/2026-07-07/water-provisional-and-corrected-salt-gate.md`
  - `operational_notes/07-26/07/2026-07-07_water_provisional_and_corrected_salt_gate.md`
  - `work_products/2026-07-07_corrected_salt_live_monitor/README.md`
  - `work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv`
  - `work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.json`
  - `work_products/2026-07-07_corrected_salt_live_monitor/overnight_decision_snapshot_2026-07-07/OVERNIGHT_SUBMIT_README.md`
  - `work_products/2026-07-07_corrected_salt_live_monitor/overnight_decision_snapshot_2026-07-07/salt1_coordinator_review.md`
- CFD postprocessing/workflow documentation:
  - `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`
  - `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_workflow_docs.md`
  - `.agent/journal/2026-07-07/documentation-workflow-hardening.md`
- Worker outputs/status:
  - `.agent/status/2026-07-07_AGENT-193.md`
  - `.agent/status/2026-07-07_AGENT-194.md`
  - `.agent/status/2026-07-07_AGENT-195.md`
  - `.agent/status/2026-07-07_AGENT-196.md`
  - `.agent/status/2026-07-07_AGENT-197.md`
  - `.agent/status/2026-07-07_AGENT-199.md`
  - `.agent/status/2026-07-07_AGENT-200.md`
  - `work_products/2026-07-07_pressure_term_ledger/README.md`
  - `work_products/2026-07-07_heat_source_sink_ledger/README.md`
  - `work_products/2026-07-07_friction_forms_comparison/README.md`
  - `work_products/2026-07-07_upcomer_correlation_v2/README.md`
  - `work_products/2026-07-07_f5_ri_corrected/README.md`

## Important Board Caveat

The board has an identifier collision that should be cleaned up tomorrow before
new workers are launched.

- Codex documentation hardening was claimed and retired as `AGENT-197` earlier
  today. It produced:
  - `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_workflow_docs.md`
  - `.agent/journal/2026-07-07/documentation-workflow-hardening.md`
  - script docstrings in selected postprocessing scripts
- Later, a Claude pressure-ledger worker also used `AGENT-197`, and
  `.agent/status/2026-07-07_AGENT-197.md` now refers to the pressure-ledger
  entry-flag fix, not the documentation-hardening task.

Do not assume `AGENT-197` uniquely identifies one task. The board/history should
be repaired tomorrow, probably by adding a note that the codex documentation
handoff is journal-only and the active status file belongs to the Claude
pressure-ledger task. Avoid renaming another worker's active/completed row
without reviewing the journal/status provenance.

## What We Did Today

### 1. Corrected Salt / Water Gate Coordination

The main operational objective was to avoid premature admission of corrected
Salt perturbation rows while still preserving useful Water provisional output.

Key outcomes:

- Water July 6 outputs remain provisional monitor evidence only.
- Corrected Salt preflight checker reported all 14 corrected cases passed the
  static heat-input / target-Q checks in earlier AGENT-181 output.
- Corrected Salt rows are still not closure- or ROM-fit admissible.
- The formal corrected-Salt gate remains blocked until live jobs finish and a
  proper gate/requalification pass is completed.
- Premature gate jobs were canceled:
  - `3279638` `saltq_gate_after`: canceled before start
  - `3279646` `saltq_gate_0707`: canceled before start
- An attempted continuation submission from `login3` was blocked by account/SU
  constraints:
  - project `ASC23046`
  - current balance recorded in status: `4633` SUs
  - already requested in queued jobs: `4688` SUs
  - requested continuation: `120` SUs
  - no continuation job ID was created

Latest live Slurm state checked near closeout:

```text
3275448  corr_saltq_g1         NuclearEnergy  RUNNING  started 2026-07-04T10:26:47
3275449  corr_saltq_g2         NuclearEnergy  RUNNING  started 2026-07-04T10:36:35
3275560  corr_saltq_salt4_all  NuclearEnergy  RUNNING  started 2026-07-04T12:21:50
3279638  saltq_gate_after      NuclearEnergy  CANCELLED before start
3279646  saltq_gate_0707       NuclearEnergy  CANCELLED before start
```

Commands used for the final live check:

```bash
squeue -j 3275448,3275449,3275560,3279638,3279646
sacct -j 3275448,3275449,3275560,3279638,3279646 --format=JobID,JobName,Partition,State,Elapsed,Start,End,ExitCode --parsable2
```

Important correction: `squeue -u andresfi` failed with `Invalid user:
andresfi`; use `$USER`, the current login account, or explicit job IDs.

### 2. Salt 1 Special Scrutiny

The early-ended corrected Salt 1 high-Q run is now documented as a special
scrutiny item.

Raw observation from AGENT-181:

- case: `salt1_jin_hi10q_corrected`
- restart time: `3756.33125 s`
- final solver time: `4010.590361446 s`
- advance past restart: about `254.259 s`
- target extension was much longer, so advance fraction was about `0.0424`
- solver log reached an `End` condition with `convergenceMonitor` involved

Interpretation:

- Do not treat this as a valid steady operating point merely because the solver
  stopped cleanly.
- It remains non-admissible for closure/ROM fitting unless a coordinator
  explicitly approves a reference/rerun interpretation.
- Future run-state inventory and postprocessing must preserve
  `needs_special_gate_scrutiny=True` or equivalent.

Tomorrow:

- Check whether the Salt 1 behavior can be explained by weak global convergence
  monitor criteria, missing nominal reference, or true fast freeze.
- Do not merge Salt 1 corrected-Q into closure fitting.

### 3. CFD Postprocessing Documentation

We created a reusable workflow note:

```text
operational_notes/07-26/07/2026-07-07_cfd_postprocessing_workflow_docs.md
```

It documents the modular end-to-end path:

1. run admission and convergence
2. heat-source/sink audit
3. pressure and hydraulic evidence
4. minor-loss features
5. upcomer/downcomer regime evidence
6. common observation table
7. 1D closure package and model-form bakeoff
8. mesh/GCI uncertainty

It also includes:

- command templates
- script integration matrix
- worker handoff contract
- testing guidance
- remaining documentation/scientific gaps
- explicit requirement to flag short corrected-Salt restarts such as
  `salt1_jin_hi10q_corrected`

Script docstrings were added to clarify workflow role, inputs, outputs,
command-line modifiers, and boundaries for:

- `tools/analyze/build_ethan_steady_state_heat_flow_audit.py`
- `tools/analyze/build_ethan_case_heat_summary.py`
- `tools/analyze/build_ethan_salt_family_heat_loss_breakout.py`
- `tools/extract/sample_leg_centerline_major_loss.py`
- `tools/extract/sample_feature_minor_loss_budget.py`
- `tools/analyze/build_ethan_1d_closure_bakeoff.py`
- `tools/analyze/build_next_1d_model_forms.py`
- `tools/analyze/cfd_closure_bundle.py`
- `tools/analyze/build_ethan_upcomer_recirculation_evidence.py`

Validation run for documentation changes:

```bash
python3.11 -m py_compile tools/analyze/build_ethan_steady_state_heat_flow_audit.py tools/analyze/build_ethan_case_heat_summary.py tools/analyze/build_ethan_salt_family_heat_loss_breakout.py tools/extract/sample_leg_centerline_major_loss.py tools/extract/sample_feature_minor_loss_budget.py tools/analyze/build_ethan_1d_closure_bakeoff.py tools/analyze/build_next_1d_model_forms.py tools/analyze/cfd_closure_bundle.py tools/analyze/build_ethan_upcomer_recirculation_evidence.py
```

Result: passed.

Runtime limitations:

- `pytest` was unavailable in this shell:
  `/usr/bin/python3.11: No module named pytest`
- some CLI help smoke checks were blocked by missing `numpy` or `matplotlib`

### 4. Board Candidates / Scientific Work Queue

The board now carries the planned closure-ledger queue. These are the main
scientific unlocks still needing worker attention:

- `TODO-PRESSURE-TERM-LEDGER`
- `TODO-OBSERVATION-TABLE-CONTRACT`
- `TODO-PATCHWISE-HEAT-LEDGER`
- `TODO-TARGETED-LITREV-FORMS`
- `TODO-MINOR-LOSS-TWO-TAP`
- `TODO-MODEL-FORM-BAKEOFF`
- `TODO-UPCOMER-ONSET`
- `TODO-MESH-UNCERTAINTY`

The queue instructions say a worker must claim exactly one row, create its own
status file, stay inside listed edit paths, and use the deep-dive note briefs:

```text
operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md
```

Tomorrow, clean the board before launching more workers. In particular:

- AGENT-200 status says complete but board still says `STATUS: CLAIMED`.
- AGENT-197 identifier collision needs a note or repair.
- Check whether completed Claude tasks should be retired from `Active` after
  reviewing their outputs.

### 5. Worker Outputs Observed Near Closeout

Observed from board/status files:

- `AGENT-193`: pressure term ledger work exists/status should be read.
- `AGENT-194`: heat source/sink ledger work exists/status should be read.
- `AGENT-195`: friction mdot comparison status/output exists.
- `AGENT-196`: upcomer recirculation correlation complete.
  - fitted form: `bf = a + b/Re`
  - `a = 0.0539`
  - `b = 15.93`
  - Re range: `68-135`
  - status note says 25 tests pass
  - output: `work_products/2026-07-07_upcomer_correlation_v2/`
- `AGENT-197` Claude pressure-ledger entry fix complete.
  - Fixed Shah entry flag bug.
  - `test_section_span` and `left_upper_leg` now non-entry spans.
  - `development_loss_pa=0.0` for non-entry spans.
  - added `flow_reset_flag`.
  - status says 11/11 direct tests pass and 299/299 suite pass.
- `AGENT-199` F4 stub mapping fix complete.
  - Added four missing horizontal manifold stub segment mappings.
  - Adopted downstream-classification principle.
  - status says 52/52 Fluid tests and 299/299 ethan_runs tests pass.
- `AGENT-200` F5 Ri-corrected implementation complete by status, but board
  still says claimed.
  - Implemented `F5_ri_corrected` framework.
  - OLS fits were poor; active coefficients set to zero.
  - F5 equals F3_shah_apparent for current S2/S3/S4 mdot comparison.
  - status says 61/61 Fluid tests and 299/299 ethan_runs tests pass.
  - output: `work_products/2026-07-07_f5_ri_corrected/`

Tomorrow's coordinator should verify outputs before treating them as accepted.
Do not assume status-file claims are sufficient for publication or fitting.

## Mesh/GCI Context

User said Ethan planned to put mesh/GCI data under:

```text
~/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/
```

Earlier inspection found the path exists and appears to contain Salt
coarse/medium/fine directories, but traversal was permission-blocked. The
workflow docs record this. The `TODO-MESH-UNCERTAINTY` row should not fabricate
GCI from unreadable data. Ask Ethan for group read/execute or a readable staged
copy before assigning this to a worker.

## Scientific State At Closeout

### What Is Usable Now

- We have a coherent workflow map for postprocessing and closure maturation.
- We have pressure, heat, friction, upcomer, and 1D closure scripts that are
  documented enough for targeted workers.
- Pressure-ledger and heat-ledger work appears to have started/completed in
  worker outputs, but needs coordinator review.
- Upcomer correlation work exists and should be evaluated against physical
  interpretation before promotion.
- F4 and F5 Fluid-side closure experiments exist, with tests passing by worker
  report.

### What Is Not Yet Safe

- Corrected Salt perturbation rows are not fit-admissible.
- Salt 1 corrected high-Q is a special scrutiny case, not steady evidence.
- Water July 6 outputs are provisional monitor evidence only.
- F5 Ri-corrected framework should not be treated as an improvement yet; by
  worker report it collapses to F3_shah_apparent for current data.
- Mesh/GCI remains blocked by data permissions.
- Observation-table contract still needs to become the canonical row-level
  source before model-form bakeoff is rigorous.

## Recommended Tomorrow Plan

1. Board hygiene:
   - Resolve/annotate the `AGENT-197` collision.
   - Retire `AGENT-200` from Active if its status/output review supports it.
   - Confirm whether `AGENT-199` and Claude `AGENT-197` should also move to
     Retired/Complete notes.

2. Corrected Salt live check:
   - Run:
     ```bash
     squeue -j 3275448,3275449,3275560,3279638,3279646
     sacct -j 3275448,3275449,3275560,3279638,3279646 --format=JobID,JobName,Partition,State,Elapsed,Start,End,ExitCode --parsable2
     ```
   - If `3275448`, `3275449`, and `3275560` finished, inspect logs and decide
     whether a gate can run.
   - Do not queue a new gate until the dependency and SU/account situation is
     clean.

3. Review worker outputs:
   - Start with pressure ledger and heat source/sink ledger because they are
     foundational for observation table and model-form bakeoff.
   - Check tests and README claims against actual CSV/JSON outputs.
   - Verify no worker accidentally admitted corrected Salt rows.

4. Choose next high-value row:
   - If ledgers look solid, prioritize
     `TODO-OBSERVATION-TABLE-CONTRACT`.
   - If ledgers have schema/scientific gaps, repair pressure/heat ledger first.
   - Keep `TODO-MESH-UNCERTAINTY` blocked until readable Ethan mesh data is
     available.

5. Decide what to do with F5:
   - Since current F5 coefficients are inactive and F5 equals F3, document it
     as a candidate framework awaiting expanded corrected-Q data, not a model
     improvement.

## Closeout Answer To User

At closeout, the practical answer was:

- no more heavy analysis or submissions tonight;
- corrected Salt remains live and gate-blocked;
- Salt 1 high-Q remains special scrutiny;
- board has a cleanup issue but no urgent scientific blocker that requires
  staying online;
- tomorrow starts with board cleanup, live job check, and review of worker
  outputs before any new worker launch.

## Provenance Commands From Final Closeout

Final checks run during this handoff discussion:

```bash
sed -n '1,85p' .agent/BOARD.md
sed -n '1,160p' .agent/status/2026-07-07_AGENT-181.md
squeue -u andresfi
squeue -j 3275448,3275449,3275560,3279638,3279646
sacct -j 3275448,3275449,3275560,3279638,3279646 --format=JobID,JobName,Partition,State,Elapsed,Start,End,ExitCode --parsable2
sed -n '160,340p' .agent/status/2026-07-07_AGENT-181.md
sed -n '1,180p' .agent/status/2026-07-07_AGENT-200.md
sed -n '1,160p' .agent/status/2026-07-07_AGENT-199.md
sed -n '1,180p' .agent/status/2026-07-07_AGENT-197.md
```

Do not use the failed `squeue -u andresfi` form tomorrow without confirming the
valid scheduler username.

## Editing Boundaries For Tomorrow

- Do not mutate native solver outputs.
- Do not broad-delete `staging/`, `tmp_extract/`, `cache/`, generated figures,
  or solver trees.
- Do not edit external `../cfd-modeling-tools/**` unless the board row
  explicitly claims that path.
- Do not let corrected Salt rows into fitting until the AGENT-181 gate or a
  successor gate explicitly admits them.
- Treat all current worker outputs as review candidates until coordinator
  review has read their status, journal, README, CSV/JSON, and tests.
