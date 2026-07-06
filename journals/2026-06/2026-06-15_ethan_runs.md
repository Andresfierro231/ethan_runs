# Ethan Runs Update

Date: 2026-06-15

## Observed Outputs

- Opened `AGENT-071` on `.agent/BOARD.md` for the next Ethan field-transport
  phase and added a dedicated `Phase-2 Field Transport Steps` checklist to the
  board.
- Extended `tools/case_analysis_profiles.py` so the Salt-family reusable case
  profile now carries canonical `thermal_patch_roles` and
  `thermal_role_groups`.
- Added `tools/extract/sample_streamwise_azimuthal_transport.py` as the first
  phase-2 extractor entrypoint. It is designed to:
  - reconstruct retained wall fields on the local extract case
  - project wall faces onto the registered repaired streamwise coordinate
  - assign azimuthal coordinates in a local cross-plane basis
  - export:
    - `azimuthal_wall_transport_geometry.csv`
    - `azimuthal_wall_transport_timeseries.csv`
    - `azimuthal_wall_transport_summary.csv`
    - `azimuthal_wall_transport_manifest.json`
- Lightweight validation passed for the new metadata and extractor CLI:
  - `python -m py_compile tools/case_analysis_profiles.py tools/extract/sample_streamwise_azimuthal_transport.py`
  - `python tools/extract/sample_streamwise_azimuthal_transport.py --help`

## Interpretation

- The repo now has a concrete start to the post-phase-1 field-reconstruction
  campaign instead of only a verbal outline. The board, journal, and code all
  now point to the same next objective: azimuthal wall transport and explicit
  heat-loss accounting.
- Centralizing thermal-role metadata in the case profile is the right base for
  parasitic heat-loss work. It removes the duplicated patch-role constants that
  were scattered across older reporting tools and gives later extractors and
  package builders one canonical classification path.
- The new azimuthal extractor is the correct first implementation slice because
  it prepares the raw `s/theta` wall data needed for:
  - azimuthal friction-factor reductions
  - local `q''(s, theta)` and reduced `q'(x)` curves
  - cumulative `Q(x)` and role-grouped parasitic-loss accounting
  - future `theta x s` maps for cross-case comparison

## Contradictions / Caveats

- This slice does not yet compute final azimuthal `Cf` / Darcy `f_D` products
  or the streamwise parasitic-loss summaries for all runs. It establishes the
  canonical metadata and raw extractor interface those later reductions will
  consume.
- The current thermal-role grouping is registered only for the Salt-family
  profile path. Water-family cases still need equivalent profile metadata
  before the same field-transport pipeline can be trusted across all 13 Ethan
  runs.
- The new extractor has only been statically validated and CLI-smoked on the
  login node. It still needs a real compute-node retained-field run before the
  geometry projection and wall-field parsing should be treated as review-clean.
- The June 12 all-run campaign remains monitor-first. None of this phase-2
  work should be retroactively read into that package until the new field
  outputs are actually generated and consumed by a dedicated builder.

## Suggested Next Actions

- Run `tools/extract/sample_streamwise_azimuthal_transport.py` on the matched
  Salt 2 trio through the existing compute-safe case-analysis workflow and
  inspect the emitted `s/theta` summaries for continuity and role coverage.
- Extend the per-case case-analysis package path so it consumes the new
  azimuthal CSVs and emits:
  - streamwise `q'(x)` summaries
  - cumulative `Q(x)` summaries
  - role-grouped parasitic-loss tables
- Add a dedicated field-transport campaign builder rather than stretching the
  June 12 monitor-first campaign.
- Register equivalent thermal-role metadata for the water-family profiles
  before attempting an all-13-run field-reconstruction rollout.

## Checkpoint / Stopping Point

- Durable coordination for this phase now exists in:
  - `.agent/BOARD.md` under `AGENT-071`
  - `.agent/status/2026-06-15_AGENT-071.md`
  - `.agent/journal/2026-06-15/coordinator-implementer-field-transport-phase2.md`
- The first code slice for phase 2 now exists in:
  - `tools/case_analysis_profiles.py`
  - `tools/extract/sample_streamwise_azimuthal_transport.py`
- Validation for this slice remained lightweight and local; no compute-node
  extraction has been run yet for the new azimuthal transport path.

## Later Same-Day Update: Salt 2 Acceptance Gate

### Observed Outputs

- Completed the corrected local Salt 2 recovery path for:
  - `viscosity_screening_salt_test_2_jin_coarse_mesh`
  - `viscosity_screening_salt_test_2_kirst_coarse_mesh`
  - `val_salt_test_2_coarse_mesh_laminar`
- Each rebuilt package under
  `tmp/2026-06-15_live_case_analysis/contract_fix_salt2/**` now contains:
  - `major_loss_summary.csv`
  - `thermal_streamwise_summary.csv`
  - `streamwise_heat_loss_summary.csv`
  - `parasitic_heat_loss_summary.csv`
  - `azimuthal_transport_mean_summary.csv`
  - `azimuthal_wall_transport_summary.csv`
  - `boundary_layer_landmark_summary.csv`
  - `summary.json`
- Verified package flags:
  - Salt 2 Jin: `boundary_layer.available = true`, `azimuthal_transport.available = true`
  - Salt 2 Kirst: `boundary_layer.available = true`, `azimuthal_transport.available = true`
  - Salt 2 validation: `boundary_layer.available = true`, `azimuthal_transport.available = true`
- The corrected validation package is explicitly on the continuation-era retained
  window `8598-8602 s`; this is not the older June 10 validation window.
- Built the trio comparison package at
  `reports/2026-06-15_ethan_representative_transport_comparison/` with:
  - `representative_transport_profiles.csv`
  - `representative_boundary_layer_landmarks.csv`
  - `summary.json`

### Interpretation

- The Salt 2 trio is now the first review-clean proof that the field
  postprocessing path can produce streamwise friction, effective HTC/thermal
  resistance, heat-loss, parasitic-loss, azimuthal wall transport, and
  first-pass boundary-layer landmarks from the same corrected workflow.
- The compatibility work is no longer hypothetical. The corrected path has now
  been exercised end-to-end on three cases with two materially different
  runtime windows:
  - the Jin/Kirst Salt 2 screening windows
  - the later validation continuation window
- This is the first point where the phase-2 workflow can be treated as a real
  reusable Salt-family method instead of a single-case local experiment.

### Contradictions / Caveats

- “Validation” in the trio comparison now means the current continuation-root
  retained window `8598-8602 s`, not the historic June 10 packaged window.
  Any direct figure-to-figure comparison against older validation products must
  acknowledge that provenance shift.
- Boundary-layer outputs remain first-pass landmark metrics sampled on
  representative wall-to-centerline lines. They should not be described as a
  full boundary-layer closure model.

### Suggested Next Actions

- Roll the same corrected package path across the remaining Salt-family cases.
- Register Salt 4 Kirst on the shared case profile map rather than leaving it
  out as a silent exception.
- After the remaining Salt-family cases finish, build the broader
  field-transport comparison package from the per-case outputs.

## Later Same-Day Update: Remaining Salt-Family Wave

### Observed Outputs

- Registered `viscosity_screening_salt_test_4_kirst_coarse_mesh` in
  `tools/case_analysis_profiles.py` as `salt4_kirst_case_v1` on the same shared
  Salt-family profile path as the other salt screening cases.
- Generated new tracked sbatch scripts for the remaining Salt-family cases and
  submitted them through the documented `ssh login3.ls6.tacc.utexas.edu sbatch
  --parsable ...` path.
- Active corrected-wave job IDs:
  - `3234341` Salt 1 Kirst
  - `3234342` Salt 1 Jin
  - `3234343` Salt 4 Jin
  - `3234344` Salt 4 Kirst
  - `3234345` Salt 3 Kirst
  - `3234346` Salt 3 Jin

### Interpretation

- The remaining Salt-family rollout is now a compute-runtime problem rather
  than a known parser/contract problem.
- Salt 4 Kirst is no longer a structural omission in the workflow. If it fails
  now, that failure should be treated as a real shared-pipeline issue rather
  than a missing-registration artifact.

### Contradictions / Caveats

- These six cases were submitted after the Salt 2 corrected path was proven,
  but they were not yet finished at the time of this journal update.
- The broader Salt-family field-transport campaign should not be declared
  complete until those six package roots are inspected for the same availability
  flags that now pass on the Salt 2 trio.

### Suggested Next Actions

- Inspect `summary.json` for each finished Salt 1 / Salt 3 / Salt 4 package.
- Require `boundary_layer.available = true` and `azimuthal_transport.available = true`
  before promoting a case to the final Salt-family comparison set.
- Once all salt cases clear, run `tools/analyze/build_ethan_field_transport_campaign.py`
  across the full Salt-family package collection.

## Later Same-Day Update: Salt-Family Campaign Closed

### Observed Outputs

- The remaining Salt-family wave finished successfully:
  - Salt 1 Jin / Kirst
  - Salt 3 Jin / Kirst
  - Salt 4 Jin / Kirst
- All six resulting package roots under
  `tmp/2026-06-15_live_case_analysis/contract_fix_salt_family/` report:
  - `boundary_layer.available = true`
  - `azimuthal_transport.available = true`
- Built the Salt-family field-transport campaign package at
  `reports/2026-06-15_ethan_field_transport_campaign/`.
- That package now contains:
  - `README.md`
  - `summary.json`
  - `field_transport_package_index.csv`
  - `field_transport_streamwise_heat_comparison.csv`
  - `field_transport_grouped_heat_comparison.csv`
  - `field_transport_azimuthal_transport_comparison.csv`
  - figure outputs for streamwise heat-loss and circumferential-mean azimuthal transport comparisons

### Interpretation

- The Salt-family detailed field-postprocessing path is now complete as a
  reusable workflow, not just a set of individual package proofs.
- The remaining work for “all Ethan runs” is no longer in the salt path. It is
  entirely the water-family extension plus the final all-runs aggregation.

### Contradictions / Caveats

- Salt-family completeness does not yet imply all-run completeness.
- Water-family still needed detailed case-analysis profile registration at this
  point in the day.

### Suggested Next Actions

- Register water-family cases on the shared case-analysis profile path.
- Launch the four water detailed package builds on the corrected workflow.
- After those finish, build the final all-Ethan field-transport campaign.

## Later Same-Day Update: Water-Family Launch

### Observed Outputs

- Added four detailed water-family case-analysis profiles:
  - `water1_val_case_v1`
  - `water2_val_case_v1`
  - `water3_val_case_v1`
  - `water4_val_case_v1`
- The implementation keeps the water rollout on the same shared case-analysis
  path as the Salt-family workflow.
- Derived retained windows from the current staged runtime roots:
  - Water 1: `5270-5274 s`
  - Water 2: `3976-3980 s`
  - Water 3: `3724-3728 s`
  - Water 4: `2538-2542 s`
- Generated tracked sbatch scripts for all four water cases and submitted them
  through the documented compute-node pattern.
- Water job IDs:
  - `3234588` Water 1
  - `3234589` Water 2
  - `3234585` Water 3
  - `3234587` Water 4

### Interpretation

- The final all-runs path is now in the same state Salt-family was in before
  its last compute wave: shared code path is ready, tracked jobs are submitted,
  and the remaining work is package completion plus one final campaign build.
- Reusing the same span/feature/thermal-role structure for water is a deliberate
  shared-geometry assumption, not an automatically derived fact. That is the
  right engineering default here because the staged water cases expose the same
  loop boundary naming and topology as the Salt-family cases.

### Contradictions / Caveats

- At this checkpoint the water jobs were still pending in queue due to priority,
  so the final all-runs package could not yet be built.
- If any water case violates the shared geometry/profile contract at runtime,
  that should trigger a shared-profile correction, not a hidden water-only fork.

### Suggested Next Actions

- Wait for the four water jobs to finish.
- Require the same two availability flags on each water package:
  - `boundary_layer.available = true`
  - `azimuthal_transport.available = true`
- Then build the final all-Ethan field-transport campaign at
  `reports/2026-06-15_ethan_all_runs_field_transport_campaign/`.

## End-Of-Day Handoff For Tomorrow

### Observed Outputs

- The final all-Ethan field-transport package is not missing because of an
  unfinished code path. It is waiting on the four submitted water package jobs:
  - `3234588` Water 1
  - `3234589` Water 2
  - `3234585` Water 3
  - `3234587` Water 4
- A dependent final-build Slurm job has already been launched:
  - `3234859` `allruns_field_transport`
  - dependency:
    `afterok:3234585:3234587:3234588:3234589`
- The dependent script is:
  - `tmp/slurm_case_analysis_jobs/contract_fix_all_runs_field_transport/build_all_runs_field_transport_campaign.sbatch`
- Its target output is:
  - `reports/2026-06-15_ethan_all_runs_field_transport_campaign/`
- Existing promoted field-transport packages already available now:
  - representative Salt 2 transport comparison:
    `reports/2026-06-15_ethan_representative_transport_comparison/`
  - Salt-family field-transport campaign:
    `reports/2026-06-15_ethan_field_transport_campaign/`
- Current streamwise transport products already present in durable report form:
  - representative `f(x)` and effective `HTC(x)` in
    `reports/2026-06-15_ethan_representative_transport_comparison/representative_transport_profiles.csv`
  - salt-family streamwise heat and azimuthal friction means in:
    - `reports/2026-06-15_ethan_field_transport_campaign/field_transport_streamwise_heat_comparison.csv`
    - `reports/2026-06-15_ethan_field_transport_campaign/field_transport_azimuthal_transport_comparison.csv`
- The DMDC manuscript was updated to use the canonical June 12/15 Ethan
  all-run campaign as the umbrella evidence layer. Key paper-facing outputs now
  live in the neighboring paper repo:
  - `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/frontmatter/abstract.tex`
  - `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/sections/03_source_artifacts.tex`
  - `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/sections/08_ethan_cfd_scope_status.tex`
  - `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/sections/10_ethan_steady_state_representatives.tex`
  - `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/sections/11_ethan_validation_ambient_loss.tex`
  - `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/sections/12_ethan_follow_on_analysis.tex`
  - `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/sections/07_conclusions.tex`
  - manuscript provenance note:
    `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/2026-06-15_ethan_all_run_campaign_update.md`
- The DMDC paper build was verified successfully after those edits with:
  - `module load texlive/2023 && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`
- Canonical ParaView component-view figure routing was normalized. The durable
  tree is now:
  - `figures/figures_rendered/paraview_field_families/<component>/<field>/<filetype>/`
- Field names currently used in that canonical component tree are:
  - `temperature`
  - `velocity`
  - `x_vel`
  - `y_vel`
  - `z_vel`
- Example of the new canonical image location:
  - `figures/figures_rendered/paraview_field_families/upcomer/y_vel/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_last_timestep_velocity_y_slice.svg`

### Interpretation

- Tomorrow's highest-value work is not to reopen the Salt-family method. That
  path is already complete enough to wait on queued water jobs.
- The only real blocker to the promoted all-Ethan field-transport package is
  scheduler/runtime progress on the four water jobs. The final aggregation
  launch itself is already handled by the dependent job `3234859`.
- The manuscript and figure-organization work from this session is already in a
  handoff-safe state. It should not be redone; it only needs to be cited or
  reused.
- The board is not administratively clean even though several slices are
  functionally complete. Some active tasks now mostly need closure bookkeeping,
  not more implementation.

### Contradictions / Caveats

- `reports/2026-06-15_ethan_all_runs_field_transport_campaign/` does not exist
  yet at this checkpoint. Do not cite it until `3234859` runs and writes the
  package.
- The four water package jobs are still `PD (Priority)` as of this handoff, and
  the dependent all-runs builder is `PD (Dependency)`.
- ParaView component-view outputs are in the new normalized tree, but ParaView's
  known post-write MPI shutdown segfault still applies. Artifact existence plus
  status JSON remain the success criteria rather than raw `pvbatch` exit code.
- The paper repo and the Ethan repo now both contain related same-day context,
  but the canonical paper-facing prose is in the paper repo while the canonical
  all-run scientific handoff remains in
  `../cfd-modeling-tools/cross_model_comparison/campaigns/2026-06-12_ethan_postprocessing_all_runs_v1/reports/2026-06-15_paper_handoff.md`.
- `.agent/BOARD.md` still lists several tasks under `Active` that may need only
  administrative closure:
  - `AGENT-070`
  - `AGENT-071`
  - `AGENT-073`
  - `AGENT-075`
  - `AGENT-072` remains truly active until the water jobs and `3234859` finish

### Suggested Next Actions For Tomorrow

- First, check queue state:
  - `squeue -j 3234585,3234587,3234588,3234589,3234859`
  - `sacct -j 3234585,3234587,3234588,3234589,3234859`
- If the four water jobs finished successfully:
  - inspect each water package root under
    `tmp/2026-06-15_live_case_analysis/contract_fix_water_family/`
  - require:
    - `boundary_layer.available = true`
    - `azimuthal_transport.available = true`
- Then verify the dependent all-runs job `3234859` produced:
  - `reports/2026-06-15_ethan_all_runs_field_transport_campaign/`
- If `3234859` failed or did not run after the water jobs completed:
  - inspect:
    - `tmp/slurm_case_analysis_jobs/contract_fix_all_runs_field_transport/slurm-3234859.out`
    - `tmp/slurm_case_analysis_jobs/contract_fix_all_runs_field_transport/slurm-3234859.err`
  - rerun the same sbatch script manually if needed
- Once the all-runs package exists:
  - inspect its `README.md`, `summary.json`, and comparison CSVs
  - confirm that the promoted package now covers all 13 runs
- After the field-transport package clears, do board cleanup:
  - close `AGENT-072` if the all-runs package is present and review-clean
  - review whether `AGENT-070`, `AGENT-071`, `AGENT-073`, and `AGENT-075`
    should be moved out of `Active`
- If manuscript work resumes tomorrow:
  - use the DMDC manuscript note
    `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/2026-06-15_ethan_all_run_campaign_update.md`
    as the immediate source-of-truth summary
  - preserve the current `FIXME` comments as explicit literature/methods gaps
    rather than silently resolving them without evidence

### Practical Restart Pointers

- Ethan queue / coordination state:
  - `.agent/BOARD.md`
  - `.agent/status/2026-06-15_AGENT-072.md`
  - `.agent/status/2026-06-15_AGENT-075.md`
- Detailed same-day transport implementation log:
  - `.agent/journal/2026-06-15/coordinator-implementer-field-transport-package-and-submissions.md`
- Detailed same-day ParaView layout/render log:
  - `.agent/journal/2026-06-15/coordinator-implementer-paraview-field-family-expansion.md`
- Paper-facing same-day provenance:
  - `/scratch/09748/andresfierro231/projects_scratch/papers/dmdc_analysis/notes/2026-06-15_ethan_all_run_campaign_update.md`

### June 22 Retrospective Status

- The June 15 checkpoint note above was accurate at the time it was written.
- Since then, `AGENT-073` and `AGENT-075` were closed and moved out of
  `Active`, so the ParaView notes from this checkpoint should no longer be read
  as pending closure bookkeeping.
- The remaining live caveats are runtime/format boundaries, not incomplete
  figure-family implementation:
  - post-write ParaView MPI shutdown can still exit noisily
  - representative movie delivery is currently durable frame sequences plus
    `frames_only`/`.ogv` status, not MP4 packaging
