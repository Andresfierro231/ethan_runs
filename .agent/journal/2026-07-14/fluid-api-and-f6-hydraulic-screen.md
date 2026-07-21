---
task: AGENT-318
date: 2026-07-14
role: Implementer/Tester/Writer
status: complete
---
# Fluid API And F6 Hydraulic Screen

Implemented the remaining executable blocker work from the plan in two lanes:

1. F6 hydraulic screen:
   - generated `2026-07-14_f6_hydraulic_screen`;
   - confirmed `F6_phi_re` exists in Fluid;
   - kept F6 screen-only because current evidence has zero publication-ready
     GCI rows and no corrected-Q admitted rows for coefficient revision;
   - preserved the H1 conclusion that mdot can move toward CFD without thermal
     fitting.

2. Fluid bridge:
   - made localized fixed K reachable from minor-loss YAML presets;
   - added external-boundary setup-parity mappings and diagnostics;
   - parsed/round-tripped F6-related scenario fields.

No native CFD outputs were mutated. No thermal fitting was used. No global
friction multiplier was introduced to hide named losses.
