---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_anchor_request_hardening/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_cfd_anchor_matrix/upcomer_onset_anchor_matrix.csv
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress/evidence_gap_queue.csv
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress/anchor_inventory.csv
tags: [journal, upcomer, onset, cfd-anchor, postprocessing-request]
related:
  - .agent/status/2026-07-17_TODO-UPCOMER-ONSET-ANCHOR-REQUEST-HARDENING.md
  - imports/2026-07-17_upcomer_onset_anchor_request_hardening.json
task: TODO-UPCOMER-ONSET-ANCHOR-REQUEST-HARDENING
date: 2026-07-17
role: Coordinator/Implementer/Tester/Writer
type: journal
status: complete
---
# Upcomer Onset Anchor Request Hardening Journal

Task: `TODO-UPCOMER-ONSET-ANCHOR-REQUEST-HARDENING`

The request hardening pass keeps the existing CFD anchor design non-launching while making the downstream postprocessing requirements explicit. The key blocker is unchanged: current upcomer evidence is diagnostic because it lacks a non-recirculating/transition anchor, same-window wall/bulk heat fields, and mesh/time uncertainty.

The package therefore asks for a target Re/thermal-drive matrix rather than a fitted model. PM5 and PM10 are treated as 1D upcomer endpoints. Junction, corner, and stub heat/pressure entries are requested separately so future 1D work can decide whether they are explicit local losses or admissible collapsed terms.

No jobs were submitted. Future execution needs a separate board row with scheduler/staging authority, duplicate-job checks, source-case manifests, and extractor dry runs before compute spend.
