---
provenance:
  - AGENTS.md
  - reference/geometry_reference.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/cfd-runs-and-admission.md
tags: [repo-user-guide, glossary, terminology]
related:
  - docs/repo_user_guide/data_and_provenance.md
  - docs/repo_user_guide/repo_organization.md
task: TODO-REPO-USER-GUIDE-README-TOOLING
date: 2026-07-22
role: Writer/Implementer/Tester
type: report
status: complete
---
# Glossary

Admission: A documented decision that a row or artifact may be used for a named
scientific purpose, such as training, diagnostic evidence, holdout scoring, or
external testing.

Board row: A task entry in `.agent/BOARD.md` naming role, owner, allowed edit
paths, read-only context, objective, and guardrails.

Candidate freeze: A predeclared runtime-legal model candidate locked before
protected scoring. No final score should exist before freeze.

External test: A row reserved for final external evidence. It must not be used
for fitting or model selection.

Generated index: `.agent/STATE.md`, `.agent/BLOCKERS.md`,
`.agent/catalog.json`, and `.agent/catalog.csv`, written by
`tools/docs/build_repo_index.py`.

Holdout/testing: Rows used to evaluate a frozen or predeclared model, not to
fit or tune it.

Import manifest: Dated JSON under `imports/` recording changed files,
read-only context, outputs, and mutation flags.

Kirst runs: Historical runs that are not current mainline evidence unless a
later dated note explicitly re-admits them.

Linked case: A convenience symlink under `linked_cases/`. It is not provenance.

Mainline continuation: The preferred current Ethan run family when a
continuation exists for a case.

Native solver output: OpenFOAM/CFD output from a source case. Read-only by
default.

Protected scoring: Validation, holdout, or external-test scoring that must not
occur before split and freeze gates allow it.

Qwall / wallHeatFlux: CFD wall heat quantities. Realized CFD `wallHeatFlux` is
not a predictive runtime input unless an explicit future release row changes
policy.

Runtime input: A value available to a predictive model before seeing validation,
holdout, external-test, or realized CFD outcome fields.

Source/property release: A row-specific decision that source validity and
property-mode sensitivity labels are adequate for a candidate. Current many
lanes remain fail-closed.

TP / TW: Temperature probe and wall thermocouple quantities of interest.

Train-only: Analysis restricted to training rows, with no validation, holdout,
or external-test scoring.

Upcomer recirculation: Persistent recirculation in the upcomer/test-section
side that blocks ordinary single-stream `Nu`, `f_D`, and `K` admission unless a
specific hybrid/exchange model is admitted.
