---
provenance:
  - tools/analyze/build_mf12_bulk_to_tp_formula_gate.py
  - work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/summary.json
tags: [journal, mf12, bulk-to-tp]
related:
  - .agent/status/2026-07-22_TODO-MF12-BULK-TO-TP-FORMULA-GATE-2026-07-22.md
  - imports/2026-07-22_mf12_bulk_to_tp_formula_gate.json
task: TODO-MF12-BULK-TO-TP-FORMULA-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# MF12 Bulk-to-TP Formula Gate

## Attempted

Implemented a reproducible source-basis gate for converting the D2/MF07
bulk-to-TP residual signal into a physically admissible model form.

## Observed

M3 is cold against all five available Salt2 train TP rows. D2 strongly improves
TP transfer RMSE relative to M3. This is evidence that a bulk-to-probe
projection/development term is worth modeling before trying to explain all TW
residuals.

MF08 provides physically sensible heat signs, but source/property release is
still absent. D3/D4 support wall-shape and source-placement interpretations,
but those are also diagnostic only.

## Inferred

The right next model form is a source-bounded TP projection:

```text
T_TP = T_bulk + sigma_q A_source Phi(Gz, x/D, reset, BC)
```

or a piecewise source-memory integral. Both are still blocked because the
source amplitude, property basis, TP projection UQ, and runtime wall/profile
basis are not released.

## Contradictions And Caveats

A formula can be written, but writing it is not the same as admitting it. The
strong D2/F2/F5 empirical evidence must remain diagnostic until the source and
projection gates pass.

The failed `bash -n` validation attempt was not a code failure; it was the
wrong validator for Python files. `python3.11 -m py_compile` passed.

## Next Useful Actions

Claim the signed source/property heat-path release preflight, then same-QOI TP
projection UQ, then runtime wall-profile basis. Only after those pass should
MF12 run a train/support-only formula smoke test.

## Guardrails

No fitting, protected scoring, source/property release, coefficient admission,
Fluid solve, scheduler action, native-output mutation, registry/admission
mutation, thesis edit, generated-index refresh, or residual absorption into
internal Nu occurred.
