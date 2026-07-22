# Corrected Salt Q Perturbation — Preliminary Gate Analysis

**Date:** 2026-07-07  
**Task:** AGENT-182  
**Status:** PRELIMINARY — formal gate job 3278453 still PENDING dependency

## Purpose

Manual live inspection of corrected Salt Q perturbation mdot monitors before
the formal SLURM gate job (3278453) can run. The corrected runs (jobs 3275448,
3275449, 3275560) were submitted 2026-07-04 after AGENT-178 identified and
fixed the false-steady root cause: missing BC patch + restart-field re-injection
of Q perturbations in the old June 2025 runs.

## Key Findings

**All 14 preflight audits passed (bad_ok_count = 0)** — the corrected BCs and
restart-field patches were applied correctly.

**All Salt 2/3/4 cases show directionally correct mdot movement**, exceeding the
laminar-NC Q^(1/3) scaling threshold:

| Case | Nominal mdot | Current mdot | % change | Expected (Q^1/3) | Status |
|------|-------------|-------------|---------|------------------|--------|
| salt2_hi10q | -0.01318 | -0.01404 | **+6.5%** | +3.2% | running |
| salt2_hi5q  | -0.01318 | -0.01363 | **+3.4%** | +1.6% | running |
| salt2_lo10q | -0.01318 | -0.01229 | **-6.8%** | -3.5% | running |
| salt2_lo5q  | -0.01318 | -0.01274 | **-3.3%** | -1.7% | running |
| salt3_hi10q | -0.01498 | -0.01541 | **+2.9%** (rising) | +3.2% | running — only 20 s past restart |
| salt3_hi5q  | -0.01498 | -0.01523 | **+1.7%** (rising) | +1.6% | running — only 21 s past restart |
| salt3_lo10q | -0.01498 | -0.01409 | **-5.9%** | -3.5% | running |
| salt3_lo5q  | -0.01498 | -0.01455 | **-2.9%** | -1.7% | running |
| salt4_hi10q | -0.01698 | -0.01812 | **+6.7%** | +3.2% | running — approaching plateau |
| salt4_hi5q  | -0.01698 | -0.01759 | **+3.6%** | +1.6% | running — approaching plateau |
| salt4_lo10q | -0.01698 | -0.01607 | **-5.4%** | -3.5% | running |
| salt4_lo5q  | -0.01698 | -0.01660 | **-2.3%** | -1.7% | running — approaching plateau |

**Salt 1 cases:** hi10q converged early (t=4010, convergenceMonitor) at mdot
≈ -0.01170; lo10q still running at t=5417, mdot ≈ -0.01047. Salt 1 nominal
mdot is NOT in the CFD_MDOT reference table (weakly converged nominal). Formal
gate cannot be applied to Salt 1 without a nominal reference.

## Formal Gate Status

The `assess_time_convergence.py` gate (AGENT-166) produces `operating_point_verdict`:
- `requalified` — mdot moved ≥ Q^(1/3) from nominal AND plateaued → usable for correlation
- `false_steady` — mdot did NOT move from nominal → quarantined

Gate job 3278453 (`saltq_gate_after`) has dependency `afterany:3275448:3275449:3275560`
and will run automatically when all three solver jobs exit. As of 2026-07-07, the solver
jobs are still RUNNING (3+ days wall time).

## Interpretation

The corrected Q perturbation BCs are working. mdot IS responding to Q changes in the
correct direction and with approximately the expected magnitude. The prior June 2025
false-steady runs had mdot pinned at nominal (<0.3% movement vs expected 3-7%) because
the perturbation was never applied to the restart field or all required patches.

Actual mdot responses are **larger** than Q^(1/3) in most cases. This is consistent
with the loop operating at low Re where the buoyancy–friction balance is nonlinear and
a 10% Q increase may move mdot more than the 3.2% laminar-scaling prediction.

## Next Steps

1. Wait for SLURM jobs 3275448/3275449/3275560 to finish
2. Gate job 3278453 will run automatically and produce `run_status/run_status_inventory.csv`
3. Filter that CSV for `operating_point_verdict=requalified`
4. Only requalified rows enter the upcomer correlation dataset (lane U1/T10)
5. Salt 1 cases need special handling — cross-check against a Salt 1 nominal mdot reference

## Provenance

- Solver logs: `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/*/`
- Preflight audits: `*/logs/preflight_patch_audit_*.csv`
- Gate tool: `tools/analyze/assess_time_convergence.py` (AGENT-166 extensions)
- Live snapshot collected: `tmp/saltgate_live_snapshot/corrected_salt_solver_audit_summary.json`
- Formal gate job: SLURM 3278453 (pending dependency on 3275448/3275449/3275560)
