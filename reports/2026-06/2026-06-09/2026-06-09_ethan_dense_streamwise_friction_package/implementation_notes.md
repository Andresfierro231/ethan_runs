# Implementation Notes

- Source case: `val_salt_test_2_coarse_mesh_laminar`.
- Primary coordinate: main-loop streamwise distance `s` with `s = 0 m` at `TP1`.
- Main-loop direction used in this package: `TP1 -> TP2 -> TP3 -> TP6 -> TP1`.
- Dense streamwise bins target a spacing of `0.025` m over a main-loop length of `3.748` m.
- Retained wall-field times sampled in this package: `6756, 6757, 6758, 6759, 6760` s.
- Merged continuation probe and mdot histories extend through `6761` s.
- Darcy friction factor is reported as `f_D = 8 tau_w / (rho U^2)`.
- `tau_w` is built from wall-face `wallShearStress` values projected onto the TP-anchored legwise streamwise direction, then area-averaged within each dense `s` bin.
- `rho` is reconstructed from the merged TP bulk-temperature history using the case density law `rho(T) = 2293.6 - 0.7497 T`.
- `U` is derived from the merged mean absolute mdot history and a fixed bulk flow area from the mdot face-zone monitor.
- Bulk flow area used: `3.730589167e-04` m^2.
- `warning_flag=yes` marks dense bins where the retained wall-face streamwise shear deviates by more than 20% from the area-weighted bin mean at that time.
- Warning rows in the dense timeseries: `430` of `750`.
- Dense main-loop wall coverage first appears at `s = 0.675` m in this implementation; `TP1` is the coordinate origin, but the lower-left corner/junction wall surfaces are not yet included in the dense main-loop patch set.
- This dense pass still uses a legwise projected `s` coordinate through bends and connectors; the next pass can replace the station generator with a centerline-based or slice-based sampler without changing the CSV contract.
- The retained-time limitation remains: this package is late-window resolved in space, while the long mdot/temperature context is still provided separately for the full continuation history.
