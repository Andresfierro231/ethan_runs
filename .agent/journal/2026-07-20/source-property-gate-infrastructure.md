---
provenance:
  - tools/agent/source_property_gate.py
  - tools/agent/finish_task.py
  - work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/README.md
tags: [source-property-gate, scorecard-enforcement, agent-tooling]
related:
  - .agent/status/2026-07-20_AGENT-554.md
  - imports/2026-07-20_source_property_gate_infrastructure.json
task: AGENT-554
date: 2026-07-20
role: Implementer/Tester
type: journal
status: complete
---
# Source/Property Gate Infrastructure

Task: AGENT-554

Observed: AGENT-546 proved the current corpus can be scanned for fit/admission
candidate rows, but its scanner lived inside a task-owned work product. Future
scorecard tasks still needed reusable tooling and a closeout warning so missing
or blocked source/property labels do not disappear during handoff.

Implemented: promoted the policy into `tools/agent/source_property_gate.py`.
The tool scans scorecard-like CSVs, detects positive fit/admission/model
selection candidates, and reports missing columns, blank labels, blocked gate
status, refresh-required label content, outside/mixed source envelope, and
diagnostic/no-fit source-use categories.

Implemented: wired `finish_task.py` to run the gate in warning mode over
changed scorecard-like CSVs from task import manifests. Warnings are explicit
`SOURCE_PROPERTY_GATE_WARNING` lines with failure-mode counts and a TODO command.
They do not fail closeout yet, matching the requested transition behavior.

Observed during validation: the final predictive scorecard shell currently has
22 candidate rows with source/property findings. The task-owned ledger
`final_scorecard_source_property_todo.csv` records those follow-up rows and
failure modes.

Inference: this closes the infrastructure gap but not the scientific gate. Salt1,
perturbation, external, and future/new-CFD rows still need row-specific
source/property refresh before fit/admission prose, and physics blockers remain
separate.

Validation: focused agent-tool tests passed, py-compile passed, the AGENT-546
package audit ran, and the final-scorecard TODO ledger was generated.

Next useful action: run `source_property_gate.py --warn --todo-out ...` from
each future scorecard/admission task, then refresh the TODO rows before using
them in fit/admission language. Use `--strict` for package-specific hard gates
once the team is ready to move beyond warning mode.
