---
provenance:
  - .agent/BLOCKERS.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/per_study_execution_packets.md
tags: [thesis-dossier, claim-ledger, admission-rules, runtime-leakage]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/acceptance_gate_matrix_template.csv
task: TODO-THESIS-STUDY-EXECUTION-DOCUMENTATION-PACKAGE-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer/Tester
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Claim And Admission Rules

## Predictive Runtime Claims

Allowed only after:

- candidate is pre-registered;
- source/property/split refresh passes;
- runtime leakage audit passes;
- holdout and external rows are used only after freeze.

Forbidden runtime inputs:

- CFD `mdot`;
- realized CFD `wallHeatFlux`;
- imposed CFD cooler duty;
- realized test-section heat;
- validation, holdout, or external-test temperatures.

## Sensor Claims

Sensor temperatures may support score interpretation only. They do not define
runtime inputs. A sensor with unknown or ambiguous location must be bounded or
excluded before it appears in a thesis score table.

## Upcomer Claims

Recirculating upcomer evidence may support hybrid/onset or exchange diagnostics.
It may not support ordinary single-stream `Nu`, `f_D`, or K until a future
study admits near-onset coverage, a nonrecirculating/transition anchor,
same-window thermal evidence, and mesh/time uncertainty.

## Pressure/F6 Claims

Two-tap and F6 pressure rows may not become component K or F6 evidence unless
the study proves:

- pressure basis consistency;
- component isolation or explicit section-effective interpretation;
- low-recirculation or recirculation-aware closure basis;
- same-QOI uncertainty;
- source/property validity;
- improvement over `F3_shah_apparent` without hidden multipliers.

## Negative Results

Negative results are publication-ready when they state:

- the hypothesis tested;
- the evidence used;
- the gate that failed;
- why the failure blocks admission;
- which future evidence would change the decision.

Do not weaken negative results into vague "needs more work" prose when the gate
failure is already established.
