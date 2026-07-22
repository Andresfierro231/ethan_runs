---
provenance:
  - reports/thesis_dossier/2026-07-15_powerpoint_outline.md
  - tools/analyze/build_2026_07_15_powerpoint_deck.py
  - work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/case_bc_response_matrix.csv
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_split_admission_matrix.csv
  - work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/best_predictive_leg_heat_loss_discrepancy.csv
  - work_products/2026-07/2026-07-14/2026-07-14_scientific_closure_forward_v1_execution_dashboard/gate_landing_requirements.csv
tags: [thesis-dossier, weekly-presentation, figures, powerpoint, forward-v1]
related:
  - reports/thesis_dossier/2026-07-15_powerpoint_outline.md
  - reports/thesis_dossier/2026-07-15_powerpoint_deck.pptx
task: AGENT-367
date: 2026-07-14
role: Thesis/Presentation/Implementer/Writer
type: work_product
status: complete
---
# PowerPoint Figures And Deck

This package turns the `2026-07-15_powerpoint_outline.md` better-figure requests
into reproducible assets and an image-backed PowerPoint deck.

## Outputs

- `figures/*.png`: standalone presentation figures.
- `slides/*.png`: full-slide rendered images used inside the deck.
- `2026-07-15_powerpoint_deck.pptx`: package-local PowerPoint copy.
- `reports/thesis_dossier/2026-07-15_powerpoint_deck.pptx`: thesis-dossier
  PowerPoint copy.
- `figure_manifest.csv`: generated figure index.
- `summary.json`: machine-readable output summary.

## How The Better Figures Are Created

| Figure | Creation method | Main source |
| --- | --- | --- |
| Loop schematic | Matplotlib schematic with branch labels. | Outline branch list. |
| Predictive contract | Matplotlib block diagram showing setup inputs, model outputs, and forbidden runtime inputs. | Mission note and outline. |
| Evidence ladder | Matplotlib ladder/table from the project evidence vocabulary. | Thesis/story sync and LitRev crosswalk. |
| Gate dashboard | Matplotlib status dashboard from the forward-v1 workstream dashboard. | `workstream_execution_dashboard.csv`. |
| +/-5Q split matrix | Matplotlib table from the split-aware corrected-Q matrix. | `corrected_q_pm5_split_admission_matrix.csv`. |
| Flow/temperature ordering | Matplotlib scatter/line chart from mainline Salt2/3/4 rows. | `case_bc_response_matrix.csv`. |
| Confounding diagram | Matplotlib causal schematic plus false-steady perturbation warning. | Flow/temperature paper analysis. |
| Heat-loss leg chart | Matplotlib grouped bar chart averaging Salt2-4 leg losses. | `best_predictive_leg_heat_loss_discrepancy.csv`. |
| Thermal ledger | Matplotlib schematic separating heater, HX, wall, radiation, storage, and residual lanes. | Boundary/HX/wall model notes. |
| Pressure ledger | Matplotlib term ledger for straight friction, reset/development, component K, cluster K, buoyancy/kinetic, and residual. | Hydraulic delta/API evidence. |
| Upcomer recirculation | Matplotlib plane schematic with forward and reverse-flow regions and current regime metrics. | Upcomer recirculation story. |
| Residual ownership | Matplotlib diagram of residuals forbidden from being hidden inside internal Nu. | Internal-Nu guardrails. |
| Forward-v1 gate funnel | Matplotlib funnel from gate requirements. | `gate_landing_requirements.csv`. |
| Next-work roadmap | Matplotlib two-lane roadmap. | Outline next-work slide. |
| Blocker table | Matplotlib open/stale blocker table. | `.agent/BLOCKERS.md` wording from outline. |
| LitRev crosswalk | Matplotlib grouped summary from tried-status classes. | `litrev_to_current_evidence_crosswalk.csv`. |
| Say/Avoid table | Matplotlib claim-boundary table. | Outline backup slide. |

## Rebuild

Run:

```bash
python3.11 tools/analyze/build_2026_07_15_powerpoint_deck.py
```

The script writes both the package-local deck and the thesis-dossier deck. It
uses Matplotlib/Pandas/Pillow and writes a minimal OOXML `.pptx` directly
because `python-pptx` is not installed in this environment.

## Guardrails

- The deck uses generated slide images, so PowerPoint text and plots are not
  independently editable objects.
- Speaker notes remain in
  `reports/thesis_dossier/2026-07-15_powerpoint_outline.md`.
- No native CFD solver outputs, registry/admission state, scheduler state,
  generated indexes, or external Fluid sources were modified.
