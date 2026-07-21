# T6 (mesh-independence GCI) — BLOCKED, needs Ethan/run-owner action

Date: 2026-07-01. Owner: claude (via AGENT-167 verification).

## The blocker (verified, not assumed)
The GCI study needs 3 mesh levels (coarse + medium + fine) at a controlled
refinement ratio. Only the COARSE mesh exists (nCells 2,166,996), and there is
**no mesh generator** in the case, the repo, or Ethan's reachable source tree:
- Cases carry only a pre-built `constant/polyMesh`, 4 `junction_*_steinmetz.stl`
  fillets, and `createNonConformalCouplesDict`. No blockMeshDict / snappyHexMeshDict
  / cfMeshDict / meshDict / .geo / mesher script anywhere.
- The mesh is PARAMETRIC-EXTERNAL: `case_config.yaml` records the recipe
  (`mesh_group_id 7ab7fb2650596980`, `kernel_factor 0.7`, `core_ratio 0.64`,
  `ncc_couples 10`, BL inflation {first_cell 0.225, bulk 1.125, expansion 1.2})
  but NOT the generator. All repo consumers only READ these keys.
- All Salt/water cases share the single `mesh_group_id` -> only one level exists.

A blunt `refineMesh` split was REFUSED: it would not refine the wall boundary
layer at a controlled ratio nor respect the NCC / Steinmetz junctions, so the
resulting p / GCI on the wall-dominated QoIs (f, Nu, y+) would be physically
meaningless. Fabricating meshes/GCI is not acceptable (scientific-rigor rule).

## Why it matters (paper)
GCI is the #1 remaining trust limiter: every closure this session (T1b friction
f/f_lam ~1-3.3, T4 thermal Nu/HTC/UA', T5 recirc, T7 bend K) is on the COARSE
mesh with NO discretization-error bound. The 1D-model READMEs themselves state
coarse mesh is diagnostic/regression-only. Until GCI closes, those closures carry
an unquantified mesh error and cannot enter a publishable result with a defensible
error bar.

## Ask (one of these unblocks it)
1. The external NCC parametric mesh generator + its inputs (so we can regenerate
   Salt 2 & Salt 4 Jin at medium & fine with a known refinement ratio r), OR
2. Pre-built medium & fine `polyMesh`es for Salt 2 & Salt 4 Jin, each with its
   nCells and the refinement ratio r relative to the coarse mesh.

## Ready to execute the moment meshes arrive
- Compute available: node c318-008 has 256 CPUs, ~128 free (T2 uses 128); can also
  sbatch multi-node.
- Tools ready: build_mesh_centerlines.py, sample_section_mean_pressure.py
  (--centerline-source mesh), derive_streamwise_momentum_budget.py (DE-BUOYED f —
  the correct one), sample_segment_htc_uaprime.py, assess_time_convergence.py,
  and tools/analyze/compute_gci.py (Roache/ASME V&V20, Fs=1.25, verified correct).
- Protocol: operational_notes/06-26/30/2026-06-30_mesh_independence_protocol.md.
- Journal: .agent/journal/2026-07-01/T6-mesh-independence-gci.md.
