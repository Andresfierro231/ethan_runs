---
task: AGENT-428
date: 2026-07-15
role: Thesis / Presentation / Documentation / Figures
status: complete
---
# Definitions-First Outline and Figure-Only Correction

## User Correction

The user clarified that they wanted Markdown outlines and standalone figures, not actual PowerPoint files. They also emphasized that the outline must define advisor-unfriendly shorthand and modeling assumptions before presenting results.

## Actions

Created `reports/thesis_dossier/2026-07-15_integrated_weekly_powerpoint_outline_definitions_first.md`. The outline is Markdown only and puts the introductory material first:

- mission and scientific question,
- final-model runtime contract,
- definitions of M1/M1b/M2/M3, PM5, F6, H1, `h_proxy`, `Nu`, `f_D`, `K`, `UA`, and SEM,
- pressure/energy/error/uncertainty equations,
- predictive/calibrated/diagnostic/blocked evidence classes,
- boundary-mode ladder,
- then the numerical results and next gates.

Updated the existing integrated outline to point to the definitions-first Markdown outline and removed the companion PowerPoint line.

Regenerated the figure package README and summary so the package now states that it creates standalone SVG figures only. Deleted the PowerPoint deck-builder script and removed the generated `.pptx`, deck manifests, slide PNGs, and deck-rendered PNGs from the package.

## Current Deliverable Shape

- Markdown outline: `reports/thesis_dossier/2026-07-15_integrated_weekly_powerpoint_outline_definitions_first.md`
- Standalone figure package: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/`
- Key tables: `term_glossary.csv`, `equation_register.csv`, `figure_manifest.csv`

## Validation

- Figure generator passed.
- Focused tests passed: `3 passed`.
- Import JSON files validate.

## Guardrails

No PowerPoint file was created. Existing generated PowerPoint artifacts from the prior pass were removed. Native CFD solver outputs, registry/admission state, generated indexes, scheduler state, and external Fluid code were untouched.
