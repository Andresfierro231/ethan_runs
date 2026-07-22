---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/three_level_score.csv
  - work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/section_effective_pressure_scorecard.csv
tags: [pressure-ledger, two-tap, section-effective, hybrid-pressure, status]
related:
  - .agent/journal/2026-07-21/two-tap-section-effective-hybrid-pressure-scorecard.md
  - imports/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard.json
  - work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/README.md
task: TODO-TWO-TAP-SECTION-EFFECTIVE-HYBRID-PRESSURE-SCORECARD-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-TWO-TAP-SECTION-EFFECTIVE-HYBRID-PRESSURE-SCORECARD-2026-07-21

## Objective

Build a thesis-safe section-effective hybrid pressure scorecard for
`corner_lower_right` from existing evidence only, quantifying signed pressure
residuals without admitting component `K`, F6, clipped `K`, or a hidden
multiplier.

## Changes Made

- Added `tools/analyze/build_two_tap_section_effective_hybrid_pressure_scorecard.py`.
- Added `tools/analyze/check_two_tap_section_effective_hybrid_pressure_scorecard.py`.
- Added `tools/analyze/test_two_tap_section_effective_hybrid_pressure_scorecard.py`.
- Published `work_products/2026-07/2026-07-21/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard/`.
- Added this status file, paired journal entry, import manifest, and task board row closeout.

## Outcome

Complete. The package scores `3` Salt2/Salt3/Salt4 `corner_lower_right`
section-effective pressure rows and `9` three-level rows:
observed decomposition, Salt2-frozen diagnostic transfer, and oracle envelope.

Canonical available signed residuals are:

- Salt2: `-1.25366731683 Pa`, diagnostic `K_eff_recirc=-7.56139965813`.
- Salt3: `-1.84957005859 Pa`, diagnostic `K_eff_recirc=-8.56843961125`.
- Salt4: `-1.67833900273 Pa`, diagnostic `K_eff_recirc=-5.90588330923`.

The Salt2-frozen diagnostic transfer has max Salt3/Salt4 absolute error
`0.47046606946166093438399 Pa`, or about `0.0155%` of Salt4 gross static rise.
This is thesis-useful diagnostic quantification, not a predictive admission.

## Validation

- `python3.11 -m py_compile tools/analyze/build_two_tap_section_effective_hybrid_pressure_scorecard.py tools/analyze/check_two_tap_section_effective_hybrid_pressure_scorecard.py tools/analyze/test_two_tap_section_effective_hybrid_pressure_scorecard.py` passed.
- `python3.11 -m unittest tools.analyze.test_two_tap_section_effective_hybrid_pressure_scorecard` passed: `Ran 4 tests`.
- `python3.11 tools/analyze/build_two_tap_section_effective_hybrid_pressure_scorecard.py` passed and wrote the package.
- `python3.11 tools/analyze/check_two_tap_section_effective_hybrid_pressure_scorecard.py` passed.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver/postprocessing/sampler/harvest launched: no.
- Fluid or external repo edited: no.
- Validation, holdout, or external-test rows consumed: no.
- Fitting, tuning, model selection, component-K/F6 admission, clipped `K`, hidden/global multiplier, S11/S15/S6 trigger, or final score claim: no.
- Blocker register or generated index mutated: no.
- Thesis current files edited: no.
- Residual absorbed into internal `Nu`: no.
