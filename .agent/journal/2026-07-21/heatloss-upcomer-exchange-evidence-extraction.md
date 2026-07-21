---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/exchange_cell_readiness.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/missing_exchange_nu_evidence_queue.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_matched_plane_recirc_field_harvest/matched_plane_recirc_field_harvest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/README.md
tags: [journal, heat-loss, upcomer, exchange-cell, recirculation]
related:
  - .agent/status/2026-07-21_TODO-HEATLOSS-UPCOMER-EXCHANGE-EVIDENCE-EXTRACTION.md
  - imports/2026-07-21_heatloss_upcomer_exchange_evidence_extraction.json
task: TODO-HEATLOSS-UPCOMER-EXCHANGE-EVIDENCE-EXTRACTION
date: 2026-07-21
role: Implementer/Tester/Writer/Thermal-modeling/Hydraulics
type: journal
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Upcomer Exchange Evidence Extraction

## Attempted

Converted the Phase 4/5 heat-loss blocker into a concrete pre-extraction
contract. The work joined the 3-row aggregate exchange-readiness table with the
matched-plane recirculation harvest windows and the throughflow exchange-cell
requirements. It did not launch the sampler or inspect native solver fields.

## Observed

The upcomer mainline cases have strong diagnostic reverse-flow evidence:
salt 2, salt 3, and salt 4 all carry max RAF near `0.83`, RMF near `0.57`, and
secondary-flow intensity near `0.78-0.79`. Their windows are known from the
matched-plane proxy harvest: salt 2 at `7915` s, salt 3 at `7618` s, and salt 4
at `10000` s.

The missing evidence remains the same scientific blocker: `V_recirc`,
`mdot_exchange`, `tau_recirc`, paired `T_main`/`T_recirc`, wall-core Delta T,
same-window pressure residual, and same-QOI UQ are not admission-grade.

## Inferred

The correct next modeling path is an exchange-state sampler, not an internal-Nu
patch. RAF/RMF/SVF can reject ordinary single-stream assumptions and prioritize
upcomer sampling, but they cannot define residence time or thermal exchange
energy. Existing energy residuals can support attribution narrative only; using
them as an internal-Nu correction would hide the heat-loss misalignment.

## Contradictions Or Caveats

The current sampler has useful reverse-flow/nondimensional machinery, but it is
not yet an exchange-state extractor. The package therefore publishes field and
window requirements, not final values. The case/time windows are derived from
proxy matched-plane evidence and remain non-admission-grade until a later
compute-node sampler row produces the requested fields under the same window.

## Next Useful Actions

1. Claim a sampler-design row that extends the upcomer extraction schema to
   emit `V_recirc`, `mdot_exchange`, `tau_recirc`, paired thermal states,
   pressure residual, and energy residual without fitting.
2. After design review, claim a compute-node execution row for salt 2/3/4
   mainline windows using `sbatch` or `srun`.
3. Pair same-label, same-formula, same-window mesh/time UQ with each extracted
   exchange QOI.
4. Only then run a Phase 4B exchange-readiness rescore, keeping residual
   attribution separate from internal Nu.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, external repo files, staged-copy/postprocessing jobs,
fitting/tuning/model selection, blocker register, generated docs index, or
scientific admission state were changed.
