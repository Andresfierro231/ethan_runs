# Predictive Forward V0 Imposed Cooler

Task: TODO-PRED-FORWARD-V0

Implemented a repo-local pressure-rooted forward-v0 runner that consumes the
strict input contract, uses heater setup input plus imposed cooler duty, and
joins experimental/CFD sensors only after solving. No external Fluid files,
native CFD outputs, registry/admission state, or solver outputs were modified.

Generated package:

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/`

Run command:

- `python3 tools/analyze/run_predictive_forward_v0_imposed_cooler.py --strict-input-contract --sensor-source both --engine fast_scan`

Observed output:

- 3 Salt cases x 2 source variants = 6 result rows.
- All 6 rows found a bracketed fast-scan pressure root and passed the residual gate.
- 102 experimental TP/TW sensor rows and 102 CFD sensor-reference rows were emitted.
- `F0_current_fluid_sources`: mean abs CFD Tmean error 34.374 K, mean mdot error vs CFD +0.008082 kg/s, mean ambient loss 185.151 W.
- `F1_heater_only`: mean abs CFD Tmean error 4.609 K, mean mdot error vs CFD +0.005477 kg/s, mean ambient loss 148.151 W.

Interpretation:

The heater-only source variant is a much better CFD thermal-state match under
imposed cooler duty, consistent with the prior fixed-mdot boundary-parity
direction. It is not yet predictive HX because cooler duty is still imposed.
It is also not a hydraulic validation success: mdot remains high versus CFD and
experimental validation, so the hydraulic gate must remain separate.

Execution note:

The full Fluid `solve_case` engine was preserved as `--engine solve_case`, but a
single interactive Salt 2 solve did not finish in several minutes. The package
therefore uses a documented `fast_scan` engine: Fluid `pressure_residual`
evaluations on a bounded mdot grid with short bracketed bisection. A compute-node
rerun should execute `--engine solve_case` before thesis-strength claims.
