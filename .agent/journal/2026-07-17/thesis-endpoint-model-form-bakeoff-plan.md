---
provenance:
  - .agent/BOARD.md
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
tags: [journal, thesis-endpoint, model-form-bakeoff, split-policy, sam]
related:
  - .agent/status/2026-07-17_AGENT-510.md
  - imports/2026-07-17_thesis_endpoint_model_form_bakeoff_plan.json
task: AGENT-510
date: 2026-07-17
role: Coordinator/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Thesis Endpoint Model-Form Bakeoff Plan

Task: AGENT-510

## Context

The user wants the thesis endpoint to remain ambitious: a fully admitted final
predictive 1D model is preferred. The near-term risk is that wall/test-section,
upcomer onset, or F6/re-correction blockers may prevent a fully admitted model
within the next week. The thesis therefore needs an explicit intermediate
model-form ladder that can be scored, explained, and defended at least in the
appendices.

## Changes Made

- Added board row `TODO-THESIS-ENDPOINT-MODEL-FORM-BAKEOFF`.
- Added current section
  `reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md`.
- Updated `reports/thesis_dossier/Outline.md` so the endpoint strategy is part
  of the main master's thesis plan.
- Updated `reports/thesis_dossier/Chapters_and_sections/current/README.md` so
  future thesis agents can find the new section.

## Decisions Recorded

- Canonical split remains locked: train on Salt1-4 nominal; score Salt2 +/-5Q,
  `val_salt2`, future +/-10Q, and new CFD only after the relevant freeze and
  admission gates.
- Intermediate forms should be compared by model equations, allowed runtime
  inputs, forbidden runtime inputs, postprocessing requirements, training cost,
  operational runtime cost, score metrics, admission state, and failure modes.
- Required model ladder: M0 setup-only baseline, M1 CFD thermal-boundary replay
  diagnostic, M2 admitted heater+cooler boundary model, M3 segment-only
  `fluid+walls`, M4 junction-aware `fluid+walls`, M5 hybrid upcomer model, and
  M6 frozen final predictive candidate if gates pass.
- The thesis should include a numerical algorithm section and a SAM-facing
  interpretation section without claiming direct SAM validation.

## Validation

- Documentation contract check: `python3.11 tools/agent/finish_task.py --task-id
  AGENT-510 --json`.
- Generated docs index refresh intentionally skipped because active board rows
  list generated index/map paths as read-only.

## Guardrails

- No native CFD outputs, registry state, scheduler state, or external Fluid code
  changed.
- No fitting or admission status changed.
