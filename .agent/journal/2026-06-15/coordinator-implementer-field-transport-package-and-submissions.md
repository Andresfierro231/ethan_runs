# Coordinator / Implementer Raw Journal

- date: `2026-06-15`
- agent role: `Coordinator / Implementer`
- task ID: `AGENT-072`
- branch/worktree: `no-HEAD`
- files inspected:
  - `AGENTS.md`
  - `.agent/BOARD.md`
  - `.agent/FILE_OWNERSHIP.md`
  - `tools/analyze/build_ethan_case_analysis_package.py`
  - `tools/extract/sample_streamwise_azimuthal_transport.py`
  - `tools/analyze/build_ethan_representative_transport_comparison.py`
  - `tools/analyze/submit_ethan_case_analysis_package_sbatch.sh`
  - `operational_notes/06-26/07/2026-06-07_runtime_operator_reference.md`
  - `../cfd-modeling-tools/andres_2d_axisymmetric_testing_heat_loss/README.md`
  - `journals/2026-06/2026-06-15_ethan_runs.md`
- files changed:
  - `.agent/BOARD.md`
  - `.agent/status/2026-06-15_AGENT-072.md`
  - `.agent/journal/2026-06-15/coordinator-implementer-field-transport-package-and-submissions.md`
  - `tools/analyze/build_ethan_case_analysis_package.py`
  - `tools/analyze/build_ethan_field_transport_campaign.py`
  - `tools/analyze/submit_ethan_case_analysis_package_sbatch.sh`
- commands run:
  - `python -m py_compile tools/analyze/build_ethan_case_analysis_package.py tools/analyze/build_ethan_field_transport_campaign.py tools/extract/sample_streamwise_azimuthal_transport.py`
  - `python tools/analyze/build_ethan_field_transport_campaign.py --help`
  - `python tools/analyze/build_ethan_case_analysis_package.py --source-id val_salt_test_2_coarse_mesh_laminar --raw-extraction-dir reports/2026-06-10_ethan_salt2_case_analysis_package/raw_extraction --output-dir tmp/2026-06-15_field_transport_phase2_smoke/raw_reuse_case_package`
  - `bash -n tools/analyze/submit_ethan_case_analysis_package_sbatch.sh`
  - `bash tools/analyze/submit_ethan_case_analysis_package_sbatch.sh ... --dry-run`
  - local `bash tools/analyze/submit_ethan_case_analysis_package_sbatch.sh ...` attempts, which failed with the documented `sbatch not available on compute nodes` notification
  - `ssh login3.ls6.tacc.utexas.edu "cd ... && bash tools/analyze/submit_ethan_case_analysis_package_sbatch.sh ..."` for the supported Salt-family live submission wave
  - `squeue -j ...`
  - `sacct -j ...`
  - `tail -40/-80` on Slurm stdout/stderr logs to diagnose failed submissions
- results or observations:
  - Integrated `tools/extract/sample_streamwise_azimuthal_transport.py` into the per-case package builder. Live package jobs now request azimuthal wall transport automatically alongside the major-loss, boundary-layer, and feature-budget extractors.
  - Added azimuthal/heat-loss package outputs:
    - `azimuthal_wall_transport_summary.csv`
    - `azimuthal_transport_mean_summary.csv`
    - `streamwise_heat_loss_summary.csv`
    - `parasitic_heat_loss_summary.csv`
    - summary/README sections that advertise those outputs when present
  - Added `tools/analyze/build_ethan_field_transport_campaign.py` as the first cross-case consumer for the new field-transport package outputs.
  - Raw-reuse backward compatibility was preserved. Rebuilding from the older June 10 Salt 2 raw extraction still succeeds, and the package reports `azimuthal_transport.available = False` when the older raw extraction does not contain the new artifacts.
  - The first live submission attempt failed for all eight cases with Slurm exit `127` because sourcing the OpenFOAM environment in the batch shell broke the Python runtime (`libpython3.9.so.1.0` missing).
  - Hardened `tools/analyze/submit_ethan_case_analysis_package_sbatch.sh` in two ways:
    - prefer `/usr/bin/python` by default when `--python-bin` is not provided
    - stop sourcing OpenFOAM in the batch shell before launching Python; the builder/extractors already source OpenFOAM inside the actual reconstruction/postprocess subprocesses
  - After that wrapper fix, the seven Salt-family jobs and the validation-case resubmission are running under the corrected job IDs:
    - `3233645` `viscosity_screening_salt_test_1_jin_coarse_mesh`
    - `3233646` `viscosity_screening_salt_test_1_kirst_coarse_mesh`
    - `3233647` `viscosity_screening_salt_test_4_jin_coarse_mesh`
    - `3233648` `viscosity_screening_salt_test_3_jin_coarse_mesh`
    - `3233649` `viscosity_screening_salt_test_2_jin_coarse_mesh`
    - `3233650` `viscosity_screening_salt_test_2_kirst_coarse_mesh`
    - `3233651` `viscosity_screening_salt_test_3_kirst_coarse_mesh`
    - `3233655` `val_salt_test_2_coarse_mesh_laminar`
  - The first validation resubmission (`3233643`) then failed with exit `1` because the currently registered runtime root no longer contains the older retained times `7483-7487 s`. Inspection of the runtime tree showed the actual latest retained times are `8598-8602 s`, so the validation case was resubmitted as `3233655` on that available window.
- contradictions or unresolved issues:
  - The first live Salt-family wave exposed a raw-extraction contract mismatch: `sample_streamwise_boundary_layer_landmarks.py` expected geometry columns such as `tangent_x` in `leg_wall_face_samples.csv`, but `sample_leg_centerline_major_loss.py` writes that file as per-time wall-face timeseries rows. The Salt 2 trio failures `3233649`, `3233650`, and `3233655` are explained by that mismatch and should not be treated as evidence against the corrected method.
  - `val_salt_test_2_coarse_mesh_laminar` no longer shares the June 10 retained window. Any comparison against the older Salt 2 validation package must acknowledge that the live rebuild is now using the current continuation runtime’s latest retained window (`8598-8602 s`), not the historic `7483-7487 s` window.
  - `viscosity_screening_salt_test_4_kirst_coarse_mesh` and the four water validation runs still do not have the detailed case-analysis profile support needed for this same field-reconstructed package path.
- follow-on contract-hardening work completed after the first failure wave:
  - Updated `tools/extract/sample_leg_centerline_major_loss.py` so live major-loss extraction now publishes a dedicated `leg_wall_face_geometry.csv` alongside the existing `leg_wall_face_samples.csv` timeseries file. The major summary now records `raw_schema_version = salt_family_major_loss_v2`, plus explicit geometry and timeseries paths.
  - Updated `tools/extract/sample_streamwise_boundary_layer_landmarks.py` so it resolves geometry from the major summary metadata, prefers `leg_wall_face_geometry.csv`, falls back to legacy `leg_wall_face_samples.csv` only if the required geometry columns are actually present, and otherwise raises a precise contract error instead of a `KeyError`.
  - Updated `tools/analyze/build_ethan_case_analysis_package.py` so raw-reuse manifests record the new schema metadata, enforce the geometry file for the new schema, and copy `leg_wall_face_geometry.csv` into rebuilt package roots when available.
  - Local validation after the contract fix:
    - `python -m py_compile tools/extract/sample_leg_centerline_major_loss.py tools/extract/sample_streamwise_boundary_layer_landmarks.py tools/analyze/build_ethan_case_analysis_package.py`
    - `python tools/extract/sample_streamwise_boundary_layer_landmarks.py --help`
    - `python tools/analyze/build_ethan_case_analysis_package.py --source-id val_salt_test_2_coarse_mesh_laminar --raw-extraction-dir reports/2026-06-10_ethan_salt2_case_analysis_package/raw_extraction --output-dir tmp/2026-06-15_contract_hardening_smoke/raw_reuse_case_package`
  - The legacy June 10 Salt 2 raw-reuse rebuild still succeeds after the contract fix. As expected, that legacy raw directory does not produce `leg_wall_face_geometry.csv` and still reports `azimuthal_transport.available = False`.
  - Checked the scheduler docs and prior journals after the first failed SSH wrapper attempt:
    - `../cfd-modeling-tools/AGENTS.md` explicitly says that when direct `sbatch` is blocked on a compute host, submission should go through an approved login node such as `login3.ls6.tacc.utexas.edu`
    - `.agent/journal/2026-06-15/coordinator-implementer-paraview-cell-association-refresh.md` documents the successful direct pattern `ssh login3.ls6.tacc.utexas.edu sbatch --parsable <script>`
  - The reliable pattern from this host is therefore:
    - generate tracked sbatch scripts locally with `submit_ethan_case_analysis_package_sbatch.sh --dry-run`
    - submit those emitted `.sbatch` files remotely with direct `ssh login3.ls6.tacc.utexas.edu sbatch --parsable ...`
  - Applied that documented pattern for the Salt 2 contract-fix trio:
    - dry-run scripts:
      - `tmp/slurm_case_analysis_jobs/contract_fix_salt2_val/casepkg_val_salt_test_2_coarse_mesh_laminar.sbatch`
      - `tmp/slurm_case_analysis_jobs/contract_fix_salt2_jin/casepkg_viscosity_screening_salt_test_2_jin_coarse_mesh.sbatch`
      - `tmp/slurm_case_analysis_jobs/contract_fix_salt2_kirst/casepkg_viscosity_screening_salt_test_2_kirst_coarse_mesh.sbatch`
    - login-submitted job IDs:
      - `3233784` `viscosity_screening_salt_test_2_jin_coarse_mesh`
      - `3233785` `val_salt_test_2_coarse_mesh_laminar`
      - `3233786` `viscosity_screening_salt_test_2_kirst_coarse_mesh`
  - Immediate queue confirmation via `ssh login3.ls6.tacc.utexas.edu squeue -j 3233784,3233785,3233786` shows all three jobs running on separate compute nodes:
    - `3233784` on `c318-016`
    - `3233785` on `c318-017`
    - `3233786` on `c318-018`
  - Follow-up local compute-node iteration after those jobs finished:
    - all three Salt 2 reruns reached the boundary-layer stage and failed on the next OpenFOAM 13 compatibility issue, not on the earlier geometry-schema bug
    - common failure 1 in `/home1/09748/andresfierro231/tmp/slurm_case_analysis_jobs/contract_fix_salt2_*/slurm-323378*.err`:
      - OpenFOAM 13 rejects `type uniform;` and requires `type lineUniform;` in the sets dictionary
    - common failure 2, reproduced locally after fixing failure 1:
      - OpenFOAM 13 writes combined landmark outputs as `<name>.xy` with columns `x y z T Ux Uy Uz`, while the extractor still expected split `<name>_T.xy` and `<name>_U.xy`
  - Implemented and locally validated both fixes in `tools/extract/sample_streamwise_boundary_layer_landmarks.py`:
    - `write_boundary_layer_sets_dict()` now emits `type lineUniform;`
    - the extractor now accepts both legacy split `_T.xy` / `_U.xy` outputs and OpenFOAM 13 combined `.xy` outputs
  - Local compute-node Jin validation:
    - reran `python tools/extract/sample_streamwise_boundary_layer_landmarks.py --source-id viscosity_screening_salt_test_2_jin_coarse_mesh --analysis-manifest tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_jin_coarse_mesh/analysis_manifest.json --output-dir tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_jin_coarse_mesh/raw_extraction`
    - first rerun confirmed that OpenFOAM 13 now sampled successfully and wrote combined `.xy` files under `tmp_extract/ethan_streamwise_friction/.../postProcessing/streamwiseBoundaryLayerLandmarks/`
    - second rerun, after the combined-output parser patch, completed and produced:
      - `boundary_layer_landmark_profiles.csv`
      - `boundary_layer_landmark_summary.csv`
      - `boundary_layer_landmark_summary.json`
    - this is the first direct local evidence that the boundary-layer path now runs successfully on the corrected Salt 2 Jin raw extraction
  - Local Jin end-to-end validation moved from “still running” to a concrete azimuthal parser bug:
    - a direct local rerun of `sample_streamwise_azimuthal_transport.py` for Jin failed in `build_timeseries_rows()` because the shared dense-face parser assumed every selected wall patch would publish `value uniform/nonuniform` entries
    - the first failing live schema was `U` on `pipeleg_lower_01_fitting`, which is simply:
      - `type noSlip;`
      - no explicit `value` entry
    - inspection of the same Jin raw case also showed:
      - `T` thermal wall patches store the wall temperature under `Tp nonuniform List<scalar>`
      - `p_rgh` thermal wall patches use `type fixedFluxPressure;` plus a `gradient` list and no boundary `value`
  - To keep the Salt-family path shared rather than baking these exceptions into
    `sample_streamwise_azimuthal_transport.py` alone, `AGENT-072` now also owns
    `tools/extract/sample_streamwise_friction_dense_faces.py`, and that parser
    has been widened locally to:
    - accept `Tp` as the readable temperature entry for wall `T`
    - infer zero vectors for `U` no-slip walls when no explicit `value` exists
    - fill `NaN` placeholders for `p_rgh` `fixedFluxPressure` walls that do not
      publish boundary values
  - The next immediate step is to rerun the Jin azimuthal extractor after this
    parser fix, confirm that the four azimuthal artifacts are emitted, and only
    then rebuild the Jin package.
- The Jin rerun after the dense-face parser fix succeeded. The raw extraction
  now contains:
  - `azimuthal_wall_transport_geometry.csv`
  - `azimuthal_wall_transport_timeseries.csv`
  - `azimuthal_wall_transport_summary.csv`
  - `azimuthal_wall_transport_manifest.json`
- One more local script bug surfaced at that point: `sample_streamwise_azimuthal_transport.py`
  was calling `csv_dump()` with the wrong signature at final writeout. That is
  now fixed.
- The subsequent local Jin package rebuild also exposed two raw-reuse/path
  assumptions in `tools/analyze/build_ethan_case_analysis_package.py` that were
  too strict for live local recovery roots:
  - the boundary-layer summary was rejected because it reported its own scratch
    extract-case root instead of the major-loss scratch root, even though it
    explicitly pointed back to the same `leg_wall_face_geometry.csv`
  - the raw-reuse heat path insisted on frozen heat artifacts already existing
    beside the raw extraction directory, which is true for older report
    packages but false when rebuilding directly into the live local package root
- Both builder issues are now fixed:
  - the boundary-layer runtime-root mismatch is tolerated when the boundary
    summary references the same major wall-face geometry CSV as the major-loss
    summary
  - when `--raw-extraction-dir` points at the same package root being rebuilt,
    the builder regenerates the heat summary instead of insisting on reused heat
    artifacts
- Result: Salt 2 Jin now rebuilds end-to-end locally at
  `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_jin_coarse_mesh`
  with:
  - `summary.json` reporting `boundary_layer.available = true`
  - `summary.json` reporting `azimuthal_transport.available = true`
  - `streamwise_heat_loss_summary.csv`
  - `parasitic_heat_loss_summary.csv`
  - `azimuthal_transport_mean_summary.csv`
  - `boundary_layer_landmark_mean_summary.csv`
- After Jin cleared, I moved immediately to Salt 2 Kirst. Its existing live
  raw directory still only had the major-loss artifacts from the failed Slurm
  wave, so I started a fresh local rerun of
  `sample_streamwise_boundary_layer_landmarks.py` against:
  - `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_kirst_coarse_mesh/raw_extraction`
  - `analysis_manifest.json` in the same package root
- That Kirst boundary-layer rerun is active now and has already progressed
  through OpenFOAM 13 `foamPostProcess` sampling on times `583-586 s`, which is
  the first sign that the same corrected path is carrying beyond Jin.
- next steps:
  - Let the local Jin azimuthal and feature extractors finish, then rebuild the Jin package from raw extraction and inspect `summary.json`.
  - After Jin clears locally, rerun the same corrected path for Salt 2 Kirst and validation, then resume the broader Salt-family rollout.
  - Only after the shared Salt-family path is stable should the next implementation slice register Salt 4 Kirst in `tools/case_analysis_profiles.py`.
- Continued local Salt 2 completion after the Jin proof case:
  - Salt 2 Kirst local rerun sequence completed:
    - `sample_streamwise_boundary_layer_landmarks.py`
    - `sample_feature_minor_loss_budget.py`
    - `sample_streamwise_azimuthal_transport.py`
    - `build_ethan_case_analysis_package.py --raw-extraction-dir ...`
  - Resulting package root:
    - `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_kirst_coarse_mesh`
  - Verification:
    - `summary.json` reports `boundary_layer.available = true`
    - `summary.json` reports `azimuthal_transport.available = true`
    - top-level package artifacts now include `streamwise_heat_loss_summary.csv`, `parasitic_heat_loss_summary.csv`, `azimuthal_transport_mean_summary.csv`, and `boundary_layer_landmark_mean_summary.csv`
- Completed the same corrected local sequence for the Salt 2 validation case on the continuation-era retained window `8598-8602 s`:
  - local extractors:
    - `sample_streamwise_boundary_layer_landmarks.py`
    - `sample_feature_minor_loss_budget.py`
    - `sample_streamwise_azimuthal_transport.py`
  - package rebuild:
    - `python tools/analyze/build_ethan_case_analysis_package.py --source-id val_salt_test_2_coarse_mesh_laminar --raw-extraction-dir tmp/2026-06-15_live_case_analysis/contract_fix_salt2/val_salt_test_2_coarse_mesh_laminar/raw_extraction --output-dir tmp/2026-06-15_live_case_analysis/contract_fix_salt2/val_salt_test_2_coarse_mesh_laminar`
  - verification:
    - `summary.json` reports `boundary_layer.available = true`
    - `summary.json` reports `azimuthal_transport.available = true`
    - `requested_times_s` in the rebuilt validation package is `[8598.0, 8599.0, 8600.0, 8601.0, 8602.0]`
- Built the corrected Salt 2 trio comparison package:
  - `python tools/analyze/build_ethan_representative_transport_comparison.py --package-dir tmp/2026-06-15_live_case_analysis/contract_fix_salt2/val_salt_test_2_coarse_mesh_laminar --package-dir tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_jin_coarse_mesh --package-dir tmp/2026-06-15_live_case_analysis/contract_fix_salt2/viscosity_screening_salt_test_2_kirst_coarse_mesh --output-dir reports/2026-06-15_ethan_representative_transport_comparison`
  - output contents confirmed:
    - `summary.json`
    - `representative_transport_profiles.csv`
    - `representative_boundary_layer_landmarks.csv`
- Registered Salt 4 Kirst on the shared Salt-family profile map:
  - added `SALT4_KIRST_SOURCE_ID = "viscosity_screening_salt_test_4_kirst_coarse_mesh"` to `tools/case_analysis_profiles.py`
  - added `SUPPORTED_CASE_ANALYSIS_PROFILES[SALT4_KIRST_SOURCE_ID] = build_salt_family_case_profile(..., "salt4_kirst_case_v1")`
  - rationale captured in code comment: Salt 4 Kirst shares the same loop geometry, patch naming, and TP/TW layout as the rest of the Salt-family screening cases, so omission would hide a shared-contract issue rather than reflect a real geometry difference
  - validation:
    - `python -c 'from tools.case_analysis_profiles import get_case_analysis_profile; print(get_case_analysis_profile("viscosity_screening_salt_test_4_kirst_coarse_mesh").profile_name)'`
    - returned `salt4_kirst_case_v1`
- Launched the corrected live Salt-family rollout beyond Salt 2 using the documented compute-node submission path:
  - generated tracked sbatch scripts locally with `submit_ethan_case_analysis_package_sbatch.sh --dry-run` for:
    - Salt 1 Jin on `3226-3229 s`
    - Salt 1 Kirst on `3276-3279 s`
    - Salt 3 Jin on `2511-2514 s`
    - Salt 3 Kirst on `3294-3297 s`
    - Salt 4 Jin on `2079-2082 s`
    - Salt 4 Kirst on `2980-2983 s`
  - submitted those scripts through `ssh login3.ls6.tacc.utexas.edu sbatch --parsable ...`
  - new live job IDs:
    - `3234341` Salt 1 Kirst
    - `3234342` Salt 1 Jin
    - `3234343` Salt 4 Jin
    - `3234344` Salt 4 Kirst
    - `3234345` Salt 3 Kirst
    - `3234346` Salt 3 Jin
  - immediate queue check via `squeue -j 3234341,3234342,3234343,3234344,3234345,3234346` showed all six jobs running in `NuclearEnergy`
- Additional code documentation added during the same recovery window:
  - `tools/extract/sample_streamwise_friction_dense_faces.py`
    - comments explain why `T` accepts `Tp`, why `U noSlip` injects zero vectors, and why `p_rgh fixedFluxPressure` stays `NaN`
  - `tools/extract/sample_streamwise_boundary_layer_landmarks.py`
    - comment explains why the legacy geometry-in-timeseries fallback still exists for June 10 raw-reuse packages
  - `tools/analyze/build_ethan_case_analysis_package.py`
    - comments explain why same-geometry boundary summaries may come from a different scratch runtime root
    - comments explain why same-root raw rebuilds must regenerate heat artifacts instead of requiring frozen reused ones
- next steps:
  - monitor `3234341-3234346`
  - inspect each finished package root for `boundary_layer.available = true` and `azimuthal_transport.available = true`
  - after those six cases clear, run `tools/analyze/build_ethan_field_transport_campaign.py` across the full Salt-family package set
- The six-case Salt-family wave finished cleanly:
  - `3234341` Salt 1 Kirst: `COMPLETED 0:0`
  - `3234342` Salt 1 Jin: `COMPLETED 0:0`
  - `3234343` Salt 4 Jin: `COMPLETED 0:0`
  - `3234344` Salt 4 Kirst: `COMPLETED 0:0`
  - `3234345` Salt 3 Kirst: `COMPLETED 0:0`
  - `3234346` Salt 3 Jin: `COMPLETED 0:0`
- Verified all six resulting Salt-family package roots under
  `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/`:
  - `summary.json` reports `boundary_layer.available = true`
  - `summary.json` reports `azimuthal_transport.available = true`
  - required CSVs exist:
    - `streamwise_heat_loss_summary.csv`
    - `parasitic_heat_loss_summary.csv`
    - `azimuthal_transport_mean_summary.csv`
    - `boundary_layer_landmark_summary.csv`
- Updated `tools/analyze/build_ethan_field_transport_campaign.py` so the final campaign ordering/styling now includes:
  - `viscosity_screening_salt_test_4_kirst_coarse_mesh`
  - `val_water_test_1_coarse_mesh_laminar`
  - `val_water_test_2_coarse_mesh_laminar`
  - `val_water_test_3_coarse_mesh_laminar`
  - `val_water_test_4_coarse_mesh_laminar`
- Built the Salt-family field-transport campaign package:
  - `python tools/analyze/build_ethan_field_transport_campaign.py --package-dir ... --output-dir reports/2026-06-15_ethan_field_transport_campaign`
  - output contents confirmed:
    - `README.md`
    - `summary.json`
    - `field_transport_package_index.csv`
    - `field_transport_streamwise_heat_comparison.csv`
    - `field_transport_grouped_heat_comparison.csv`
    - `field_transport_azimuthal_transport_comparison.csv`
    - `figures/`
- Added water-family detailed case-analysis profiles in `tools/case_analysis_profiles.py`:
  - `val_water_test_1_coarse_mesh_laminar` -> `water1_val_case_v1`
  - `val_water_test_2_coarse_mesh_laminar` -> `water2_val_case_v1`
  - `val_water_test_3_coarse_mesh_laminar` -> `water3_val_case_v1`
  - `val_water_test_4_coarse_mesh_laminar` -> `water4_val_case_v1`
- Modeling assumption documented in code:
  - the staged water validation cases reuse the Salt-family TP/TW station map,
    major spans, feature budgets, and patch-role groupings because the staged
    OpenFOAM boundary naming and loop topology match the Salt-family cases
  - if a water case fails this shared contract later, that should be treated as
    a real geometry/profile mismatch, not papered over with a separate hidden
    path
- Water retained windows derived from the live runtime roots:
  - Water 1: `5270,5271,5272,5273,5274`
  - Water 2: `3976,3977,3978,3979,3980`
  - Water 3: `3724,3725,3726,3727,3728`
  - Water 4: `2538,2539,2540,2541,2542`
- Generated tracked sbatch scripts for the four water runs:
  - `tmp/slurm_case_analysis_jobs/contract_fix_water1/casepkg_val_water_test_1_coarse_mesh_laminar.sbatch`
  - `tmp/slurm_case_analysis_jobs/contract_fix_water2/casepkg_val_water_test_2_coarse_mesh_laminar.sbatch`
  - `tmp/slurm_case_analysis_jobs/contract_fix_water3/casepkg_val_water_test_3_coarse_mesh_laminar.sbatch`
  - `tmp/slurm_case_analysis_jobs/contract_fix_water4/casepkg_val_water_test_4_coarse_mesh_laminar.sbatch`
- Submitted the four water jobs through the same documented compute-node pattern:
  - `3234588` Water 1
  - `3234589` Water 2
  - `3234585` Water 3
  - `3234587` Water 4
- Current queue state at submission check:
  - all four water jobs are `PD (Priority)` in `NuclearEnergy`
- next steps:
  - wait for `3234585,3234587,3234588,3234589`
  - inspect each completed water package for the same availability flags
  - build the final all-Ethan campaign at `reports/2026-06-15_ethan_all_runs_field_transport_campaign`

- follow-on launch after user request for the promoted all-runs report:
  - reason the all-Ethan promoted package was not present yet:
    - the builder itself was not blocked by code anymore
    - the missing prerequisite was simply that the four water package jobs were
      still `PD (Priority)` and had not yet populated
      `tmp/2026-06-15_live_case_analysis/contract_fix_water_family/**`
  - created a dependent final-build script at:
    - `tmp/slurm_case_analysis_jobs/contract_fix_all_runs_field_transport/build_all_runs_field_transport_campaign.sbatch`
  - the script builds:
    - `reports/2026-06-15_ethan_all_runs_field_transport_campaign`
    - from the 13 package roots:
      - Salt 2 trio under `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/`
      - remaining six Salt-family cases under `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/`
      - four water validation cases under `tmp/2026-06-15_live_case_analysis/contract_fix_water_family/`
  - syntax check:
    - `bash -n tmp/slurm_case_analysis_jobs/contract_fix_all_runs_field_transport/build_all_runs_field_transport_campaign.sbatch`
  - submitted through the documented login-node path with dependency:
    - `ssh login3.ls6.tacc.utexas.edu sbatch --parsable --dependency=afterok:3234585:3234587:3234588:3234589 /scratch/09748/andresfierro231/projects_scratch/ethan_runs/tmp/slurm_case_analysis_jobs/contract_fix_all_runs_field_transport/build_all_runs_field_transport_campaign.sbatch`
  - new job id:
    - `3234859`
  - immediate queue state:
    - `3234859` is `PD (Dependency)`
    - the four water jobs remain `PD (Priority)`
