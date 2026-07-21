# Observation Table Downstream Progress

Date: `2026-07-09`
Task: `AGENT-247`
Role: Coordinator / Implementer / Tester / Writer / Cleaner

## Prompt

The user asked to proceed with the recommended next steps after completing the
July 9 canonical observation-table thermal refresh.

## Work Performed

Claimed `AGENT-247` to avoid overlap with active steady-state, Salt1 monitor,
and Salt2 mesh-repair tasks.

Refreshed `tools/analyze/build_model_form_bakeoff_from_observations.py` so it
now writes:

- `work_products/2026-07/2026-07-09/2026-07-09_model_form_bakeoff_thermal_refresh/`

The bakeoff now consumes:

- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/closure_observations.csv`
- July 7 friction-form mdot comparison
- July 7 F5 Ri-corrected comparison
- July 7 pressure term ledger

It no longer depends on the July 8 starter observation table or the old
top-level work-product paths. It carries recirculation and no-`qr` quality
summaries from the canonical observation table.

Added `tools/analyze/build_thermal_control_volume_admission_review.py`, which
compresses the July 9 thermal rows into:

- detailed control-volume admission rows;
- a 9-row thesis-facing evidence table for Salt 2/3/4 by heater,
  cooler/reducer, and junction class.

Published:

- `operational_notes/07-26/09/2026-07-09_canonical_products_and_cleanup_index.md`

This note identifies the current canonical product chain, superseded July 8
provenance packages, and cleanup candidates. The cleanup action remains
non-destructive.

## Observed Results

Model-form bakeoff refresh:

- observation rows consumed: `1032`
- case/model rows: `15`
- mdot ordering: `F3_shah_apparent`, `F5_ri_corrected`,
  `F3_hagenbach`, `F1`, `F4_leg_class`
- recirculation-flagged observation rows: `291`
- radiation-present observation rows: `0`

Thermal admission review:

- detail rows: `66`
- thesis evidence rows: `9`
- fit-eligible detail rows: `0`
- radiation-present detail rows: `0`
- heater class: validation-only but defensible in all three Salt cases
- cooler/reducer class: recirculation-contaminated in compact rollup
- junction class: recirculation-contaminated in compact rollup and still lacks
  complete residual assignment for sampled junction planes

Cleanup scale:

- `tmp/`: about `187G`
- `tmp_extract/`: about `205G`
- `work_products/2026-07-06_overnight_postprocess_jobs`: `67K`

## Validation

Commands:

- `python3 -m pytest tools/analyze/test_model_form_bakeoff_from_observations.py tools/analyze/test_thermal_control_volume_admission_review.py -q`
- `python3 -m py_compile tools/analyze/build_model_form_bakeoff_from_observations.py tools/analyze/build_thermal_control_volume_admission_review.py tools/analyze/test_model_form_bakeoff_from_observations.py tools/analyze/test_thermal_control_volume_admission_review.py`
- `python3 tools/analyze/build_model_form_bakeoff_from_observations.py`
- `python3 tools/analyze/build_thermal_control_volume_admission_review.py`

Result:

- focused tests: `6 passed`
- py-compile: passed
- both generators completed

## Interpretation Boundary

This work proves downstream tooling can consume the July 9 canonical table and
creates compact thermal validation/admission evidence. It does not rerun the
external Fluid model, mutate CFD outputs, submit jobs, or promote thermal rows
to fit targets.

Thermal model-form scoring remains limited because current model forms do not
emit comparable per-segment heat predictions. The current thermal mismatch is a
common CFD validation axis, not a model-specific score.
