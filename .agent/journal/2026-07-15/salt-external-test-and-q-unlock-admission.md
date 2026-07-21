---
provenance:
  - .agent/status/2026-07-15_AGENT-417.md
  - work_products/2026-07/2026-07-15/2026-07-15_salt_external_test_and_q_unlock_admission/README.md
tags: [journal, salt-cfd, admission, external-test, perturbed-q]
related:
  - imports/2026-07-15_salt_external_test_and_q_unlock_admission.json
  - operational_notes/maps/cfd-runs-and-admission.md
task: AGENT-417
date: 2026-07-15
role: cfd-pp/Thermal-admission/Hydraulics/Writer/Tester
type: journal
status: complete
supersedes: []
superseded_by:
---
# Salt External-Test And Perturbed-Q Unlock Admission

The user asked to unlock Salt1, Salt3, `val_salt_test_2_coarse_mesh`, and relevant +/-Q cases, with full postprocessing confidence and thorough documentation. I claimed AGENT-417 and built a consolidation/admission package from existing evidence only.

Important observed facts:

- AGENT-415 already supplies steady TP/TW/mdot evidence for Salt1, Salt2, Salt3, Salt4, val_salt2, and selected +/-Q rows.
- AGENT-354 documents val_salt2 lineage, boundary conditions, and material properties.
- AGENT-406/414 establish that Salt2/Salt4 +/-5Q PM5 rows now have wallHeatFlux and Re/Pr/Ri fields, but F6/internal-Nu fit admission remains zero because recirculation/sign/admission gates fail.
- Job `3293924` is still the blocker for selected Salt2/Salt4 +/-10Q rows, with `3295438` held behind it.

Interpretation:

Salt1 and selected +/-5Q rows can support thermal training/testing only under explicit user-policy labels. `val_salt_test_2_coarse_mesh` is the best external-test candidate but remains blocked for thesis-strength external scoring until it has a matching section heat-loss ledger and admission package. Salt3 nominal is steady and usable under a frozen split policy, but Salt3 corrected-Q rows are not ready: low-Q rows need continuation/re-gate and high-Q rows failed.

No native CFD outputs were modified.
