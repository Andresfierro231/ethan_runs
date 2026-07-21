# T6 — Mesh-Independence (GCI) Study — BLOCKER report

Agent: AGENT-167 (claude) · Date: 2026-07-01 · Node: c318-008 (SLURM 3269598)

## Verdict

**HARD BLOCKER. T6 cannot be executed in this repo as scoped.** The three-level GCI
study requires generating *medium* and *fine* meshes at a controlled refinement
ratio, but there is **no mesh generator** — the meshes were delivered as pre-built
OpenFOAM `polyMesh` directories from a bespoke external parametric mesher that is
not present in the repo and not reachable in Ethan's source tree. I refuse to
fabricate meshes or GCI numbers (protocol + task instruction explicitly forbid it),
so this is reported as a blocker rather than guessed.

Nothing was launched. T2 (128 foamRun ranks on c318-008) was not disturbed.

## Evidence chain (rigorous)

### 1. Resource / node reality (corrected from the prompt)
- `scontrol show job 3269598`: **NumCPUs=256, NumNodes=1, NodeList=c318-008**,
  Partition=NuclearEnergy-dev, EndTime 2026-07-05. `SLURM_NTASKS=256`,
  `SLURM_CPUS_ON_NODE=256`. (`nproc`→1 is a cgroup artifact, as warned.)
- T2 occupies 128 ranks (2 variants × 64). So ~128 cores *are* physically free,
  contrary to "fully occupied" — but this is moot given the blocker below. Had a
  mesh existed, the coarse solve could coexist at ≤64–128 ranks; a ~17M fine mesh
  would have been deferred to sbatch to avoid thrashing T2.

### 2. Coarse mesh (the only level that exists)
From `constant/polyMesh/owner` header note (authoritative):
```
nPoints:2268735  nCells:2166996  nFaces:6598756  nInternalFaces:6403220
```
→ **coarse = 2,166,996 cells (≈2.17M)** — matches the campaign's "coarse_mesh".
Boundary has 109 patches incl. non-conformal-couple patches `ncc_junction_*`.

### 3. No mesh-generation inputs anywhere
Case `system/` = controlDict, createNonConformalCouplesDict, decomposeParDict,
functions, fvSchemes, fvSolution, topoSetDict. Case `constant/` = fvMesh, fvModels,
g, geometry (4× `junction_*_steinmetz.stl`), momentumTransport, physicalProperties,
polyMesh, thermophysicalTransport.
- **Absent:** blockMeshDict, snappyHexMeshDict, cfMeshDict/meshDict, surfaceFeaturesDict,
  any `*.geo`, any mesher/Allrun script.
- Repo-wide `find` for those dict names → only hit is the protocol doc (speculative).
- Repo-wide `grep` for `blockMesh|snappyHexMesh|cartesianMesh|cfMesh` in .py/.sh/.md
  → only the protocol doc.

### 4. The mesh is parametric-external (recipe present, generator absent)
`case_config.yaml` carries the mesher *inputs* but not the mesher:
```
mesh_group_id: 7ab7fb2650596980
mesh_settings: {kernel_factor 0.7, kernel_blend 0.5, core_ratio 0.64,
                ncc_radius_tol 0.01, inflation{first_cell_size 0.225,
                bulk_cell_size 1.125, c2c_expansion 1.2}}
ncc_couples: 10 ; scale_to_meters: 0.001
```
Every consumer of `mesh_group_id/kernel_factor/core_ratio/...` in the repo is an
inventory/report tool (build_campaign_tables, extract_case_inventory,
build_ethan_*_case_inventory, qoi_definitions.yaml, metadata indexes) — all READ
this as metadata; **none generate a mesh**. The `mesh_group_id` hash implies a
mesh registry/generator in Ethan's tooling.

### 5. External source tree — only delivered cases, no tooling
`jadyn_runs/.../2026-06-01_source_inventory` documents the meshes were imported from
`/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs`.
Inspected that tree: it holds only the delivered OpenFOAM cases (each a pre-built
`constant/polyMesh`, `postProcessing`, `processors64`, `dynamicCode`). A depth-6
`find` for `*.py | Makefile | *.geo | Allrun* | *MeshDict` returned **nothing**.
Ethan's own build/mesh tooling is not accessible from this node.

### 6. Only one mesh level exists
No `medium_mesh` / `fine_mesh` / `refined` case dirs anywhere (repo or external);
all Salt/water cases share the single `mesh_group_id 7ab7fb2650596980`. There is
literally one grid level available — you cannot form a 2-level (order-less) let
alone a 3-level GCI from it.

## Why a workaround would be dishonest (confidence boundary)
The protocol demands 3 *systematically* refined, geometry-consistent grids
(r≈1.5–2) with the same boundary-layer inflation family and the NCC Steinmetz
junctions. The QoIs (apparent Darcy f, Nu on the heated leg, near-wall y+) are
**wall-dominated**. A generic `refineMesh` uniform split would not refine the
first-cell wall layer in a controlled ratio, would not preserve the NCC couplings
or fillet-resolved junctions, and would violate the constant-r / matched-family
assumption underlying the observed order p. The resulting p/GCI would be a
fabricated discretization-error bound — worse than no number. Task instruction:
"do NOT fabricate meshes or fake GCI numbers." → stop and report.

## Readiness (so re-open is fast, ~unblocked-day turnaround)
- `tools/analyze/compute_gci.py` reviewed end-to-end: correct Roache/ASME V&V20-2009
  implementation (general-r fixed-point order solve, Richardson extrapolation,
  Fs=1.25 justified for 3-grid, asymptotic-range ratio + convergence verdict
  disclosed, degenerate inputs handled). **No fix needed** (I did not edit it).
- Per-level extractor pipeline confirmed present & compatible (mesh-source aware):
  `build_mesh_centerlines.py` → `sample_section_mean_pressure.py --centerline-source mesh`
  → `derive_streamwise_momentum_budget.py` (de-buoyed friction = correct f) →
  `sample_segment_htc_uaprime.py` (Nu on left_lower_leg; `--admit-downcomer`) →
  `assess_time_convergence.py` (steadiness gate) → `compute_gci.py`.
- OF13 runtime recipe confirmed (`source tools/ofenv/of13_env.sh; of13_assert_ready`
  = OF13 build + gcc/15.2.0 + libRCWallBC.so via controlDict libs). Python must run
  under system python3, not an OF-sourced shell.
- QoI plan (once meshes exist), per protocol: mdot (GCI<2%), gross wall duty +
  heater/cooler split (GCI<5%), apparent f on lower_leg & test_section_span, Nu on
  left_lower_leg, near-wall y+. Both Re-envelope ends (Salt 2 Jin Re≈98/… and
  Salt 4 Jin Re≈174/…).

## To unblock (owner action required)
Get from Ethan / the run owner ONE of:
1. **The external NCC parametric mesh generator + its inputs** (the tool behind
   `mesh_group_id`), so medium & fine can be built at a controlled r with the
   matched BL inflation family and NCC junctions; OR
2. **Pre-built medium & fine polyMeshes** for Salt 2 Jin and Salt 4 Jin, delivered
   like the coarse cases, WITH their nCells and the refinement ratio r used.

Then execution plan (unchanged, ready to run): stage fresh under
`jadyn_runs/modern_runs/2026-07-01_mesh_independence_gci/`, set OF13
controlDict/decompose/run scripts, dry-run each level at tiny endTime to confirm the
custom BC constructs (no segfault), solve to pseudo-steady at a T2-coexisting rank
count or via multi-node sbatch, extract the 3-level QoI table, run compute_gci, and
write the paper-grade GCI report (p, Richardson, GCI bands, asymptotic-range check,
y+ trend, honest confidence bounds).

## Housekeeping
- Board row AGENT-167 claimed (166 was the highest prior active → 167 free, no
  collision). Status: `.agent/status/2026-07-01_AGENT-167.md`.
- Launched: nothing. PIDs/logs: none. T2 untouched.
