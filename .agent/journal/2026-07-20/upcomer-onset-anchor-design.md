---
task: AGENT-559
date: 2026-07-20
role: Hydraulics/Thermal-modeling/cfd-pp/Writer
status: complete
---
# Upcomer Onset Anchor Design

Task: `AGENT-559`

I claimed the runbook-defined upcomer onset anchor design row and ran
`python3.11 tools/agent/preflight_task.py --task-id AGENT-559`; ownership
preflight passed with no conflicts.

I reviewed the blocker register, AGENT-556 runbook, AGENT-558 UMX1 intake,
F6/upcomer blocker scorecard, July 17 upcomer onset matrix, hardened
same-window request, July 20 upcomer execution package, active matched-plane
relaunch package, and high-heat monitor package. The evidence is consistent:
there are three observed recirculating upcomer points, zero ordinary upcomer
fit rows, four PM10 rows waiting on matched-plane extraction, and four high-heat
Salt4 rows that should remain monitor-only until terminal success.

The important process decision is no launch from this row. A separate
matched-plane extraction package already submitted job `3305547`, and duplicate
compute would add ambiguity. The high-heat jobs `3299610` and `3299620` were
still running in the cited monitor evidence, so harvesting or postprocessing
them here would violate the row scope.

I wrote a bounded evidence contract. The next row should first consume landed
PM10 matched-plane QOIs, then harvest high-heat rows only after terminal
success, then launch the two Salt3 sentinels only if those existing evidence
lanes still fail to bracket onset. The nine-row Salt3 Q-by-insulation matrix is
explicitly deferred until after sentinel failure. No ordinary `Nu`, `f_D`, or
component-`K` promotion is allowed without same-window reverse-flow metrics,
regime coordinates, thermal drive, pressure terms, heat ledger, and same-QOI
uncertainty.
