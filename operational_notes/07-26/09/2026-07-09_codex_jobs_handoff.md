# Codex Jobs Handoff

Date: `2026-07-09`

This note indexes the Codex jobs completed in the current cleanup and thermal
observation-table sequence. It is meant to answer where the important outputs
landed and which rows are current evidence.

## Boundary-Condition Audit And Cleanup Dry Run

Task: `AGENT-240`

Purpose: verify documented Ethan-run boundary-condition claims against actual
OpenFOAM dictionaries and classify repo cleanup needs without destructive
actions.

Primary package:

- `work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit/`

Key files:

- `claim_verdicts.csv`
- `openfoam_case_boundary_summary.csv`
- `openfoam_field_boundary_summary.csv`
- `temperature_patch_inventory.csv`
- `target_q_restart_consistency.csv`
- `cleanup_dry_run.csv`
- `summary.json`

Operational cleanup note:

- `operational_notes/07-26/09/2026-07-09_repo_cleanup_dry_run.md`

Result:

- `6/6` documented boundary-condition claims verified against implemented
  OpenFOAM dictionaries.
- Mainline Salt 2/3/4 `0/T` dictionaries match the documented boundary family:
  `externalTemperature=10`, `rcExternalTemperature=36`, `zeroGradient=23`.
- No `constant/radiationProperties`, `qr`, or `G` radiation output was found in
  the audited roots/latest retained times.
- No native solver outputs, registry rows, staging mirrors, or external model
  files were mutated.
- Cleanup remains non-destructive: six candidates were classified, with
  deletion/move actions requiring owner review.

## Physical-Interface Thermal OpenFOAM Sampling

Task: `TODO-THERMAL-OPENFOAM-INTERFACE-SAMPLING`

Purpose: submit a bounded compute-node sampling job to bracket heater,
cooler/reducer, and junction control volumes with OpenFOAM cut planes.

Primary package:

- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/`

Key files:

- `sampling_plane_plan.csv`
- `sampling_targets.csv`
- `combined_openfoam_interface_samples.csv`
- `job_completion_summary.json`
- `local_smoke_summary.json`
- `scripts/submit_overnight_thermal_sampling.sbatch`
- `scripts/run_thermal_openfoam_interface_sampling.sh`

Scheduler:

- Job ID: `3287311`
- Job name: `th_ofsamp`
- Final state: `COMPLETED`, `ExitCode=0:0`, elapsed `00:01:20`

Result:

- Salt 2: `16/16` sampled planes OK at `t=7915`
- Salt 3: `16/16` sampled planes OK at `t=7618`
- Salt 4: `16/16` sampled planes OK at `t=10000`
- Combined: `48/48` planned rows OK, `0` missing
- Control-volume groups sampled: heater, cooler/reducer, junction
- Directional semantics preserved: signed mixing-cup temperature, positive-
  normal bulk temperature, negative-normal bulk temperature, dominant-forward
  bulk temperature, signed flux proxy, positive/negative flux proxies, and
  backflow fraction.
- Radiation output term: `absent_no_qr_output`; no `qr` was invented.

Important correction:

- After the first completion parse, the raw OpenFOAM plane parser was corrected
  for the `fields (U T rho p_rgh)` output order. The plane files were
  re-parsed without rerunning OpenFOAM, and tests now cover both raw-column
  orders.

## Canonical Observation Table Thermal Refresh

Task: `TODO-OBSERVATION-TABLE-THERMAL-REFRESH`

Purpose: make one canonical observation table for pressure, mass flow, thermal
residuals, exclusions, uncertainty placeholders, physical-interface bracketing,
recirculation flags, and no-`qr` semantics.

Primary package:

- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/`

Key files:

- `closure_observations.csv`
- `closure_observation_schema.csv`
- `excluded_sources.csv`
- `summary.json`
- `README.md`

Result:

- `1032` total observation rows
- `342` pressure rows
- `690` thermal rows
- `45` fit-eligible rows
- `1032` validation-eligible rows
- `414` observation rows from the July 9 OpenFOAM interface samples
- `195` observation rows from the July 8 physical-interface enthalpy ledger
- `291` rows with `recirculation_flag=yes`; all are
  `fit_use_status=not_fit_recirculation`
- `0` rows with `radiation_present=yes`
- Validation errors: `0`

Current canonical path for downstream closure work:

- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/closure_observations.csv`

Fit/validation policy:

- Existing pressure and approved fit targets remain fit-eligible where the
  prior contract allowed them.
- New OpenFOAM interface sample rows are validation diagnostics only.
- New physical-interface enthalpy residual rows are validation-only.
- Recirculation/backflow contaminated rows cannot validate as fit-eligible.
- Radiation is present only if OpenFOAM outputs a radiation term; the current
  canonical table records no `qr` output.

## Practical Use

Use the July 9 closure observation refresh as the canonical table for current
closure scoring and thesis validation extracts. Keep the July 8 closure table
as superseded provenance. Use the July 9 OpenFOAM sampling package when you
need raw physical-interface thermal plane evidence. Use the AGENT-240 boundary
audit when checking setup claims or explaining why radiation is absent rather
than modeled.

Do not use these packages as permission to promote thermal rows into fitting.
The new thermal rows are defensible validation evidence, but fit promotion still
requires a reviewed control-volume method and uncertainty/mesh support.
