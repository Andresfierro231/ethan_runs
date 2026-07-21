---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_paper_results_section/paper_results_section.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_paper_results_section/table_ready_claim_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_paper_results_section/caption_text.md
tags: [pressure-ledger, pressure-corner, publication-writing, section-effective]
related:
  - .agent/status/2026-07-21_TODO-PRESSURE-CORNER-PAPER-RESULTS-SECTION.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_paper_results_section/README.md
task: TODO-PRESSURE-CORNER-PAPER-RESULTS-SECTION
date: 2026-07-21
role: Writer / Reviewer / Hydraulics
type: journal
status: complete
---

# Pressure Corner Paper Results Section

## Attempted

I converted the pressure-corner publication freeze and comparison/admission
review into paper-facing prose and a table-ready claim ledger. The builder reads
the frozen/comparison rows and writes methods, results, limitations, captions,
and a compact row ledger.

## Observed

The three current Salt2/Salt3/Salt4 rows all remain `section_effective`. Gross
static pressure rise is positive, hydrostatic contribution accounts for
approximately the full gross change, and the signed available residual is small
and negative after hydrostatic and kinetic correction. Reverse-flow metrics,
same-QOI uncertainty, straight/developing reference, and component isolation
still block coefficient use.

## Inferred

The publication-safe result is a pressure-budget finding: a hydrostatic
dominated static rise with signed residual preserved as diagnostic evidence.
The wording should emphasize decomposition, recovery diagnostics, and row label,
not convert the residual into an ordinary loss coefficient or F6 input.

## Contradictions Or Caveats

The phrase "pressure rise" is numerically true for gross static pressure, but it
is easy to overread. The paper text therefore ties the rise immediately to the
hydrostatic term and the signed available residual. It also keeps the
ordinary-flow and same-QOI blockers visible.

## Next Useful Actions

Use the generated `paper_results_section.md`, `table_ready_claim_ledger.csv`,
and `caption_text.md` as the manuscript-ready source text for the frozen
diagnostic result. Revisit coefficient language only after a terminal
low-recirculation anchor and same-QOI uncertainty package land.
