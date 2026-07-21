# CFD Postprocessing Workflow Documentation

Date: 2026-07-07
Agent: AGENT-197
Role: Coordinator / Writer / Implementer

## Purpose

This note turns the current CFD postprocessing scripts into a reusable workflow
map for worker agents. It separates raw run admission, thermal closure,
hydraulic closure, minor-loss extraction, upcomer/downcomer regime evidence,
observation-table assembly, 1D model-form trials, and mesh uncertainty.

The key rule is to separate physics evidence before fitting. A model-form
comparison should not hide pressure decomposition, heat-source accounting,
time-window quality, or mesh uncertainty inside a fitted coefficient.

## Operating Rules

- Treat native solver outputs and imported source directories as read-only.
- Run expensive OpenFOAM reconstruction/sampling on compute nodes, not login
  nodes.
- Prefer dated output roots:
  `work_products/YYYY-MM-DD_<slug>/`, `reports/YYYY-MM/YYYY-MM-DD/<slug>/`,
  or a documented historical report path when preserving continuity.
- Every product that feeds closure fitting should include source paths,
  retained time windows, units, admission flags, and quality flags.
- Continuation runs are the mainline evidence when a continuation exists.
- Corrected Salt perturbation rows stay out of closure fitting until the
  `AGENT-181` gate admits them.
- A short run ending early after restart, for example
  `salt1_jin_hi10q_corrected` ending about 254 s past restart, must be flagged
  in run-state inventory and postprocessing outputs. It may still be useful as
  a frozen snapshot, but it is not automatically a steady operating point.

## End-to-End Workflow

1. Run admission and convergence

   Goal: decide whether a case is live, failed, early-ended, frozen-only,
   quasi-steady, or fit-admissible.

   Primary scripts:

   ```bash
   python tools/analyze/build_postprocessing_run_status_inventory.py
   python tools/analyze/assess_time_convergence.py --help
   python tools/analyze/check_corrected_salt_preflight.py --help
   python tools/analyze/monitor_live_corrected_salt.py --help
   ```

   Required outputs:

   - case identity and exact runtime/source paths
   - latest time and retained-time window
   - restart offset where applicable
   - termination status, scheduler status, and evidence horizon
   - gate flags: `fit_eligible`, `validation_eligible`,
     `needs_special_gate_scrutiny`, `early_restart_end`, `missing_fields`,
     `permission_blocked`

   The run-state layer owns warnings such as a 33 second postprocess,
   an unexpectedly short continuation, missing fields, unreadable processor
   directories, and dependency jobs scheduled on the wrong partition.

2. Heat-source and sink audit

   Goal: separate heater input, cooler removal, passive ambient loss/gain,
   wallHeatFlux integral, enthalpy-flow change, residual, and sign convention
   before using heat data for 1D closure.

   Primary scripts:

   ```bash
   python tools/analyze/build_ethan_case_heat_summary.py \
     --source-id <source_id> \
     --output-dir work_products/<date>_case_heat_summary/<source_id> \
     --window-count 50

   python tools/analyze/build_ethan_steady_state_heat_flow_audit.py \
     --source-id <source_id> \
     --window-count 50

   python tools/analyze/build_ethan_salt_family_heat_loss_breakout.py \
     --source-report-dir reports/2026-06/2026-06-15/2026-06-15_ethan_field_transport_campaign \
     --output-dir work_products/<date>_salt_family_heat_loss_breakout

   python tools/extract/sample_segment_htc_uaprime.py \
     --source-id <source_id> \
     --output-dir work_products/<date>_segment_htc_uaprime/<source_id>
   ```

   Current strength: case heat summaries and segment HTC/UA prime sampling are
   useful today.

   Main gap: `TODO-PATCHWISE-HEAT-LEDGER` must build the auditable thermal
   companion to the pressure ledger. The older heat-flow audit is case-level,
   not patchwise.

3. Pressure and hydraulic evidence

   Goal: separate hydrostatic/buoyancy, dynamic pressure, distributed major
   loss, boundary development/reset, minor losses, recirculation-invalid
   regions, and residual before fitting friction or minor-loss coefficients.

   Primary scripts:

   ```bash
   python tools/extract/sample_section_mean_pressure.py \
     --source-id <source_id> \
     --output-dir work_products/<date>_section_mean_pressure/<source_id>

   python tools/extract/sample_leg_centerline_major_loss.py \
     --source-id <source_id> \
     --last-n-times 5 \
     --output-dir work_products/<date>_leg_centerline_major_loss/<source_id>

   python tools/analyze/derive_segment_friction.py \
     --input-dir <major_loss_or_section_pressure_dir> \
     --output-dir work_products/<date>_segment_friction

   python tools/analyze/derive_streamwise_momentum_budget.py \
     --input-dir <pressure_or_friction_source_dir> \
     --output-dir work_products/<date>_streamwise_momentum_budget
   ```

   Current strength: mean section pressure, segment friction, and streamwise
   momentum budget scripts provide strong diagnostics.

   Main gap: `TODO-PRESSURE-TERM-LEDGER` must convert these diagnostics into a
   station-aligned ledger with no buoyancy double counting.

4. Minor-loss features

   Goal: estimate local `K` for bends, reducers, junctions, and other feature
   losses using pressure evidence that is separated from adjacent straight-pipe
   distributed loss.

   Primary scripts:

   ```bash
   python tools/extract/sample_bend_minor_loss.py \
     --source-id <source_id> \
     --output-dir work_products/<date>_bend_minor_loss/<source_id>

   python tools/extract/sample_feature_minor_loss_budget.py \
     --source-id <source_id> \
     --last-n-times 5 \
     --output-dir work_products/<date>_feature_minor_loss_budget/<source_id>

   python tools/analyze/summarize_corner_pressure_drops.py \
     --input-dir <bend_or_feature_source_dir> \
     --output-dir work_products/<date>_corner_pressure_drops
   ```

   Current strength: bend sampling and corner summaries are useful for
   diagnostics and sign-convention checks.

   Main gap: `TODO-MINOR-LOSS-TWO-TAP` must emit `K_local` and `K_apparent`
   using two-tap total pressure, adjacent-straight subtraction, and local bulk
   dynamic pressure.

5. Upcomer/downcomer regime evidence

   Goal: determine whether the upcomer behaves as ordinary pipe friction or as
   a buoyancy/recirculation-cell regime where normal friction fitting is not
   valid.

   Primary scripts:

   ```bash
   python tools/extract/sample_upcomer_convection_cell.py \
     --source-id <source_id> \
     --output-dir work_products/<date>_upcomer_convection_cell/<source_id>

   python tools/extract/sample_downcomer_recirculation.py \
     --source-id <source_id> \
     --output-dir work_products/<date>_downcomer_recirculation/<source_id>

   python tools/analyze/build_ethan_upcomer_recirculation_evidence.py \
     --output-dir reports/2026-07/2026-07-07/<slug> \
     --work-product-dir work_products/<date>_upcomer_recirculation_evidence
   ```

   Current strength: reduced-output evidence packages and recent correlation
   work can diagnose recirculation behavior.

   Main gap: `TODO-UPCOMER-ONSET` must turn diagnostics into a regime table
   with Re, Pr, Gr, Ra, Ri, wall-bulk temperature difference, recirculation
   metrics, onset criterion, uncertainty, and fit-admission status.

6. Common observation table

   Goal: put every CFD-to-1D closure observation into one auditable table before
   fitting. One row equals one observable.

   Proposed minimum columns:

   - `observation_id`
   - `source_id`
   - `run_family`
   - `case_role`
   - `mesh_level`
   - `time_window_start_s`
   - `time_window_end_s`
   - `time_count`
   - `observable_kind`
   - `observable_name`
   - `value`
   - `uncertainty`
   - `units`
   - `source_path`
   - `script`
   - `ledger_id`
   - `quality_flags`
   - `fit_eligible`
   - `validation_eligible`
   - `notes`

   Board row: `TODO-OBSERVATION-TABLE-CONTRACT`.

7. 1D closure package and model-form bakeoff

   Goal: compare model forms only after the observation table and ledgers expose
   what physics each fitted term is allowed to absorb.

   Primary scripts:

   ```bash
   python tools/analyze/cfd_closure_bundle.py \
     --output-dir work_products/<date>_cfd_closure_bundle \
     --manifest-path imports/<date>_cfd_closure_bundle.json

   python tools/analyze/build_ethan_1d_closure_bakeoff.py \
     --frozen-dir reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_1d_validation \
     --closure-bundle-dir work_products/<date>_cfd_closure_bundle \
     --output-dir reports/2026-07/2026-07-07/<slug> \
     --import-manifest-path imports/<date>_1d_closure_bakeoff.json

   python tools/analyze/build_next_1d_model_forms.py \
     --input-dir work_products/<date>_closure_observation_table \
     --output-dir work_products/<date>_next_1d_model_forms
   ```

   Current strength: closure-bundle and bakeoff scripts package existing
   evidence and can replay local comparisons.

   Main gap: `TODO-MODEL-FORM-BAKEOFF` must compare baseline, per-leg,
   literature, F4 leg class, and any admitted Ri/F4 candidates on the same
   observations, with fitted rows held apart from validation rows.

8. Mesh and GCI uncertainty

   Goal: determine which quantities of interest are mesh-stable enough to use
   for publication or closure fitting.

   Expected source path from Ethan:

   ```text
   ~/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/
   ```

   Current access note: the path exists and appears to contain Salt
   coarse/medium/fine directories, but traversal was blocked by permissions
   during the July 7 check. Ethan needs to grant group read/execute or stage a
   readable copy before a worker can compute defensible GCI.

   Board row: `TODO-MESH-UNCERTAINTY`.

## Script Integration Matrix

| Area | Script | Workflow role | Strong CLI modifiers | Current status |
| --- | --- | --- | --- | --- |
| Run state | `build_postprocessing_run_status_inventory.py` | Inventory run/latest-time/postprocess state | output-root style modifiers in script help | Useful for admission inventory; must keep early-restart flags visible |
| Run state | `assess_time_convergence.py` | Quantify retained-window stability | case/window/output modifiers | Strong documentation and tests |
| Run state | `check_corrected_salt_preflight.py` | Corrected Salt gate preflight | owned by `AGENT-181` | Active gate script, read-only for this task |
| Run state | `monitor_live_corrected_salt.py` | Live corrected-Salt monitor | owned by `AGENT-181` | Active gate script, read-only for this task |
| Heat | `build_ethan_steady_state_heat_flow_audit.py` | Cross-case wallHeatFlux audit | `--source-id`, `--window-count`, `--skip-figures` | Documented in this pass; still case-level |
| Heat | `build_ethan_case_heat_summary.py` | Per-case wallHeatFlux summary | `--source-id`, `--runtime-root`, `--window-count`, `--validation-csv`, `--output-dir` | Documented in this pass |
| Heat | `build_ethan_salt_family_heat_loss_breakout.py` | Reduced-report Salt heat breakout | `--source-report-dir`, `--output-dir` | Documented in this pass |
| Heat | `sample_segment_htc_uaprime.py` | Segment HTC/UA prime extraction | source/window/output modifiers | Strong documentation; useful now |
| Pressure | `sample_section_mean_pressure.py` | Section mean pressure extraction | source/window/output modifiers | Strong documentation; useful now |
| Pressure | `sample_leg_centerline_major_loss.py` | Major-loss primitive extraction | `--source-id`, `--analysis-manifest`, `--last-n-times`, `--time-selector`, `--target-ds-m`, `--skip-extraction`, `--output-dir` | Documented in this pass; downstream ledger required |
| Pressure | `derive_segment_friction.py` | Segment friction derivation | input/output modifiers | Strong tests; useful now |
| Pressure | `derive_streamwise_momentum_budget.py` | Momentum budget derivation | input/output modifiers | Strong tests; useful now |
| Minor loss | `sample_bend_minor_loss.py` | Bend loss evidence | source/window/output modifiers | Strong documentation; useful now |
| Minor loss | `sample_feature_minor_loss_budget.py` | Feature endpoint pressure diagnostic | `--source-id`, `--analysis-manifest`, `--last-n-times`, `--time-selector`, `--extract-key`, `--skip-extraction`, `--output-dir` | Documented in this pass; not final `K_local` |
| Minor loss | `summarize_corner_pressure_drops.py` | Corner pressure-drop summary | input/output modifiers | Useful sign-convention summary |
| 1D | `cfd_closure_bundle.py` | Package closure contract | `--output-dir`, `--manifest-path` | Documented in this pass |
| 1D | `build_ethan_1d_closure_bakeoff.py` | Local 1D closure bakeoff | `--frozen-dir`, `--closure-bundle-dir`, `--output-dir`, `--import-manifest-path` | Documented in this pass; follow-on bakeoff still needed |
| 1D | `build_incremental_model_form_comparison.py` | Compare model ladder | input/output modifiers | Good framing from July 4 work |
| 1D | `build_next_1d_model_forms.py` | Lightweight next-form triage | `--input-dir`, `--output-dir` | Documented in this pass; should consume observation contract later |
| Up/down | `sample_upcomer_convection_cell.py` | Upcomer convection-cell extraction | source/window/output modifiers | Strong documentation; useful now |
| Up/down | `sample_downcomer_recirculation.py` | Downcomer recirculation extraction | source/window/output modifiers | Strong documentation; useful now |
| Up/down | `build_ethan_upcomer_recirculation_evidence.py` | Reduced-output recirculation evidence package | all input table paths plus `--output-dir`, `--work-product-dir`, `--import-manifest-path` | Documented in this pass |

## Worker Handoff Contract

Every independent worker resolving one of the board rows should write:

- a status file in `.agent/status/`
- a journal entry in `.agent/journal/<date>/`
- a README in the dated `work_products/<date>_<slug>/` root
- machine-readable CSV/JSON outputs with exact source paths
- a validation note that lists commands run and any tests skipped

Each worker should state:

- what physics terms are observed directly
- what terms are inferred
- what terms remain residual
- which rows are fit-eligible
- which rows are validation-only
- which rows are excluded and why

## Testing Guidance

For documentation-only edits:

```bash
python3.11 -m py_compile <edited scripts>
```

For workflow scripts with direct tests:

```bash
python3.11 -m pytest \
  tools/analyze/test_cfd_closure_bundle.py \
  tools/analyze/test_ethan_upcomer_recirculation_evidence.py
```

For new ledger rows, require both unit tests and a smoke run that writes a small
dated `work_products/**` package from existing reduced data. Do not require
expensive raw OpenFOAM extraction in unit tests.

## Remaining Documentation Gaps

- The pressure ledger needs a canonical row schema and station naming contract.
- The heat ledger needs patch role naming, sign convention, and radiation
  caveat fields.
- The observation table needs a validation script that fails missing units,
  source paths, time windows, and admission flags.
- The minor-loss two-tap script needs a stable feature/station identifier that
  joins to the pressure ledger.
- The model-form bakeoff needs a fitted-vs-validation split and pressure
  distribution score, not just mass-flow error.
- The upcomer onset workflow needs explicit exclusion rules for recirculation
  regimes before friction fitting.
- The mesh uncertainty row is blocked until Ethan's modern-runs mesh data is
  readable or restaged.
