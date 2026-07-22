# Junction Split Heat Ledger And Model Gate

## Bottom Line

Salt2-4 mainline now have a physical-junction split of the aggregate `junction_other` heat loss. The split closes exactly against the AGENT-462 aggregate audit and is suitable as diagnostic training/holdout target evidence. It is not enough to edit the 1D Fluid model in this task because val_salt2 and perturbation cases do not yet have equivalent patch-split ledgers, and the pressure corner-K lane remains diagnostic.

## Split Heat Result

| case | split loss W | source aggregate W | closure error W |
|---|---:|---:|---:|
| `salt2_mainline` | 39.128350 | 39.128350 | 0.000000e+00 |
| `salt3_mainline` | 43.234691 | 43.234691 | 7.105427e-15 |
| `salt4_mainline` | 48.485216 | 48.485216 | 0.000000e+00 |

## Case Coverage

| case | junction heat status | model status |
|---|---|---|
| `salt1_hi10q` | bc_metadata_available_realized_junction_heat_not_promoted | not_usable_for_junction_fit_until_realized_heat_ledger_promoted |
| `salt1_lo10q` | bc_metadata_available_realized_junction_heat_not_promoted | not_usable_for_junction_fit_until_realized_heat_ledger_promoted |
| `salt1_nominal` | bc_metadata_available_realized_junction_heat_not_promoted | not_usable_for_junction_fit_until_realized_heat_ledger_promoted |
| `salt2_hi5q` | not_available_or_diagnostic_only | not_usable_for_junction_fit |
| `salt2_lo5q` | not_available_or_diagnostic_only | not_usable_for_junction_fit |
| `salt2_mainline` | admitted_junction_split_patch_heat_ledger | usable_as_training_or_holdout_target_after_runtime_leakage_guard |
| `salt3_mainline` | admitted_junction_split_patch_heat_ledger | usable_as_training_or_holdout_target_after_runtime_leakage_guard |
| `salt4_hi5q` | not_available_or_diagnostic_only | not_usable_for_junction_fit |
| `salt4_lo5q` | not_available_or_diagnostic_only | not_usable_for_junction_fit |
| `salt4_mainline` | admitted_junction_split_patch_heat_ledger | usable_as_training_or_holdout_target_after_runtime_leakage_guard |
| `val_salt2` | aggregate_section_ledger_available_no_patch_split | external_validation_aggregate_only_not_local_junction_fit |

## Model Update Gate

| gate | status | evidence |
|---|---|---|
| `salt2_4_junction_patch_split_available` | pass | split cases=salt2_mainline;salt3_mainline;salt4_mainline |
| `split_rows_close_to_agent462_aggregate` | pass | max closure error W=7.105427357601002e-15 |
| `all_pressure_mapped_cases_have_junction_split_heat` | fail | Only Salt2/Salt3/Salt4 mainline have admitted split ledgers. |
| `val_salt2_patch_split_available` | fail | val_salt2 has aggregate section ledger only. |
| `pressure_corner_k_fit_admitted` | fail | pressure admitted fit rows=0; low-recirc branch rows=0 |
| `runtime_setup_only_inputs_available_for_mainline_split` | pass | Salt2-4 split rows include setup BC metadata and wall-shell temperature proxies; realized heat remains target only. |
| `overall_ready_for_fluid_model_edit` | fail | Mainline Salt2-4 split is usable, but val_salt2 and perturbation split ledgers are missing and pressure K remains diagnostic. |

## Scientific Interpretation

The split shows that the junction/stub heat-loss pathway is localized but distributed across corner bodies, extensions, stubs, steps, and non-conformal coupling/interface patches. The Salt2-4 rows include setup boundary metadata and wall-shell temperature proxies, so they can support a future setup-only candidate model form. Realized `wallHeatFlux` must remain a training or validation target, never a runtime model input.

The immediate 1D-model action is therefore not a Fluid code edit. The next implementation task should either harvest/promote missing split ledgers for val_salt2 and perturbation cases or deliberately define a narrower Salt2-4-only candidate experiment with that limitation documented.

## Outputs

- `junction_split_patch_ledger.csv`: patch-level Salt2-4 split rows.
- `junction_split_heat_ledger.csv`: physical-junction aggregate rows plus source-total checks.
- `junction_temperature_drive_candidates.csv`: setup-only candidate drive quantities.
- `case_heat_ledger_admission.csv`: heat-ledger coverage for every pressure-mapped case.
- `model_update_gate.csv`: explicit pass/fail gate for Fluid model edits.
- `junction_split_heat_by_bucket.svg`: visual audit of the split heat by case and bucket.

## Tomorrow Handoff

Start with `model_update_gate.csv`. The gate intentionally blocks Fluid edits because the evidence is not broad enough yet. The next evidence task should add comparable patch-split junction heat ledgers for `val_salt2`, `salt2_hi5q`, `salt2_lo5q`, `salt4_hi5q`, and `salt4_lo5q`, then rerun this gate.

If a narrower Salt2-4-only model experiment is desired before those ledgers exist, claim it as a separate diagnostic Fluid task and label it non-production/non-admitted. It must use setup-only parameters derived from this package and must not consume realized CFD `wallHeatFlux` at runtime.

Rebuild commands:

```bash
python3.11 -m unittest tools.analyze.test_junction_split_heat_ledger_and_model_gate
python3.11 tools/analyze/build_junction_split_heat_ledger_and_model_gate.py
```
