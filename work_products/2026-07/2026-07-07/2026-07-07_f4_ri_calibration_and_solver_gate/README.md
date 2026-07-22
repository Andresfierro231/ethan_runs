# F4 Ri Calibration And Solver Gate

Date: `2026-07-07`  
Task: `AGENT-191`  
Role: Coordinator / Implementer / Reviewer / Writer

## Objective

Freeze the admitted Salt F4 evidence, build a read-only Ri-audited calibration table, fit a bounded residual F4 candidate, and decide whether a later Fluid solver edit is admissible.

## Inputs / Provenance Inspected

- `work_products/2026-07-01_claude_momentum_budget/momentum_budget.csv`
- `work_products/2026-07-04_friction_forms/friction_forms_comparison.csv`
- `work_products/2026-07-01_claude_segment_friction/segment_friction.csv`
- `work_products/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv`
- `work_products/2026-07-01_claude_1d_predictivity_trial/perleg_vs_global_mdot.csv`
- `work_products/2026-07-01_claude_1d_predictivity_trial/segment_dp_compare.csv`
- `work_products/2026-07-01_claude_allspan_convection`
- `work_products/2026-07-01_claude_thermal_downcomer`
- `work_products/2026-07-07_f4_evidence_freeze_review/README.md`
- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`

## Planned Outputs

- `recent_coordination_audit.{csv,json}`
- `admitted_evidence_freeze.{csv,json}`
- `f4_ri_calibration_table.{csv,json}`
- `ri_definition_audit.md`
- `f4_candidate_fit_report.md`
- `model_comparison_f1_f3_f4_f5.{csv,json,md}`
- `corrected_salt_gate_monitor_snapshot.{csv,json,md}`

## Acceptance Criteria

- Admitted closure-fit rows are mainline Salt 2/3/4 Jin only.
- `needs_special_gate_scrutiny` is carried forward; no flagged row is closure-fit admissible without coordinator review.
- Ri definition uses median section Ri and records streamwise projection/property/length-scale basis.
- False-steady, short/canceled, Salt 1, and corrected Salt Q rows are excluded from closure fitting.
- F4 candidate is bounded and labeled as a screen, not a validated ROM closure law.

## Commands Run

- `python3.11 tools/analyze/build_f4_ri_calibration_and_solver_gate.py`
- `python3.11 -m json.tool work_products/2026-07-07_f4_ri_calibration_and_solver_gate/f4_ri_calibration_table.json`
- `python3.11 -m json.tool work_products/2026-07-07_f4_ri_calibration_and_solver_gate/admitted_evidence_freeze.json`
- `squeue -j 3279646 -o "%i|%j|%T|%P|%M|%l|%E|%r"`
- `sacct -j 3279646 --format=JobID,JobName%30,State,Partition,Elapsed,Start,End,ReqCPUS,ReqMem,Dependency%80 -P` (failed: this Slurm `sacct` lacks `Dependency` field)
- `python3.11 tools/analyze/test_build_f4_ri_calibration_and_solver_gate.py`
- `python3.11 -m py_compile tools/analyze/build_f4_ri_calibration_and_solver_gate.py tools/analyze/test_build_f4_ri_calibration_and_solver_gate.py`
- `pytest tests/test_friction_closures.py` in external Fluid
- `/opt/apps/intel19/python3/3.9.7/bin/python3.9 -c '<F4 solver routing smoke>'` in external Fluid

## Files Changed / Generated

- `tools/analyze/build_f4_ri_calibration_and_solver_gate.py`
- `tools/analyze/test_build_f4_ri_calibration_and_solver_gate.py`
- External Fluid F4 context-routing hardening in `friction_closures.py`, `solver.py`, and `tests/test_friction_closures.py`.
- This work-product directory and its CSV/JSON/Markdown outputs.

## Validation

- Local AGENT-191 admission tests passed: `3` tests.
- Local Python syntax compilation passed for the builder and test.
- External Fluid `tests/test_friction_closures.py` passed: `45` tests under Python 3.9 pytest.
- External Fluid lightweight solver routing smoke passed for heater/downcomer/upcomer/cooler parent-segment mapping.
- `python3.11 -m pytest` was unavailable because that interpreter lacks `pytest`; system `pytest` was used instead.
- `python3.11` package import smoke for Fluid was blocked by missing `yaml`; direct module and Python 3.9 Fluid checks passed.
- Gate job `3279646` dependency recorded from `squeue`; `sacct` dependency query failed because the local `sacct` field set does not include `Dependency`.

## Raw Observations vs Interpretation

Raw observations:

- The calibration table contains `18` admitted Salt 2/3/4 span rows.
- The evidence freeze contains `18` rows including held Salt 1 and corrected Salt Q rows.
- Corrected Salt Q rows are not admitted because the formal operating-point gate has not requalified them.
- Salt 1 remains held because the qualification package is not complete and Salt 1 nominal mdot confidence is weaker.

Interpretation:

- The read-only evidence gate is complete enough for coordinator review.
- The bounded F4 Ri candidate should not yet be used as a final ROM correlation.
- Solver edits may proceed only to harden explicit F4 segment-context routing and preserve default behavior; coefficient use still needs review.

## Blockers

- Corrected Salt Q formal gate output is still unavailable.
- Salt 1 qualification remains unresolved.
- External Fluid dirty/untracked state must be respected before any solver edit.

## Exact Next Action

Coordinator review should decide whether to keep `F4_Ri_candidate` as a diagnostic-only screen or open a later coefficient-refinement task. Do not admit corrected Salt Q rows until job `3279646` completes and flags are reviewed.

## Recent Coordination Audit

| path | mtime_iso | observation |
| --- | --- | --- |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/campaigns.yaml |  | external Fluid git status: M |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/journals/2026-06/2026-06-29_practical_reduced_order_broadened_v1_practical-reduced-order-broadened-v2_campaign_checkpoint.md |  | external Fluid git status: ?? |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/journals/2026-06/2026-06-29_test_section_diameter_refresh_report_v1.md |  | external Fluid git status: M |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/journals/2026-06/2026-06-29_workflow_journal.md |  | external Fluid git status: M |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/journals/2026-06/2026-06-30_baseline_internal_losses_predictive-validation-baseline-v2_campaign_checkpoint.md |  | external Fluid git status: ?? |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/journals/2026-06/2026-06-30_baseline_internal_losses_salt-promoted-internal_campaign_checkpoint.md |  | external Fluid git status: ?? |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/journals/2026-06/2026-06-30_ethan_cfd_informed_salt_v2_ethan-cfd-informed-salt-v2_campaign_checkpoint.md |  | external Fluid git status: ?? |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/journals/2026-06/2026-06-30_ethan_forced_losses_predictive-validation-ethan-v2_campaign_checkpoint.md |  | external Fluid git status: ?? |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/journals/2026-06/2026-06-30_ethan_forced_losses_salt-promoted-ethan_campaign_checkpoint.md |  | external Fluid git status: ?? |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/journals/2026-06/2026-06-30_morning_todo.md |  | external Fluid git status: ?? |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/journals/2026-06/2026-06-30_salt_promoted_property_matrix_v2_promoted_salt_property_campaign.md |  | external Fluid git status: ?? |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/journals/2026-06/2026-06-30_workflow_journal.md |  | external Fluid git status: ?? |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/run_registry.csv |  | external Fluid git status: M |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py |  | external Fluid git status: ?? |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/materials.py |  | external Fluid git status: M |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py |  | external Fluid git status: M |
| ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_friction_closures.py |  | external Fluid git status: ?? |
| .agent/BOARD.md | 2026-07-07T17:37:25 | modified within last 120 minutes at package build time |
| .agent/status/2026-07-07_AGENT-190.md | 2026-07-07T16:49:21 | modified within last 120 minutes at package build time |
| .agent/status/2026-07-07_AGENT-191.md | 2026-07-07T17:06:46 | modified within last 120 minutes at package build time |
