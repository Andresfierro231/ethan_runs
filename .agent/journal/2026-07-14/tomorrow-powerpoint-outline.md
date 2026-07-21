---
task: AGENT-364
date: 2026-07-14
role: Thesis / Presentation / Writer
status: complete
---
# Tomorrow PowerPoint Outline

Built `reports/thesis_dossier/2026-07-15_powerpoint_outline.md` as the
presentation assembly guide for the July 15 meeting.

## Sources Used

- Project mission and scientific questions note.
- Current thesis/presentation story sync.
- Upcomer recirculation/internal-Nu story update.
- LitRev lessons and model-form crosswalk.
- Scientific closure / forward-v1 execution dashboard.
- Forward-v1 +/-5Q / hydraulic delta.
- Corrected-Q +/-5Q admission/split processing.
- Flow-rate / temperature / boundary-condition paper analysis.
- Best predictive heat-loss discrepancy presentation brief.
- Fluid reset/development API closeout.

## Story Decisions

- Lead with admission-gated progress rather than a raw activity list.
- Present final forward-v1 as `blocked_no_go_final_forward_v1_not_admitted`,
  but make the blocker path actionable.
- Present heat-loss placement as the strongest central visual result: aggregate
  heat balance can look close while losses are assigned to the wrong physical
  regions.
- Present upcomer recirculation as a scientific/admission result, not merely
  "Nu blocked."
- Keep corrected +/-5Q rows as terminal-harvested perturbation evidence with
  `0` independent training expansion rows.
- Separate implementation progress, such as the Fluid reset/development API,
  from admitted hydraulic closure.

## Artifact Notes

Several better figures should be made before the live presentation:

- loop schematic with branch labels;
- evidence-ladder/gate dashboard;
- split-aware +/-5Q admission matrix;
- grouped bar chart from `best_predictive_leg_heat_loss_discrepancy.csv`;
- pressure-loss ledger schematic;
- upcomer recirculation plane schematic;
- forward-v1 gate funnel.

No solver outputs, scheduler state, registry/admission state, generated
indexes, or external Fluid sources were modified.
