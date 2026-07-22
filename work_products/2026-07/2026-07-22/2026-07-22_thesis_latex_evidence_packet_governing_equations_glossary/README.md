---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_ch1_ch4_foundations/equations_definitions_ledger.csv
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/17_ch5_csem_fluid_walls_model.md
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
tags: [thesis, governing-equations, glossary, definitions, external-writer]
task: TODO-THESIS-LATEX-EVIDENCE-PACKET-GOVERNING-EQUATIONS-GLOSSARY-2026-07-22
date: 2026-07-22
role: Coordinator/Writer/Reviewer/Integrator
status: current
---
# Governing Equations And Definitions Glossary

This packet gives the external thesis writer a compact, audited vocabulary for
the CSEM `fluid+walls` thesis.  It is not manuscript prose and it does not
admit new coefficients.

Use these files before writing any model-form, results, limitations, or SAM
relevance text:

- `governing_equation_ledger.csv`: equations, model slots, assumptions, and
  admission status.
- `symbol_glossary.csv`: symbols, units, and writer notes.
- `sign_convention_ledger.csv`: sign/basis conventions for heat, pressure,
  flow, and recirculation.
- `model_slot_admission_terms.csv`: definitions of admitted, diagnostic,
  blocked, fit-safe, score-only, runtime-legal, and related terms.
- `runtime_legality_ledger.csv`: allowed and forbidden runtime variables.
- `assumptions_caveats_ledger.csv`: assumptions/caveats that must travel with
  equations.
- `external_writer_brief.md`: short reading guide.

Guardrail: an equation appearing here is a model-form or bookkeeping object
unless the admission ledger says otherwise.  Do not infer admission from
notation.
