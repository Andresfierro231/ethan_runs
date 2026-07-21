---
provenance:
  task: AGENT-419
  generated_by: codex
tags: [journal, recirculation-policy, coefficient-labels, forward-v1, hydraulics]
related:
  - .agent/status/2026-07-15_AGENT-419.md
  - work_products/2026-07/2026-07-15/2026-07-15_recirculation_policy_forward_hydraulic_unblock_plan/README.md
---
# Recirculation Policy Forward/Hydraulic Unblock Plan

Date: 2026-07-15
Task: AGENT-419

This task converted the current PM5 and raw two-tap evidence into explicit
admission rules. The central rule is that material reverse area or reverse mass
fraction invalidates true single-stream coefficient labels for fitting. Such
rows may be useful as diagnostics, but only with section-effective names.

The policy uses these formulas:

- `RAF = A(U_axial < 0) / A_total`.
- `RMF = |sum(rho U_axial dA for U_axial < 0)| / sum(|rho U_axial| dA)`.
- `SVF = area-mean ||U_secondary|| / area-mean ||U||`.
- `Ri = Gr / Re^2`.
- `h_proxy = q_wall'' / (T_wall - T_bulk)`.

Fit admission for true single-stream `Nu`, `f_D`, or component `K` defaults to
`RAF < 0.01` and `RMF < 0.01`, plus sign, pressure, heat-balance, boundary,
source-path, and mesh/GCI gates. Rows with `RAF >= 0.20` or `RMF >= 0.20` are
diagnostic-only for true coefficients.

The generated current-evidence classification has 15 rows: 12 AGENT-406 PM5 rows
and 3 AGENT-409 raw two-tap rows. All 15 are `diagnostic_only` and
`fit_admissible=no`. This is why neither final forward-v1 nor final hydraulic
residual attribution is unlocked today.

The shortest next executable path is:

1. Score the setup-only HX/cooler model with Salt2 fit, Salt3 validation, and
   Salt4 holdout.
2. Build a raw pressure admission package with admitted pressure definition,
   tap orientation, straight-loss subtraction, and mesh/GCI.
3. Refresh PM5/F6 pressure-onset review under the new coefficient-label policy.
4. Keep internal-Nu closed to fitting until low-recirculation, positive-sign,
   heat-balance-admitted, mesh/GCI rows exist.

No native CFD outputs, scheduler state, registry/admission files, generated
indexes, or external Fluid files were mutated.
