# Ethan Runs Update

Date: 2026-06-12

## Observed Outputs

- Added `tools/analyze/build_ethan_run_postprocessing_package.py` to package one
  registered Ethan CFD run into tables, figures, artifact maps, and dual-layer
  narrative reports.
- Added `tools/analyze/build_ethan_postprocessing_campaign.py` to orchestrate
  the full 13-run build into the canonical cross-model publication tree.
- Built the canonical campaign at
  `../cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/`.
- The campaign now contains:
  - one per-run package for each of the 13 registered CFD cases
  - campaign-level `run_index.csv`, `readiness_matrix.csv`, and
    `cross_run_summary.csv`
  - campaign-level executive, technical, and methodology reports
  - CSV-backed `svg`, `pdf`, and PGFPlots/TikZ figure exports for both
    per-run and cross-run plots
  - a markdown and JSON artifact map for every run

## Interpretation

- The repository now has a reproducible monitor-first reporting path that moves
  Ethan-run postprocessing into the canonical `cross_model_comparison`
  publication home instead of leaving the analysis fragmented across local
  staging and ad hoc report directories.
- The build is broad enough to support paper drafting structure now:
  every run has a setup/runtime/velocity/temperature/heat-transfer/wall-quality
  interpretation layer, and the campaign adds a uniform cross-run comparison
  frame.
- The current campaign is strongest as a manuscript backbone for trends,
  maturity labeling, and monitor-derived thermal/flow comparison. It is not yet
  a full field-reconstruction paper pass.

## Contradictions / Caveats

- Pressure remains an explicit boundary in this v1 campaign because the native
  labeled `postProcessing` stack does not publish direct pressure histories for
  these runs.
- The campaign includes all 13 registered runs, but only `3` are currently
  labeled `comparison_candidate`; the other `10` are carried as
  `convergence_audit_required` rather than being silently dropped.
- Runtime status remains mixed across the registered set:
  `{'running': 1, 'terminated': 10, 'completed': 2}`.
- Existing rendered figures were reused where already available, but this pass
  intentionally did not launch new OpenFOAM or ParaView field reconstruction.

## Suggested Next Actions

- Run a focused reviewer pass on representative water, Salt Jin, and Salt Kirst
  packages to verify that the per-run prose stays disciplined relative to the
  exported monitor evidence.
- If stronger paper claims need pressure or field-shape arguments, open a phase-2
  campaign that reconstructs those outputs explicitly instead of stretching the
  monitor-only interpretation boundary.
- Use the new per-run artifact maps as the citation backbone when drafting a
  manuscript section, so every claim can point back to the exact table, figure,
  and source postProcessing path.

## Checkpoint / Stopping Point

- The canonical all-run package exists at
  `../cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/`.
- Cross-model checkpoint and workflow-journal provenance were written alongside
  the campaign.
- Local provenance for this interpretive pass now exists in:
  - `imports/2026-06-12_ethan_postprocessing_campaign.json`
  - `.agent/status/2026-06-12_AGENT-056.md`
  - `.agent/journal/2026-06-12/coordinator-implementer-ethan-postprocessing-campaign.md`
