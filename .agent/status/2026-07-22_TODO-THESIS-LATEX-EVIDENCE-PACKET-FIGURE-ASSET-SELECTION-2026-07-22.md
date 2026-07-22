---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_latex_evidence_packet_figure_asset_selection/README.md
  - ../papers/UTexas_Research/csem-Masters_dissertation/evidence/figure_asset_selection/README.md
tags: [thesis, figures, evidence, asset-selection, no-binary-import]
related:
  - .agent/journal/2026-07-22/thesis-latex-evidence-packet-figure-asset-selection.md
  - imports/2026-07-22_thesis_latex_evidence_packet_figure_asset_selection.json
task: TODO-THESIS-LATEX-EVIDENCE-PACKET-FIGURE-ASSET-SELECTION-2026-07-22
date: 2026-07-22
role: Coordinator/Figures/Writer/Reviewer/Integrator
status: complete
---
# TODO-THESIS-LATEX-EVIDENCE-PACKET-FIGURE-ASSET-SELECTION-2026-07-22

## Objective

Import a compact figure-asset selection manifest into the thesis repo without
copying binary figure files or editing chapter prose.

## Outcome

Complete.  The thesis repo now contains:

`evidence/figure_asset_selection/`

with a candidate figure ledger, copy/no-copy decision table, and external
writer brief.

## Changes Made

- Created local packet:
  `work_products/2026-07/2026-07-22/2026-07-22_thesis_latex_evidence_packet_figure_asset_selection/`.
- Imported compact manifest files into:
  `../papers/UTexas_Research/csem-Masters_dissertation/evidence/figure_asset_selection/`.
- Updated the thesis evidence README to link the figure-selection packet.
- Added papers-side status/journal and a Done Awaiting Review row for
  `csem-latex-evidence-figure-asset-selection-2026-07-22`.

## Changes Made Details

The manifest identifies high-value figure candidates:

- Salt1-Salt4 upcomer `U_y` side-Z composite.
- Salt1-Salt4 upcomer velocity-magnitude side-Z composite.
- S12 residual-owner waterfall SVG.
- S13 predictive-path-status SVG.
- Model-form ladder SVG.
- Blocked-scorecard waterfall SVG.
- M3 TP/TW temperature-vs-elevation diagnostic panels for Salt2-Salt4.

## Validation

- `python3.11 -m py_compile work_products/2026-07/2026-07-22/2026-07-22_thesis_latex_evidence_packet_figure_asset_selection/apply_papers_figure_asset_selection_packet.py`: PASS
- CSV parse check for `figure_candidate_ledger.csv` and `copy_decision_table.csv`: PASS
- `git diff --check -- work_products/2026-07/2026-07-22/2026-07-22_thesis_latex_evidence_packet_figure_asset_selection .agent/BOARD.md`: PASS
- `python3.11 work_products/2026-07/2026-07-22/2026-07-22_thesis_latex_evidence_packet_figure_asset_selection/apply_papers_figure_asset_selection_packet.py`: PASS
- `find ../papers/UTexas_Research/csem-Masters_dissertation/evidence/figure_asset_selection -maxdepth 1 -type f | sort`: PASS; 4 compact files present
- `git -C ../papers/UTexas_Research/csem-Masters_dissertation diff --check -- evidence`: PASS
- `scripts/check_guardrails.sh` in the CSEM thesis repo: PASS
- `scripts/build_thesis.sh` in the CSEM thesis repo: PASS

## Guardrails

- Thesis chapter body `.tex` prose edited: no.
- Binary figure files copied: no.
- Raw CFD/OpenFOAM output copied: no.
- Native CFD/OpenFOAM output mutated: no.
- Registry/admission/scheduler/Fluid state mutated: no.
- Coefficient admission: no.
- Final predictive score claimed: no.
- Runtime-leakage rules relaxed: no.
- Generated documentation index refreshed: no.

## Next Actions

Open a separate final figure import row only after the user chooses the exact
assets to copy into the thesis repo.  The likely first binary import is the
Salt upcomer `U_y` side-Z composite and/or the velocity-magnitude side-Z
composite.
