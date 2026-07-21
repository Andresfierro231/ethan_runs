# Checkpoint — 2026-07-01: self-generating a finer mesh for mesh-independence (T6)

Owner: claude (AGENT-162). Status: RESEARCH + OPTIONS ONLY (execution deferred to
2026-07-02/03 per user). Context: Ethan will NOT share the pre-built medium/fine
meshes or the parametric NCC generator, so the mesh-independence study (T6 — the #1
trust limiter on every closure) must be done by generating finer meshes OURSELVES
from the existing coarse mesh.

## 1. What we have (inventory, verified)
- Coarse polyMesh: **2,166,996 cells / 2,268,735 points / 6,598,756 faces** (single
  level; all Salt/water cases share mesh_group_id 7ab7fb2650596980).
- Boundary: **40 non-conformal-couple patches** (20 `nonConformalCyclic` + 20
  `nonConformalError`) + **69 `wall` patches**. => the loop is ASSEMBLED from
  separately-meshed legs joined by non-conformal couples (NCC), not one conformal block.
- Steinmetz junction fillets: 4 `junction_*_steinmetz.stl` in the case.
- Mesh recipe params (case_config.yaml, NOT the generator): kernel_factor 0.7,
  core_ratio 0.64, ncc_couples 10, BL inflation {first_cell 0.225, bulk 1.125,
  expansion 1.2}, test-section diameter change (20.9 mm quartz vs 22.1 mm).
- **OF13 utilities AVAILABLE** (confirmed in $FOAM_APPBIN): blockMesh, refineMesh,
  refineWallLayer, snappyHexMesh, snappyHexMeshConfig, foamToSurface, polyDualMesh,
  createNonConformalCouples, topoSet, checkMesh.
- NOT available: the parametric generator, blockMeshDict/snappyHexMeshDict for this loop.

## 2. Constraints any self-meshing must respect
- **NCC assembly**: 40 nonConformalCyclic/Error patches. Any refinement that changes
  the interface faces requires re-running `createNonConformalCouples` afterward.
- **Boundary layer**: graded inflation at the walls (first cell 0.225 of bulk). Wall
  gradients drive the wall-dominated QoIs (f, Nu, y+), so BL resolution is what matters.
- **69 named wall patches** carry the BCs (heater/cooler fixed-Q, insulated externals,
  test section). Any rebuild must PRESERVE these patch names/regions or BCs break.
- **Test-section diameter change** (contraction) and Steinmetz fillets are real geometry.

## 3. Candidate approaches (a couple to try), with honest pros/cons
### Approach A — uniform `refineMesh -all` (r = 2), RECOMMENDED primary
- Splits every hex into 8 (halves every edge, incl. the first BL cell → y+ halves).
  2.17M → ~17.3M cells. Geometry preserved EXACTLY (topological subdivision); patch
  names preserved; no CAD/STL needed.
- NCC handling: refine the internal mesh, then `createNonConformalCouples` to rebuild
  the couples on the refined interface patches (delete old couples → refineMesh →
  recreate). This is the main technical risk to de-risk first on a clone.
- GCI: gives coarse + fine = **2 levels**. A formal GCI wants 3 (to get OBSERVED order
  p). Honest first step: 2-level Richardson with the scheme's FORMAL order assumed
  (report p_assumed + the Roache Fs=1.25 GCI band via the existing compute_gci.py) —
  a real first discretization-error bound, clearly labeled "2-level, assumed order."
  For a 3rd level, a further uniform refine = 4× linear = ~140M cells (infeasible), so
  the 3rd level would come from Approach B or a directional refine.
- Cost: 17.3M-cell run to pseudo-steady is heavy (est. ~1 day on 128-256 cores). Node
  has 256 CPUs (~128 free while T2 runs), or sbatch multi-node.

### Approach B — boundary extraction + `snappyHexMesh` rebuild (independent levels)
- `foamToSurface` → export the current boundary as STL; blockMesh background block +
  snappyHexMesh onto the STL + addLayers, at 2-3 controlled resolutions → clean 3-level
  GCI with independent meshes.
- Pros: truly independent resolutions; controlled refinement ratio + BL; 3 levels.
- Cons: (1) snappy makes a CONFORMAL single-region mesh → NCC structure is LOST
  (acceptable — NCC was an assembly convenience, a conformal loop is valid), but it is
  a DIFFERENT mesh family than the original, which weakens the "refine the same mesh"
  GCI interpretation (report it as an independent-mesh convergence, not pure Richardson).
  (2) Heavy BC RE-MAPPING: the 69 wall patches (heater/cooler/insulated/test-section)
  must be re-created from per-region surface patches or the physics BCs can't be applied.
  (3) faceted STL loses exact curvature (minor at mesh resolution).
- Use as the INDEPENDENT cross-check / 3rd level, given the BC-remap effort.

### Approach C — `refineWallLayer` near-wall refinement (cheap sensitivity), COMPLEMENTARY
- Refines only the cells adjacent to the wall patches (splits the BL). Cheap (adds few
  M cells), preserves bulk mesh + NCC, directly targets y+ and the wall-gradient QoIs
  (f, Nu) that are the actual sensitivity.
- Not a uniform ratio → NOT a formal GCI, but a legitimate, cheap wall-resolution
  sensitivity check that answers "are f/Nu limited by wall resolution?" Run in parallel
  with A as a fast sanity signal while the 17M uniform run is queued.

## 4. Recommended plan for 2026-07-02/03 (execution)
1. `checkMesh` on the coarse mesh → baseline quality (skewness, non-orthogonality,
   aspect ratio, y+) — needed for both the report and the presentation "mesh quality" Q.
2. Clone case (read-only source untouched); de-risk NCC: delete couples → `refineMesh
   -all` → `createNonConformalCouples` → `checkMesh` → tiny-endTime solver dry run
   (custom BC constructs, no segfault). This proves Approach A is viable BEFORE the big run.
3. If viable: run coarse + fine (r=2) to the same pseudo-steady criterion; extract
   mdot, gross duty, de-buoyed f (T1b tool), Nu (T4 tool), y+ per level; 2-level GCI
   via compute_gci.py (assumed order, labeled honestly).
4. In parallel: Approach C (refineWallLayer) for a cheap wall-resolution sensitivity.
5. If a 3rd independent level is needed for a publishable observed-order GCI: Approach B
   (snappy from extracted surface) with the BC-remap effort budgeted separately.

## 5. Honest caveats to state up front
- 2-level Richardson gives an ASSUMED-order bound, not an observed order — weaker than a
  3-level GCI but a real, defensible first bound (better than the current NONE).
- refineMesh preserves geometry but the NCC-couple regeneration on refined interfaces is
  unproven here — must be de-risked on a clone (step 2) before trusting any refined run.
- 17M-cell run is expensive; budget compute (node/ sbatch) and time accordingly.
- snappy rebuild changes the mesh family and needs BC re-mapping — independent check, not
  a drop-in refinement.
- None of this fabricates a result: if refineMesh+NCC won't validate on the clone, we
  report that and fall back to Approach B or escalate the ask to Ethan again.

## 6. Pointers
- Blocker context: operational_notes/07-26/01/2026-07-01_T6_gci_blocker_ethan_request.md
- Protocol: operational_notes/06-26/30/2026-06-30_mesh_independence_protocol.md
- GCI calculator (ready, tested): tools/analyze/compute_gci.py
- Per-level extractors: tools/extract/build_mesh_centerlines.py,
  tools/analyze/derive_streamwise_momentum_budget.py (de-buoyed f),
  tools/extract/sample_segment_htc_uaprime.py (Nu/HTC, --mesh-length).
