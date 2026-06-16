# Implementation Notes

- Source case: `val_salt_test_2_coarse_mesh_laminar`.
- Primary coordinate: main-loop streamwise distance `s` with `s = 0 m` at `TP1`.
- Main-loop direction used in this package: `TP1 -> TP2 -> TP3 -> TP6 -> TP1`.
- The main-loop friction profile is patchwise in this first pass, not dense centerline-resolved.
- Retained field times sampled for wall-shear reductions: `6744, 6745, 6746, 6747, 6748` s.
- Merged continuation probe and mdot histories extend through `6749` s.
- Darcy friction factor is reported as `f_D = 8 tau_w / (rho U^2)`.
- `tau_w` is the streamwise projection of the patch area-average `wallShearStress` vector.
- `rho` is reconstructed from the merged TP bulk-temperature history using the case density law `rho(T) = 2293.6 - 0.7497 T`.
- `U` is derived from the merged mean absolute mdot history and a fixed bulk flow area from the mdot face-zone monitor.
- Bulk flow area used: `3.730589167e-04` m^2.
- Equivalent circular hydraulic diameter from that area: `0.021794` m.
- `warning_flag=yes` marks either large wall-shear spread proxy (>20%) or strong yPlus nonuniformity proxy (`yPlus_max / yPlus_avg > 5`).
- The branch/test-section patches are extracted in raw form for future use, but this v1 package keeps the public friction profile on the primary main loop only.
- Next pass target: replace patchwise positions with much denser `s` sampling and preserve the same reduction contract so internal HTC can be added without changing the package schema.
