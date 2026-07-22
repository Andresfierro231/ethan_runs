---
provenance:
  generated_by: tools/analyze/build_mf11_empirical_f2_f5_physical_attribution_gate.py
  task_id: TODO-MF11-EMPIRICAL-F2-F5-PHYSICAL-ATTRIBUTION-GATE-2026-07-22
  generated_at_utc: 2026-07-22T14:04:10.220341+00:00
task: TODO-MF11-EMPIRICAL-F2-F5-PHYSICAL-ATTRIBUTION-GATE-2026-07-22
tags:
  - journal
  - MF11
  - empirical-bias
related:
  - work_products/2026-07/2026-07-22/2026-07-22_mf11_empirical_f2_f5_physical_attribution_gate
---

# MF11 empirical F2/F5 physical attribution gate

## Attempted

Joined the empirical F2/F5 publication package to completed D2/D3/D4 and
MF07/MF08/MF09 source-basis gates, then classified whether the empirical
coefficients can be tied to physical residual owners.

## Observed

F2 and F5 both reduce transfer error strongly, but every candidate physics lane
that could explain those coefficients is still diagnostic-only, source-basis
blocked, mesh/GCI blocked, or runtime-input blocked.

## Inferred

The correct claim is empirical diagnostic attribution. The coefficients help
rank physical hypotheses, but no unique physical attribution or closure release
is supportable.

## Contradictions or Caveats

F5 being numerically best does not make it the best scientific model; its extra
degrees of freedom can absorb several unresolved mechanisms at once. F2 being
low-DOF and transferable makes it useful for publication, not admissible as a
temperature-scale law.

## Next Useful Actions

Use MF11 to prioritize MF10 only after source-basis gates are released; otherwise
continue same-label mesh-family/source-property work for S13 and signed source
basis for MF08.
