---
provenance:
  task: AGENT-421
  generated_by: codex
tags: [journal, hydraulics, agent373, f6, pm5]
related:
  - .agent/status/2026-07-15_AGENT-421.md
  - work_products/2026-07/2026-07-15/2026-07-15_agent373_hydraulic_chain_node_verification/README.md
---
# AGENT-373 Hydraulic Chain Node Verification

2026-07-15T10:42:00-05:00 - Claimed AGENT-421 after the user asked to actually
run the AGENT-373 chain and verify raw two-tap / F6 / reset-K / PM5 landing and
admission. Scope was intentionally narrow and non-overlapping with active
AGENT-419/420 work.

2026-07-15T10:43:00-05:00 - Reran the original AGENT-373 Python stage logic
locally into
`work_products/2026-07/2026-07-15/2026-07-15_agent373_hydraulic_chain_node_verification/agent373_stage_outputs/`.
The rerun produced `3` raw-two-tap preflight rows, `4` F6 gate rows, and `128`
reset-K sweep rows.

2026-07-15T10:44:00-05:00 - Built the combined verification package using:
AGENT-373 rerun outputs, AGENT-409 scratch OpenFOAM raw two-tap surfaces,
AGENT-406 PM5 matched-pressure/upcomer rows, and AGENT-414 F6 row-readiness.
Final decision: outputs landed and diagnostic admission is supported, but fit
admission is not supported today. Raw two-tap rows are coarse-only
reduced-pressure proxies with recirculation/no mesh-GCI/component policy
admission; all PM5 F6 rows are recirculating/onset diagnostics; reset-K only
proves component-separation arithmetic.

Validation passed:

- `python3.11 tools/analyze/build_agent373_hydraulic_chain_node_verification.py`
- `python3.11 -m unittest tools.analyze.test_agent373_hydraulic_chain_node_verification`

No native CFD solver output, scheduler state, registry/admission state,
generated indexes, or external Fluid files were mutated.
