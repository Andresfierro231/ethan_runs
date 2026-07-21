---
provenance:
  generated_by: codex
  generated_at: 2026-07-21
tags:
  - s13
  - upcomer-exchange
  - topology-forensics
  - fail-closed
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv/alternate_cv_release_gate.csv
---

# Task TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-FORENSICS-AND-ALT-CV-2026-07-21

Task: `TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-FORENSICS-AND-ALT-CV-2026-07-21`

## Changes Made

- Added `tools/extract/build_s13_upcomer_exchange_topology_forensics_alt_cv.py`.
- Added `tools/extract/test_s13_upcomer_exchange_topology_forensics_alt_cv.py`.
- Published `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv/`.
- Output result: `56` face-connected reverse-flow components reviewed, `2` components with trusted right-leg wall contact, `0` alternate CV releases, and `surface_extraction_allowed=false`.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_topology_forensics_alt_cv.py tools/extract/test_s13_upcomer_exchange_topology_forensics_alt_cv.py` passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_topology_forensics_alt_cv` passed: `Ran 6 tests`.
- `python3.11 tools/extract/build_s13_upcomer_exchange_topology_forensics_alt_cv.py` passed.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv` passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv --strict` passed.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv` passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-FORENSICS-AND-ALT-CV-2026-07-21` passed.
- `python3.11 tools/docs/build_repo_index.py --check` passed: blocker register OK.

## Guardrails

- Native solver outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver, postprocessing, surface extraction, sampler, or harvest launched: no.
- Fluid or external repo mutated: no.
- Threshold relaxation or proxy-interface admission: no.
- Fitting, model selection, S11/S15/S6 trigger, or exchange-cell admission: no.
- Blocker register or generated index mutated: no.
- Residual absorption into internal Nu: no.

## Outcome

Complete fail-closed topology forensics. The alternate wall-adjacent
face-connected CV rule does not release S13: Salt2 has no reverse-flow component
touching trusted right-leg wall patches, while Salt3 and Salt4 only have tiny
wall-contact components that fail dominance and touch `ncc_pipeleg_right_03_upper_end`.
S13 surface extraction, sampler manifest admission, and production harvest
remain disabled.
