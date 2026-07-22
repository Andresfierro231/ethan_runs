---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/upcomer_extraction_contract.csv
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/upcomer_onset_candidate_cases.csv
tags: [therm-reconstr, upcomer-recirculation, internal-nu, extraction-contract]
related:
  - tools/extract/sample_upcomer_matched_plane_metrics.py
  - tools/extract/sample_upcomer_convection_cell.py
  - tools/extract/sample_physical_segment_interface_temperatures.py
task: AGENT-341
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Upcomer Matched Plane Extraction Plan

## Decision

Existing postprocessing can provide diagnostic proxies for some matched
upcomer inlet/mid/outlet quantities, but it does not provide an admission-grade
internal-Nu dataset. Admission-grade extraction still requires a compute-node
OpenFOAM sampling pass because current raw planes do not include face areas and
do not provide station-band wall temperature plus wallHeatFlux on the same
matched planes.

## Closest Existing Scripts

- `tools/extract/sample_upcomer_convection_cell.py`: closest vector/nondim
  sampler; useful for `Ra/Ri/Gr/Re/Pr`, but its legacy metric normal is
  mean-velocity based and is not admissible for this contract.
- `tools/extract/sample_physical_segment_interface_temperatures.py`: closest
  compute-node plane-plan and raw parser pattern; it already separates signed
  mixing-cup and forward-dominant bulk temperature.
- `tools/extract/sample_span_endpoint_temperatures.py`: closest existing
  `secmeanSurfaces` parser; it recovers bulk T from rho where raw T is absent.
- `tools/extract/sample_segment_htc_uaprime.py`: closest wall T/wallHeatFlux
  sign-convention source, but it is segment-level rather than upcomer
  inlet/mid/outlet station-band matched.

## Outputs

- `upcomer_matched_plane_extraction_plan.csv`: 27 case-plane
  rows. Existing values are diagnostic proxies only where source files exist.
- `mesh_family_repeat_plan.csv`: 9 rows for Salt2
  coarse/medium/fine repeat planning.
- `existing_postprocessing_metric_status.csv`: copy of parsed plan rows for
  quick filtering by metric availability.
- `openfoam_sampling_targets.csv`: compute-node target table with station
  coordinates, geometric normals, source case paths, and representative times.
- `scripts/submit_upcomer_matched_plane_sampling.sbatch`: compute-node shell
  wrapper. It is intentionally a plan template; no heavy OpenFOAM command was
  run on the login node.

## Exact Commands

Regenerate this package:

```bash
python3.11 tools/extract/sample_upcomer_matched_plane_metrics.py \
  --output-dir work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan
```

Validate parser logic:

```bash
python3.11 -m unittest tools.extract.test_sample_upcomer_matched_plane_metrics
```

Compute-node sampling plan:

```bash
sbatch work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan/scripts/submit_upcomer_matched_plane_sampling.sbatch
```

## Compute Requirements

Use one development node, one task, about 30 minutes for the current Salt2/3/4
terminal reconstructed cases. Do not run `foamPostProcess` for the matched
planes on a login node. Corrected-Q and targeted Re cases must first pass their
terminal/admission harvest before this extractor should sample them.

## Admission Guardrails

- Existing proxy rows remain diagnostic-only.
- No GCI is invented for missing, two-level, or non-monotone mesh data.
- Repair-smoke mesh-family rows stay diagnostic until an admission gate admits
  them.
- `rcExternalTemperature` wallHeatFlux already includes radiation effects; do
  not add a separate `qr` residual unless an explicit `qr` output is sampled.
