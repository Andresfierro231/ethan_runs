---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/paper_ready_report.md
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/trend_conclusion_register.csv
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_audit_tomorrow_handoff/overnight_study_queue.csv
tags: [tomorrow-start, mdot, temperature-probes, forward-model, overnight-compute]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_audit_tomorrow_handoff/README.md
task: AGENT-372
date: 2026-07-14
role: Coordinator/Forward-pred/Writer
type: operational_note
status: complete
---
# mdot/Temperature Audit Tomorrow Handoff

## Why This Note Exists

AGENT-360 completed a Salt1-4 1D audit comparing mass-flow error (`mdot`) to
TP/TW temperature-probe error under several boundary-condition information
levels. The user wants this context preserved for tomorrow and wants candidate
overnight studies that can use an allocated compute node without mutating native
CFD solver outputs.

This note is the quick start point for that thread. It should be read before
creating new board rows for test-section, cooler, heater, or reference-state
follow-up studies.

## Open First Tomorrow

1. `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/README.md`
2. `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/paper_ready_report.md`
3. `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/trend_conclusion_register.csv`
4. `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/mdot_error_summary.csv`
5. `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/temperature_probe_error_summary.csv`
6. `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/part3_test_section_error_increment.csv`
7. `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/part4_cooling_rmse_summary.csv`
8. `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/part5_heating_rmse_summary.csv`
9. `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_audit_tomorrow_handoff/overnight_study_queue.csv`
10. `.agent/BOARD.md`

Before launching or editing, check whether active rows still own heater,
thermal parity, forward-v1, generated indexes, or CFD postprocessing scopes.

## What AGENT-360 Produced

AGENT-360 built:

- `tools/analyze/build_mdot_temperature_probe_error_audit.py`
- `tools/analyze/test_mdot_temperature_probe_error_audit.py`
- `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/**`
- `.agent/status/2026-07-14_AGENT-360.md`
- `.agent/journal/2026-07-14/mdot-temperature-probe-error-audit.md`
- `imports/2026-07-14_mdot_temperature_probe_error_audit.json`

The final `summary.json` reports:

- 4 case rows.
- 4 model modes.
- 16 model-result rows.
- 12 executed Fluid rows.
- 204 sensor-error rows.
- 23 heating/cooling heat-score rows.
- 21 mdot/probe correlation rows.
- 6 trend/conclusion rows.

The builder was regenerated with Fluid-backed execution and validated with:

```bash
python3.11 -m unittest tools.analyze.test_mdot_temperature_probe_error_audit
```

Result: 6 tests passed.

## Scientific State

### Case Use

- Salt2: training row.
- Salt3: validation row.
- Salt4: holdout row.
- Salt1: diagnostic/context only. It is blocked for CFD heat-flux modes because
  the consumed current patch heat ledger covers Salt2/Salt3/Salt4 but not a
  current admitted Salt1 ledger.

Do not fit closures on Salt3 or Salt4. Do not promote Salt1 until a separate
admission gate resolves the missing ledger and split status.

### Boundary Modes

Part 1:

- `M1_full_cfd_segment_heat_flux_pressure_root`: prescribes the realized CFD
  segment heat ledger and solves mdot from pressure balance.
- `M1b_full_cfd_segment_heat_flux_fixed_mdot`: prescribes the same heat ledger
  but imposes CFD mdot; this is only a thermal/sensor diagnostic.

Part 2:

- Prescribes CFD heater heat entry, CFD test-section net heat, and CFD cooler
  heat removal. It solves mdot from pressure balance.
- The test-section term is currently encoded as a compatibility negative
  source, not a first-class physical boundary model.

Part 3:

- Prescribes CFD heater heat entry and CFD cooler heat removal only.
- The Part2-Part3 difference is the current estimate of test-section influence.

Part 4:

- Cooling-leg heat-removed scoring at fixed mdot.

Part 5:

- Heating-leg heat-added scoring at fixed mdot.

## Main Findings To Preserve

1. Full CFD heat matching is not enough.
   M1 pressure-root rows reproduce net heat balance but still leave average
   absolute Tmean error of 161.566 K and average absolute mdot error of
   35.874 percent. This points to reference-state/start-temperature/thermal
   state closure, not only segment heat flux.

2. Test-section omission is not harmless.
   Omitting the CFD test-section net term changes all-probe RMSE by -8.949 K on
   average but increases mdot error by 0.00099 kg/s on average. In the current
   ladder, dropping the term improves TP/TW agreement while worsening hydraulic
   buoyancy agreement.

3. Cooler closure is the highest-value model improvement.
   Current fixed-mdot Fluid cooler RMSE is 102.886 W. A Salt2-fit constant-UA
   bulk-drive diagnostic transfers to Salt3/Salt4 with 4.638 W RMSE. The
   zero-error `salt2_fit_cooler_imposed_ratio` row is not predictive; it is a
   CFD-boundary scaling diagnostic.

4. Heater heat-entry fraction is tractable.
   Electrical 1:1 heater RMSE is 24.629 W. Salt2-fit heater efficiency RMSE is
   0.68 W across non-Salt1 rows. Check active heater rows before duplicating
   this work.

5. mdot/probe error correlation is only descriptive.
   Across pressure-root non-Salt1 rows, absolute mdot error and all-probe RMSE
   have Pearson r = 0.47 with n = 9. Do not use this as a causal model or fit
   objective by itself.

## Guardrails

- Do not mutate native CFD solver outputs.
- Keep external `../cfd-modeling-tools/**` read-only unless a board row
  explicitly claims it.
- Do not run long or expensive work on login nodes.
- Treat realized CFD wallHeatFlux modes as diagnostic, not setup-only
  predictive.
- Do not let internal Nu, cooler UA, heater fraction, or test-section closures
  absorb unrelated residuals without a residual ledger.
- Do not double count radiation: CFD `rcExternalTemperature` already includes
  radiation in total wallHeatFlux, and no separate exported `qr` term exists.
- Keep Salt2 train, Salt3 validation, Salt4 holdout discipline.

## Best Overnight Studies

The full queue is in:

`work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_audit_tomorrow_handoff/overnight_study_queue.csv`

Recommended order:

1. `ON-COOLER-SETUP`: setup-only cooler closure bakeoff.
   This is the best compute-node candidate because it is likely local Fluid
   execution, not OpenFOAM solver work. It directly targets the largest heat
   removal gap: current Fluid cooler RMSE 102.886 W versus a nontrivial Salt2
   fit at 4.638 W. Acceptance is a Salt2-train, Salt3/Salt4-score table for
   setup-only cooler forms that do not consume realized CFD cooler heat at
   runtime.

2. `ON-TS-BOUNDARY`: test-section boundary-form bakeoff.
   Compare zero test-section, compatibility negative source, distributed sink,
   and passive ambient UA. This addresses the Part2/Part3 mdot-probe tradeoff.
   Acceptance is a clear Pareto table showing which form improves mdot and
   TP/TW errors without refitting on Salt3/Salt4.

3. `ON-REFERENCE-STATE`: reference temperature and sensor-state audit.
   M1's large Tmean error means the next model may be failing because of
   reference-state anchoring, not only boundary heat. Compare Fluid default,
   CFD Tmean, inlet TP, and loop-mean anchors as diagnostics. Do not use
   validation sensors as predictive runtime inputs.

4. `ON-PRESSURE-ROOT-QA`: pressure-root solver quality and speed audit.
   Useful infrastructure work if the node has idle time. The AGENT-360 builder
   took several minutes because pressure residual evaluations are repeated.
   Compare fast scan with full `solve_case` and profile runtime before broad
   sweeps.

5. `ON-SALT1-HEAT-LEDGER`: Salt1 patch heat ledger backfill.
   Launch only if source cases and extraction scripts are confirmed. This may
   be heavier than local Fluid sweeps and should not mutate native outputs.
   Any Salt1 output remains diagnostic until a separate admission decision.

6. `ON-HEATER-SOURCE`: heater source-entry follow-up.
   Scientifically useful but likely overlaps active or recently completed
   heater-specific work. Check AGENT-370 before launching.

7. `ON-MDOT-PROBE-MULTIOBJECTIVE`: Pareto residual map.
   Run after the cooler or test-section bakeoff, not before, because it needs
   candidate model-form outputs.

## Suggested Board Rows For Tomorrow

Use one row per study. Suggested first row:

`AGENT-next | BC-modeling / Forward-pred / Implementer / Tester / Writer`

Scope:

- `.agent/BOARD.md` own row only.
- `.agent/status/2026-07-15_AGENT-next.md`
- `.agent/journal/2026-07-15/setup-only-cooler-closure-bakeoff.md`
- `imports/2026-07-15_setup_only_cooler_closure_bakeoff.json`
- `tools/analyze/build_setup_only_cooler_closure_bakeoff.py`
- `tools/analyze/test_setup_only_cooler_closure_bakeoff.py`
- `work_products/2026-07/2026-07-15/2026-07-15_setup_only_cooler_closure_bakeoff/**`

Read-only:

- AGENT-360 package as input.
- Native CFD solver outputs.
- Registry/admission state.
- Generated indexes unless explicitly claimed.
- External Fluid unless explicitly claimed.

Acceptance:

- Salt2-only fitted cooler alternatives.
- Salt3/Salt4 validation/holdout scoring without refit.
- Explicit runtime-input leakage audit.
- RMSE of heat removed plus mdot/probe impact if coupled through Fluid.

## Tomorrow Decision Points

1. Is the next priority to improve predictive boundary conditions, or to make
   the audit itself faster/more robust?
   If boundary conditions, start with cooler or test-section. If robustness,
   start with pressure-root QA and reference-state audit.

2. Should Salt1 be elevated?
   Not yet. First produce a candidate patch heat ledger and a separate
   admission note.

3. Should the zero-error cooler ratio be reported?
   Yes, but only as a diagnostic upper bound or leakage warning. The
   nontrivial candidate is the Salt2-fit constant-UA bulk-drive form.

4. Should the mdot/probe correlation be used as an objective?
   No. Use it as triage and visual evidence only.

## Closeout

This handoff launched no jobs, changed no admission state, and mutated no
native CFD or external Fluid files. It only documents AGENT-360 context and an
overnight study queue.
