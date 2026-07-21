---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_sensor_tp2_restore_tw10_exclude/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_sensor_tp2_restore_tw10_exclude/summary.json
tags: [status, sensor-map, TP2, TW10]
related:
  - .agent/journal/2026-07-17/sensor-tp2-restore-tw10-exclude.md
  - imports/2026-07-17_sensor_tp2_restore_tw10_exclude.json
task: TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE
date: 2026-07-17
role: Sensor-map/Forward-pred/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE Status

## Observed Facts

- July 15 policy excluded TP2 and TW10 from aggregate scoring.
- July 16 TP2 evidence projected TP2 onto the bottom-horizontal/right-downcomer junction and produced 3 finite TP2 rows.
- TW10 remains a cooling-jacket shell surrogate with no active-HX shell-state model output.

## Changes Made

- Wrote `work_products/2026-07/2026-07-17/2026-07-17_sensor_tp2_restore_tw10_exclude/` with final TP2 restore/TW10 exclude scorecard rows.
- Preserved runtime and fit forbiddance for TP2/TW10.
- Documented before/after aggregate RMSE impact.

## Validation

- `python3 -m unittest tools.analyze.test_sensor_tp2_restore_scorecard`
- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.

## Blockers

- TP2 aggregate scoring blocker is resolved for validation-only use.
- TW10 remains blocked until the active-HX shell-state output exists.
- Generated docs index refresh was skipped because active AGENT-482 owns generated index files.
