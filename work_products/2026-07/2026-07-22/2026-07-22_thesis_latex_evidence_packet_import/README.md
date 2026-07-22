---
provenance:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_ch1_ch4_foundations/README.md
tags: [thesis, evidence-import, external-writer, no-prose-rewrite]
related:
  - promote_papers_artifact_import_active.py
  - apply_papers_evidence_packet_import.py
  - close_papers_artifact_import.py
task: TODO-THESIS-LATEX-EVIDENCE-PACKET-IMPORT-2026-07-22
date: 2026-07-22
role: Coordinator/Writer/Reviewer/Integrator
type: work-product
status: current
---
# Thesis Evidence Packet Import

This package imports compact evidence artifacts into the CSEM dissertation repo
for an external writer.  It does not rewrite chapter prose.

Target external directory:

- `../papers/UTexas_Research/csem-Masters_dissertation/evidence/`

Imported material is limited to small Markdown and CSV files: packet index,
schema, Ch1-Ch4 foundations ledgers, claim boundaries, figure/table targets,
compact import manifest, and study dispatch matrix.

Explicitly excluded:

- native CFD/OpenFOAM case trees;
- raw sampled fields;
- broad generated figure folders;
- unreviewed numerical outputs;
- thesis chapter body rewrites.

