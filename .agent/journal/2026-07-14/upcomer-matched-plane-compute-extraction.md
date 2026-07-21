---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/upcomer_extraction_contract.csv
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/upcomer_onset_candidate_cases.csv
tags: [therm-reconstr, upcomer-recirculation, internal-nu, openfoam, slurm]
related:
  - .agent/status/2026-07-14_AGENT-344.md
  - imports/2026-07-14_upcomer_matched_plane_compute_extraction.json
  - tools/extract/sample_upcomer_matched_plane_metrics.py
task: AGENT-344
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: submitted-pending
---
# Upcomer Matched Plane Compute Extraction

## Implemented

Converted the AGENT-341 diagnostic plan into a compute-node workflow. The
extractor now writes scratch-only controlDicts, samples matched upcomer planes
and wall bands, parses VTK geometry for true area weighting, classifies
candidate readiness, and documents the method.

The package explicitly separates:

- current nominal Salt2/Salt3/Salt4 rows that can run now;
- corrected-Q rows blocked on terminal harvest and representative times;
- Salt1 policy-blocked rows;
- failed corrected-Q rows;
- targeted Re150/200/250 rows that require a new CFD campaign;
- Salt2 mesh-family rows that stay in the mesh repeat plan.

## Submission

Direct `sbatch` from the current compute-node shell was refused. Submission was
made from `login3` using the repo-root `cd` pattern. The first attempt failed
because Slurm required an account; regenerated sbatch scripts now include
`#SBATCH -A ASC23046`.

Nominal Salt2/Salt3/Salt4 compute extraction was submitted as job `3295492`.
First queue check showed `PENDING (Priority)`.

## Method Boundary

Existing raw `.xy` plane files remain diagnostic. Admission-grade metrics require
the submitted VTK geometry workflow so face areas and wall-band thermal fields
are available. The parser will not invent GCI, wallHeatFlux, wall T, or
corrected-Q terminal times.

## Verification

- Unit tests passed: 9 tests.
- Python compile passed.
- Package build passed.
- Runner and sbatch shell syntax passed.
- Login-safe preflight passed.

