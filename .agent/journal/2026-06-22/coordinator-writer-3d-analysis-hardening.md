# AGENT-096 Journal

Date: `2026-06-22T11:27:11-05:00`
Role: `Coordinator / Writer`
Task: `AGENT-096`

## Intent

Turn `../papers/3d_analysis` from an outline-first Salt paper scaffold into a
scientifically solid draft that external technical readers can follow without
already knowing the repo.

## Observed state at start

- The manuscript already has the figure assets and several table fragments.
- The abstract still says the paper is an outline-first scaffold.
- Every major section still contains `\FillTarget{...}` guidance and
  outline-language such as “this section should”.
- The Salt evidence path is strong enough to draft a real main-text paper from
  the current report packages.
- Water evidence is present and useful for methods/setup/trust context, but it
  still does not support co-equal defended main-text transport claims.
- The setup-modeling audit under
  `reports/2026-06-15_ethan_boundary_modeling_report/README.md`
  now contains a direct case-assembly map that can be promoted into the paper.

## Planned action

- Keep Salt as the main-text result layer.
- Replace the scaffold prose in the abstract, sections, and appendices with
  real manuscript text grounded in existing report packages.
- Add manuscript-native quantitative tables for:
  - Salt family case matrix refresh
  - Salt family quantitative trend summary
  - matched Salt 2 comparison summary
  - trust boundaries
  - artifact provenance
  - Water support matrix
- Add a bounded Water appendix/context layer rather than broadening the main
  paper into a full Salt+Water results manuscript.

## Current blocker

- The paper tree sits outside the writable workspace, so direct manuscript
  edits require an outside-workspace write path before the drafting pass can
  land there.

## Completion

- Claimed the missing `frontmatter/metadata.tex` scope locally before editing
  so the manuscript title could stop advertising itself as an outline scaffold.
- Used the existing Salt campaign CSVs, representative Salt 2 CSVs, the June 18
  promotion gate, the June 16 boundary-modeling audit, and the June 19 Water
  readiness handoff to rewrite the manuscript as a real draft rather than a
  planning scaffold.
- Added two new paper tables:
  - `table_salt_family_quantitative_summary.tex`
  - `table_water_support_matrix.tex`
- Rebuilt the Salt 2 matched-case table as a compact quantitative mechanism
  table and tightened the case-matrix / provenance-table layouts after the
  first compile exposed width warnings.
- Reframed Appendix B from an internal drafting-aid list into a durable
  support-and-future-work appendix that documents the Water exclusion boundary.

## Validation

- Placeholder scan after the write pass showed no remaining scaffold markers in
  the source `.tex` files; only stale generated `.aux` / `.toc` entries matched
  before the rebuild refreshed them.
- `module load texlive/2023 && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`
  completed successfully in `../papers/3d_analysis`.
- Residual TeX output is limited to non-fatal underfull-box warnings in dense
  tables and long appendix rows. The new Salt 2 quantitative table no longer
  triggers the earlier `tabularx` width warning.
