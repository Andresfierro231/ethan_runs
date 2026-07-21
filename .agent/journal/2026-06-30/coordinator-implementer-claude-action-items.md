# AGENT-156 Raw Journal

Date: `2026-06-30`
Role: Coordinator / Implementer / Writer
Owner: claude
Task: Address the 8 ranked action items from the 2026-06-30 claude-inspection
review of the CFD→1D closure pipeline, via reusable scripts + heavy docs.

## Scope / non-collision

Claimed AGENT-156 on the board with NEW files only. Did NOT edit codex-owned
files (`tools/extract/sample_leg_centerline_major_loss.py` AGENT-155,
`tools/case_analysis_profiles.py`, any AGENT-15x report/script). Extractor-
touching fixes delivered as standalone tools + a documented proposed patch.

## Environment established (reusable)

- LS6 compute node, 1 core. OpenFOAM via `module load intel/24.1 impi/21.12
  openfoam/12` (Foundation v12 reading v13 cases). Helper:
  `tools/ofenv/of12_env.sh` (+ assert).
- Cases are v13 collated; custom BC `rcExternalTemperature`/`libRCWallBC.so` on
  `T` only — blocks `T` reconstruction, but `p p_rgh U phi rho` reconstruct fine
  (density from stored `rho`, so `T` not needed for pressure work).
- v12/v13 `faceZones` format differs (v13 drops `type`); reconstruct with a
  zone-free scratch mesh. Recipe in the workflow note.
- Gotcha: OF toolchain swap breaks system python3.9 → run Python tools with
  system python; OF calls wrapped in a subshell.

## Observed output (per item)

- #2 `assess_time_convergence.py` (run): Salt 2/3/4 Jin stationary in mdot AND
  gross wall duty (<0.2%); heat closes <0.2% of gross. Salt 1 quasi-stationary
  (1.3% mdot drift, −2.4% closure). KEY fix: `total_Q` is a near-zero net
  imbalance; must normalize by gross duty (else false 18–54% "drift").
- #3 `represent_closures_per_case.py` (run): apparent f = 3.5–4× (legs) / ~70×
  (test section) laminar 64/Re; ~20% of Re spread is Jin/Kirst; fits dof≤1
  (R²=1 overfit, flagged); log Re/log Pr corr −1.00 → Nu(Re,Pr) unidentifiable.
- #6 `reconcile_freeze_windows.py` (run): 13/14 freeze-window lanes unverifiable
  from staged data (claimed times exceed disk by 450–6041 s).
- #7 `validate_segment_map.py` (run): only `upcomer` unresolved, `heated_incline`
  provisional; `lower_leg` = right vertical heated leg (misleading name).
- #1 `sample_section_mean_pressure.py` (run): reconstruct→cutPlane→section-mean
  p_rgh per station + measured median bore ≈7.9e-4 m². Dynamic head NOT trusted
  (areaAverage(U)·n ≈ 0, flux ~100× below mdot monitor) — top open issue.
- #4 measured bore ~2.2× the legacy idealized-circle area (proposed patch).
- #5 mesh-independence protocol (3-level GCI, Salt 2/4 Jin) — blocked on runtime.
- #8 proposed patches documented (signed τ_w, ρu·cp bulk T, qr, NaN, stale surf).

## Interpretation

- Convergence evidence actually STRENGTHENS the late-window approach for Salt
  2/3/4 while quantifying Salt 1's weakness — honest both ways.
- The closures are single-regime calibrations dominated by form losses, not
  transferable correlations; this is now machine-checkable and flagged.
- Reproducibility gap (mainline continuation data absent here) is the binding
  constraint on closure-grade #1/#2.

## Contradictions / open

- #1 velocity flux anomaly (clean cross-sections integrate to ~0 net flux vs a
  steady mdot monitor) — needs faceZone areaNormalIntegrate cross-check.
- Staged data = parent warmup; mainline = continuation (not staged here).
- Segment map: confirm heated_incline→lower_leg; resolve `upcomer`.

## Artifacts

- tools: `tools/ofenv/of12_env.sh`,
  `tools/analyze/{assess_time_convergence,represent_closures_per_case,reconcile_freeze_windows,validate_segment_map,test_claude_action_items}.py`,
  `tools/extract/sample_section_mean_pressure.py`
- docs: `operational_notes/06-26/30/2026-06-30_{cfd_1d_closure_workflow,cfd_to_1d_segment_map,mesh_independence_protocol}.md`
- report: `reports/2026-06/2026-06-30/2026-06-30_claude_action_items_summary/README.md`
- work_products: `work_products/2026-06-30_claude_*`
- manifest: `imports/2026-06-30_claude_action_items.json`
- tests: 9 passing.

## Next actions

See workflow note §5. Priority: resolve #1 velocity flux; stage continuation
data; confirm segment map with Ethan; run mesh-independence when runtime returns.
