---
provenance:
  - AGENTS.md
  - .agent/BOARD.md
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/README.md
  - ../papers/AGENTS.md
  - ../papers/.agent/BOARD.md
  - ../papers/UTexas_Research/csem-Masters_dissertation/AGENTS.md
  - ../papers/UTexas_Research/csem-Masters_dissertation/README.md
  - ../papers/UTexas_Research/csem-Masters_dissertation/structural/body.tex
tags: [thesis, latex, csem, workflow, board-dispatch, evidence-contract]
related:
  - operational_notes/07-26/21/2026-07-21_THESIS_LATEX_PARALLEL_WORKFLOW_CONTRACT.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/latex_sync_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/artifact_handoff_schema.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/parallel_work_lanes.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/papers_board_rows.md
task: TODO-THESIS-LATEX-PARALLEL-WORKFLOW-CONTRACT-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer
type: work-product
status: reference
supersedes: []
superseded_by:
---
# Thesis LaTeX Parallel Workflow Contract

This package defines how the CSEM thesis moves from `ethan_runs` evidence and
markdown drafts into the actual master's dissertation LaTeX while allowing
parallel work.

## Current Answer

No, the current `ethan_runs` writing passes were not editing the actual LaTeX.
They were building and enriching the thesis dossier markdown under
`reports/thesis_dossier/Chapters_and_sections/current/`. The actual LaTeX
manuscript is:

`../papers/UTexas_Research/csem-Masters_dissertation/`

Actual manuscript edits must be claimed on `../papers/.agent/BOARD.md` with
exact target paths before editing.

## Workspace Responsibilities

| Workspace | Owns | Must not do |
| --- | --- | --- |
| `ethan_runs/` | CFD evidence packages, analysis scripts, generated thesis-facing artifacts, provenance manifests, claim/admission ledgers, copy-ready markdown source. | Mutate imported native solver outputs; silently admit closures; edit external LaTeX without a papers-board row and filesystem approval. |
| `../papers/UTexas_Research/csem-Masters_dissertation/` | Actual dissertation LaTeX, figure inclusion, table inclusion, captions, cross references, build and guardrail checks. | Invent missing values; import unfinished evidence packages as admitted results; weaken runtime-leakage or split rules. |

## Parallel Roles

| Role | Allowed output | Required closeout |
| --- | --- | --- |
| LaTeX writer | One chapter or appendix `.tex` path per board row. May incorporate ready prose and ready artifacts only. | Papers status/journal entry, guardrail check, build attempt or explicit reason build was not run. |
| Artifact producer | A dated `ethan_runs/work_products/**` package with CSV/figure/table outputs and README. | Ethan status/journal/import manifest, validation command, artifact handoff fields. |
| Evidence reviewer | Claim-ledger or package review, no manuscript rewrite unless separately claimed. | Review note identifying admissible, diagnostic, blocked, and forbidden uses. |
| Integrator | Imports completed artifacts into LaTeX after producer closeout. | Updated `.tex`, figure/table references, guardrail/build results. |

## Artifact Handoff Contract

Every analysis package intended for thesis insertion must provide the fields in
`artifact_handoff_schema.json`. The minimum contract is:

- `artifact_id`
- exact source paths and source package README
- target LaTeX section and intended figure/table label
- claim IDs or claim-ledger row names supported
- split role: training, diagnostic, validation, holdout, external-test, or
  literature/context
- admission state: admitted, diagnostic-only, blocked, negative result, or
  context-only
- allowed use and forbidden use
- runtime-leakage audit
- validation command and result

An artifact with missing split role, admission state, or forbidden-use field is
not ready for LaTeX import.

## LaTeX Writer Contract

A writer may edit LaTeX only when the papers board row names:

- the exact target `.tex` file or files
- the source markdown and evidence packages to open first
- any figure/table files to include
- claim boundaries and forbidden phrases
- required validation command

The writer must not convert diagnostic CFD quantities into predictive runtime
inputs. Specifically, predictive-runtime prose must not use CFD `mdot`,
realized `wallHeatFlux`, imposed cooler duty, validation temperatures, holdout
rows, or external-test rows as hidden inputs.

## Chapter Sync Map

| Thesis topic | Source markdown/evidence | Target LaTeX |
| --- | --- | --- |
| Motivation and contribution | `15_ch1_csem_motivation_and_contribution.md`, `14_csem_narrative_integration_plan.md` | `intro_adjacent/introduction.tex`, `intro_adjacent/motivation.tex` |
| CFD evidence database | `16_ch3_csem_cfd_evidence_database.md`, 3D analysis Salt figures, evidence package READMEs | `chapters/03_physical_system_and_evidence.tex` |
| CFD-to-1D reduction and split policy | `03_split_policy_and_evidence_classes.md`, `25_litrev_csem_thesis_incorporation.md` | `chapters/04_cfd_to_1d_reduction.tex` |
| Fluid+walls model form | `02_model_form_fluid_walls.md`, `17_ch5_csem_fluid_walls_model.md`, `09_fluid_walls_segment_atlas.md` | `chapters/05_coupled_fluid_walls_model.tex` |
| Closure/admission/uncertainty | `18_ch6_csem_closure_admission_uncertainty.md`, `08_thesis_claim_ledger.md`, `10_uncertainty_chapter_package.md` | `chapters/06_closure_admission_uncertainty.tex` |
| Pressure/thermal results and negative results | `19_ch7_csem_pressure_thermal_predictive_results.md`, pressure and thermal work-product packages | `chapters/07_reduced_cfd_evidence.tex`, `chapters/08_predictive_model_assessment.tex` |
| SAM/CSEM relevance, limits, future work | `20_ch8_csem_sam_limitations_conclusions.md`, `11_sam_facing_interpretation.md` | `chapters/09_implications_conclusions_future_work.tex` |
| Claim ledger, segment atlas, validation split | `08_thesis_claim_ledger.md`, `09_fluid_walls_segment_atlas.md`, split-policy packages | `chapters/appendix_claim_ledger.tex`, `chapters/appendix_segment_atlas.tex`, `chapters/appendix_validation_split.tex` |

## Parallel Work Rule

One LaTeX writer owns one chapter file or tightly coupled chapter pair at a
time. Analysis agents may work in parallel in `ethan_runs` because their output
contract is a dated package, not direct LaTeX edits. The integrator imports only
closed packages whose README identifies legal thesis use.

## Immediate Board Packet

Use `papers_board_rows.md` to seed the papers board with claimable LaTeX tasks.
Use `latex_sync_contract.csv` to decide which chapter can move now and which
must wait for an artifact producer.

## Next-Session Handoff

For the next writing session, open:

`operational_notes/07-26/21/2026-07-21_THESIS_LATEX_TOMORROW_HANDOFF.md`

The recommended first actual LaTeX implementation row is
`csem-latex-ch5-model-form-sync-2026-07-21`, followed by
`csem-latex-ch6-admission-uncertainty-sync-2026-07-21`. Chapters 7/8 should
avoid final predictive scorecard claims until the current thermal/upcomer/
pressure evidence packages close and satisfy the artifact handoff schema.
