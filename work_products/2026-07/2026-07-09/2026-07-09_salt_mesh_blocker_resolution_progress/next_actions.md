# Next Actions

## Do Now

1. Use `endpoint_monitor_gci_mainline_coarse.csv` as the current endpoint-monitor
   GCI screen for cases with aligned mainline coarse baselines: `salt_test_2_jin;salt_test_4_jin`.
2. Stage a compute-node sampling task for medium/fine pressure and thermal closure QoIs.
3. Keep `closure_observations.csv` unchanged until admitted closure-QOI mesh-UQ
   rows exist.

## Sampling Targets

- pressure: section-mean or centerline-derived `p_rgh`, `U`, `T/rho` reductions for lower leg and test-section spans;
- thermal: physical-interface bulk temperatures, wallHeatFlux, wall/wall-adjacent temperature, Nu/HTC or UA-prime metrics;
- provenance: exact source case root, mesh level, time window, processor layout, and sampling dictionary.

## Salt 4

Salt 4 medium/fine still require a log/admission decision before publication GCI.
Full-history monitors are useful screening evidence, but signal-15/no convergence
monitor evidence remains the controlling blocker unless a later task explicitly
admits the runs.
