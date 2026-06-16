# Ethan Essential Steadiness Audit

This audit answers a narrower question than the coded solver convergence flag: are the current salt runs flat enough, and with a small enough net heat-balance residual, to use as practical steady-state approximations right now?

## Criteria

- `essentially_steady`: final `|total_Q|` residual <= 0.5% of heater power, late-window mdot drift <= 1%, late-window probe drift <= 0.1 K, late-window `|total_Q|` drift <= 0.1 W.
- `borderline_but_usable`: final `|total_Q|` residual <= 2% of heater power with similarly small late-window drifts.
- `not_steady_enough`: higher residual floor or visibly larger late-window drift, even if the coded monitor declared convergence.

## Main result

- Salt Test 2, 3, and 4 rows are effectively steady enough to use for analysis now.
- Salt Test 1 rows are the main exceptions: they are flat in the late window, but their net heat-balance residual floor is about 4% of heater power, which is materially larger than the others and supports the concern that they stopped on a non-negligible enthalpy residual floor.
- The active `val_salt_test_2` continuation is already usable now under this practical criterion, but it is still worth refreshing once continued probe outputs extend beyond the current pre-continuation window.

## Interpretation

- A flat late tail is not by itself enough for a clean steady-state claim if `|total_Q|` is still sitting at a non-trivial floor.
- Conversely, a row can be non-converged by the coded monitor and still be practically usable if both the state drift and the residual heat imbalance are already small.
