# Pressure Decomposition Slide Fix

Date: 2026-07-09  
Task: AGENT-232  
Role: Coordinator / Implementer / Writer  
Owner: codex

## Trigger

The user noted that the pressure-decomposition figure still looked wrong to an
initial viewer: `right_leg` and `test_section_span` also had negative
density-gradient terms, and the `upper_leg` appeared to dominate pressure drop.
The user also emphasized the physical loop directions:

- `right_leg` goes down with gravity.
- `left_lower_leg + test_section_span + left_upper_leg` goes up against gravity.

## Finding

The regenerated signed decomposition was mathematically closer than the first
chart, but it was still not presentation-safe. It mixed:

- irreversible mechanical loss terms, and
- signed `p_rgh` density-gradient source/cancellation terms.

That visual framing made the upper leg look like a large pressure-loss span even
though its de-buoyed distributed friction is only about `6-7 Pa`.

## Fix

Updated `tools/analyze/build_postprocessor_summary_charts.py` to emit a new
primary pressure figure:

```text
work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/mechanical_pressure_terms_by_span.svg
```

This figure shows:

- de-buoyed distributed friction target
- development/reset estimate
- minor-loss upper bound

It excludes the signed density-gradient source terms from the primary slide.

Updated Slide 3 in:

```text
work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/slide_outline_with_speaker_notes.md
```

Added:

```text
work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/pressure_decomposition_misunderstanding_and_slide_fix.md
```

## Validation Commands

```bash
python3.11 tools/analyze/build_postprocessor_summary_charts.py --output-dir work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts
python3.11 -m py_compile tools/analyze/build_postprocessor_summary_charts.py
python3.11 -c 'import json; json.load(open("imports/2026-07-09_pressure_decomposition_slide_fix.json")); print("json ok")'
git diff --check -- .agent/BOARD.md tools/analyze/build_postprocessor_summary_charts.py work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/slide_outline_with_speaker_notes.md work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/pressure_decomposition_misunderstanding_and_slide_fix.md imports/2026-07-09_pressure_decomposition_slide_fix.json .agent/status/2026-07-09_AGENT-232.md .agent/journal/2026-07-09/pressure-decomposition-slide-fix.md
```

## Boundary

No native OpenFOAM outputs, external solver code, or source pressure-ledger rows
were modified.
