---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_heated_incline_tw4_tw6_local_audit/failure_classification.csv
tags: [journal, heated-incline, TW5, TW6, external-bc]
related:
  - .agent/status/2026-07-21_TODO-HEATED-INCLINE-TW4-TW6-LOCAL-AUDIT-2026-07-21.md
  - imports/2026-07-21_heated_incline_tw4_tw6_local_audit.json
task: TODO-HEATED-INCLINE-TW4-TW6-LOCAL-AUDIT-2026-07-21
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Writer / Reviewer
type: journal
status: complete
---
# Heated-Incline TW4-TW6 Local Audit

Observed: Phase E underpredicts Salt2 train TW4/TW5/TW6 by about `89`, `109`,
and `98 K`. S8 identifies TW5 and TW6 as the dominant residual targets and
records failure across prior passive/source selector families.

Observed: lower-leg ambient-wall metadata is finite and setup-known. Heater Q
is also present in setup files, but Fluid currently treats heater source rows as
document-only/source-sink blocked.

Inferred: the leading issue is missing source treatment, with model form second
after that source lane is executable. Sensor mapping remains a caveat because
TW4-TW6 are bounded/not exact, but it is not the primary explanation.

Caveat: this is train-only diagnostic reasoning and does not admit a source
model, closure, or final score.

Next useful action: implement the legal lower-leg heater source lane, rerun
train-only residual decomposition, then decide whether axial mixing or exchange
model form is still needed.
