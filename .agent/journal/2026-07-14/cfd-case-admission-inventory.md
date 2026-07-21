---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_cfd_case_admission_inventory/cfd_case_admission_inventory.csv
  - work_products/2026-07/2026-07-14/2026-07-14_cfd_case_admission_inventory/boundary_condition_role_table.csv
  - work_products/2026-07/2026-07-14/2026-07-14_cfd_case_admission_inventory/training_validation_holdout_candidate_table.csv
tags: [journal, cfd-pp, admission, boundary-conditions, corrected-q]
related:
  - .agent/status/2026-07-14_AGENT-331.md
  - imports/2026-07-14_cfd_case_admission_inventory.json
task: AGENT-331
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
---
# CFD Case Admission Inventory

Observed: the current split admits `salt_2` for training, `salt_3` for
validation scoring, and `salt_4` for holdout scoring. None of the corrected
Salt-Q rows is admitted today; the four selected live rows remain
`blocked_pending_terminal_gate`.

Observed: the boundary-condition role table covers Salt2/3/4 mainline rows with
heater, cooler, ambient wall, junction/stub, test-section, and zero-gradient
connector roles. The `rcExternalTemperature` patches preserve emissivity `0.95`
and case-specific Tsur values, with radiation folded into total `wallHeatFlux`.

Inferred: the current CFD evidence can support existing mainline split scoring
and boundary-label provenance, but it does not expand the training set without a
new dated split revision. Corrected-Q can only become sensitivity,
validation, or holdout evidence after terminal harvest and row-specific
admission.

Blocked: Salt1 still lacks a promotion policy; Salt3 high-Q corrected attempts
need investigation before resubmission; corrected-Q live job evidence remains
pending terminal state; Kirst and the original false-steady perturbation sweep
remain excluded.

Validation passed:

```bash
python3.11 -m unittest tools.analyze.test_cfd_case_admission_inventory
```

No native CFD solver outputs were modified.
