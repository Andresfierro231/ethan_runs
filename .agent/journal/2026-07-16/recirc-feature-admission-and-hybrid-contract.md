---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/recirculation_feature_admission_table.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/hybrid_1d_model_contract.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/next_extraction_queue.csv
tags: [journal, AGENT-467, recirculation, upcomer, admission, hybrid-model]
related:
  - .agent/status/2026-07-16_AGENT-467.md
  - imports/2026-07-16_recirc_feature_admission_and_hybrid_contract.json
task: AGENT-467
date: 2026-07-16
role: Hydraulics/Upcomer-onset/Implementer/Tester/Writer
type: journal
status: complete
---
# Recirculation Feature Admission And Hybrid Contract

## Observed Output

AGENT-467 consolidated existing AGENT-455/457/461/464 evidence into a single
recirculation feature/admission package. The output table contains `42`
feature rows and keeps `0` rows fit-admissible for ordinary single-stream
upcomer/test-section `Nu`, `f_D`, or component `K`.

The hybrid contract records four lanes: ordinary pipe, transition diagnostic,
recirculating upcomer effective, and test-section upcomer subspan.

## Interpretation

The useful scientific result today is not a calibrated recirculation closure.
It is a stricter validity boundary: material reverse-flow evidence keeps the
current upcomer and test-section rows in a regime/admission lane. A future 1D
model should represent this as a named hybrid upcomer lane with explicit
ordinary, transition, and recirculating states.

## Next Sequence

Use `next_extraction_queue.csv` as the handoff for follow-on work. The main
unblocks remain onset anchors, same-window wall/bulk or wall/core thermal
metrics, mesh/time uncertainty, and coupled M3+TS scoring for frozen TS1/TS2
candidates.

## Files

- `.agent/status/2026-07-16_AGENT-467.md`
- `imports/2026-07-16_recirc_feature_admission_and_hybrid_contract.json`
- `tools/analyze/build_recirc_feature_admission_and_hybrid_contract.py`
- `tools/analyze/test_recirc_feature_admission_and_hybrid_contract.py`
- `work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/`
