---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate/coupled_delta_vs_m3.csv
  - tools/analyze/build_wall_temperature_drive_candidate.py
tags: [forward-model, wall-circuit, wall-temperature-drive, test-section, handoff]
related:
  - .agent/status/2026-07-17_AGENT-513.md
  - imports/2026-07-17_wall_temperature_drive_candidate.json
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-513
date: 2026-07-17
role: Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
---
# Wall-Temperature-Drive Candidate

## Why This Exists

AGENT-507 narrowed the wall/passive/test-section blocker to local
thermal-field physics. Passive-total hA and local PB2/PB3 distribution changes
could improve mdot but still made TP/TW field shape much worse than M3. The
next cautious step was to test whether the upcomer/test-section passive roles
should lose heat against a local wall state instead of bulk-fluid temperature.

## Files To Open First

1. `work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate/README.md`
2. `work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate/candidate_admission_review.csv`
3. `work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate/coupled_delta_vs_m3.csv`
4. `work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate/next_steps.csv`

## Observed Output

- `9/9` coupled Fluid rows completed with accepted package output; no timeout
  rows were produced.
- Runtime audit passed for all scenario rows.
- `18` targeted upcomer role rows used supported wall-state selectors.
- `0/3` candidates were admitted.
- WTD1 with pipe-outer-wall drive improves mdot versus M3 on validation and
  holdout but worsens all-probe and TW RMSE by tens of kelvin.
- WTD2 with outer-surface drive worsens both mdot and temperature metrics.

## Inference

Changing the passive upcomer/test-section drive from bulk to a solved wall
temperature is not sufficient to repair the coupled temperature field. The WTD1
result is important because it isolates the drive selector while preserving the
PB2 Salt2 local shape: mdot still improves, but the TW/all-probe regression
persists. That points away from another passive-loss drive tweak and toward
source placement, wall/fluid state coupling, or upcomer mixing/recirculation
physics.

## Contradictions Or Caveats

- The dry static proxy fields in `static_drive_audit.csv` are not admission
  evidence and were not consumed at runtime.
- WTD1 mdot improvement alone is not sufficient for admission; the predeclared
  gate requires mdot, all-probe RMSE, and TW RMSE to be no worse than M3 on
  validation and holdout.
- This package retained the PB2 Salt2 shape to isolate drive-selector behavior.
  It does not prove every possible wall-temperature-drive formulation is bad,
  only that this cautious next candidate is not admitted.
- The test section remains part of the upcomer lane, not an ordinary
  single-stream Nu fit row.

## Next Useful Actions

1. Continue the active heater/source redistribution lane and score it against
   the same M3 mdot/all-probe/TW gates.
2. Build an explicit test-section wall/fluid coupling candidate rather than a
   passive hA drive-only candidate.
3. Add upcomer axial mixing or pipe-plus-recirculation-cell coupling before
   attempting ordinary upcomer/test-section Nu fits.
4. Only after a candidate passes both validation and holdout coupled gates,
   freeze it for the corrected split/final predictive scorecard.

## Do Not Do

- Do not admit WTD1 from mdot improvement alone.
- Do not use validation/holdout wall proxy fields as runtime inputs.
- Do not rerun PB1/PB2/PB3 unless their source artifacts change.
- Do not mutate native OpenFOAM outputs, registry/admission state, blocker
  register, or external Fluid source.
