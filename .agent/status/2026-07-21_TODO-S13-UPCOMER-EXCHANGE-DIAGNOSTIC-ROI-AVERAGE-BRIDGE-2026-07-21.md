---
provenance:
  - tools/extract/build_s13_upcomer_exchange_diagnostic_roi_average_bridge.py
  - tools/extract/test_s13_upcomer_exchange_diagnostic_roi_average_bridge.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge/diagnostic_roi_average_metrics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge/proxy_admission_support_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge/diagnostic_roi_average_bridge.csv
tags: [s13, upcomer-exchange, diagnostic-proxy, roi-average, status]
related:
  - .agent/journal/2026-07-21/s13-upcomer-exchange-diagnostic-roi-average-bridge.md
  - imports/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_roi_patch_alignment_audit/README.md
task: TODO-S13-UPCOMER-EXCHANGE-DIAGNOSTIC-ROI-AVERAGE-BRIDGE-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-S13-UPCOMER-EXCHANGE-DIAGNOSTIC-ROI-AVERAGE-BRIDGE-2026-07-21

## Objective

Compute a clearly diagnostic ROI-average fallback for S13 from existing
whole-mesh cell VTK, cell volumes, reverse-flow masks, topology interface
areas, and static source/sink ledgers while keeping production harvest and
admission disabled.

## Outcome

Complete as diagnostic-only/no-release. Published
`work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge/`.

The package carries one generated diagnostic basis. `diagnostic_roi_average_bridge.csv`
and `diagnostic_roi_average_metrics.csv` are identical dominant-component
ROI-average tables, and `proxy_admission_support_matrix.csv` contains five
non-admissible support indicators per case.

Dominant-component proxy results:

- Salt2: `V_recirc_proxy=5.67507313777e-05 m3`,
  `mdot_exchange_proxy=0.0805548458516 kg/s`,
  `tau_recirc_proxy=1.38090988886 s`, `T_recirc_proxy=444.800554947 K`.
- Salt3: `V_recirc_proxy=5.85459031166e-05 m3`,
  `mdot_exchange_proxy=0.0964918191233 kg/s`,
  `tau_recirc_proxy=1.18344032993 s`, `T_recirc_proxy=457.683301576 K`.
- Salt4: `V_recirc_proxy=5.90806538276e-05 m3`,
  `mdot_exchange_proxy=0.109435101294 kg/s`,
  `tau_recirc_proxy=1.04676755296 s`, `T_recirc_proxy=473.085704255 K`.

All proxy rows are nonadmissible. `Q_wall_W` remains blocked because no trusted
wall/core band or wallHeatFlux integration has been released.

## Changes Made

- Added `tools/extract/build_s13_upcomer_exchange_diagnostic_roi_average_bridge.py`.
- Added `tools/extract/test_s13_upcomer_exchange_diagnostic_roi_average_bridge.py`.
- Generated/updated diagnostic proxy CSVs, guardrails, source manifest,
  README, and summary.
- Added this status file, journal entry, and import manifest.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_diagnostic_roi_average_bridge.py tools/extract/test_s13_upcomer_exchange_diagnostic_roi_average_bridge.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_diagnostic_roi_average_bridge`:
  passed, `4` tests.
- `python3.11 tools/extract/build_s13_upcomer_exchange_diagnostic_roi_average_bridge.py`:
  passed and generated `3` diagnostic proxy rows.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge --strict`:
  passed.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge`:
  passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-S13-UPCOMER-EXCHANGE-DIAGNOSTIC-ROI-AVERAGE-BRIDGE-2026-07-21`:
  passed.
- `python3.11 tools/docs/build_repo_index.py --check`:
  passed, blocker register OK.

## Unresolved Blockers

- The bridge uses blocked dominant velocity components, so the proxy values are
  scale diagnostics only.
- No released source-bounded CV, trusted exchange surface, trusted wall/core
  band, `Q_wall_W`, same-window UQ, S11/S15/S6 trigger, coefficient, or
  production harvest exists.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver/postprocessing/surface extraction/sampler/harvest launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, or exchange-cell admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Residual absorbed into internal `Nu`: no.
