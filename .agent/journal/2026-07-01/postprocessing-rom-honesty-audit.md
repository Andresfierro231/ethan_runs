# Post-Processing / ROM Honesty Audit

Date: `2026-07-01`
Task: `AGENT-163`
Role: Coordinator / Writer / Reviewer

## Request

Ethan asked for a deep dive into post-processing capabilities and a
paper-facing internal note that is mathematically rigorous about:

- hard-to-understand CFD geometry records;
- possible flaws in average pressure values (`p_rgh`, corrected, absolute);
- pressure along the loop;
- HTC methodology;
- analysis left on the table;
- honest 1D model closures, correlations, and rigorous error quantification;
- reusable scripts for plotting and quantifying error across model forms.

## Coordination

Claimed a new standalone Writer/Reviewer task to avoid active overlap:

- AGENT-161 owns the existing 3D-to-1D field-reduction methods report.
- AGENT-162 owns the mesh-centerline geometry/refit lane and related extractor
  files.
- AGENT-163 owns only the new July audit report package and this status/journal.

## Work Completed

Created:

- `reports/2026-07/2026-07-01/2026-07-01_postprocessing_rom_honesty_audit/README.md`
- `reports/2026-07/2026-07-01/2026-07-01_postprocessing_rom_honesty_audit/summary.json`
- `.agent/status/2026-07-01_AGENT-163.md`

Updated:

- `.agent/BOARD.md` with the AGENT-163 row.

## Technical Findings Recorded

- Mesh geometry is the authoritative source; the schematic probe CSV should not
  be used as a geometry basis for closure derivation.
- Section-mean pressure and total pressure now exist, but heated/cooled
  non-isothermal legs need a variable-density buoyancy correction before pressure
  gradients are interpreted as friction.
- HTC/UA' extraction now uses enthalpy-flux bulk temperature; the publication
  risk is sign-convention clarity and uncertainty labeling.
- Current `f(Re)` and `Nu(Re)` fits are narrow laminar calibrations, not broad
  correlations.
- The report proposes a reusable closure-observation table plus model-form spec
  so future thesis comparisons can quantify error across closure families.

## Deferred / Not Done

- No OpenFOAM jobs were run.
- No extractor scripts were edited because those are in or adjacent to AGENT-162
  scope.
- Did not edit `operational_notes/07-26/01/2026-07-01_scaling_study_resume_later.md`
  because it is owned by AGENT-162. The audit report records the user's reminder
  that another 2026-06-30 scaling job should be resubmitted when the scaling
  study reopens.

## Validation

Static validation only:

- verify the report and summary files exist;
- parse `summary.json`;
- check cited repo paths used in the report.

Completed:

- `summary.json OK`
- report/status/journal line counts checked
- cited paths check returned `cited paths OK`

No OpenFOAM, Slurm, or heavy post-processing commands were run.
