---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_recirc_switching_calibration/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_recirc_switching_calibration/switching_calibration_template.csv
tags: [recirculation, switching-calibration, pressure-ledger, thermal-closure]
related:
  - .agent/journal/2026-07-21/litrev-recirculation-switching-calibration.md
  - imports/2026-07-21_litrev_recirc_switching_calibration.json
task: TODO-LITREV-RECIRCULATION-SWITCHING-CALIBRATION
date: 2026-07-21
role: Hydraulics / Thermal-modeling / Writer
type: status
status: complete
---

# TODO-LITREV-RECIRCULATION-SWITCHING-CALIBRATION

## Objective

Define the TAMU-specific recirculation/recovery switching calibration template
for `F_A`, `F_m`, secondary flow, stratification, velocity recovery, and
pressure-gradient recovery without selecting final numeric thresholds or
changing admission state.

## Changes Made

- Created `work_products/2026-07/2026-07-21/2026-07-21_litrev_recirc_switching_calibration/`.
- Published `switching_calibration_template.csv` with 7 switch rows.
- Published `switching_training_split_requirements.csv` with 4 split-discipline
  rows.
- Published `unresolved_threshold_fields.csv` with 6 unresolved epsilon rows.
- Published `source_manifest.csv`, `summary.json`, and package `README.md`.

## Outcome

The package defines the switch fields, required pressure/velocity/thermal bases,
training versus held-out split requirements, false-negative/model-error handling,
and next evidence needs. It selects 0 numeric thresholds and makes 0 admission
changes.

## Validation

- `python3.11 -c "import csv,json,pathlib; p=pathlib.Path('work_products/2026-07/2026-07-21/2026-07-21_litrev_recirc_switching_calibration'); assert len(list(csv.DictReader((p/'switching_calibration_template.csv').open())))==7; assert len(list(csv.DictReader((p/'switching_training_split_requirements.csv').open())))==4; assert len(list(csv.DictReader((p/'unresolved_threshold_fields.csv').open())))==6; s=json.loads((p/'summary.json').read_text()); assert s['selected_numeric_thresholds']==0; assert s['admission_status']=='no_admission_change'"` — passed.

## Guardrails

No code was added for this task. No native CFD/OpenFOAM outputs were mutated.
No registry/admission state was changed. No scheduler action,
solver/postprocessing launch, Fluid edit, external edit, fitting, tuning, model
selection, coefficient admission, universal literature-threshold import,
blocker-register edit, or generated-index refresh was performed.

## Remaining Blockers / Next Useful Action

Future threshold selection needs same-window plane definitions, signed/absolute
flux fields, transverse velocity components, wall/core thermal stratification,
same-QOI time/mesh uncertainty, source-envelope labels, and locked train/heldout
split discipline.
