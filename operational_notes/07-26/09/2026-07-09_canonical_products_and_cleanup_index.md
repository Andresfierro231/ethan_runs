# Canonical Products And Cleanup Index

Date: `2026-07-09`
Task: `AGENT-247`

This is the current reference map after the July 9 thermal observation-table
refresh and downstream progress pass. It is intentionally non-destructive: no
large scratch tree, source case, solver output, registry row, or external model
repository was moved or deleted.

## Current Canonical Analysis Chain

Use these packages in this order for closure/thesis validation work:

| Role | Current package | Primary file | Status |
| --- | --- | --- | --- |
| OpenFOAM boundary/setup audit | `work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit/` | `claim_verdicts.csv` | Complete; verified `6/6` documented OpenFOAM boundary-condition claims. |
| Physical-interface thermal sampling | `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/` | `combined_openfoam_interface_samples.csv` | Complete; Slurm job `3287311` parsed `48/48` planned planes, no `qr` output. |
| Canonical observation table | `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/` | `closure_observations.csv` | Current canonical table; `1032` rows, `45` fit targets, `0` validation errors. |
| Model-form bakeoff refresh | `work_products/2026-07/2026-07-09/2026-07-09_model_form_bakeoff_thermal_refresh/` | `model_form_summary.csv` | Complete refresh against July 9 canonical table; no external Fluid rerun. |
| Thermal control-volume admission review | `work_products/2026-07/2026-07-09/2026-07-09_thermal_control_volume_admission_review/` | `thermal_thesis_evidence_table.csv` | Compact 9-row thesis-facing thermal validation table; all rows validation-only. |

## Superseded But Still Useful Provenance

Keep these as provenance, not current targets:

| Package | Superseded by | Keep because |
| --- | --- | --- |
| `work_products/2026-07/2026-07-08/2026-07-08_closure_observation_table/` | July 9 thermal-refresh observation table | Shows the pre-physical-interface seed contract and 423-row baseline. |
| `work_products/2026-07/2026-07-08/2026-07-08_model_form_bakeoff/` | July 9 bakeoff refresh | Starter bakeoff; useful for diffing the July 9 canonical-table impact. |
| `work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/` | Consumed by July 9 observation table and admission review | Source enthalpy residual provenance; not superseded as raw evidence. |
| `work_products/2026-07/2026-07-07/2026-07-07_pressure_term_ledger/` | Consumed by July 9 observation table and bakeoff | Current pressure source ledger for admitted Salt 2/3/4 rows. |

## Current Downstream Results

### Observation Table

- `1032` total rows.
- `342` pressure rows.
- `690` thermal rows.
- `45` fit-eligible rows.
- `414` rows from the OpenFOAM physical-interface samples.
- `195` rows from the physical-interface enthalpy ledger.
- `291` rows are `recirculation_flag=yes`; all are
  `fit_use_status=not_fit_recirculation`.
- `0` rows have `radiation_present=yes`.

### Model-Form Bakeoff

- Current package:
  `work_products/2026-07/2026-07-09/2026-07-09_model_form_bakeoff_thermal_refresh/`
- Observation rows consumed: `1032`.
- Case/model score rows: `15`.
- Current mdot ordering remains:
  `F3_shah_apparent`, `F5_ri_corrected`, `F3_hagenbach`, `F1`,
  `F4_leg_class`.
- Thermal mismatch is carried as a common validation axis from the canonical
  table; it is not model-specific until each candidate form emits comparable
  segment heat predictions.

### Thermal Admission Review

- Current package:
  `work_products/2026-07/2026-07-09/2026-07-09_thermal_control_volume_admission_review/`
- Detail rows: `66`.
- Thesis evidence rows: `9` (`Salt 2/3/4` by heater, cooler/reducer, junction).
- Heater class: defensible validation evidence in all three Salt rows, still
  fit-ineligible.
- Cooler/reducer class: recirculation-contaminated in compact rollup.
- Junction class: recirculation-contaminated in compact rollup and contains
  sampled-interface diagnostics without a complete residual assignment.
- Radiation-present detail rows: `0`.

## Cleanup Status

The next cleanup step should remain a dry-run manifest, not deletion.

Already documented:

- `operational_notes/07-26/09/2026-07-09_repo_cleanup_dry_run.md`
- `work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit/cleanup_dry_run.csv`

High-priority cleanup candidates:

| Path | Current evidence | Recommendation |
| --- | --- | --- |
| `tmp/` | Size probe reported about `187G` before continuing into deeper checks. | Build a manifest by subtree/date/task and classify report references before deleting or archiving anything. |
| `tmp_extract/` | Size probe reported about `205G`; provenance-sensitive extraction scratch tree. | Manifest first; identify report-cited roots before pruning. |
| `work_products/2026-07-06_overnight_postprocess_jobs` | Outside sorted `work_products/YYYY-MM/YYYY-MM-DD` layout; size probe reported only `67K`. | Move only after reference checks, manifest update, and compatibility symlink approval. |
| `reports/2026-06/2026-06-23/2026-06-23_ethan_cfd_freeze_checkpoint` | Missing clear README per AGENT-240 cleanup dry run. | Add README; no destructive action needed. |
| `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/TODO.md` | Stale coordination note. | Add additive status update; do not rewrite original launch facts. |
| `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/submitted_jobs.csv` | Initial submission metadata may be stale relative to live job status. | Add status addendum after terminal evidence; do not rewrite submission rows. |

## Next Work After This Pass

1. Update the model-form report narrative if an external Fluid rerun becomes
   available with per-segment heat predictions.
2. Build a manifest for `tmp/` and `tmp_extract/` before any cleanup approval.
3. Add the June 23 freeze-checkpoint README so frozen-window semantics are
   easy to cite.
4. Keep Salt 1 nominal and corrected Salt-Q rows out of canonical fit targets
   until their active/terminal gates explicitly admit them.
5. Treat the July 9 observation table as current mainline; keep July 8 products
   as provenance only.
