---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/summary.json
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/section_effective_model_contract.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/paper_claims_and_limitations.csv
tags: [pressure-ledger, two-tap, recirculation, section-effective, paper-dossier]
related:
  - .agent/journal/2026-07-20/two-tap-recirc-section-effective-model.md
  - imports/2026-07-20_two_tap_recirc_section_effective_model.json
  - operational_notes/maps/pressure-and-momentum-budget.md
  - reports/thesis_dossier/Chapters_and_sections/current/13_two_tap_recirc_section_effective_pressure_model.md
task: TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: status
status: complete
---
# TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL Status

## Objective

Address the two-tap `corner_lower_right` blockers by defining a
recirculation-aware pressure model path and documenting the completed work in a
paper-facing form.

## Outcome

Complete. The package keeps current Salt2/Salt3/Salt4 `corner_lower_right` rows
out of ordinary `component_K` and F6 admission, but preserves them as diagnostic
evidence for a section-effective recirculating pressure residual model. It
documents why static apparent `K` is hydrostatic/buoyancy dominated, why
recirculation and component isolation block ordinary K, and what same-QOI UQ
family is required next.

## Changes Made

- `work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/**`
- `reports/thesis_dossier/Chapters_and_sections/current/13_two_tap_recirc_section_effective_pressure_model.md`
- `reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md`
- `reports/thesis_dossier/Chapters_and_sections/current/README.md`
- `operational_notes/maps/pressure-and-momentum-budget.md`
- `.agent/BOARD.md`
- `.agent/status/2026-07-20_TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL.md`
- `.agent/journal/2026-07-20/two-tap-recirc-section-effective-model.md`
- `imports/2026-07-20_two_tap_recirc_section_effective_model.json`

## Validation

- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/build_two_tap_recirc_section_effective_model.py`
  passed.
- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/test_two_tap_recirc_section_effective_model.py`
  passed: 6 tests.
- `python3.11 tools/docs/build_repo_index.py --check`
  passed.
- `python3.11 tools/agent/preflight_task.py --task-id TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL`
  passed: no conflicts detected.
- `python3.11 tools/agent/finish_task.py --task-id TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL`
  passed.

## Unresolved Blockers

- Same-QOI mesh/time UQ remains missing.
- Current rows remain `apparent_cluster_only`, not clean component K.
- Material reverse flow remains expected and must be modeled as recirculation,
  not suppressed into ordinary single-stream K.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. Scheduler state was not mutated. Fluid and external repositories were
not edited. No solver/postprocessing launch, F6 fit, component-K admission,
hidden global multiplier, clipped K, model selection, or endpoint-pressure
invention was performed.
