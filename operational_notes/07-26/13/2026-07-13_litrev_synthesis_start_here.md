# Lit-Rev Synthesis Start Here

Date: `2026-07-13`

Task: `AGENT-285`

Tags: #litrev-synthesis #closure-ledger #source-envelope #property-sensitivity
#cfd-to-1d #heat-loss #minor-loss #research-pathways

## Why This Exists

`AGENT-282` converted the HITEC closure literature review into a practical
lessons-learned and research-pathways package. This note is the lightweight
index that makes the package visible from the current thermal-parity and
CFD-to-1D documentation cluster.

## Open First

1. `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md`
   - Main narrative.
   - Lessons learned.
   - Model forms to carry forward.
   - Things to try.
   - Highest-value near-term work.

2. `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/research_pathways.csv`
   - Board-ready research ideas.
   - Expected products.
   - Author/title provenance.
   - Acceptance gates.

3. `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/summary.json`
   - Machine-readable package index.

## Board Rows Added

The following unclaimed rows were added to `.agent/BOARD.md` under
`Planned / Unclaimed`:

- `TODO-LITREV-SOURCE-ENVELOPE`
- `TODO-LITREV-PROPERTY-SENSITIVITY`
- `TODO-LITREV-RESET-NAMED-LOSSES`
- `TODO-LITREV-HEAT-LOSS-CALIBRATION`
- `TODO-LITREV-CFD-VALIDITY-DIAGNOSTICS`

These are deliberately unclaimed. A future worker should claim one row at a
time, create a task-specific status/journal/import set, and stay inside that
row's allowed paths.

## How To Use The Synthesis

Use the lit-rev package as a gate before promoting a model form:

- source-envelope overlap before active use of a source-bounded correlation;
- property sensitivity before fitting pressure or heat residuals;
- reset-distance and named-loss extraction before global friction calibration;
- separated heat-loss calibration before internal `Nu` tuning;
- invalid-single-stream CFD diagnostics before exporting section coefficients.

## Related

- `operational_notes/07-26/10/2026-07-10_NEXT_MEETING_START_HERE.md`
- `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/README.md`
- `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md`
- `.agent/BOARD.md`
