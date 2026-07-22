---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract/evidence_packet_schema.csv
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
  - reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
  - reports/thesis_dossier/Chapters_and_sections/current/13_two_tap_recirc_section_effective_pressure_model.md
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
tags: [thesis, external-writer, evidence-packet, equations, glossary, assumptions]
related:
  - equation_ledger.csv
  - symbol_glossary.csv
  - assumptions_caveats.csv
  - claim_use_map.csv
  - source_manifest.csv
  - summary.json
task: TODO-THESIS-GOVERNING-EQUATIONS-DEFINITIONS-GLOSSARY-PACKET-2026-07-22
date: 2026-07-22
role: Writer/Reviewer/Hydraulics/Thermal-modeling
type: work_product
status: complete
---
# Thesis Governing Equations Definitions Glossary Packet

Decision: `writer_glossary_packet_ready_no_latex_no_admission`.

This package gives the outside thesis writer a compact reference for symbols,
equations, definitions, assumptions, caveats, and claim boundaries. It is not
chapter prose and it does not edit LaTeX. Its purpose is to prevent terms from
changing meaning as evidence packets are incorporated into the dissertation.

## What This Packet Supports

- Target manuscript area: methods/reduction, model form, closure admission,
  uncertainty, pressure/thermal/recirculation results, and appendix glossary.
- Writer use: use these tables to define terms consistently and attach caveats
  to claims before drafting prose.
- Admission state: `diagnostic_support_packet`; equation slots are not
  coefficient admissions.
- Runtime-leakage status: this packet repeats the forbidden runtime inputs from
  the split policy. CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler
  duty, validation temperatures, holdout targets, and external-test targets are
  not predictive runtime inputs.

## Files

- `equation_ledger.csv`: governing balances, pressure terms, thermal circuit
  slots, recirculation residual forms, and admission meaning.
- `symbol_glossary.csv`: symbols, units, sign conventions, and safe writer
  definitions.
- `assumptions_caveats.csv`: assumptions and caveats by evidence family.
- `claim_use_map.csv`: allowed/forbidden thesis uses and linked claim IDs.
- `source_manifest.csv`: source paths consumed by this packet.
- `summary.json`: machine-readable counts and guardrail flags.

## Writer Instructions

Use `equation_ledger.csv` before writing any equation in prose. Each row states
whether the equation is a balance, model slot, diagnostic residual, or admitted
term. If `slot_not_admission` is `true`, the writer may describe the slot as
part of the model architecture but must not say the coefficient is admitted.

Use `symbol_glossary.csv` for units and sign conventions. In particular:

- `Q_wall_W` is trusted-wall heat into the seeded fluid when the source package
  says so; it is not interchangeable with source-side static BC heat flow.
- `Q_source_side_net_static_bc_W` is a source-side static boundary accounting
  quantity and must not be relabeled as wall heat flux.
- `Delta_p_recirc_section` is a section-effective pressure residual lane, not
  ordinary component `K`.
- `Nu`, `f_D`, and `K` are model slots until row-level admission gates pass.
- TP/TW temperatures are score targets or diagnostic residuals, never runtime
  inputs.

Use `assumptions_caveats.csv` and `claim_use_map.csv` as caption and paragraph
guardrails. Negative results are allowed when they identify an exact missing
evidence path or forbidden reduction.

## Open Questions

- Same-QOI UQ is triplet-ready for selected S13 labels but not executed in this
  packet.
- Mesh/GCI admission for direct S13 exchange/Qwall QOIs remains separate.
- Source/property release remains separate.
- No frozen final predictive candidate exists, so final score values remain
  blocked.

## Do Not Do

- Do not edit LaTeX or manuscript files from this packet.
- Do not use this packet to admit coefficients.
- Do not hide unresolved heat or pressure residuals in internal `Nu`.
- Do not convert diagnostic pressure residuals into ordinary component `K`.
- Do not mutate native CFD/OpenFOAM outputs, registry/admission state,
  scheduler state, Fluid source, external repos, blocker register, or generated
  docs indexes.
