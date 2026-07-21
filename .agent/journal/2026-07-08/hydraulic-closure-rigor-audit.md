# Hydraulic Closure Rigor Audit

Date: `2026-07-08`
Role: Coordinator / Implementer / Tester / Writer
Task ID: `AGENT-223`

## Purpose

The user requested the highest-value hydraulic analyses as one integrated audit:
independent total-pressure accounting, two-tap minor-loss refinement,
station-resolved development diagnostics, recirculation invalidity,
uncertainty, and loop-level closure interpretation. This pass keeps the scope to
admitted Salt 2/3/4 Jin mainline evidence.

## Files Created

- `tools/analyze/build_hydraulic_closure_rigor_audit.py`
- `tools/analyze/test_hydraulic_closure_rigor_audit.py`
- `imports/2026-07-08_hydraulic_closure_rigor_audit.json`
- `work_products/2026-07/2026-07-08/2026-07-08_hydraulic_closure_rigor_audit/`
- `.agent/status/2026-07-08_AGENT-223.md`

## Source Evidence

The builder reads prior artifacts only:

- July 8 pressure ledger.
- July 8 two-tap minor-loss ledger.
- July 8 closure observation table and upcomer-onset package.
- July 7 quasi-steady UQ package.
- July 1 section-mean pressure, momentum-budget, segment-friction, and
  bend/minor-loss packages.
- June 30 upcomer and downcomer recirculation cut-plane metrics.

No native solver outputs, staged case trees, or external Fluid files were
modified.

## Observed Outputs

The package writes:

- `18` independent total-pressure-proxy span rows.
- `15` refined minor-loss feature rows.
- `18` station-development diagnostic rows.
- `9` recirculation-invalidity rows.
- `108` uncertainty/status rows.
- `3` loop-closure rows.
- `4` closure-decision rows.

## Interpretation

The integrated result supports this hierarchy:

- Keep F3/Shah as the current baseline for fit-eligible straight spans.
- Treat explicit minor losses as sensitivity/upper-bound terms, not
  closure-grade fitted `K` coefficients yet.
- Treat upcomer recirculation spans as a separate regime, not ordinary
  single-stream pipe friction.
- Do not promote per-leg/development tuning to paper-grade status until mesh/GCI,
  station-placement sensitivity, and raw tap extraction blockers are closed.

## Important Limitations

- The total-pressure quantity is explicitly a proxy:
  `p_rgh + 0.5*rho*U_bulk^2`.
- Mesh/GCI is still not quantified.
- Preserved two-tap rows lack full centerline tap-to-tap length; `K_local` remains
  an upper bound.
- Station-development analysis uses section-mean slope diagnostics and
  flow-alignment proxies, not raw profile-shape fields.
- Salt 1 and corrected-Salt rows remain out of scope until separately admitted.

## Validation

Commands run:

```bash
python tools/analyze/build_hydraulic_closure_rigor_audit.py
python -m pytest tools/analyze/test_hydraulic_closure_rigor_audit.py -q
python -m py_compile tools/analyze/build_hydraulic_closure_rigor_audit.py tools/analyze/test_hydraulic_closure_rigor_audit.py
```

Results:

- Builder completed and wrote the package.
- Focused tests passed: `5 passed`.
- Python compilation succeeded.

## Recommended Next Action

Run a compute-node raw two-tap/profile extraction follow-up for connector and
feature regions that need centerline tap-to-tap length and profile-shape metrics.
Then refresh this audit and the closure observation table with closure-grade
minor-loss and development-state rows.
