---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_fluid_temperature_periodicity_bracket_repair/
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/
  - work_products/2026-07/2026-07-17/2026-07-17_heater_source_leave_salt3_out_score/
tags: [fluid, temperature-periodicity, root-bracket, umx1, handoff]
related:
  - .agent/status/2026-07-18_TODO-FLUID-TEMP-PERIODICITY-BRACKET-REPAIR.md
  - .agent/journal/2026-07-18/fluid-temperature-periodicity-bracket-repair.md
  - imports/2026-07-18_fluid_temperature_periodicity_bracket_repair.json
task: TODO-FLUID-TEMP-PERIODICITY-BRACKET-REPAIR
date: 2026-07-18
role: Forward-pred/Thermal-modeling/Writer
type: handoff
status: complete
---

# Fluid Temperature Periodicity Bracket Repair Handoff

## Open First

1. `work_products/2026-07/2026-07-18/2026-07-18_fluid_temperature_periodicity_bracket_repair/README.md`
2. `work_products/2026-07/2026-07-18/2026-07-18_fluid_temperature_periodicity_bracket_repair/temperature_root_bound_audit.csv`
3. `work_products/2026-07/2026-07-18/2026-07-18_fluid_temperature_periodicity_bracket_repair/fluid_patch_contract.csv`
4. `work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/umx1_root_status_by_case.csv`
5. `work_products/2026-07/2026-07-17/2026-07-17_heater_source_leave_salt3_out_score/training_objective_by_lambda.csv`

## What Is Known

The UMX1 Salt3/Salt4 accepted-root failure is a Fluid temperature-periodicity
bracketing problem. The current `_temperature_scan_bounds()` upper bound is
about `550 K`; Salt3 and Salt4 still have positive residual at that bound, so
`solve_temperature_periodicity()` returns no bracket or too-large periodicity
instead of using the existing bisection path.

Audit result:

- Salt2 rows are already bracketed by current bounds: `3/9`.
- Salt3/Salt4 rows recover roots above the current upper bound: `6/9`.
- No audited row remains unbracketed before the audit ceiling.
- Salt3 recovered root temperatures are about `565.06 K`, `565.46 K`, and
  `566.90 K`.
- Salt4 recovered root temperatures are about `586.67 K`, `587.12 K`, and
  `588.76 K`.

AGENT-529 already documented the policy: finite rejected roots are
diagnostic-only. Do not admit or select from finite rejected rows.

## Current Blocker

The actual Fluid source patch was not applied because external
`tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py` is owned by active
external task `impl-2026-07-18-fluid-tswfc2-distributed-wall-fluid-api`.

## Next Task Sequence

1. Check both boards before editing:
   - `ethan_runs/.agent/BOARD.md`
   - `../cfd-modeling-tools/.agent/BOARD.md`
2. When `solver.py` is free, claim a non-conflicting external Fluid row for the
   narrow patch.
3. Apply the `fluid_patch_contract.csv` requirement:
   - target function: `solve_temperature_periodicity()`
   - after initial no-bracket scan, if both endpoint residuals have the same
     sign, expand the relevant temperature bound in bounded increments
   - stop at a sign change or hard ceiling
   - reuse the existing bisection path once a bracket is found
4. Preserve invariants:
   - no `ScenarioConfig` API change
   - no `TEMPERATURE_PERIODICITY_TOL_K` change
   - no pressure-root gate change
   - no validity gate change
   - no UMX conservation or split-discipline change
   - no admission-policy change
5. Run Fluid-side validation from `../cfd-modeling-tools/tamu_first_order_model/Fluid`:
   - `python -m pytest tests/test_solver_contracts.py -q -k 'temperature or scenario_config_defaults_match_active_solver_contract'`
   - `python -m py_compile tamu_loop_model_v2/solver.py tamu_loop_model_v2/config_loader.py tests/test_solver_contracts.py`
6. Return to `ethan_runs` and rerun strict UMX1 smoke validation:
   - rerun `tools/analyze/build_umx1_dry_smoke_scorer.py --run-smoke --engine fast_scan`
   - require `umx1_root_status_by_case.csv` to improve from `3/9` root pass to
     `9/9`
   - require conservation to remain `9/9`
   - keep `admission_status=not_admitted_smoke_only`
7. Only after strict smoke passes should a separate task consider a broader
   grid or full `solve_case` confirmation.

## Do Not Do

- Do not relax accepted-root tolerance.
- Do not use finite rejected roots for selection or admission.
- Do not change UMX multipliers to hide a solver root issue.
- Do not launch a broader Fluid grid before strict smoke roots and conservation
  pass.
- Do not edit external Fluid source while another active row owns `solver.py`.
