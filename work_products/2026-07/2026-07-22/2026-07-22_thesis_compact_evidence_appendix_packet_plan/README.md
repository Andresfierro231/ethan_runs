---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract/latex_repo_compact_evidence_manifest.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_ch1_ch4_foundations/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_governing_equations_definitions_glossary_packet/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_latex_evidence_packet_ch7_ch8_results/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_latex_evidence_packet_ch9_limits_sam/README.md
tags: [thesis, evidence-packet, appendix-plan, external-writer, no-latex-writing]
related:
  - copy_no_copy_manifest.csv
  - evidence_directory_plan.md
  - appendix_table_targets.csv
  - exclusion_ledger.csv
  - summary.json
task: TODO-THESIS-COMPACT-EVIDENCE-APPENDIX-PACKET-PLAN-2026-07-22
date: 2026-07-22
role: Coordinator/Writer/Reviewer/Integrator
type: work_product
status: complete
---
# Thesis Compact Evidence Appendix Packet Plan

Decision: `compact_evidence_appendix_plan_ready_no_copy_no_latex`.

This package decides what compact evidence should be offered to the outside
thesis writer and what must stay out of any manuscript/evidence directory. It
does not copy files to `../papers`, edit LaTeX, or write chapter prose.

## Core Recommendation

Give the outside writer a small `evidence/` support layer made of packet
READMEs, CSV ledgers, source manifests, claim-boundary tables, and selected
figure/table target lists. Keep raw CFD, raw sampled fields, native OpenFOAM
case trees, broad generated figure folders, scheduler logs, and unreviewed
work-product trees out.

The evidence layer should be treated as writer context and appendix support,
not as a source of new claims. Every copied or summarized artifact must carry:

- exact source path;
- split role;
- admission state;
- runtime-leakage status;
- allowed claims;
- forbidden claims;
- open blockers or next tasks.

## File Guide

- `copy_no_copy_manifest.csv`: selected compact sources, byte sizes where
  checked, proposed destination names, and copy/summarize/no-copy policy.
- `evidence_directory_plan.md`: proposed directory/import structure for an
  outside writer or later papers-board artifact-transfer row.
- `appendix_table_targets.csv`: appendix/table suggestions and source ledgers.
- `exclusion_ledger.csv`: explicit do-not-copy categories.
- `summary.json`: machine-readable counts and guardrail flags.

## Best Immediate Use

1. Give the outside writer `evidence_directory_plan.md` and the completed
   glossary packet.
2. Use `copy_no_copy_manifest.csv` to select a small set of files for a later
   artifact-transfer row.
3. Use `appendix_table_targets.csv` to decide which source tables should become
   appendix tables or in-text evidence tables.
4. Keep manuscript prose composition outside this Codex lane.

## Do Not Do

- Do not copy or mutate `../papers/**` from this row.
- Do not write LaTeX or full thesis chapter prose.
- Do not copy native OpenFOAM trees, raw sampled fields, or broad generated
  folders.
- Do not use compact evidence packets to admit coefficients.
- Do not relax runtime-leakage, split, source/property, or uncertainty gates.
