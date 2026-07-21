---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/upcomer_extraction_contract.csv
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/upcomer_onset_candidate_cases.csv
  - operational_notes/maps/mesh-gci-and-uncertainty.md
tags: [therm-reconstr, upcomer-recirculation, internal-nu, extraction-contract]
related:
  - .agent/status/2026-07-14_AGENT-341.md
  - imports/2026-07-14_upcomer_matched_plane_extraction_plan.json
  - tools/extract/sample_upcomer_matched_plane_metrics.py
task: AGENT-341
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Upcomer Matched Plane Extraction Plan

## Context

The internal-Nu gate identified missing upcomer recirculation and thermal plane
metrics: reverse area fraction, reverse mass fraction, secondary velocity
fraction, direct bulk/wall temperature difference, wallHeatFlux, and local
nondimensional groups at inlet/mid/outlet planes. The extraction contract
requires geometric station normals rather than velocity-derived normals.

## Implemented

Added `tools/extract/sample_upcomer_matched_plane_metrics.py`, which builds a
dated work-product package with two evidence lanes:

- existing-postprocessing diagnostic parsing from `secmeanSurfaces` and
  `convcellSurfaces`;
- compute-node OpenFOAM target planning for admission-grade face-area and
  matched wall-band thermal sampling.

The package writes:

- `upcomer_matched_plane_extraction_plan.csv`;
- `existing_postprocessing_metric_status.csv`;
- `openfoam_sampling_targets.csv`;
- `mesh_family_repeat_plan.csv`;
- `source_manifest.csv`;
- `summary.json`;
- `scripts/submit_upcomer_matched_plane_sampling.sbatch`.

Focused parser tests live in
`tools/extract/test_sample_upcomer_matched_plane_metrics.py`.

## Observed

Existing proxy rows are available for Salt2/Salt3/Salt4 nominal terminal
reconstructed cases at their current representative times. The target table
records exact station coordinates, geometric normals, source paths, and time
windows for upcomer inlet, mid, and outlet planes.

The existing rows are not fit-admissible because current raw plane outputs lack
face areas and matched station-band `wallHeatFlux`/wall temperature. Wall thermal
fields therefore require compute-node sampling; they were not inferred or fit
from residuals.

The Salt2 coarse/medium/fine repair-smoke rows are listed only as a mesh-family
repeat plan. They remain diagnostic until an explicit admission gate admits the
same metric/sign/radiation semantics and permits monotone triplet evaluation.

## Validation

- `python3.11 -m unittest tools.extract.test_sample_upcomer_matched_plane_metrics`
- `python3.11 -m py_compile tools/extract/sample_upcomer_matched_plane_metrics.py tools/extract/test_sample_upcomer_matched_plane_metrics.py`
- `python3.11 tools/extract/sample_upcomer_matched_plane_metrics.py --output-dir work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan`

## Next

Run the supplied sbatch plan on a compute node only after selecting the admitted
terminal case set. The next extractor pass should add the temporary
`sampledSurface`/wall-band functionObject configuration and parse the resulting
face-area-weighted surfaces into admission-grade rows.

