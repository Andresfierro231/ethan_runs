---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/candidate_terminal_preflight.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/anchor_decision.csv
tags: [pressure-corner, low-recirculation-anchor, cfd-pp, two-tap]
related:
  - .agent/journal/2026-07-21/pressure-corner-low-recirc-anchor-harvest.md
  - imports/2026-07-21_pressure_corner_low_recirc_anchor_harvest.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/README.md
task: TODO-PRESSURE-CORNER-LOW-RECIRC-ANCHOR-HARVEST
date: 2026-07-21
role: cfd-pp/Hydraulics/Tester/Writer
type: status
status: complete
---
# Pressure-Corner Low-Recirculation Anchor Harvest Status

## Objective

Preflight same-topology `corner_lower_right` low-recirculation anchor candidates
before any staged-copy sampler or scheduler/postprocessing action.

## Outcome

Built `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/`.

`CAND-001` remains the preferred source family: Salt4 high-heat/no-recirculation
probes. It is not ready for harvest or ordinary component-K review because the
cited evidence still has terminal/scheduler state unknown and no endpoint raw
fields or RAF/RMF/SVF for `lower_leg__s04;right_leg__s00`.

Current Salt2/Salt3/Salt4 rows remain rejected as ordinary anchors because they
already fail the material reverse-flow gate. No sampler was launched and no
component-K/F6 admission changed.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-PRESSURE-CORNER-LOW-RECIRC-ANCHOR-HARVEST.md`
- `.agent/journal/2026-07-21/pressure-corner-low-recirc-anchor-harvest.md`
- `imports/2026-07-21_pressure_corner_low_recirc_anchor_harvest.json`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/build_pressure_corner_low_recirc_anchor_harvest.py`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/test_pressure_corner_low_recirc_anchor_harvest.py`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/candidate_terminal_preflight.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/source_case_readiness.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/endpoint_field_availability.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/anchor_decision.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/sampler_or_no_launch_decision.json`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/source_manifest.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/summary.json`

## Validation

- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/build_pressure_corner_low_recirc_anchor_harvest.py`
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/test_pressure_corner_low_recirc_anchor_harvest.py`
  - Result: `PASS: validated low-recirc preflight (4 candidates, 4 source cases, 15 field rows)`

## Guardrails

- Native CFD/OpenFOAM outputs: read-only, not mutated.
- Registry/admission state: not mutated.
- Scheduler/solver/postprocessing/sampler: no action launched.
- Fluid/external repos: not edited.
- Generated docs index: not refreshed.
- Scientific admission: no component-K, cluster-K, F6 fit, clipped-K, or global
  multiplier admission.
