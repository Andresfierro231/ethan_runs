---
task: AGENT-367
date: 2026-07-14
role: Thesis / Presentation / Implementer / Writer
status: complete
---
# PowerPoint Figures And Deck

Created a reproducible figure/deck package from the July 15 presentation
outline. The output deck is stored at
`reports/thesis_dossier/2026-07-15_powerpoint_deck.pptx`.

## Figure Strategy

The "better figure" requests were converted into two classes:

- data-driven charts/tables from existing CSVs, including corrected +/-5Q split
  status, mainline `mdot` versus probe temperature, heat-loss by physical leg,
  forward-v1 gate requirements, and LitRev tried-status groups;
- schematic figures for concepts that need visual explanation but do not yet
  have admitted field data, including the loop branch map, predictive-input
  contract, thermal ledger, pressure ledger, upcomer recirculation plane,
  residual ownership, and next-work roadmap.

## Important Limits

- The PowerPoint is image-backed, not object-editable, because `python-pptx`
  is not installed.
- The generated upcomer figure is a schematic; replace it with admitted
  matched-plane extraction when AGENT-344/357/363 successor outputs are parsed
  and admitted.
- Heat-loss and flow/temperature figures remain diagnostic/observational; they
  are not final predictive validation claims.

## Files

- `tools/analyze/build_2026_07_15_powerpoint_deck.py`
- `work_products/2026-07/2026-07-14/2026-07-14_powerpoint_figures_and_deck/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_powerpoint_figures_and_deck/figure_manifest.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_powerpoint_figures_and_deck/figures/*.png`
- `work_products/2026-07/2026-07-14/2026-07-14_powerpoint_figures_and_deck/slides/*.png`
- `work_products/2026-07/2026-07-14/2026-07-14_powerpoint_figures_and_deck/2026-07-15_powerpoint_deck.pptx`
- `reports/thesis_dossier/2026-07-15_powerpoint_deck.pptx`

No native CFD solver output, registry/admission state, scheduler state,
generated index, or external Fluid source was modified.
