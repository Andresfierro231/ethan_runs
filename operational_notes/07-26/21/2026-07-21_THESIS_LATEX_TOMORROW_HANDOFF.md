---
provenance:
  - operational_notes/07-26/21/2026-07-21_THESIS_LATEX_PARALLEL_WORKFLOW_CONTRACT.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/latex_sync_contract.csv
  - ../papers/.agent/BOARD.md
  - ../papers/UTexas_Research/csem-Masters_dissertation/README.md
tags: [start-here, thesis, latex, next-session, csem]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/artifact_handoff_schema.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/papers_board_rows.md
task: TODO-THESIS-LATEX-TOMORROW-HANDOFF-2026-07-21
date: 2026-07-21
role: Coordinator/Writer
type: operational-note
status: reference
supersedes: []
superseded_by:
---
# Next Session Handoff: CSEM Thesis LaTeX Implementation

## What Changed Today

The actual LaTeX was identified as:

`../papers/UTexas_Research/csem-Masters_dissertation/`

The previous thesis writing work in `ethan_runs` was a copy-ready markdown and
evidence layer, not direct LaTeX editing. To support direct LaTeX implementation
without breaking parallel analysis work, a cross-workspace contract was created:

`work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/README.md`

The CSEM dissertation README now points future agents to that workflow before
they edit manuscript files. The papers board now has claimable backlog rows for
chapter-level LaTeX sync, artifact import, and integration review.

## Start Here Tomorrow

1. Open `../papers/UTexas_Research/csem-Masters_dissertation/AGENTS.md`.
2. Open `../papers/.agent/BOARD.md`.
3. Promote exactly one CSEM LaTeX row from `Backlog` to `Active` with a real
   owner and exact file scope.
4. Open the matching row in
   `work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/latex_sync_contract.csv`.
5. Read the listed source markdown from
   `reports/thesis_dossier/Chapters_and_sections/current/`.
6. Edit only the claimed `.tex` file or tightly coupled pair.
7. Run from the CSEM dissertation directory:

```bash
scripts/check_guardrails.sh
scripts/build_thesis.sh
```

## First Recommended LaTeX Row

Promote `csem-latex-ch5-model-form-sync-2026-07-21` first.

Reason: Chapter 5 has ready source prose and does not depend on unfinished
numerical evidence. It can safely import the `fluid+walls` model architecture,
segment state, wall/material stack, source/sink roles, external boundary
conditions, recirculation flag, and runtime contract.

Open first:

- `reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md`
- `reports/thesis_dossier/Chapters_and_sections/current/17_ch5_csem_fluid_walls_model.md`
- `reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md`

Target:

- `../papers/UTexas_Research/csem-Masters_dissertation/chapters/05_coupled_fluid_walls_model.tex`

## Second Recommended LaTeX Row

Promote `csem-latex-ch6-admission-uncertainty-sync-2026-07-21` next.

Reason: Chapter 6 is the methodological contribution chapter. It can be
strengthened now with no-silent-promotion logic, admission states, split roles,
uncertainty labels, and runtime-leakage prevention without waiting for final
predictive scores.

## Hold Until More Evidence

Do not write final predictive scorecard claims in Chapters 7/8 until the current
thermal/upcomer/pressure evidence packages close and satisfy the artifact
handoff schema. Chapters 7/8 can still be written as:

- reduced CFD evidence
- diagnostic evidence
- negative results
- blocked final-scorecard logic
- future work requirements

## Artifact Rule

Any figure/table from `ethan_runs` must satisfy:

`work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/artifact_handoff_schema.json`

before a LaTeX writer imports it. The package README must state split role,
admission state, allowed use, forbidden use, runtime-leakage audit, and
validation result.

## Guardrails To Preserve

- CFD evidence is high-fidelity computational reference, not experimental
  validation.
- Diagnostic CFD evidence must not be promoted to admitted predictive closure.
- Predictive runtime prose must not use CFD `mdot`, realized `wallHeatFlux`,
  imposed cooler duty, validation temperatures, holdout rows, or external-test
  rows as hidden inputs.
- The SAM/CSEM claim is a vetted closure/admission workflow and branchwise
  evidence map, not SAM validation.
- One writer owns one `.tex` target at a time.

## What Was Not Done

- No chapter LaTeX was edited.
- No figure/table was imported into the dissertation.
- No claim/admission state was changed.
- No solver, sampler, scheduler, Fluid, registry, or native-output mutation was
  performed.
