---
provenance:
  - .agent/BOARD.md
  - operational_notes/06-26/30/2026-06-30_thermal_extraction_spec.md
  - operational_notes/maps/cfd-runs-and-admission.md
  - work_products/2026-07/2026-07-22/2026-07-22_cfd_extraction_methodology_thesis_study/README.md
tags: [cfd-extraction, methodology, thesis, journal]
related:
  - .agent/status/2026-07-22_TODO-CFD-EXTRACTION-METHODOLOGY-THESIS-STUDY-2026-07-22.md
  - imports/2026-07-22_cfd_extraction_methodology_thesis_study.json
  - work_products/2026-07/2026-07-22/2026-07-22_cfd_extraction_methodology_thesis_study/README.md
task: TODO-CFD-EXTRACTION-METHODOLOGY-THESIS-STUDY-2026-07-22
date: 2026-07-22
role: cfd-pp / Thermal-modeling / Hydraulics / Writer / Reviewer
type: journal
status: complete
---
# CFD Extraction Methodology Thesis Study

## Attempted

Checked the live board for an existing source/property/cp/viscosity/pressure
basis preflight. Existing MF13 and nominal-train source/property rows were
complete and useful, but they did not leave a narrow unclaimed row for the exact
preflight the user requested. Added
`TODO-SOURCE-PROPERTY-CP-VISCOSITY-PRESSURE-BASIS-PREFLIGHT-2026-07-22`.

Claimed and executed
`TODO-CFD-EXTRACTION-METHODOLOGY-THESIS-STUDY-2026-07-22` to publish the
methodology packet.

## Observed

The S13 exact pressure/Qwall package has exact target-window reductions for
Salt2/Salt3/Salt4. `Q_wall_W` is released as a diagnostic target-window value
with sign positive into seeded recirculation fluid, and the native outward
OpenFOAM wallHeatFlux integral is retained separately.

The limited sampled-field extraction has face-level `U`, `T`, and `rho` plus
wall/core/bulk summaries, but the rows remain limited/nonharvest and not
production-ready.

The thermal accounting ledger already separates heat paths and explicitly
forbids hiding residual heat in internal `Nu`.

MF13 reports `cp_basis_released` as fail-closed. The nominal-train source/property
preflight has complete labels but zero release-ready rows because source-envelope
strict-pass evidence is missing.

## Inferred

The thesis methodology section should describe CFD extraction as a gated
evidence pipeline: source/time provenance, fixed geometry masks, field
reduction, sign convention, property/source permission, uncertainty permission,
and split/admission permission. This is more accurate than describing the CFD
outputs as a single monolithic dataset.

The next technical unblock should not be an internal-Nu adjustment. It should be
a source/property/cp/viscosity/pressure preflight that decides whether each
formula has legal property values, source provenance, pressure basis, and heat
path ownership.

## Contradictions Or Caveats

Target-window values exist for several S13 QOIs, but same-QOI neighbor windows
are missing in the current fail-closed package. Therefore target values should
not be promoted to production harvest or admission.

`Q_wall_W` is a legitimate CFD-extracted heat-path diagnostic, but realized CFD
`wallHeatFlux` is still forbidden as a predictive runtime heat-loss input.

## Next Useful Actions

1. Claim `TODO-SOURCE-PROPERTY-CP-VISCOSITY-PRESSURE-BASIS-PREFLIGHT-2026-07-22`
   after the active source-property atlas row closes or after confirming
   non-overlap.
2. Consume the active S13 medium/fine exact-label sampler only after it closes.
3. Keep heat residual as its own owner lane until source/property, wall/cooler,
   storage, radiation, and UQ gates say otherwise.
