# T5 — All-span recirculation / Ri / Ra on mesh geometry (paper notes)

Date: 2026-07-01
Owner: claude (AGENT-162). Depends on T1 (mesh geometry). Also completes the
T1b upcomer-tool wiring (--centerline-source mesh).

## What
Added `--spans all` and `--centerline-source mesh` to
`tools/extract/sample_upcomer_convection_cell.py`. Ran all six legs on
recon_salt{2,3,4}_of13 with mesh-true centerlines.

## RESULT — recirculation is EXCLUSIVE to the upcomer
Max backflow area fraction per leg (Salt 2 / Salt 4):
| Leg               | S2 max bf | S4 max bf | alignment |
|-------------------|-----------|-----------|-----------|
| lower_leg (HEATER)    | 0.00 | 0.00 | 1.00 |
| right_leg (DOWNCOMER) | 0.00 | 0.00 | 1.00 |
| upper_leg (COOLER)    | 0.00 | 0.00 | 1.00 |
| left_lower (UPCOMER)  | 0.28 | 0.19 | 0.87-0.92 |
| test_section_span     | 0.28 | 0.27 | 0.89 |
| left_upper (UPCOMER)  | 0.34 | 0.31 | 0.86-0.94 |

## Interpretation (paper)
- Backflow (the convection cell) exists ONLY in the upcomer (left_lower +
  test_section + left_upper); heater, downcomer, cooler have ZERO backflow and
  alignment 1.00. This CONFIRMS U3: the downcomer is an ordinary non-recirculating
  leg, so its closure is f(Re)+Nu (T1b friction + T4 thermal), NOT a cell model.
- The cell is strongest at the TOP of the upcomer (left_upper backflow highest).
- Downcomer Ri_section_mean ~36-59 with zero backflow = its margin from reversal.

## CAVEAT (critical, from the prior lane)
The tool reports Ri_SECTION_MEAN (O(50-300) here). The CHARACTERISTIC Ri for the
reversal correlation is the section MEDIAN (~O(1)); mean is ~100x larger, dominated
by low-velocity cells. For the T10 correlation use Ri_streamwise = Ri_median*cos(theta),
NOT these means. These all-span values are SEED data on corrected geometry, not the
fitted correlation.

## Confidence / limits
Coarse mesh (GCI pending T6); single time per case (mainline continuation);
laminar. Ra/Ri solver definitions still need the page-audit (T9) before publishing.

## Outputs
`work_products/2026-07-01_claude_allspan_convection/upcomer_convection_cell_*.{json,csv}`.
192 tests pass (no regression from the tool edits).
