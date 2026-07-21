---
provenance:
  - operational_notes/07-26/20/2026-07-20_THESIS_RECIRCULATION_IMAGE_CANDIDATES.md
  - figures/figures_rendered/paraview_field_families/upcomer/y_vel/
  - figures/figures_rendered/paraview_velocity_arrows/
tags: [journal, thesis, figures, recirculation, upcomer]
related:
  - .agent/status/2026-07-20_AGENT-562.md
  - imports/2026-07-20_thesis_recirculation_image_candidates.json
task: AGENT-562
date: 2026-07-20
role: Writer/Figures/Coordinator
type: journal
status: complete
---
# Thesis Recirculation Image Candidates

Task: AGENT-562

## Attempted

Converted the chat-discovered recirculation/upcomer image list into a durable
operational note for later thesis figure work.

## Observed

There are existing real CFD visual assets under the rendered ParaView upcomer
field-family and velocity-arrow directories. There are also slide-friendly
recirculation schematics, quantitative recirculation/onset plots, and an
editable thesis schematic at `reports/thesis_dossier/figures/svg/F03_upcomer_hybrid_schematic.svg`.

## Inferred

The likely thesis figure strategy is to pair one real CFD upcomer field/arrow
visual with the current conceptual `F03` hybrid schematic. Quantitative plots
can support the text or appendix, but should not be used to imply final
ordinary-pipe closure admission.

## Caveats

Some rendered images are historical or illustrative. A later thesis figure row
should verify case selection, caption wording, and export format before using
them in the final document.

## Next Useful Actions

When `TODO-THESIS-FIGURES-DIAGRAMS` is claimed, open the candidate note first,
select one real CFD visual and one schematic, and preserve exact source paths in
the figure manifest or caption notes.
