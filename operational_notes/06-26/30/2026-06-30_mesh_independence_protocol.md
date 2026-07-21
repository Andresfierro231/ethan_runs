# Mesh-Independence Study Protocol (action item #5)

Date: `2026-06-30`
Owner: claude (AGENT-156)
Status: protocol only — execution is BLOCKED on runtime recovery (see §Blockers).

## Why this is required

Every training case is `*_coarse_mesh`, yet both 1D READMEs state coarse mesh is
diagnostic/regression-only and medium/fine is required for any thermal-closure /
wall-temperature interpretation. So the apparent-`f` (3.5–70× laminar) and
Nu/UA'/HTC closures currently have NO mesh-independence support. Until that gap
is closed, those closures cannot enter a publishable 1D result with a defensible
discretization-error bound. This protocol defines the minimum study to close it.

## Scope (minimum defensible study)

- Cases: at least **Salt 2 Jin and Salt 4 Jin** (the Re-range endpoints, ~98 and
  ~174), to bound mesh error at both ends of the fitted domain. Justification:
  errors in `f`/`Nu` can be Re-dependent; bracketing the domain is the least that
  supports the existing fit window.
- Mesh levels: **3 levels** (coarse = current, medium, fine) with a uniform
  refinement ratio r ≈ 1.5–2 per level, so a Grid Convergence Index (GCI,
  Roache) and observed order of accuracy `p` can be computed. Two levels cannot
  give an order estimate; 3 is the minimum for a defensible GCI.

## QoIs to track for convergence (with target bands)

For each mesh level, extract and compare:
1. loop `mdot` (hydraulic) — target GCI < 2%.
2. gross wall duty (thermal) and heater/cooler split — target GCI < 5%.
3. apparent Darcy `f` on `lower_leg` and `test_section_span`.
4. `Nu` on `left_lower_leg`.
5. near-wall `y+` distribution (already a function object) — confirm wall-cell
   resolution improves as expected.

Use the existing reusable tools on each level:
- `tools/analyze/assess_time_convergence.py` (steadiness per level),
- `tools/analyze/represent_closures_per_case.py` (f/Nu per level),
- `tools/extract/sample_section_mean_pressure.py` (section pressure per level).
Add a small GCI calculator that ingests the per-level QoI table (3 values → p,
GCI). Report Richardson-extrapolated values + GCI bands as the headline.

## Execution plan

1. Recover the OpenFOAM v13 tree + `libRCWallBC.so` (the solver and the custom
   wall BC are required to RUN new meshes; v12 only READS existing fields).
2. Generate medium/fine meshes from the case `blockMesh`/`snappyHexMesh` inputs
   with the chosen refinement ratio.
3. Run each level to the same pseudo-steady criterion used for the mainline
   (continuation) runs; verify steadiness with `assess_time_convergence.py`
   before extracting closures.
4. Extract QoIs, compute GCI, write a dated report with Richardson extrapolation
   and explicit discretization-error bands on `f` and `Nu`.

## Compute sizing / sbatch

A single coarse case is ~2.17M cells; medium (r≈1.7) ≈ ~10M, fine ≈ ~45M cells.
These solves are many-hour, multi-node runs — well past the 1 h interactive
threshold — so they MUST go through `sbatch` on `NuclearEnergy` (reuse the
existing array-campaign launchers under `Fluid/submit_array_campaign.sh` as the
pattern). Do NOT attempt on a login node or the 1-core interactive node.

## Blockers (must clear before running)

- OF13 runtime + `libRCWallBC.so` not recovered on LS6 (see
  `imports/2026-06-02_openfoam13_runtime_source.json`). Until then this study
  cannot execute; only the protocol is delivered.
