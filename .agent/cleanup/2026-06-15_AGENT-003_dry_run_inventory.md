# AGENT-003 Dry-Run Cleanup Inventory

## Scope

- Workspace roots inspected: `tmp/`, `tmp_extract/`, `cache/`
- Explicit exclusions from this inventory:
  - `tmp/slurm_codex_board_jobs/**` because `.agent/BOARD.md` assigns it to active `AGENT-068`
  - `tmp/2026-06-15_streamwise_transport_phase1_smoke/**` because `.agent/BOARD.md` assigns it to active `AGENT-070`
  - `tmp/2026-06-15_field_transport_phase2_smoke/**` because `.agent/BOARD.md` assigns it to active `AGENT-071`
  - `tmp/2026-06-15_12R_smoke/**` because queue repair row `12R` is live with `Plotting = running` under `AGENT-058`
- No move or delete commands were executed in this task.

## Candidate Table

| Path | Classification | Why it is a candidate | Proposed action | Reproducible from script? | Needs confirmation? |
| --- | --- | --- | --- | --- | --- |
| `tmp/mplconfig` | `safe generated artifact` | Contains only Matplotlib cache data (`fontlist-v330.json`), last touched `2026-06-09`, with no research content. | Delete when a cleanup pass is approved. | `yes` | `yes` |
| `tmp/slurm_case_analysis_jobs` | `safe generated artifact` | Contains only historical `.sbatch` submission stubs for June 11 case-package jobs. | Archive or delete after confirming no one still wants the launch records. | `yes` | `yes` |
| `tmp/2026-06-11_feature_minor_loss_manifest_check`, `tmp/2026-06-11_feature_minor_loss_smoke`, `tmp/2026-06-11_feature_minor_loss_smoke_live`, `tmp/2026-06-11_heat_summary_smoke`, `tmp/2026-06-11_case_analysis_live_smoke` | `safe generated artifact` | Small or empty smoke/check directories used to test extractor or summary behavior; contents are CSV/JSON outputs only. | Delete first in any approved cleanup pass. | `yes` | `yes` |
| `tmp/2026-06-12_ethan_postprocessing_plot_smoke`, `tmp/2026-06-12_ethan_postprocessing_plot_smoke_2`, `tmp/2026-06-12_ethan_postprocessing_plot_smoke_3`, `tmp/2026-06-12_ethan_postprocessing_plot_smoke_4`, `tmp/2026-06-12_ethan_postprocessing_plot_smoke_5`, `tmp/2026-06-12_ethan_postprocessing_campaign_smoke`, `tmp/2026-06-12_ethan_postprocessing_campaign_smoke_campaign` | `duplicate output` | These are temporary package/campaign smoke rebuilds with generated manifests, data tables, and report drafts; canonical outputs now live under the campaign publication tree. | Delete after one final coordinator check that no pending review step still needs a smoke tree. | `yes` | `yes` |
| `tmp/2026-06-11_case_analysis_raw_reuse_smoke`, `tmp/2026-06-11_case_analysis_raw_reuse_smoke_v2`, `tmp/2026-06-11_case_analysis_raw_reuse_smoke_v3`, `tmp/2026-06-11_case_analysis_raw_reuse_smoke_v4` | `duplicate output` | Four Salt 2 raw-reuse smoke package variants with the same README structure and near-identical generated outputs, differing mainly by iteration/time horizon. | Keep at most one representative if someone still wants a local smoke example; otherwise delete all four together. | `yes` | `yes` |
| `tmp/2026-06-11_case_analysis_package_mismatch`, `tmp/2026-06-11_case_analysis_package_mismatch_should_fail`, `tmp/2026-06-11_case_analysis_raw_reuse_mismatch`, `tmp/2026-06-11_case_analysis_raw_reuse_should_fail`, `tmp/2026-06-11_case_analysis_raw_reuse_missing_heat_should_fail`, `tmp/2026-06-11_case_analysis_raw_reuse_no_heat_should_fail` | `safe generated artifact` | Names and contents indicate bounded failure-mode or mismatch experiments; they contain only generated CSV/JSON raw-extraction or package outputs. | Delete after approval unless someone still needs them for debugging the June 11 package-builder path. | `yes` | `yes` |
| `tmp/2026-06-11_case_analysis_raw_reuse_rawonly`, `tmp/2026-06-11_salt1_jin_probe`, `tmp/2026-06-11_salt1_jin_raw`, `tmp/2026-06-11_salt1_jin_raw_seed_package`, `tmp/2026-06-11_salt1_jin_major_only`, `tmp/2026-06-11_salt1_kirst_major_debug`, `tmp/2026-06-11_salt1_kirst_major_debug_skip`, `tmp/2026-06-11_salt1_jin_case_analysis_direct` | `stale but potentially useful` | These look like intermediate debug or raw-extraction snapshots that may still help reproduce June 11 rollout behavior. They are generated, but more diagnostic than smoke clutter. | Archive first; do not delete in the first cleanup wave. | `likely yes` | `yes` |
| `tmp/2026-06-11_salt1_jin_case_analysis_package`, `tmp/2026-06-11_salt1_jin_case_analysis_package_window4`, `tmp/2026-06-11_salt1_kirst_case_analysis_package_window4`, `tmp/2026-06-11_salt2_jin_case_analysis_package_window4`, `tmp/2026-06-12_salt2_kirst_case_analysis_package_window4`, `tmp/2026-06-12_salt3_jin_case_analysis_package_window4`, `tmp/2026-06-12_salt3_kirst_case_analysis_package_window4`, `tmp/2026-06-12_salt4_jin_case_analysis_package_window4` | `stale but potentially useful` | These are durable late-window package directories with README narratives, manifests, and reused review evidence for the Salt-family rollout. | Archive to a dated holding area if space pressure requires action; do not delete first. | `yes, but expensive` | `yes` |
| `tmp/2026-06-11_salt1_jin_case_analysis_smoke`, `tmp/2026-06-11_salt1_jin_case_analysis_smoke_py39`, `tmp/2026-06-11_salt1_jin_case_analysis_smoke_rerun`, `tmp/2026-06-11_salt1_jin_case_analysis_smoke_unbuffered` | `duplicate output` | Multiple smoke variants for the same Salt 1 Jin package path, kept mainly to compare runtime behavior or Python/runtime invocation choices. | Keep none or one representative; otherwise delete as a family. | `yes` | `yes` |
| `tmp_extract/ethan_case_analysis_snapshots`, `tmp_extract/ethan_streamwise_friction`, `tmp_extract/ethan_legwise_hydraulic_budget`, `tmp_extract/ethan_section_transport`, `tmp_extract/salt2_jin_probe` | `stale but potentially useful` | Large extraction caches (`22G`, `12G`, `2.0G`, `1.1G`, `227M`) that contain expensive intermediate products and partially reconstructed case data. | Leave in place for now; if storage pressure exists, archive selectively only after verifying no downstream workflow still points to them. | `yes, but expensive` | `yes` |
| `cache/paraview_cases` | `stale but potentially useful` | Small convenience cache of `.foam` launcher stubs for ParaView; rebuildable, but harmless and occasionally useful. | Optional delete or archive last; low-priority candidate. | `yes` | `yes` |
| `tmp/2026-06-15_12R_smoke` | `unknown / do not touch` | Repair row `12R` is active on `.agent/BOARD.md` with `Plotting = running` under `AGENT-058`. | Do nothing until the repair row closes. | `unknown` | `n/a` |

## Commands Proposed

These are intentionally not executed in this task.

```bash
rm -rf tmp/mplconfig
rm -rf tmp/2026-06-11_feature_minor_loss_manifest_check tmp/2026-06-11_feature_minor_loss_smoke tmp/2026-06-11_feature_minor_loss_smoke_live tmp/2026-06-11_heat_summary_smoke tmp/2026-06-11_case_analysis_live_smoke
rm -rf tmp/2026-06-12_ethan_postprocessing_plot_smoke tmp/2026-06-12_ethan_postprocessing_plot_smoke_2 tmp/2026-06-12_ethan_postprocessing_plot_smoke_3 tmp/2026-06-12_ethan_postprocessing_plot_smoke_4 tmp/2026-06-12_ethan_postprocessing_plot_smoke_5 tmp/2026-06-12_ethan_postprocessing_campaign_smoke tmp/2026-06-12_ethan_postprocessing_campaign_smoke_campaign
rm -rf tmp/2026-06-11_case_analysis_raw_reuse_smoke tmp/2026-06-11_case_analysis_raw_reuse_smoke_v2 tmp/2026-06-11_case_analysis_raw_reuse_smoke_v3 tmp/2026-06-11_case_analysis_raw_reuse_smoke_v4
rm -rf tmp/2026-06-11_case_analysis_package_mismatch tmp/2026-06-11_case_analysis_package_mismatch_should_fail tmp/2026-06-11_case_analysis_raw_reuse_mismatch tmp/2026-06-11_case_analysis_raw_reuse_should_fail tmp/2026-06-11_case_analysis_raw_reuse_missing_heat_should_fail tmp/2026-06-11_case_analysis_raw_reuse_no_heat_should_fail
```

For the archive-first rows, prefer a dated archive destination rather than direct deletion.

## Commands Executed

- None. This task stopped at dry-run classification.

## Files Moved

- None.

## Files Deleted

- None.

## Follow-Up Risks

- The `duplicate output` classification is based on naming, timestamps, README structure, and file-family similarity, not a full byte-for-byte diff.
- Some `tmp_extract/` directories may still be referenced informally by notes or one-off local workflows outside this task scope.
- The active exclusions must remain frozen until `AGENT-058`, `AGENT-068`, `AGENT-070`, and `AGENT-071` close their owned paths.
