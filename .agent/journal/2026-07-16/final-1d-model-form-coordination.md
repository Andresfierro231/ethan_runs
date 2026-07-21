---
task: AGENT-465
date: 2026-07-16
role: Coordinator/Writer
type: journal
status: complete
tags: [coordination, final-1d-model, wall-thermal-circuit, upcomer-recirculation]
related:
  - .agent/BOARD.md
  - .agent/status/2026-07-16_AGENT-465.md
  - reference/geometry_reference.md
---
# Final 1D Model Form Coordination

User and Codex discussed the final 1D model form. The key carried-forward modeling principle is that each segment carries its own pressure model, thermal model, boundary-loss model, source/sink role, validity flags, and uncertainty/admission status.

Observed from the board: test-section heat-loss modeling, segment pressure/thermal scorecards, coupled M3+TS, TP2 restoration, upcomer hybrid modeling, branch-specific ordinary-pipe scoring, and boundary-layer development already have planned rows or active implementations.

Observed from `reference/geometry_reference.md`: the test section is explicitly the middle upcomer span (`left_lower_leg -> test_section_span -> left_upper_leg`), with `test_section_span = pipeleg_left_04`.

Two gaps were added to the board:

- `TODO-PREDICT-WALL-THERMAL-CIRCUIT`: make the fluid-to-ambient thermal circuit explicit, including internal convection with boundary-layer/development flags, wall/quartz/insulation conduction, and external convection plus radiation using CFD setup values.
- `TODO-THESIS-UPCOMER-RECIRCULATION-SECTION`: write a thesis/paper-ready section explaining why the upcomer needs a throughflow-plus-recirculation-cell model rather than ordinary single-stream coefficient fitting.

No native CFD outputs, registry files, scheduler state, generated indexes, or external Fluid source were changed.
