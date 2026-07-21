# 1D Closure Results — Mainline Continuation (Salt Jin)

Date: `2026-06-30` · Owner: claude (AGENT-156) · Status: results package, paper-oriented.
Companion: `.agent/journal/2026-06-30/1d-model-status-and-plan.md` (plan),
`operational_notes/06-26/30/2026-06-30_cfd_1d_closure_workflow.md` (how to run).

This package reports the friction, pressure, HTC, and effective-heat-resistance
closures derived from the MAINLINE continuation CFD (Salt 2/3/4 Jin), after the
OF13 thermal blocker (B1) was resolved this session. All numbers separate
observed output from interpretation and carry explicit confidence boundaries.

## 0. The unlock (B1 RESOLVED)

The temperature field `T` (custom BC `rcExternalTemperature` / `libRCWallBC.so`)
now reconstructs natively: locally-built **OpenFOAM 13** + **gcc/15.2.0** libstdc++
(for `GLIBCXX_3.4.32`) + `libRCWallBC.so`. Reusable env: `tools/ofenv/of13_env.sh`.
This unblocked the entire thermal leg. (Under OF12 the OF13-compiled BC loads but
segfaults — ABI mismatch.)

## 1. Pressure (section-mean) — DONE, closure-grade

Per-station section-mean static `p_rgh`, dynamic head ½ρu², total pressure, and
MEASURED hydraulic diameter, on the mainline continuations
(`work_products/2026-06-30_claude_continuation_section_mean/` and the
T-augmented `..._of13_section_mean_T/`).
- Measured **D_h ≈ 21.8 mm** on every clean leg (bore ≈3.7e-4 m^2) — consistent
  across cases; replaces the idealized-circle assumption (action #4).
- Dynamic head is small (0.18 / 0.26 / 0.36 Pa for Salt 2/3/4) vs ±~20 Pa p_rgh
  swings — real but ~1% (very low velocity laminar loop).
- Clean (mid-leg, TW) stations have flow alignment 0.99–1.00; corner (TP)
  stations are auto-flagged (bend/junction).

## 2. Apparent friction factor — partial, cross-validated

`tools/analyze/derive_segment_friction.py` from section-mean gradients +
measured D_h (`work_products/2026-06-30_claude_segment_friction/`).
- **Heated `lower_leg` cross-validates the legacy wall-based fit**: independent
  section-mean-gradient method gives f in the same range as the defended ~2.5.
- Re now computable via Jin viscosity (`--auto-mu-jin`, `tools/analyze/salt_properties.py`):
  Re ≈ 59 / 81 / 111 (Salt 2/3/4) — deeply laminar.
- **Upcomer (incl. `upper_leg`) gives NEGATIVE f because there is a REAL
  buoyancy-driven recirculation / convection cell — model it, do not assign a
  friction factor.** Confirmed: 15–33% of the upcomer cross-section flows
  backward; Ri = Gr/Re² ≈ 64–300 ≫ 1 (buoyancy-dominated). The upcomer is closed
  with a convection-cell + natural-circulation model and a recirculation
  correlation in nondimensional groups (Ri, Ra, Gr, Re, Pr); seed data and the
  framework are in `operational_notes/06-26/30/2026-06-30_upcomer_convection_cell_model.md`
  and `work_products/2026-06-30_claude_upcomer_convection_cell/`. Friction on the
  near-horizontal / strongly driven legs (lower_leg) remains the trustworthy
  Darcy-f subset.

## 3. HTC / UA' / Nu / effective heat resistance R'=1/UA' — DONE (NEW)

`tools/extract/sample_segment_htc_uaprime.py` on the OF13 reconstructions
(`work_products/2026-06-30_claude_thermal_htc/`). T_wall from the reconstructed T
boundaryField (area-weighted by Q/q); q_w/q' from wallHeatFlux; T_bulk =
ENTHALPY-FLUX-weighted (ρ·u·cp(T)) mixed mean from the T-augmented cut planes.

| Case | lower_leg HTC [W/m²K] | lower_leg UA' [W/m/K] | lower_leg R' [m·K/W] | upcomer HTC | upcomer Nu | upcomer R' |
| --- | --- | --- | --- | --- | --- | --- |
| Salt 2 Jin | 252 | 16.6 | 0.060 | 77 | 3.11 | 0.196 |
| Salt 3 Jin | 269 | 17.7 | 0.057 | 102 | 4.06 | 0.149 |
| Salt 4 Jin | 288 | 18.9 | 0.053 | 126 | 4.99 | 0.121 |

Physical sanity checks (all pass):
- T_wall > T_bulk on the heated lower_leg; T_bulk > T_wall on the cooled upcomer
  (signs consistent with q).
- **Upcomer Nu = 3.1 / 4.1 / 5.0 brackets the laminar fully-developed reference
  (3.66 const-T, 4.36 const-q)** and rises monotonically with Re — independent
  corroboration of the legacy direct-Nu fit (Nu≈3.9–6.8).
- HTC and UA' rise with flow; R' falls. Monotonic across the Re sweep.

`downcomer` (right_leg) is policy-blocked for direct thermal closure (residual
bucket).

## 4. Confidence boundaries / open items (NEEDS MORE ANALYSIS)

Carried so they don't get lost (see also the per-tool TODO docstrings):
1. **Coarse mesh** — no mesh-independence bound yet on any f/Nu/UA'. GCI harness
   ready (`tools/analyze/compute_gci.py`); needs medium/fine runs (the OF13
   runtime is now available, so this is unblocked for execution via sbatch).
2. **Inferred bulk T ~445–490 K looks low** for a molten salt; it is consistent
   between the rho-EoS inference and the reconstructed T field, but verify the
   operating temperature / property set against Ethan's intended case. If T is
   off, mu(T)→Re and k(T)→Nu shift.
3. **`upper_leg` friction unusable** (buoyancy residual); re-derivation needed,
   and at u~0.013 m/s true friction may be below the coarse-mesh noise floor.
4. **T_wall nan faces**: 2–7 isolated wall faces per case had `-nan` (custom BC);
   sanitized to the field mean (446.5 K) to allow sampling — negligible by count,
   but a cleaner fix is to exclude them in the wall parser.
5. **Area weighting** of section means uses face-mean ≈ area-mean (uniform cut);
   exact area weighting is a refinement.
6. **Salt 1 Jin** excluded from closure-grade (heat closes only −2.08%; short
   window). Treat as provisional only.
7. **Nu(Re,Pr) not identifiable** (Pr collinear with Re in this laminar salt set)
   — report Nu(Re) only.

## Reproduce
Env: `source tools/ofenv/of13_env.sh`. Reconstruct (foreground, ~5 min):
`reconstructPar -case <scratch> -time <t> -fields '(T p_rgh U rho)'`. Then the
section-mean (with `--of-env-script tools/ofenv/of13_env.sh --dump-temperature`)
and thermal tools with `--skip-run`. Tests: 62 pass across the five test files.
