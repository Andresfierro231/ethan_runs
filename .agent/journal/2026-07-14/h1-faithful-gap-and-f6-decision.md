---
task: AGENT-333
date: 2026-07-14
role: Hydraulics / Implementer / Tester / Writer
status: complete
---
# H1 Faithful Gap And F6 Decision

Read the project mission, friction map, pressure/momentum map, H1 scorecard,
hydraulic correction candidates, current blocker register, AGENT-318 Fluid/F6
bridge outputs, and AGENT-328 localized fixed-K score.

The decisive new evidence is AGENT-328: localized fixed-K-only scoring through
the Fluid hook worsened F1 mean mdot error by `6.78%` versus baseline. That
means the aggregate H1 proxy should not be treated as a faithful closure.

Outcome:

- H1 current forms are retired as proxy-only.
- The faithful H1 path is blocked on reset/development semantics, component vs
  cluster vs branch-apparent separation, centerline tap lengths, mesh/admission
  status, and recirculation-invalid coefficient labeling.
- `F6_phi_re` is selected as the next bounded candidate after admitted
  Re-variation evidence exists.

No thermal fitting, native CFD mutation, or global friction multiplier was used.
