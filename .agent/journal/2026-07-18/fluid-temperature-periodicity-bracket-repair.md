---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/
  - work_products/2026-07/2026-07-17/2026-07-17_heater_source_leave_salt3_out_score/
  - work_products/2026-07/2026-07-18/2026-07-18_fluid_temperature_periodicity_bracket_repair/
tags: [fluid, temperature-periodicity, root-bracket, umx1, no-admission]
related:
  - .agent/status/2026-07-18_TODO-FLUID-TEMP-PERIODICITY-BRACKET-REPAIR.md
  - imports/2026-07-18_fluid_temperature_periodicity_bracket_repair.json
task: TODO-FLUID-TEMP-PERIODICITY-BRACKET-REPAIR
date: 2026-07-18
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---

# Fluid Temperature Periodicity Bracket Repair

## Attempted

Built a narrow audit around the AGENT-544 UMX1 smoke failure: pressure roots
were bracketed for all rows, but Salt3/Salt4 had finite temperature periodicity
errors at the current Fluid upper scan bound. I kept Fluid source read-only
because the external repo board shows active ownership of `solver.py`.

## Observed

The replay evaluated `march_temperatures()` at the fixed smoke `mdot` and
expanded only the start-temperature scan window. Salt2 rows were already
bracketed by the existing bounds. All six Salt3/Salt4 rows recovered a
temperature root above the current upper bound:

- Salt3 required the sweep to reach the `562.79 K` to `570.79 K` bracket range.
- Salt4 required the sweep to reach the `583.97 K` to `604.97 K` bracket range.
- Bisection residuals closed to about `1e-9 K`.

AGENT-529 provided the prior documented policy: finite rejected Salt4 roots were
diagnostic-only and blocked strict selection. This task keeps that policy.

## Inferred

The current UMX1 accepted-root failure is a numerical bracketing blocker, not a
reason to admit rejected roots or relax the periodicity tolerance. The next
Fluid patch should adaptively expand `solve_temperature_periodicity()` bounds
after an initial no-bracket scan, preserving the existing bisection and strict
acceptance gates.

## Caveats

This task did not edit external Fluid source, rerun full `solve_case`, submit a
Slurm job, or run a score grid. It proves the repair path for the fixed-mdot
smoke rows only.

## Next Useful Actions

Claim a non-conflicting external Fluid row after the TSWFC2 solver task clears,
apply `fluid_patch_contract.csv`, run Fluid solver-contract tests, then rerun
UMX1 smoke with strict validation. Only after roots and conservation pass should
any broader grid be launched.
