# Tomorrow Start Here: Recirculation CFD Anchor Study

1. Open `.agent/BOARD.md` and check active rows before editing.
2. Check live jobs `3299610` and `3299620`; do not duplicate their Salt4
   high-Q nominal-insulation cases.
3. Open this package README and `proposed_cfd_run_matrix.csv`.
4. If staging is approved, start with the two Salt3 sentinel rows:
   `q1500w_hiins` and `q0150w_loins`.
5. Before launch, implement the insulation mutation as an actual OpenFOAM
   boundary/restart-field change, not only a case label:
   root `0/T`, copied `processors64/<restart>/T`, and case metadata must agree.
6. Run restart-level preflight before `foamRun`, following the AGENT-471/475
   Q-patching pattern.
7. Make every submitted case produce or retain enough data for U, T,
   wallHeatFlux, Re/Pr/Ri/Gr/Ra/Gz, wall-core Delta T, reverse area/mass
   fraction, secondary velocity, steady-window status, and mesh/time
   uncertainty.

Do not fit ordinary single-stream upcomer coefficients from material
recirculation rows.
