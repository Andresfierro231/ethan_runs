# Salt 4 Jin Mesh And Runtime Diagnostics

Date: `2026-06-09`
Case: `jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation`
Purpose: summarize the current `Salt 4 Jin` continuation state, record the mesh-adjacent diagnostics already available in the staged case, and define the safest next diagnostic commands for HPC use.

## Observed Outputs

- Current Slurm accounting on `2026-06-09`:
  - `3210231`: `TIMEOUT` after `3-00:00:12`, start `2026-06-05T11:29:37-05:00`, end `2026-06-08T11:29:49-05:00`
  - `3211200`: `RUNNING`, elapsed `1-01:20:28` at inspection time, start `2026-06-08T11:30:13-05:00`
- Current live solver tail from `logs/log.foamRun_continuation` is still numerically calm:
  - latest observed time about `4601.975369458 s`
  - mean Courant about `0.0987205679`
  - max Courant about `0.995249154`
  - cumulative continuity error about `3.19199105e-05`
- The staged mesh is the same general size as the Salt 2 coarse staged mesh:
  - `nCells: 2166996`
  - `nPoints: 2268735`
  - `nFaces: 6598756`
  - `nInternalFaces: 6403220`
  - `boundary patches: 109`
- The case already writes useful runtime diagnostics through `system/functions`:
  - `yPlus`
  - `wallHeatFlux`
  - `wallShearStress`
  - `nuEff`
  - `temperature_probes`
  - `velocity_profiles`
  - `piv_slab_velocity`
  - several `surfaceFieldValue` mass-flow monitors
  - coded dimensionless fields including `Pr`, `Re`, `Gr`, `Ri`, `Ra`, and wall `Nu`
- Latest available `yPlus` snapshot inspected was `postProcessing/yPlus/3930/yPlus.dat`.
  - Straight lower pipe sections stay low:
    - `pipeleg_lower_02_straight`: average about `0.159`
    - `pipeleg_lower_05_straight`: average about `0.227`
    - `pipeleg_lower_08_straight`: average about `0.150`
  - Main nonconformal / junction-connected patches are much more active:
    - `ncc_junction_lower_left_upper_start`: max about `109.97`, average about `4.23`
    - `ncc_junction_lower_right_left_start`: max about `217.16`, average about `4.92`
    - `ncc_junction_upper_right_left_end`: max about `207.01`, average about `3.25`
    - `ncc_junction_upper_left_lower_end`: max about `82.25`, average about `5.60`
    - `ncc_pipeleg_lower_01_fitting_start`: max about `13.36`, average about `1.64`
- Latest available total wall-heat proxy tail from `postProcessing/total_Q.dat` around `t = 4602 s` still moves noticeably:
  - `4598`: `0.143447`
  - `4599`: `0.148644`
  - `4600`: `0.168468`
  - `4601`: `0.197757`
  - `4602`: `0.231495`
- Latest available PIV slab volume-average tail from `postProcessing/piv_slab_velocity/3929/volFieldValue.dat` around `t = 4602 s` remains stable:
  - `|U|` near `3.345e-02 m/s`
  - slab-average `T` near `4.8129e+02 K`

## Interpretation

- The continuation is operationally healthy right now. The repaired runtime/bootstrap path is not the current blocker for `Salt 4 Jin`.
- Existing evidence does **not** yet point to the straight legs as the first refinement target. The strongest mesh-adjacent warning signs in the available diagnostics are localized at the `ncc_*` and junction transition patches, not the long straight pipe segments.
- The current `yPlus` field is consistent with a laminar low-wall-shear coarse mesh in the straight legs, while the large local maxima near nonconformal junction-linked patches suggest that any finer rerun should first consider:
  - junction transition quality
  - NCC interface neighborhood resolution
  - fitting / bend transition resolution
- This is not yet a full geometric mesh-quality judgment. No stored `checkMesh` audit was found in the staged `salt4` workspace, so non-orthogonality, skewness, determinant, and face-pyramid checks still need an explicit run.
- On the scientific side, the runtime tail looks calmer than the original `2083 s` cutoff, but the late total-wall-heat signal is still active enough that `Salt 4 Jin` should remain in the `usable with caveat` category rather than being treated as a fully settled steady row.

## Contradictions / Caveats

- The June 8 sponsor and presentation packages describe `3210231` as the relevant live job. That is now stale. `3210231` timed out and `3211200` is the current live continuation.
- The `yPlus` snapshot used here is from `t = 3930 s`, not from the current live tail at about `4602 s`. It is still useful for location-of-problem screening, but it is not the newest possible wall diagnostic.
- `yPlus` alone is not enough to justify full-mesh refinement. A coarse laminar case can have acceptable straight-leg `yPlus` while still having poor local geometric quality at junctions or NCC transitions.
- `checkMesh` and any heavier `postProcess` refresh should not be launched from the login node.

## Recommended Next Actions

- First diagnostic pass on HPC compute allocation:

```bash
source /scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh
CASE=/scratch/09748/andresfierro231/projects_scratch/ethan_runs/jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation
cd "$CASE"

checkMesh -allGeometry -allTopology > logs/log.checkMesh.$(date +%F)
postProcess -func yPlus -latestTime > logs/log.postProcess_yPlus_latest.$(date +%F)
postProcess -func wallShearStress -latestTime > logs/log.postProcess_wallShearStress_latest.$(date +%F)
```

- If `checkMesh` flags only localized bad cells near `ncc_*` / junction transitions, prefer a targeted junction/interface refinement study before paying for a broad global refinement.
- If `checkMesh` shows widespread high non-orthogonality or skewness across long legs too, then a broader coarse-to-fine rerun becomes more defensible.
- After the current continuation stops, refresh the continuation diagnosis and any June 8 presentation wording so `3211200` replaces stale `3210231` live-status language.
- If a follow-on diagnostic package is needed, add a small scripted summary that ranks worst `yPlus` maxima and worst `checkMesh` regions by patch so refinement decisions are tied to named geometry sections.

## Source References

- `jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/README.md`
- `jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/TODO.md`
- `jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/logs/log.foamRun_continuation`
- `jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/postProcessing/yPlus/3930/yPlus.dat`
- `jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/postProcessing/total_Q.dat`
- `jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/postProcessing/piv_slab_velocity/3929/volFieldValue.dat`
- `jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/system/functions`
- `jadyn_runs/salt4/2026-06-04_jin_continuation_candidate/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/constant/polyMesh/owner`
- `jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh`
- `reports/2026-06-05_ethan_continuation_diagnosis/README.md`
