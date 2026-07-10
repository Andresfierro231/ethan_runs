# Journal — AGENT-234 — 2026-07-09

Date: 2026-07-09
Role: Implementer / Writer
Task: AGENT-234

## Files inspected

- `AGENTS.md`, `.agent/BOARD.md`, `.agent/FILE_OWNERSHIP.md`, `.agent/ROLES.md`
- `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/pressure_decomposition_by_span.svg`
- `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/mechanical_pressure_terms_by_span.svg`
- `tools/analyze/build_postprocessor_summary_charts.py` (read-only reference)
- `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/README.md`
- Memory files: `feedback-pre-edit-protocol.md`, `feedback-output-structure-conventions.md`

## Files changed / generated

- `tools/analyze/build_pressure_decomposition_figures.py` (new)
- `tools/analyze/test_pressure_decomposition_figures.py` (new)
- `work_products/2026-07/2026-07-09/2026-07-09_pressure_decomposition_figures/figures/mechanical_pressure_stacked_by_span.svg`
- `work_products/2026-07/2026-07-09/2026-07-09_pressure_decomposition_figures/figures/pressure_budget_decomposition_by_span.svg`
- `work_products/2026-07/2026-07-09/2026-07-09_pressure_decomposition_figures/README.md`
- `work_products/2026-07/2026-07-09/2026-07-09_pressure_decomposition_figures/summary.json`
- `.agent/BOARD.md` (own row claimed)
- `.agent/status/2026-07-09_AGENT-234.md`

## Commands run

```bash
python tools/analyze/build_pressure_decomposition_figures.py
# -> {"figures": ["figures/mechanical_pressure_stacked_by_span.svg", ...], "rows": 18}

python -m pytest tools/analyze/test_pressure_decomposition_figures.py -v
# -> 17 passed in 0.38s
```

## Key observations

**Column misidentification (resolved):**
Column 40 of the pressure ledger is `distributed_mechanical_loss_pa_m` (Pa/m rate),
NOT `development_loss_pa`. Initial manual inspection suggested development losses were
18–21 Pa per span; the correct value is 0–1.9 Pa. The SVG figures are data-accurate
and were generated from the current ledger, not a stale version.

**AGENT-233 defect (Codex grouped-bar):**
`draw_horizontal_grouped_bars()` draws 3 independent sub-bars per group, all anchored
at x=LEFT (zero). A reader cannot see composition; e.g., they cannot tell if friction
or development loss dominates the total. Fixed with a stacked design where bars
accumulate left-to-right.

**AGENT-207 defect (my scale-compression):**
`draw_stacked_diverging()` computes axis range from the max positive and min negative
stacked totals across ALL rows. The upper_leg (downcomer) buoyancy of -36 to -39 Pa
dominates the negative side, setting the left axis to -40 Pa. All mechanical bars
(max ~13 Pa) are compressed into the right quarter of the axis. Fixed by:
(a) keeping the full scale to show all data honestly,
(b) adding value annotations on bars that exceed 18% of the axis range,
(c) adding case-separator dashes between Salt 2/3/4 groups to reduce visual clutter.

**Sign convention for buoyancy (confirmed correct):**
`buoyancy_contribution_pa` is negative for the upper_leg (downcomer) under the
station-order momentum-budget sign convention. This does NOT mean buoyancy is a loss.
It means the density-gradient force acts opposite to the reference positive flow
direction. Physically it drives the natural-circulation loop by pulling dense cold
fluid downward. The README and module docstring make this explicit.

**Development loss = 0 for non-entry spans (confirmed):**
test_section_span and left_upper_leg have `flow_reset_flag=False` after AGENT-197's
entry-flag fix. Their `development_loss_pa = 0`. This is physically correct: they
inherit already-developed flow from the preceding sub-span and do not experience
a fresh-entry Shah excess.

## Incomplete lines of investigation

- The right_leg (Salt 4) has the highest friction (10.5 Pa) across all spans/cases.
  This is a physical result (higher Re → higher absolute friction despite lower f/Re).
  Not investigated further here.
- Upcomer backflow fraction trend with Re (Salt 2→3→4) is consistent with the
  upcomer correlation package (AGENT-196) but not cross-checked in this task.

## Redesign round 2 (user: "crowded with text drawn on itself ... both look bad")

Rendered the first-cut SVGs to PNG and inspected pixel coordinates. Confirmed defects:
1. Case label (`Salt 2` at x=238,y=93) sat on top of the first span label
   (`lower leg (heater)` at x=242,y=87) — same right-aligned column, 6px apart.
2. The diverging decomposition chart drew overlapping colored rects: buoyancy and the
   mechanical stack shared the zero origin, so positive buoyancy (heater +5 Pa) was
   painted over the friction bar. Only the downcomer's −39 Pa diverged left, which
   also compressed the axis to [−50,+20] and squashed every other bar.

Fixes:
- Section-header rows for case grouping (no shared label column).
- Replaced the diverging chart with a **paired driver-vs-resistance** chart:
  buoyancy magnitude (green) and mechanical total (blue) on their own baselines per
  span; sign carried in the buoyancy label. No overlaps; axis is a clean 0→magnitude.
- Adopted the dataviz-skill validated palette. Ported `validate_palette.js` to Python
  (`scratchpad/validate_palette.py`) since node is unavailable on this node; confirmed
  friction #2a78d6 / dev #eb6834 / minor #4a3aa7 / buoyancy #008300 pass all checks
  (worst adjacent CVD ΔE ≈ 97, target ≥ 12; contrast all ≥ 3:1).
- Mark spec: 2px surface gaps between stacked segments, 4px rounded outer data-ends,
  recessive hairline grid, one legend, one value label per bar.
- Rendered to PNG with ImageMagick (`convert -density 110`) and visually verified no
  collisions before finalizing.

New filenames: `mechanical_loss_composition_by_span.svg`,
`buoyancy_drive_vs_resistance_by_span.svg`. Tests rewritten: 22/22 pass.

## Round 3 — modular refactor + data disclosure + presentation reference

User: "document how you made it, have the July8 presentation reference these
figures too, and make the script modular and reusable as well as very clear with
data disclosure."

Files added/changed:
- `tools/analyze/svg_chart_kit.py` (new) — reusable SVG bar-chart toolkit.
- `tools/analyze/palette_validator.py` (new) — Python port of the dataviz JS
  validator (verified against the reference palette output; identical PASS).
- `tools/analyze/build_pressure_decomposition_figures.py` — rewritten to import
  both modules; validates the palette at build time (raises on FAIL); emits
  `figure_data.csv` + `DATA_DISCLOSURE.md`; writes an in-SVG provenance comment;
  docstring now carries the 6-step "HOW THIS WAS MADE" method.
- `tools/analyze/test_svg_chart_kit.py` (new) — 15 tests for kit + validator.
- `work_products/.../2026-07-08_tomorrow_presentation_package/pressure_figures_improved_agent234.md`
  (new, additive) — points Slide 3 to the new figures; does not edit Codex files.
- `imports/2026-07-09_pressure_decomposition_figures.json` (new).

Verification:
- `python tools/analyze/palette_validator.py "#2a78d6,#eb6834,#4a3aa7,#008300"` → ALL PASS.
- Rebuilt figures; re-rendered both to PNG (`convert -density 110`) — identical clean
  output, no collisions.
- `python -m pytest test_pressure_decomposition_figures.py test_svg_chart_kit.py -q`
  → 37 passed.

Data-disclosure design decision: `figure_data.csv` holds every plotted value so a
reader can reconstruct each bar exactly; `DATA_DISCLOSURE.md` explicitly lists the
columns that are NOT used (gross_static_dp_pa, residual_pa) and why, so the
exclusion is transparent rather than silent.

Coordination note: I did not modify Codex-owned `build_postprocessor_summary_charts.py`
or the existing presentation files. If the July 8 package should regenerate these
improved figures in place (calling svg_chart_kit), that needs a claim on Codex paths —
flagged as an open question in the imports manifest.

## Next steps

- If the user wants to replace figures in `2026-07-08_postprocessor_summary_charts/`,
  that requires a BOARD claim on paths currently under AGENT-233 scope.
- The standalone script is reusable: point `--ledger` at any compatible pressure
  ledger CSV to regenerate figures for future data vintages.
- Consider adding a third figure: friction coefficient vs Re per span/case to show
  the closure convergence trend.
