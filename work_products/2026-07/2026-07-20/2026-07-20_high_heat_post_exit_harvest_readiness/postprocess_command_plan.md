# Postprocess Command Plan

Do not run these while jobs `3299610` or `3299620` are still running.

1. Refresh scheduler state:

```bash
ssh login1 squeue -j 3299610,3299620
ssh login1 sacct -j 3299610,3299620
```

2. If a job is terminal and successful, claim a new extraction task before any
native-output reads that create postProcessing artifacts.

3. Required extraction products for each case:

- matched upcomer planes: `U`, `T`, `rho`, and wall-band/core samples
- wall/source fields: `wallHeatFlux` and patch-integrated heat ledger
- derived dimensionless rows: `Re`, `Pr`, `Ri`, `Gr`, `Ra`, `Gz`
- recirculation rows: reverse area fraction, reverse mass fraction, secondary velocity fraction
- terminal-window rows: mdot, heat residual, T probes, wall-T probes
- uncertainty rows: time-window UQ immediately; mesh/GCI only after endpoint selection

4. Admission rule:

Rows with material reverse flow remain onset/recirculation evidence. Do not use
them as ordinary single-stream upcomer `Nu`, `f_D`, or component `K` fits.
