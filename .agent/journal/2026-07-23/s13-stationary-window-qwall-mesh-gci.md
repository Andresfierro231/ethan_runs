# Journal: S13 stationary-window Q_wall mesh GCI

Date: `2026-07-23`
Role: Hydraulics / Thermal-modeling / Mesh-GCI / Implementer / Tester / Writer / Reviewer
Task ID: `TODO-S13-STATIONARY-WINDOW-QWALL-MESH-GCI-2026-07-23`

## Context
User asked how to work on the item-4 science unlock (S13 closeout / source-property
release / low-recirc anchor / TW-after-TP residual). Four parallel scoping scans
found: S13 DATA-BLOCKED, source/property 3-of-4 analysis-actionable, low-recirc
COMPUTE-BLOCKED (job 3308712 running), TW-residual COMPUTE-BLOCKED. But three of
four share ONE master blocker (missing medium/fine fields at coarse target times).
I flagged a methodological shortcut: the medium/fine terminal windows already show
0.50% Q_wall agreement; S13 fail-closed the GCI only because windows aren't the
same ABSOLUTE time. User chose "C then A" -> investigate the stationary-window GCI
reframe first.

## Files inspected (read-only)
- `.../2026-07-22_s13_medium_fine_mesh_gci_disposition/{summary.json,case_qoi_medium_fine_spread.csv,qoi_mesh_disposition_summary.csv,README.md}`
- `.../2026-07-22_s13_medium_fine_exact_label_split_rerun/aggregated_exact_label_qoi_rows.csv`
- `.../2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/direct_sampled_coarse_surface_field_rows.csv`
- `.../2026-07-09_salt_mesh_refinement_discovery/mesh_case_inventory.csv`
- `tools/analyze/compute_gci.py`

## Files changed
- NEW `tools/analyze/build_s13_stationary_window_qwall_mesh_gci.py`
- NEW `tools/analyze/test_s13_stationary_window_qwall_mesh_gci.py`
- NEW `work_products/2026-07/2026-07-23/2026-07-23_s13_stationary_window_qwall_mesh_gci/**`
- `.agent/BOARD.md` (own row), status, this journal, import, operational_notes note.

## Commands run
```
python3.11 tools/analyze/build_s13_stationary_window_qwall_mesh_gci.py
python3.11 -m pytest tools/analyze/test_s13_stationary_window_qwall_mesh_gci.py -q
```

## Results / observations
- Terminal windows ARE statistically stationary: Q_wall within-window half-range
  <= 0.003% of mean on every (case, mesh). The same-absolute-time objection is
  therefore immaterial for Q_wall.
- Coarse Q_wall exists at the target windows (Salt2 23.116, Salt3 25.347, Salt4
  28.123) and is also stationary; forms a real 3-mesh triplet with medium/fine.
- GCI (r21=1.478, r32=1.460): Q_wall admitted all 3 cases; p=10.2/2.06/2.02,
  GCI_fine 0.0005/0.51/0.36%, asymptotic ratio ~0.99. Salt3/Salt4 near 2nd order.
- Exchange proxies fail-closed: GCI 79-768%, asymptotic ratio 0.51-0.65, some
  divergent -> recirculation exchange is mesh-unconverged.
- No release/freeze/score; 16 guardrails False; 6 tests pass.

## Not contradicting prior work
The prior S13 disposition (16:40-17:28 on 2026-07-22) fail-closed the formal GCI
because it declined to assume coarse-continuation-window == medium/fine-terminal-
window equivalence. This pass supplies the missing justification (measured
stationarity) and applies it only where the asymptotic-range check independently
passes. It does not relax any guardrail.

## Incomplete lines
- PASSIVE-H2 `qambient` / loop `mdot` not sampled at medium/fine -> their mesh-UQ
  needs those exact QOIs sampled at the stationary windows (small sampler task).
- Exchange-transport QOIs need a finer mesh (new CFD) to converge.

## Next steps
Independent review of the stationarity-equivalence argument; optional qambient/mdot
GCI extension; then option A (PASSIVE-H2-R4 release-proof-minus-UQ) with this GCI
as the loop-thermal mesh-UQ leg.
