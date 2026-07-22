# Corrected Salt Postprocess Gate

This directory is produced after the live corrected Salt Q jobs exit.
It summarises launch preflight audits, solver-log health, and a
monitor-based operating-point direction check.

- Cases scanned: `14`
- Solver logs with `End`: `1`
- Preflight `*_ok` failures: `0`
- mdot moving in correct direction: `14` / `14`
- Cases flagged for special gate scrutiny: `1`

## Direction check

The `mdot_move_direction_ok` flag checks whether `|mdot|` is moving
in the direction predicted by laminar NC scaling (mdot ∝ Q^(1/3)).
The monitor `mdot_pipeleg_lower_05_straight` writes `sum(phi)` which
is always negative here (face normal opposes flow); we compare magnitudes.

This is a **direction** check only — not a magnitude or plateau check.
A small movement in the right direction passes.  The formal operating-point
gate (`assess_time_convergence.py --require-moved-from`) applies the full
Q^(1/3) threshold and plateau requirement.

## Late-window statistics

The `late_window_drift_pct` and `late_window_amp_pct` columns summarise
the last 300 simulated seconds of the mdot monitor.
Check `write_interval_s` and `late_window_n_samples` to verify the window
contains enough records (expect ~1 s/step → ~300 records for a full window).

## Scrutiny flag

The `needs_special_gate_scrutiny` column is an **inspection flag**.  It is
raised for: fatal-log markers, preflight audit failures, mdot moving in
the wrong direction, or solver logs that ended before enough post-restart
advancement.  **No flagged row is closure-fit admissible without coordinator
review.**  Admission requires `operating_point_verdict=requalified` from
the formal gate.

## Independent verification

Run the standalone verification script to cross-check this output:

```bash
python3 work_products/2026-07-07_collect_salt_status_verification/verify_direction_logic.py
```

That script reads every `surfaceFieldValue.dat` directly (no shared code
with this module) and prints a per-case table of first/latest mdot,
move_pct vs expected_pct, and direction_ok.
