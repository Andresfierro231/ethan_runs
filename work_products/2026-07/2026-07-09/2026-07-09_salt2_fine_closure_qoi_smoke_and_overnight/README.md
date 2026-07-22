# Salt2 Fine Closure-QOI Smoke And Overnight

Generated: `2026-07-09T16:40:06-05:00`

This package launches compute-node processing for Salt2 refined-mesh closure
QoIs while keeping the imported Ethan case folders read-only.

## Execution Contract

- Smoke test: run the Salt2 Jin medium mesh through reconstruction, section-mean
  pressure sampling, segment friction, momentum budget, and thermal closure
  extraction.
- Overnight target: run the same pipeline on the Salt2 Jin fine mesh only after
  the smoke step succeeds.
- Provenance: the physical source case is medium/fine; the station and segment
  contract uses `viscosity_screening_salt_test_2_jin_coarse_mesh` because refined-mesh source IDs are not
  registered in `tools.case_analysis_profiles`.

## Entrypoints

- `scripts/launch_smoke_srun.sh`
- `scripts/launch_overnight_srun.sh`
- `scripts/launch_smoke_then_overnight_srun.sh`
- Direct driver: `scripts/run_refined_closure_qoi.sh [preflight|smoke|overnight|smoke_then_overnight]`

## Expected Outputs

Each mesh level writes under `outputs/<mesh_level>/`:

- `section_mean_pressure_viscosity_screening_salt_test_2_jin_coarse_mesh.json/.csv`
- `segment_friction.json/.csv`
- `momentum_budget.json/.csv`
- thermal closure outputs from `sample_segment_htc_uaprime.py`
- `run_provenance.json`

Logs write under `logs/`; staged reconstructions write under `recon/`.

## Interpretation Boundary

These outputs are extraction products, not closure-table admissions. Do not
update `closure_observations.csv` until the medium/fine rows are reviewed,
compared with the aligned mainline coarse baseline, and converted into explicit
closure-QOI mesh-UQ/GCI rows.
