# Mechanical Pressure Figure Readability

Date: 2026-07-09  
Task: AGENT-233  
Role: Coordinator / Implementer / Writer  
Owner: codex

## Trigger

The user reported that `mechanical_pressure_terms_by_span.svg` was hard to read
because the text overlapped.

## Fix

The original chart used 18 x-axis labels in a vertical grouped-bar layout. Even
with a wide figure, labels such as `Salt 2 test_section_span` collided.

Updated `tools/analyze/build_postprocessor_summary_charts.py` to add
`draw_horizontal_grouped_bars()` and render
`mechanical_pressure_terms_by_span.svg` horizontally with one row per case/span.
Span labels were shortened:

- `right_leg` -> `right/down`
- `test_section_span` -> `test section`
- `left_lower_leg` -> `left lower`
- `left_upper_leg` -> `left upper`

Regenerated:

```text
work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/mechanical_pressure_terms_by_span.svg
```

## Validation Commands

```bash
python3.11 tools/analyze/build_postprocessor_summary_charts.py --output-dir work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts
python3.11 -m py_compile tools/analyze/build_postprocessor_summary_charts.py
python3.11 -c 'import json; json.load(open("imports/2026-07-09_mechanical_pressure_figure_readability.json")); print("json ok")'
git diff --check -- .agent/BOARD.md tools/analyze/build_postprocessor_summary_charts.py work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/pressure_decomposition_misunderstanding_and_slide_fix.md imports/2026-07-09_mechanical_pressure_figure_readability.json .agent/status/2026-07-09_AGENT-233.md .agent/journal/2026-07-09/mechanical-pressure-figure-readability.md
```

## Boundary

No solver outputs, source pressure-ledger rows, or external solver-code files
were modified.
