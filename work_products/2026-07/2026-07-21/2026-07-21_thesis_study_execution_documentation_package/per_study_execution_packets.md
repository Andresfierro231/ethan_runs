---
provenance:
  - .agent/BOARD.md
  - .agent/BLOCKERS.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_next_studies_board_dispatch/next_study_portfolio.csv
tags: [thesis-dossier, study-execution, study-packets]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/study_execution_workflow.md
task: TODO-THESIS-STUDY-EXECUTION-DOCUMENTATION-PACKAGE-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer/Tester
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Per-Study Execution Packets

## S7 - Sensor Map Contract

Claim `TODO-THESIS-STUDY-S7-SENSOR-MAP-TP-TW-CONTRACT-2026-07-21`.

Required outputs:

- TP/TW coordinate ledger;
- 1D path-position map;
- bounded/excluded sensor table;
- sensor score policy;
- runtime leakage audit.

Acceptance:

- every TP/TW sensor is mapped, bounded, or excluded;
- excluded sensors have a thesis-safe rationale;
- validation, holdout, and external temperatures remain score-only targets.

Thesis use:

- uncertainty chapter;
- results-score interpretation;
- figure/table captions that reference TP/TW probes.

## S8 - Wall/Test-Section Physical Candidate

Claim `TODO-THESIS-STUDY-S8-WALL-TEST-SECTION-AXIAL-MIXING-CANDIDATE-2026-07-21`.

Required outputs:

- pre-registered candidate contract;
- comparison against M3 and prior AMX/UMX/TSWFC attempts;
- mdot, TP, TW, all-probe, and TW5/TW6 score table;
- runtime leakage audit;
- admission-ready or negative-result decision.

Acceptance:

- if admitted, the candidate is setup-only and S11-ready;
- if rejected, the failure mode is written as a falsification result;
- no passive wall-state selector retry is treated as the primary lane.

Thesis use:

- final predictive model chapter;
- wall/test-section limitations and negative-results section.

## S9 - Upcomer Onset Anchor And Exchange UQ

Claim `TODO-THESIS-STUDY-S9-UPCOMER-ONSET-ANCHOR-EXCHANGE-UQ-2026-07-21`.

Required outputs:

- onset-anchor ledger;
- near-onset and nonrecirculating evidence gap table;
- exchange-QOI contract for `V_recirc`, `mdot_exchange`, and `tau_recirc`;
- same-window uncertainty requirements;
- sampler/harvest requirements if data are missing.

Acceptance:

- ordinary upcomer `Nu`, `f_D`, and K stay disabled unless all gates pass;
- missing terminal/source evidence is converted into exact future work;
- no sampler, harvest, or scheduler action occurs unless separately claimed.

Thesis use:

- upcomer recirculation modeling;
- closure admission/uncertainty chapter;
- future-work section.

## S10 - Pressure/F6 Low-Recirculation Anchor UQ

Claim `TODO-THESIS-STUDY-S10-PRESSURE-F6-LOW-RECIRC-ANCHOR-UQ-2026-07-21`.

Required outputs:

- pressure candidate ledger;
- isolation-basis table;
- recirculation status table;
- same-QOI UQ status;
- source/property labels;
- comparison to `F3_shah_apparent`.

Acceptance:

- no component K or F6 claim without isolation, recirculation, UQ, source, and
  property gates;
- no clipped K, hidden global multiplier, or mixed-basis promotion;
- `0` admitted rows is valid if the non-admission is fully evidenced.

Thesis use:

- pressure diagnostics chapter;
- admission rules;
- negative-results contribution.

## S11 - Candidate Source/Property Refresh

Claim `TODO-THESIS-STUDY-S11-CANDIDATE-SOURCE-PROPERTY-REFRESH-2026-07-21`
only after S8, S9, or S10 yields one admission-worthy physical candidate.

Required outputs:

- candidate-specific release ledger;
- source-validity envelope;
- property-mode sensitivity labels;
- split-permission table;
- freeze release or blocked summary.

Acceptance:

- exactly one candidate is released for predeclared freeze or blocked;
- protected holdout, external, future, and support rows stay score-only where
  required;
- no broad release refresh is performed.

Thesis use:

- frozen-candidate handoff;
- split/source/property discipline;
- scorecard prerequisites.

## Frozen Scorecard Follow-On

The existing S6 row is complete as a blocked shell. If S11 releases a candidate,
open a new `S6B` row or an explicit coordinator-approved reopening row rather
than editing the completed S6 package casually.

Required outputs:

- frozen candidate manifest;
- split-role scorecard;
- pressure and thermal residual waterfalls;
- source/property release linkage;
- final runtime leakage audit;
- no tuning after freeze.

## Negative Results Contribution

Claim `TODO-THESIS-NEGATIVE-RESULTS-SCIENTIFIC-CONTRIBUTION-SECTION-2026-07-21`.

Required outputs:

- negative-results claim ledger;
- chapter insertion plan;
- source manifest;
- table of rejected hypotheses and evidence gates.

Acceptance:

- rejected closures are framed as scientific constraints;
- blocked final scorecard logic is explained without implying missing work is
  an admitted result;
- no thesis chapter body edit occurs unless a later exact-file row claims it.
