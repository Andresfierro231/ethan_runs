---
task: AGENT-429
date: 2026-07-15
role: Thesis / Presentation / Documentation / Figures
status: complete
---
# Loop Schematic Physical Leg Label Fix

## Issue

The previous `fig01_loop_schematic.svg` was a high-level model-flow diagram. It showed heater, test section, cooler, and pressure solve blocks, but it did not explicitly identify the physical loop legs or junction regions. That made it less useful for an advisor-facing intro slide.

## Fix

Updated `tools/analyze/build_integrated_powerpoint_figures_and_definitions.py` so `fig01_loop_schematic.svg` is a physical loop topology sketch. It now labels:

- upcomer / test section,
- downcomer,
- cooling leg / cooler branch,
- heated lower leg,
- lower, upper, cooler, and return junctions,
- mdot plane,
- TP/TW probes.

Also updated the figure manifest caption and README caption to say the schematic includes named legs and junctions.

## Validation

Regenerated the figure package and added a regression test ensuring the physical labels are present in `fig01_loop_schematic.svg`. Focused tests passed with `4 passed`.

## Guardrails

No PowerPoint was created. No native CFD outputs, registry/admission state, generated indexes, scheduler state, or external Fluid code were changed.
