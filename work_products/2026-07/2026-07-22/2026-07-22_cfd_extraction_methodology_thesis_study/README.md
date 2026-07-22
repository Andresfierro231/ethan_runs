---
provenance:
  - operational_notes/06-26/30/2026-06-30_thermal_extraction_spec.md
  - operational_notes/maps/cfd-runs-and-admission.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/pressure_reduction_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/trusted_wall_Q_wall_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/sampled_field_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_thermal_accounting_traceability_evidence_packet/thermal_accounting_traceability_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight/source_property_release_gate.csv
tags: [cfd-extraction, thesis-methodology, source-property, qwall, pressure, heat-loss]
related:
  - .agent/status/2026-07-22_TODO-CFD-EXTRACTION-METHODOLOGY-THESIS-STUDY-2026-07-22.md
  - .agent/journal/2026-07-22/cfd-extraction-methodology-thesis-study.md
  - imports/2026-07-22_cfd_extraction_methodology_thesis_study.json
task: TODO-CFD-EXTRACTION-METHODOLOGY-THESIS-STUDY-2026-07-22
date: 2026-07-22
role: cfd-pp / Thermal-modeling / Hydraulics / Writer / Reviewer
type: work_product
status: complete
---
# CFD Extraction Methodology Thesis Study

Decision: `methodology_packet_ready_no_new_release`.

This packet explains what data are extracted from CFD, how the reductions are
done, and how the outputs are allowed to be used in the thesis. It is a
methodology/support packet only. It does not release source/property values,
admit coefficients, run a sampler, score validation/holdout rows, mutate native
OpenFOAM outputs, or edit thesis LaTeX.

## What Is Extracted

The CFD postprocessing extracts seven classes of information.

First, it extracts exact source provenance: case identifier, time window,
native field path, and whether each field came from native solver output. For
the S13 exact pressure/Qwall package, the source audit records native `p`,
`p_rgh`, `wallHeatFlux`, `cellProcAddressing`, `faceProcAddressing`, and
`boundary` files at exact target windows. These files are read only.

Second, it extracts geometry masks before fields are reduced. The relevant
S13 masks are seeded recirculation control-volume cells, exchange-interface
faces, trusted-wall faces, and wall/core bands. These masks define the
integration and averaging domain. Field values are not allowed to redefine the
surface or cell set after the fact.

Third, it extracts pressure basis quantities from `p` and `p_rgh`. The exact
pressure package computes volume-averaged pressure over the seeded control
volume and area-averaged pressure over the interface, adjacent core, and
trusted-wall owner-cell basis. Salt2/Salt3/Salt4 current-coarse rows have
`pressure_basis_released=true` for exact target-window reductions. This is
pressure-basis evidence, not a component-loss admission.

Fourth, it extracts trusted-wall heat flow from native `wallHeatFlux`.
`wallHeatFlux` is integrated over the predeclared trusted-wall faces. The
native OpenFOAM integral is retained with its outward wall-normal sign, and the
reported `Q_wall_W` is defined as the negative of that native integral so that
positive `Q_wall_W` adds heat to the seeded recirculation fluid. Current
Salt2/Salt3/Salt4 target-window values are:

| case | time window | `Q_wall_W` |
| --- | ---: | ---: |
| Salt2 | 7915 s | 23.1161370708 W |
| Salt3 | 7618 s | 25.3465488205 W |
| Salt4 | 10000 s | 28.1231837021 W |

Fifth, it extracts sampled interface and wall/core fields. The limited
sampled-field package records face-level `U`, `T`, and `rho` on the exchange
interface, plus trusted-wall temperature and seeded/core temperature summaries.
The reduced summary includes interface area, area-average seed/core
temperature, seed/core density, seed/core velocity, net/positive/negative
exchange mass-flow proxies, trusted-wall area-average temperature, seeded-CV
volume-average temperature, and wall/core/bulk contrasts.

Sixth, it extracts property/source labels and release gates. These are not raw
CFD fields in the same sense as `U` or `p`; they are the provenance and
permission metadata needed to decide whether a formula may consume properties
such as `cp_J_kg_K`, viscosity, and thermal conductivity. The current nominal
train source/property labels are present, but release-ready rows remain zero.
MF13 explicitly marks `cp_basis_released` as fail-closed.

Seventh, it extracts thermal accounting and use-permission metadata. The
thermal accounting ledger separates heater source, internal Nu, wall
conduction, contact/layer resistance, insulation/quartz, external convection,
radiation, jacket/cooler removal, storage, and residual lanes. The split and
admission ledgers then state whether each reduction may be used for diagnostic
evidence, training support, model selection, holdout/external score-only use,
or not at all.

See `extracted_data_dictionary.csv` for the compact field-by-field dictionary.

## Methodology

The extraction method is contract first.

1. Select an admitted or explicitly diagnostic case/time window.
   The case and time window come from run-admission and extraction packages, not
   from convenience. The exact source field path is recorded before reduction.

2. Apply a predeclared geometry domain.
   For S13 this means the seeded recirculation CV, exchange interface, and
   trusted wall. For segment HTC/UA/Nu work it means the locked segment map and
   single-leg station masks. This prevents the method from moving a surface or
   sample window until it gives a preferred answer.

3. Reduce fields on that fixed domain.
   Pressure is volume- or area-weighted on the correct cell/face basis.
   Heat flow is integrated over trusted-wall faces. Interface exchange proxies
   use `rho U dot A` with an outward area-vector convention. Thermal contrasts
   use area or volume averages stated in the output table.

4. Preserve sign conventions.
   The S13 `Q_wall_W` sign is positive into the seeded recirculation fluid.
   The native `wallHeatFlux` outward integral remains in the table. Source-side
   heat-flow quantities are kept separate unless a later conservation/property
   contract explicitly relates them.

5. Join property and source permissions after the physical reduction.
   Property modes and source envelopes decide whether a formula can be used for
   release, fit, or model selection. They do not change the raw CFD reduction.
   Current property/source release is blocked, especially the row-level
   `cp_J_kg_K` basis needed for source-integral formulas.

6. Join uncertainty and split permissions last.
   Target-window values do not become production values by themselves. Same-QOI
   temporal windows, mesh/GCI evidence, sampler-readiness, production harvest,
   and split/admission permissions are separate gates.

The file `reduction_method_table.csv` lists these method steps as machine-readable
rows.

## Use Boundary

The CFD reductions are strong evidence for methodology, diagnostics, and
mechanism identification. They are not automatically predictive runtime inputs.
In the forward model, CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD
cooler duty, validation temperatures, holdout temperatures, and external-test
temperatures are forbidden runtime inputs unless a separate setup-only
source/property contract admits a corresponding physical input.

The most important heat-loss guardrail is unchanged: missing heat residual is
not allowed to disappear into internal `Nu`. Internal Nu is the internal
salt-side convective lane. Heater/source error, wall conduction, insulation,
external convection, radiation, cooler/jacket removal, storage, recirculation,
and residual terms remain separate owners.

See `allowed_forbidden_use_matrix.csv` for the row-level use matrix.

## Current Blockers

The most useful next blocker to unlock is now explicit on the board:
`TODO-SOURCE-PROPERTY-CP-VISCOSITY-PRESSURE-BASIS-PREFLIGHT-2026-07-22`.
It should decide, by case and QOI, whether `cp_J_kg_K`, viscosity/property mode,
pressure basis, legal source/sink inputs, and signed heat-path ownership are
ready for release or must remain blocked.

Other blockers are same-QOI neighbor windows for S13 UQ, medium/fine exact-label
sampling, pressure component isolation, and source-envelope strict-pass evidence.
See `blocker_next_work_table.csv`.

## Package Files

- `extracted_data_dictionary.csv`
- `reduction_method_table.csv`
- `allowed_forbidden_use_matrix.csv`
- `blocker_next_work_table.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state,
Fluid/external repository, thesis LaTeX/manuscript body, source/property release
state, Qwall/admission state, blocker register, or generated index was changed
by this methodology packet.
