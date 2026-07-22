# Ready Prose Blocks

## Ch. 6 Admission Workflow

The chapter should be read as a methods result, not only as administration. It
defines the conditions under which high-fidelity CFD evidence can move into a
reduced model without becoming a hidden replay of the same CFD row. The
discipline is especially important for the CSEM/SAM-facing use case, where the
eventual systems-code value is not a single tuned number but a traceable
decision about which terms are admitted, diagnostic, blocked, or score-only.

## Ch. 6 Runtime Leakage

The runtime-leakage rule is a thesis contribution because it makes the reduced
model auditable before any accuracy number is shown. A model can match a CFD
target for the wrong reason if it is allowed to ingest the row response as a
boundary condition, source, or target-derived coefficient. The workflow avoids
that failure by making runtime status an explicit field in every closure,
score, and figure/table caption.

## Ch. 7 Result Sequence

This results chapter should keep the reader in one sequence: first the CFD
shows structured pressure and heat behavior; then the reduced-model ledgers
assign owners; then the admission gates explain which terms remain diagnostic;
then the blocked scorecard shows why no final accuracy claim is yet legal. The
negative results are therefore part of the evidence chain, not an appendix of
failed attempts.

## Ch. 7 Blocked Scorecard

Use the S6 blocked-scorecard package as the figure/table companion. The
preferred order is the S0-S11 gate-flow table, then the blocked scorecard
visual table, then the frozen-candidate placeholder table if space allows.
The caption should state that empty score cells are the current rigorous
result, not missing formatting.
