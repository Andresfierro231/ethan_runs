# AGENT-078 Journal

Date: `2026-06-15T18:10:00-05:00`
Role: `Coordinator / Writer`
Task: `AGENT-078`

## Intent

Write a local report that explains exactly how the readable Ethan CFD cases
model the heater, cooler, test section, and insulation, using the actual
boundary-condition files rather than only summary metadata.

## Observed state at start

- The workspace already had a strong metadata summary of wall-loss treatment in
  `reports/2026-06-04_ethan_case_metadata_index/`, but no dedicated local
  report focused specifically on the heater/cooler/test-section/insulation
  implementation question.
- A quick evidence pass showed that the cooler patch was handled differently
  from most other walls: the main cooler and adjacent reducers were fixed-`Q`
  `externalTemperature` boundaries rather than layered
  `rcExternalTemperature` walls.
- The same evidence pass also showed that the test-section patch was powered in
  salt-family cases but passive in the readable water laminar cases.

## Planned action

- Use the metadata index and recent journals to frame the setup conservatively.
- Read representative native salt and staged water/salt `case_config.yaml` and
  `0/T` files to document the actual wall models.
- Produce one local README-style report package with direct file citations and
  explicit contradiction notes where metadata and boundary files do not match
  cleanly.

## Outcome

- Added the report package:
  `reports/2026-06-15_ethan_boundary_modeling_report/README.md`
- The report documents four core conclusions from direct file evidence:
  - heater power is split across three powered `rcExternalTemperature` lower-leg
    patches with `powerLayer 1`
  - the cooler branch is imposed through fixed-`Q` `externalTemperature`
    surrogates on the cooler patch and its two reducers
  - the test section is powered in salt-family cases but passive in the
    readable water laminar cases
  - insulation is represented by explicit `thicknessLayers` in layered wall
    BCs, with family-specific outer insulation thicknesses and region-specific
    local wall stacks
- The report also records two interpretation boundaries:
  - `heater.emissivity = 0.25` in `case_config.yaml` does not match the
    observed `emissivity 0.95` in the representative `0/T` files
  - `cooler_h` exists in setup metadata, but the readable cooler patch
    implementation is fixed `Q`, so the transformation from operating metadata
    to final sink BC is not directly visible in the inspected files

## 2026-06-16 Extension

- Extended the same report in place for heavier numerical-analysis use rather
  than creating a second package.
- Added explicit sections on:
  - case-family and provenance boundaries
  - shared mesh and convergence settings
  - the three BC classes used in practice: `zeroGradient`,
    `rcExternalTemperature`, and `externalTemperature`
  - metadata-to-implementation reconciliation for heater power, heater `h`,
    ambient `Ta`, emissivity, cooler `h`, and test-section `h`
  - reusable wall-layer material families and coefficients
  - cross-case heater and cooling-branch consistency tables
  - numerical implications of fixed-`Q` cooling versus layered loss walls
- Verified from readable `0/T` files that:
  - heater power repartitions exactly across the three lower-leg patches in the
    readable cases
  - readable Jin/Kirst salt pairs appear BC-identical for the same test number
  - the cooling-branch total imposed sink exceeds nominal `cooling_power_W`
    substantially in salt cases and modestly in water cases
  - water readable test sections remain passive while readable salt-family test
    sections carry `Q = 37 W`

## 2026-06-16 Paper Threading

- Extended the active `AGENT-078` scope to a bounded paper-facing write slice
  under `../papers/3d_analysis/` so the new setup audit would not remain only
  in the local Ethan report package.
- Added the setup-modeling material to:
  - `sections/03_postprocessing_method_and_provenance.tex`
  - `sections/06_trust_limits_and_interpretation.tex`
  - `appendices/app_a_evidence_and_provenance_map.tex`
  - `notes/source_of_truth_audit.md`
  - `notes/paper_journal.md`
- The paper-side edits explicitly tell later drafters that the readable Salt
  cases are wall-surrogate thermal models rather than resolved
  conjugate-heat-transfer / coolant-jacket simulations.
- Verified the paper tree builds successfully with:
  `module load texlive/2023 && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`
  from `../papers/3d_analysis`.
- Build result: success. Remaining log noise is limited to table-width and
  underfull-box warnings in existing manuscript tables, not errors from the new
  boundary-modeling text.
