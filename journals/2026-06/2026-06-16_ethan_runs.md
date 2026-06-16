# Ethan Runs Update

Date: 2026-06-16

## Observed Outputs

- Promoted the five core Salt paper figures from the June 15 report packages
  into the manuscript workspace at `../papers/3d_analysis/figures/`:
  - `fig_salt_family_heat_loss.pdf`
  - `fig_salt_family_azimuthal_means.pdf`
  - `fig_salt2_friction_pressure.pdf`
  - `fig_salt2_thermal_resistance.pdf`
  - `fig_salt2_boundary_landmarks.pdf`
- Added the first four paper-side LaTeX tables under
  `../papers/3d_analysis/tables/`:
  - `table_salt_case_matrix.tex`
  - `table_artifact_provenance.tex`
  - `table_salt2_matched_case_summary.tex`
  - `table_trust_boundaries.tex`
- Rewired the `3d_analysis` manuscript sections so the Salt-family results
  section now uses imported field-transport campaign figures and the matched
  Salt 2 mechanism section now uses imported trio figures plus a matched-case
  summary table.
- Updated the paper-side provenance records:
  - `../papers/3d_analysis/notes/asset_import_log.md`
  - `../papers/3d_analysis/notes/paper_journal.md`
  - `../papers/3d_analysis/appendices/app_a_evidence_and_provenance_map.tex`

## Interpretation

- The `3d_analysis` paper is no longer just an outline scaffold. It now has
  the actual core Salt figures and first-pass paper tables needed to support
  the central storyline.
- The manuscript evidence hierarchy is now materially encoded in the repo:
  - the Salt-family field-transport campaign is the broad trend layer
  - the matched Salt 2 representative transport package is the mechanism layer
  - the June 15 monitor-first handoff remains the maturity and trust-limit
    layer
- Moving the tables into the manuscript repo is useful because it fixes the
  paper-side wording and provenance boundaries in the same place as the draft
  text, rather than leaving them implicit in the analysis repo.

## Contradictions / Caveats

- The paper still remains Salt-only in this first serious draft pass. Water is
  intentionally not being folded into the storyline yet.
- The imported matched Salt 2 figures still carry the established caveats:
  - validation retained times are `8598-8602 s`
  - effective thermal metrics are QC-masked upstream
  - boundary-layer landmarks remain first-pass comparative diagnostics
- The new manuscript tables are paper-facing summaries, not new analysis
  outputs. Their authority still depends on the June 15 report packages named
  in the provenance log.

## Suggested Next Actions

- Expand the current outline prose into fuller methods and results text now
  that the core figures and first tables are present.
- Decide whether any per-case support figures should move into an appendix
  import pass, especially if local heat-loss or per-case hydraulic examples are
  needed.
- Keep the trust-boundary wording conservative as the prose grows; the new
  table imports should prevent the draft from drifting into stronger claims
  than the June 15 packages actually support.

## Checkpoint

- Manuscript-side imports and tables now exist under `../papers/3d_analysis/`.
- The next paper pass should focus on prose expansion, not storyline
  redefinition.
