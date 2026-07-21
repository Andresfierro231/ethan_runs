---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/salt_cfd_candidate_inventory.csv
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/corrected_q_perturbation_status.csv
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/recommended_salt_split.csv
tags: [journal, cfd-pp, salt-cfd, corrected-q, admission, training-split]
related:
  - .agent/status/2026-07-14_AGENT-334.md
  - imports/2026-07-14_salt_cfd_training_evidence_inventory.json
task: AGENT-334
date: 2026-07-14
role: cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
---
# Salt CFD Training Evidence Inventory

Observed: the salt-only inventory contains 25 candidate rows and excludes water.
The only rows that can enter the current split now are Salt2 nominal for
training, Salt3 nominal for validation, and Salt4 nominal for holdout. Salt1 is
context/diagnostic only pending an explicit Salt1 policy.

Observed: corrected Salt-Q has 14 manifest rows. Job `3293924` still carries the
selected continuation rows `salt2_lo10q`, `salt2_hi10q`, `salt4_lo10q`, and
`salt4_hi10q`; a direct scheduler check at `2026-07-14T12:31:59-05:00` showed
the job running on `c318-016`. Those four rows are `pending-terminal-harvest`,
not admitted. Six non-live corrected rows are sensitivity-only/stopped, and the
failed/not-accepted rows remain excluded until a documented rerun.

Observed: the Salt2 mesh family has readable pressure/thermal repair evidence,
but mesh/GCI is diagnostic only for this inventory. Current mesh gates still
show zero publication-ready closure-QOI rows and zero fit-admissible thermal
rows.

Inferred: no corrected-Q perturbation should expand training now. Even after a
terminal gate admits a corrected-Q row, it should remain sensitivity/correlation
support unless a dated split policy explicitly permits perturbations of a
baseline to become training rows without leakage.

Boundary note: corrected-Q rows inherit the mainline thermal-boundary semantics,
but row-level patch-role/heat-ledger reduction is still pending terminal
postprocessing. `rcExternalTemperature` includes emissivity/Tsur radiation, and
OpenFOAM `wallHeatFlux` already contains that total wall heat balance.

Validation passed:

```bash
python3.11 -m unittest tools.analyze.test_salt_cfd_training_evidence_inventory
python3.11 tools/analyze/build_salt_cfd_training_evidence_inventory.py
```

No native CFD solver outputs were modified.
