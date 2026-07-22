# Expanded Salt Pressure-Ladder 8 PM sbatch

Task: AGENT-447
Generated: 2026-07-15

## Why This Exists

AGENT-445 already queued the nominal Salt2/Salt3/Salt4 pressure ladder. This
package expands the overnight postprocessing queue to the Salt1 training
candidate rows, Salt2 +/-5Q holdout rows, Salt4 +/-5Q training perturbation
rows, and the val_salt2 external-validation row. The goal is to make hydraulic
and closure-QOI pressure evidence available for training/validation studies
without reusing realized pressure information as a predictive-model input.

All rows here remain diagnostic until a later admission gate explicitly admits
pressure definition, mesh/GCI, branch orientation, straight-loss subtraction,
and recirculation masks.

## Included Cases

- `salt1_nominal`: Salt1 training candidate, terminal window `7284-7884`, sampled at `7884`.
- `salt1_lo10q`: Salt1 -10%Q training perturbation, terminal window `7416-8016`, sampled at `8016`.
- `salt1_hi10q`: Salt1 +10%Q training perturbation, terminal window `4987-5587`, sampled at `5587`; preserve documented conflict-resolution caveat.
- `salt2_lo5q`: Salt2 -5%Q holdout, terminal window `9975-10275`, sampled at `10275`; do not use for training/model selection.
- `salt2_hi5q`: Salt2 +5%Q holdout, terminal window `9480-9780`, sampled at `9780`; do not use for training/model selection.
- `salt4_lo5q`: Salt4 -5%Q training perturbation, terminal window `11395-11695`, sampled at `11695`.
- `salt4_hi5q`: Salt4 +5%Q training perturbation, terminal window `11099-11399`, sampled at `11399`.
- `val_salt2`: external validation coarse case, terminal window `8302-8602`, sampled at `8602`.

## Deliberate Non-Duplication

- Salt2/Salt3/Salt4 nominal pressure ladders are already covered by AGENT-445 job `3297860`.
- Salt2/Salt4 +/-10Q remain in the corrected-Q chain and are not duplicated here.
- Legacy Salt4 `balq`/`hiins` and Salt3 low/high perturbations are not promoted into this job.

## Tomorrow Unlock Plan

1. Check job `3297863` with `sacct`.
2. If terminal, run `python3.11 tools/analyze/build_expanded_salt_pressure_ladder_8pm_sbatch.py --harvest --record-job-id 3297863`.
3. Open `station_pressure_ladder.csv` and `adjacent_pressure_ladder.csv`.
4. Build an orientation table by branch using adjacent `p` and `p_rgh` trends.
5. Use branch-specific adjacent pairs to estimate straight/distributed pressure gradients before computing any local/component K.
6. Mask rows with material reverse-area fractions before any true `f_D` or `K` fit.
7. Keep all rows diagnostic until mesh/GCI, pressure definition, tap orientation, straight-loss subtraction, and recirculation gates explicitly admit them.

## Current Status

- Preflight rows: `8`
- Preflight failures: `0`
- Station planes targeted per case: `30`
- Submitted begin time: `2026-07-15T20:00:00`
- Submitted job id: `3297863`
- Latest submitted state: `SUBMITTED_BEGIN_2026-07-15T20:00:00`
- Harvested station row slots: `240`
- Harvested parsed station rows: `240`
- Harvested adjacent row slots: `192`
- Harvested parsed adjacent rows: `192`

## Guardrails

Native CFD outputs are read-only. The sbatch job writes only under
`tmp/2026-07-15_expanded_salt_pressure_ladder_8pm_sbatch` and this work-product package. Outputs are diagnostic until an
admission gate promotes them.
