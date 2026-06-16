# Ethan Steady-State Heat-Flow Audit

Generated: `2026-06-12T16:50:37-05:00`.

This package audits where heat is going at the latest usable steady-state checkpoint for all `13` currently registered CFD cases in `ethan_runs/` (13 CFD rows, excluding the separate `inventory_only` campaign registry row).

## Inputs and interpretation rules

- Latest heat partitions are recomputed directly from each case's current `postProcessing/wallHeatFlux/*/wallHeatFlux.dat` tail using the existing `build_salt2_behavior_package.py` logic.
- The late-window summary freezes the last `50` available wall-heat samples per case when possible; shorter tails are flagged explicitly.
- `ambient_proxy_w` is a derived proxy, not a directly measured column: it combines passive losses, powered-section deficits, and cooling-branch removal beyond the operating-point cooling duty.
- `exp_tw_rmse_k` and the Ethan-linked ambient-loss reference still come from `reports/2026-06-04_ethan_direct_validation/ethan_direct_validation_metrics.csv` and may lag any later live continuation state.
- Positive section heat means net heat into the fluid. Negative section heat means net heat removed from the fluid.

## How to read the heat columns

- `Ambient proxy [W]` is a bookkeeping estimate for "ambient-like" loss, not a separate wall patch family. In the generator it is:
  `ambient_proxy_w = passive_ambient + powered_section_ambient + cooling_branch_excess`.
- `passive_ambient` means heat leaving through ordinary non-powered walls with negative `wallHeatFlux` totals.
- `powered_section_ambient` means a positive-power patch did not deliver all of its imposed power into the fluid, so the shortfall is treated as local loss to surroundings.
- `cooling_branch_excess` means the cooling branch removed more heat than the nominal operating-point cooler duty; only that excess is counted inside `ambient_proxy_w`.
- `Cooling removal [W]` is different from `Ambient proxy [W]`: it is the full magnitude of heat removed by the three cooling-branch patches. Do not add `Cooling removal` and `Ambient proxy` as if they were independent sinks, because the ambient proxy already includes the cooling-branch excess term.
- `Junction net [W]` is the signed net heat transfer summed over patches whose names start with `junction_`. In plain language, it is the heat entering or leaving the fluid around tees, elbows, and local connector regions rather than along the long straight pipe legs.
- `Junction bucket` in the findings section means this same `junction_*` aggregate. A value like `-40.93 W` means the junction-region walls are removing about `40.93 W` from the fluid at that late checkpoint.
- `Test-section net [W]` follows the same sign convention. A negative value means the modeled test-section walls are a net sink from the fluid even if that region also contains an imposed source term in some salt-family cases.
- The table is most useful as a diagnostic ranking, not a perfect physical decomposition. `Ambient proxy` is meant to answer "how much heat is behaving like missing or redistributed external loss?" while `Junction net`, `Cooling removal`, and the other section columns answer "where is the signed wall exchange appearing in the patch totals?"

## Cross-case findings

- Steady-window coverage: `{"usable_window": 13}`.
- Run-status mix: `{"completed": 2, "running": 1, "terminated": 10}`.
- Mean signed ambient-proxy gap vs Ethan-linked reference: salt `-52.78` W, water `-2.52` W.
- Across nearly every case, the cooling branch is the dominant explicit heat sink and the junction bucket (`section_junctions_net_q_w`) is the next recurring nontrivial sink after the cooler and test-section branch.
- The salt cases carry materially larger ambient-proxy gaps than the water cases, which is consistent with the existing suspicion that salt TW disagreement is more sensitive to wall-loss partitioning and local 3D parasitics.

## Case-by-case table

| Case | Fluid | Run status | Latest heat time [s] | Heater net [W] | Ambient proxy [W] | Cooling removal [W] | Test-section net [W] | Junction net [W] | TW RMSE [K] | Hypothesis |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| S2 | salt | running | 8602.00 | 244.63 | 188.10 | 136.35 | -7.46 | -40.93 | 6.26 | under-loss |
| S1 jin | salt | terminated | 3230.00 | 213.15 | 167.77 | 135.60 | 0.75 | -34.37 | 17.80 | under-loss |
| S1 kirst | salt | completed | 3279.16 | 213.09 | 167.81 | 135.60 | 0.81 | -34.39 | 17.69 | under-loss |
| S2 jin | salt | terminated | 2432.00 | 243.60 | 186.89 | 136.35 | -5.50 | -39.40 | 6.62 | under-loss |
| S2 kirst | salt | completed | 586.56 | 243.66 | 188.09 | 136.35 | -5.04 | -41.53 | 6.97 | under-loss |
| S3 jin | salt | terminated | 2515.00 | 273.29 | 211.76 | 150.77 | -10.24 | -43.39 | 6.90 | under-loss |
| S3 kirst | salt | terminated | 3298.00 | 273.16 | 211.74 | 150.77 | -10.27 | -43.19 | 6.64 | under-loss |
| S4 jin | salt | terminated | 2083.00 | 310.59 | 244.24 | 169.23 | -16.52 | -48.85 | 7.56 | under-loss |
| S4 kirst | salt | terminated | 2984.00 | 310.49 | 244.09 | 169.23 | -16.55 | -48.54 | 7.27 | under-loss |
| W1 | water | terminated | 5274.00 | 53.44 | 26.37 | 30.39 | -2.78 | -6.14 | 1.67 | heat partition broadly consistent |
| W2 | water | terminated | 3985.00 | 70.66 | 35.24 | 40.83 | -3.75 | -8.08 | 2.05 | heat partition broadly consistent |
| W3 | water | terminated | 3732.00 | 84.81 | 42.02 | 49.42 | -4.53 | -9.54 | 2.25 | heat partition broadly consistent |
| W4 | water | terminated | 2542.00 | 117.78 | 59.59 | 67.91 | -6.55 | -13.27 | 2.90 | heat partition broadly consistent |

### Filtered Down Salt Cases

| Case | Fluid | Run status | Latest heat time [s] | Heater net [W] | Ambient proxy [W] | Cooling removal [W] | Test-section net [W] | Junction net [W] | TW RMSE [K] | Hypothesis |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| S2 | salt | running | 8602.00 | 244.63 | 188.10 | 136.35 | -7.46 | -40.93 | 6.26 | under-loss |
| S1 jin | salt | terminated | 3230.00 | 213.15 | 167.77 | 135.60 | 0.75 | -34.37 | 17.80 | under-loss |
| S2 jin | salt | terminated | 2432.00 | 243.60 | 186.89 | 136.35 | -5.50 | -39.40 | 6.62 | under-loss |
| S3 jin | salt | terminated | 2515.00 | 273.29 | 211.76 | 150.77 | -10.24 | -43.39 | 6.90 | under-loss |
| S4 jin | salt | terminated | 2083.00 | 310.59 | 244.24 | 169.23 | -16.52 | -48.85 | 7.56 | under-loss |

### Water cases Zoom in
| Case | Fluid | Run status | Latest heat time [s] | Heater net [W] | Ambient proxy [W] | Cooling removal [W] | Test-section net [W] | Junction net [W] | TW RMSE [K] | Hypothesis |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| W1 | water | terminated | 5274.00 | 53.44 | 26.37 | 30.39 | -2.78 | -6.14 | 1.67 | heat partition broadly consistent |
| W2 | water | terminated | 3985.00 | 70.66 | 35.24 | 40.83 | -3.75 | -8.08 | 2.05 | heat partition broadly consistent |
| W3 | water | terminated | 3732.00 | 84.81 | 42.02 | 49.42 | -4.53 | -9.54 | 2.25 | heat partition broadly consistent |
| W4 | water | terminated | 2542.00 | 117.78 | 59.59 | 67.91 | -6.55 | -13.27 | 2.90 | heat partition broadly consistent |

## Case-by-case notes

- `S2`: latest heat time `8602.00` s, heater net `244.63` W, ambient proxy `188.10` W, cooling removal `136.35` W, test-section net `-7.46` W, junction net `-40.93` W, TW RMSE `6.26` K. Hypothesis: The derived ambient proxy differs from the Ethan-linked ambient reference by -48.31 W (-20.44%), making wall-loss partitioning the first TW suspect.
  Extra note: latest wall-heat time 8602.0 s extends beyond the June 4 metadata snapshot at 3871.0 s; TW RMSE provenance remains the June 4 direct-validation package
- `S1 jin`: latest heat time `3230.00` s, heater net `213.15` W, ambient proxy `167.77` W, cooling removal `135.60` W, test-section net `0.75` W, junction net `-34.37` W, TW RMSE `17.80` K. Hypothesis: The derived ambient proxy differs from the Ethan-linked ambient reference by -63.19 W (-27.36%), making wall-loss partitioning the first TW suspect.
- `S1 kirst`: latest heat time `3279.16` s, heater net `213.09` W, ambient proxy `167.81` W, cooling removal `135.60` W, test-section net `0.81` W, junction net `-34.39` W, TW RMSE `17.69` K. Hypothesis: The derived ambient proxy differs from the Ethan-linked ambient reference by -63.16 W (-27.35%), making wall-loss partitioning the first TW suspect.
- `S2 jin`: latest heat time `2432.00` s, heater net `243.60` W, ambient proxy `186.89` W, cooling removal `136.35` W, test-section net `-5.50` W, junction net `-39.40` W, TW RMSE `6.62` K. Hypothesis: The derived ambient proxy differs from the Ethan-linked ambient reference by -49.52 W (-20.95%), making wall-loss partitioning the first TW suspect.
- `S2 kirst`: latest heat time `586.56` s, heater net `243.66` W, ambient proxy `188.09` W, cooling removal `136.35` W, test-section net `-5.04` W, junction net `-41.53` W, TW RMSE `6.97` K. Hypothesis: The derived ambient proxy differs from the Ethan-linked ambient reference by -48.32 W (-20.44%), making wall-loss partitioning the first TW suspect.
- `S3 jin`: latest heat time `2515.00` s, heater net `273.29` W, ambient proxy `211.76` W, cooling removal `150.77` W, test-section net `-10.24` W, junction net `-43.39` W, TW RMSE `6.90` K. Hypothesis: The derived ambient proxy differs from the Ethan-linked ambient reference by -49.70 W (-19.01%), making wall-loss partitioning the first TW suspect.
- `S3 kirst`: latest heat time `3298.00` s, heater net `273.16` W, ambient proxy `211.74` W, cooling removal `150.77` W, test-section net `-10.27` W, junction net `-43.19` W, TW RMSE `6.64` K. Hypothesis: The derived ambient proxy differs from the Ethan-linked ambient reference by -49.73 W (-19.02%), making wall-loss partitioning the first TW suspect.
- `S4 jin`: latest heat time `2083.00` s, heater net `310.59` W, ambient proxy `244.24` W, cooling removal `169.23` W, test-section net `-16.52` W, junction net `-48.85` W, TW RMSE `7.56` K. Hypothesis: The derived ambient proxy differs from the Ethan-linked ambient reference by -51.46 W (-17.40%), making wall-loss partitioning the first TW suspect.
- `S4 kirst`: latest heat time `2984.00` s, heater net `310.49` W, ambient proxy `244.09` W, cooling removal `169.23` W, test-section net `-16.55` W, junction net `-48.54` W, TW RMSE `7.27` K. Hypothesis: The derived ambient proxy differs from the Ethan-linked ambient reference by -51.61 W (-17.45%), making wall-loss partitioning the first TW suspect.
- `W1`: latest heat time `5274.00` s, heater net `53.44` W, ambient proxy `26.37` W, cooling removal `30.39` W, test-section net `-2.78` W, junction net `-6.14` W, TW RMSE `1.67` K. Hypothesis: TW RMSE (1.67 K) and the ambient-loss proxy are both reasonably aligned, so the steady-state wall heat partition is broadly self-consistent for this case.
- `W2`: latest heat time `3985.00` s, heater net `70.66` W, ambient proxy `35.24` W, cooling removal `40.83` W, test-section net `-3.75` W, junction net `-8.08` W, TW RMSE `2.05` K. Hypothesis: TW RMSE (2.05 K) and the ambient-loss proxy are both reasonably aligned, so the steady-state wall heat partition is broadly self-consistent for this case.
- `W3`: latest heat time `3732.00` s, heater net `84.81` W, ambient proxy `42.02` W, cooling removal `49.42` W, test-section net `-4.53` W, junction net `-9.54` W, TW RMSE `2.25` K. Hypothesis: TW RMSE (2.25 K) and the ambient-loss proxy are both reasonably aligned, so the steady-state wall heat partition is broadly self-consistent for this case.
- `W4`: latest heat time `2542.00` s, heater net `117.78` W, ambient proxy `59.59` W, cooling removal `67.91` W, test-section net `-6.55` W, junction net `-13.27` W, TW RMSE `2.90` K. Hypothesis: TW RMSE (2.90 K) and the ambient-loss proxy are both reasonably aligned, so the steady-state wall heat partition is broadly self-consistent for this case.

## Recommended refreshes or reruns

- `val_salt_test_2_coarse_mesh_laminar`: priority `medium`; refresh direct validation against the current runtime snapshot. The wall-heat tail is newer than the June 4 validation snapshot, so the TW comparison is slightly out of date for this case.
- `viscosity_screening_salt_test_1_jin_coarse_mesh`: priority `low`; no immediate rerun required for heat accounting. Current wall-heat history is sufficient for a first-pass steady-state heat partition audit.
- `viscosity_screening_salt_test_1_kirst_coarse_mesh`: priority `low`; no immediate rerun required for heat accounting. Current wall-heat history is sufficient for a first-pass steady-state heat partition audit.
- `viscosity_screening_salt_test_2_jin_coarse_mesh`: priority `low`; no immediate rerun required for heat accounting. Current wall-heat history is sufficient for a first-pass steady-state heat partition audit.
- `viscosity_screening_salt_test_2_kirst_coarse_mesh`: priority `low`; no immediate rerun required for heat accounting. Current wall-heat history is sufficient for a first-pass steady-state heat partition audit.
- `viscosity_screening_salt_test_3_jin_coarse_mesh`: priority `low`; no immediate rerun required for heat accounting. Current wall-heat history is sufficient for a first-pass steady-state heat partition audit.
- `viscosity_screening_salt_test_3_kirst_coarse_mesh`: priority `low`; no immediate rerun required for heat accounting. Current wall-heat history is sufficient for a first-pass steady-state heat partition audit.
- `viscosity_screening_salt_test_4_jin_coarse_mesh`: priority `low`; no immediate rerun required for heat accounting. Current wall-heat history is sufficient for a first-pass steady-state heat partition audit.
- `viscosity_screening_salt_test_4_kirst_coarse_mesh`: priority `low`; no immediate rerun required for heat accounting. Current wall-heat history is sufficient for a first-pass steady-state heat partition audit.
- `val_water_test_1_coarse_mesh_laminar`: priority `low`; no immediate rerun required for heat accounting. Current wall-heat history is sufficient for a first-pass steady-state heat partition audit.
- `val_water_test_2_coarse_mesh_laminar`: priority `low`; no immediate rerun required for heat accounting. Current wall-heat history is sufficient for a first-pass steady-state heat partition audit.
- `val_water_test_3_coarse_mesh_laminar`: priority `low`; no immediate rerun required for heat accounting. Current wall-heat history is sufficient for a first-pass steady-state heat partition audit.
- `val_water_test_4_coarse_mesh_laminar`: priority `low`; no immediate rerun required for heat accounting. Current wall-heat history is sufficient for a first-pass steady-state heat partition audit.

## Output files

- `case_heat_inventory.csv`: runtime coverage, latest timestamps, and window-status inventory.
- `latest_heat_partition.csv`: latest steady-state heat partition per case.
- `heat_window_summary.csv`: frozen late-window heat statistics per case and metric.
- `tw_hypothesis_matrix.csv`: joined TW-oriented interpretation matrix.
- `rerun_recommendations.csv`: explicit refresh and rerun recommendations with rationale.
- `summary.json`: machine-readable package summary and top-ranked cases.
- `figures/`: cross-case heat-partition comparison and TW-vs-heat-error scatter plots.
