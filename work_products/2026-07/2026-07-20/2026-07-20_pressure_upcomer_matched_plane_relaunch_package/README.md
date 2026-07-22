---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/upcomer_onset_candidate_cases.csv
tags: [therm-reconstr, upcomer-recirculation, internal-nu, openfoam]
related:
  - tools/extract/sample_upcomer_matched_plane_metrics.py
  - work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package/method_trace.md
task: AGENT-344
date: 2026-07-20
role: Implementer/Tester/Writer
type: work_product
status: active
---
# Upcomer Matched Plane Compute Extraction

## Status

This package converts the AGENT-341 diagnostic plan into a compute-node
workflow. It generated 23 candidate readiness rows:
7 runnable now, 4
dependency-gated, and 12 blocked by policy, failed runs,
missing terminal harvest, or missing targeted CFD cases.

## Commands

Build or refresh this package:

```bash
python3.11 tools/extract/sample_upcomer_matched_plane_metrics.py build-openfoam-package \
  --output-dir work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package
```

Login-safe preflight:

```bash
bash work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package/scripts/run_upcomer_matched_plane_compute.sh preflight
```

Submit nominal Salt2/Salt3/Salt4 compute extraction:

```bash
sbatch work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package/scripts/submit_nominal_upcomer_matched_plane_compute.sbatch
```

Submit corrected-Q dependency extraction after harvest jobs:

```bash
sbatch --dependency=afterok:3295437:3295438 \
  work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package/scripts/submit_corrected_q_dependency_upcomer_matched_plane_compute.sbatch
```

## Outputs

- `candidate_readiness_matrix.csv`
- `slurm_submission_log.csv`
- `matched_plane_metrics_admission.csv`
- `mesh_family_repeat_status.csv`
- `method_trace.md`
- `scripts/run_upcomer_matched_plane_compute.sh`

No native CFD solver outputs are mutated; scratch reconstructions live under
`tmp/2026-07-20_pressure_upcomer_matched_plane_relaunch_package/`.
