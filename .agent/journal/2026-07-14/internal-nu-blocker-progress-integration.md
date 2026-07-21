# Internal-Nu Blocker Progress Integration

Task: `AGENT-345`
Date: `2026-07-14`

## Assumptions

- Current fit-admissible internal-Nu row count remains `0`.
- Existing upcomer matched-plane proxies are diagnostic only.
- Corrected-Q rows require terminal harvest and admission before onset or Nu use.
- CFD `rcExternalTemperature` wallHeatFlux includes radiation; no separate
  exported `qr` residual is available.
- Repaired/smoke thermal rows remain diagnostic until admitted.

## Method

Read the current blocker ledger plus July 14 internal-Nu, matched-plane,
candidate-onset, residual-guardrail, forward-gate, hydraulic, and submitted-run
packages. Encoded the result in reproducible CSV tables and tests rather than a
free-form memo only.

## Result

The major open blockers now have executable next actions and owner lanes. This
does not reopen internal-Nu fitting; it documents the evidence required to make
that future decision without guessing scientific criteria.

Generated at: `2026-07-14T14:00:14`
