---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_heater_source_split_screen/README.md
tags: [boundary-modeling, heater-source, validation-split, journal]
related:
  - .agent/status/2026-07-14_AGENT-332.md
  - imports/2026-07-14_heater_source_split_screen.json
task: AGENT-332
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Heater Source Split Screen

Implemented the next repo-local BC-modeling task recommended by AGENT-327:
`BCM-HEATER-FRACTION-V1`.

The work converted the heater/test-section source contract into a locked-split
screen with Salt2 as train, Salt3 as validation, and Salt4 as holdout. The
screen uses the existing linearized Tmean sensitivity from the heater contract:

```text
T_pred = T_heater_only + S_test_source * DeltaQ
DeltaQ = (eta_heater - 1) * P_heater_setup
       + f_test * P_test_section_setup
       - Q_test_section_external_loss
```

The result keeps `C1_heater_only_unfitted` as the next setup-only source
contract. Two one-scalar candidates improve the Salt3/Salt4 Tmean proxy when
fit only on Salt2:

- `C2_eta_heater_fit_salt2`: `eta_heater = 0.989703290269`, Salt3/Salt4 mean
  absolute Tmean proxy reduction `2.553 K` versus C1.
- `C3_test_section_external_loss_fit_salt2`:
  `test_section_external_loss_W = 2.7358357756`, Salt3/Salt4 mean absolute
  Tmean proxy reduction `2.140 K` versus C1.

These are not final forward-v1 admissions because the package does not rerun
Fluid and only scores a linearized Tmean proxy. A future full scorecard must
report branch/sensor targets and keep the same no-runtime-cheat discipline.

Validation:

```text
python3.11 -m unittest tools.analyze.test_heater_source_split_screen
....
Ran 4 tests in 0.008s
OK
```

No native CFD solver outputs, registry/admission state, scheduler state,
generated indexes, or external Fluid files were modified.
