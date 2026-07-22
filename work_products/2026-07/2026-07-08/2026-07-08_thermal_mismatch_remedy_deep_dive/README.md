# Thermal Mismatch Remedy Deep Dive

Generated: `2026-07-08T19:38:10+00:00`
Task: `AGENT-209`

## Scope

This package answers the follow-up questions on the Salt 2/3/4 1D thermal-state mismatch using bounded fixed-mdot thermal replays against existing July 8 CFD contracts.

## Main Result

The strongest single issue is the cooler/HX path: the current prior 1D comparison removes only 46-54 W through the cooling jacket, while the CFD cooler wallHeatFlux removes 136-169 W.

## Files

- `heater_values.csv`: exact heater imposed duty versus heater wallHeatFlux.
- `energy_defect_budget.csv`: first-order heat-defect accounting.
- `fixed_mdot_replay_results.csv`: four remedy paths tried at CFD mdot plus baseline.
- `remedy_path_summary.csv`: aggregate gate results by path.
- `parallel_agent_prompts.md`: ready prompts for helper agents.
- `fixed_mdot_solver_plan.md`: proposed Fluid fixed-mdot/frozen-hydraulics design.
- `summary.json`: machine-readable summary.

## Caveat

These are fixed-mdot thermal replays using existing Fluid functions, not committed Fluid solver changes and not full predictive hydraulic solutions.
