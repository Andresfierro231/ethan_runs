---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/f6_candidate_admission_decision.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/gate_rollup.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/f3_comparison_status.csv
tags: [f6, same-qoi-uq, admission-gate, f3-comparison, no-admission]
related:
  - .agent/status/2026-07-21_TODO-F6-SAME-QOI-UQ-AND-ADMISSION-GATE.md
  - imports/2026-07-21_f6_same_qoi_uq_and_admission_gate.json
task: TODO-F6-SAME-QOI-UQ-AND-ADMISSION-GATE
date: 2026-07-21
role: Hydraulics / Reviewer / Tester / Writer
type: journal
status: complete
---

# F6 Same-QOI UQ And Admission Gate

## Attempted

I built a reproducible gate package that merges three evidence layers:

- Stage A harvested medium/fine endpoint-pair QA.
- The coarse source-path/UQ repair package.
- The broader same-QOI UQ execution package's F6 context summary.

The builder writes a row-level decision table constrained to the allowed labels:
`component_K`, `cluster_K`, `section_effective`, `pressure_recovery`, and
`diagnostic`.

## Observed

The gate evidence is internally consistent. Stage A raw face sampling passed,
but all four F6 endpoint pairs fail ordinary-flow criteria because RAF/RMF are
material. The coarse path repair found retained reconstructions for the twelve
blocked endpoint rows, but all twelve lack static `p`, and Salt3/Salt4 remain
coarse-only contexts. The same-QOI UQ execution package has zero admitted F6
rows in the relevant source families.

The first generated table used absolute source paths. I corrected the builder
to write repo-relative source paths and reran build, compile, and tests.

## Inferred

The scientifically correct current outcome is admission closure, not a weak F6
fit. The F6 rows cannot be promoted to `component_K`, `cluster_K`, or
`section_effective` because there is no ordinary-flow candidate and no
same-QOI static-pressure mesh/UQ support. F3 comparison is also withheld because
comparing F6 against F3 before F6 passes ordinary-flow and UQ gates would only
create an apparent calibration target.

## Contradictions Or Caveats

The repaired coarse rows are useful progress: they unlock a future VTK
face-area/recirculation sampler. They do not unlock pressure-basis admission,
because `p_rgh` was not converted into static `p` under a declared hydrostatic
and reference-pressure convention in this task.

The package does not claim that F6 has no pressure-recovery physics. It claims
that the present evidence only supports diagnostic classification.

## Next Useful Actions

Run `TODO-F6-COARSE-VTK-SAMPLER-SUBMIT` to harvest coarse VTK face diagnostics
from the repaired reconstructions. If that improves recirculation/area evidence,
open a separate pressure-basis task to define and test any `p_rgh` to static
`p` reconstruction before reattempting same-QOI UQ or F3 comparison.
