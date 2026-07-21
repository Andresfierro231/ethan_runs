---
provenance:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/mentor_thesis_outline.md
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
  - reports/thesis_dossier/Chapters_and_sections/current/11_sam_facing_interpretation.md
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - work_products/2026-07/2026-07-18/2026-07-18_blocker_research_path_next_step_synthesis/research_paths.csv
  - work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan/README.md
  - operational_notes/07-26/18/2026-07-18_UMX1_SCORING_READINESS.md
  - operational_notes/07-26/18/2026-07-18_MONDAY_SOURCE_PROPERTY_AND_AGENT_DISPATCH.md
  - .agent/BLOCKERS.md
tags: [thesis-handoff, masters-thesis, research-avenues, next-steps, writing]
related:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/mentor_thesis_outline.md
  - operational_notes/07-26/18/2026-07-18_MONDAY_SOURCE_PROPERTY_AND_AGENT_DISPATCH.md
  - .agent/status/2026-07-18_AGENT-550.md
task: AGENT-550
date: 2026-07-18
role: Writer/Coordinator
type: operational_note
status: complete
supersedes: []
superseded_by:
---
# Thesis Next Context And Steps

Use this as the thesis/writing restart note after the standard startup files.
It records the current thesis context, what is already safe to write, and the
research avenues that would make the thesis stronger.

## Why This Exists

The external UT master's thesis scaffold now exists at:

`../papers/UTexas_Research/csem-Masters_dissertation`

That scaffold is intentionally structural. It has chapter files and
`TODO[source]` markers, but it does not import large thesis prose or claim final
predictive results. The next session should use the Ethan thesis dossier as the
source of truth and then decide whether to write prose, build tables, or launch
a new research package.

## Open First

1. `AGENTS.md`
2. `.agent/BOARD.md`
3. `.agent/STATE.md`
4. `.agent/BLOCKERS.md`
5. `reports/thesis_dossier/README.md`
6. `reports/thesis_dossier/mentor_thesis_outline.md`
7. `reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md`
8. `reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md`
9. `reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md`
10. `operational_notes/07-26/18/2026-07-18_MONDAY_SOURCE_PROPERTY_AND_AGENT_DISPATCH.md`
11. External scaffold `../papers/UTexas_Research/csem-Masters_dissertation/README.txt`
12. External scaffold `../papers/UTexas_Research/csem-Masters_dissertation/structural/body.tex`

## Current Thesis Story

The thesis is strongest as a defensible CFD-to-1D closure workflow for the TAMU
molten-salt natural-circulation loop. Ethan OpenFOAM is the high-fidelity
reference, not experimental validation.

The current model target is steady `fluid+walls`: each segment carries a fluid
state, wall/material stack, pressure model, thermal circuit, source/sink role,
development state, recirculation/admission flags, uncertainty status, and
source/property labels. The contribution is a branchwise closure ledger and
admission framework, not a tuned global coefficient.

The external thesis scaffold currently maps this into:

- Chapter 1: introduction and motivation.
- Chapter 2: background and literature.
- Chapter 3: physical system, CFD database, and evidence structure.
- Chapter 4: CFD-to-1D reduction methodology.
- Chapter 5: coupled `fluid+walls` model.
- Chapter 6: closure admission and uncertainty.
- Chapter 7: results and predictive assessment.
- Chapter 8: systems-code interpretation.
- Chapter 9: conclusions.
- Appendices: claim ledger, segment atlas, and validation split.

## Thesis-safe Material Now

These claims are safe to write now if their caveats are preserved:

- The method claim: provenance-controlled CFD-to-1D closure reduction is the
  central thesis product.
- The model-form claim: the final target is steady `fluid+walls`, not a
  fluid-only heat-leak model.
- The split claim: final training, support, holdout/testing, and external-test
  roles must stay separated.
- The runtime-leakage claim: CFD `mdot`, realized CFD `wallHeatFlux`, imposed
  CFD cooler duty, scored-row pressure loss, and validation TP/TW temperatures
  are forbidden predictive runtime inputs.
- The upcomer claim: recirculating upcomer rows cannot be converted into
  ordinary single-stream `Nu`, `f_D`, or `K`.
- The SAM claim: current SAM relevance is interpretation and future
  implementation guidance, not SAM validation.

## Current Open Blockers

Use `.agent/BLOCKERS.md` for authoritative status. The thesis-facing open set
is:

| Blocker | Thesis meaning | What would strengthen the thesis |
| --- | --- | --- |
| `predictive-wall-test-section-submodels` | Wall/test-section/passive-boundary heat loss is not yet admitted even though heater and cooler/HX evidence is stronger. | UMX1 stratification/mixing or TSWFC2 distributed wall/fluid evidence that improves TP/TW/all-probe shape without runtime leakage. |
| `upcomer-onset-data-sparsity` | Current upcomer evidence is recirculating; onset remains extrapolated. | Near-onset or non-recirculating anchor rows with same-window pressure, thermal, recirculation, mesh/time, and source/property labels. |
| `f6-friction-re-correction` | F6 remains narrowed but unresolved; production remains `F3_shah_apparent` unless a gated candidate wins. | Non-recirculating pressure anchors or an explicit recirculation-modeled F6/onset closure that beats `F3_shah_apparent` without hidden multipliers. |
| `two-tap-corner-lower-right-material-reverse-flow` | Raw endpoints exist, but all finite `corner_lower_right` pairs fail ordinary reverse-flow gates. | Treat current two-tap rows as diagnostic or design a non-recirculating/apparent-cluster path; do not admit component K from reverse-flow rows. |

Do not re-open resolved/superseded blockers such as `thermal-cfd-1d-parity`,
`fluid-external-boundary-api-gap`, `closure-qoi-mesh-gci`, or
`cfd-no-radiation-parity` unless a later dated package explicitly reopens them.

## Research Avenues That Most Strengthen The Thesis

### 1. UMX1 upcomer mixing / stratification

Purpose: attack the main wall/test-section temperature-shape blocker through
upcomer exchange/stratification physics.

Current state: AGENT-540 established a disabled-by-default UMX1 Fluid API.
AGENT-543 created scoring-readiness contracts. AGENT-544/548 evidence shows
bounded smoke attempts did not yet admit a candidate and a deeper
stratified-reservoir implementation is blocked by overlapping external Fluid
ownership.

Next useful task: after active TSWFC2/external Fluid ownership clears, open a
new Fluid-edit row for UMX1 stratified reservoir or bracket/root handling only
if it does not overlap active files.

Acceptance signal: accepted roots, conservation residuals, runtime legality,
and split-legal scorecard all pass, with TP/TW/all-probe improvement instead of
only `mdot` improvement.

### 2. TSWFC2 distributed test-section wall/fluid nodes

Purpose: provide a physically resolved alternative to single bulk-to-ambient
test-section heat loss.

Current state: active `TODO-TSWFC2-DISTRIBUTED-WALL-FLUID` owns this lane and
external Fluid files. Do not duplicate or overlap it.

Next useful task: once it completes, read its status/journal/import and decide
whether to write thesis prose, run a bounded smoke score, or mark the lane as
negative evidence.

Acceptance signal: distributed wall/fluid states improve `mdot` and TP/TW/all
probe shape versus M3 without realized wallHeatFlux, CFD `mdot`, imposed cooler
duty, realized test-section heat, or validation temperatures at runtime.

### 3. Source/property label enforcement

Purpose: make closure admission rigorous and thesis-ready.

Current state: AGENT-546 scanned 735 scorecard/gate CSV artifacts, found 1110
fit/admission candidate rows, and produced an enforced view with zero blank
required labels and zero currently allowed rows after gate enforcement.

Next useful task: promote the task-owned AGENT-546 scanner into a reusable
repo-level gate or scorecard template, then refresh Salt1 and holdout/external
labels before any final scorecard prose.

Acceptance signal: every future fit/admission row has nonblank `property_mode`,
`property_sensitivity_label`, `source_validity_envelope_status`,
`source_use_category`, and `provenance_author_title`.

### 4. Upcomer onset anchor matrix

Purpose: turn the upcomer hybrid argument into a regime/onset result.

Current state: current evidence has recirculation points but no
non-recirculating anchor that can promote ordinary coefficients.

Next useful task: design first; launch only under a later compute row. The
design should name Q/Re/insulation cases, same-window pressure/thermal fields,
recirculation metrics, mesh/time uncertainty, and source/property labels.

Acceptance signal: at least one admitted non-recirculating or transition anchor
exists before ordinary coefficient promotion.

### 5. F6 / pressure-anchor path

Purpose: strengthen the hydraulic chapter and reduce dependence on diagnostic
pressure evidence.

Current state: AGENT-547 produced a legwise F6 anchor plan with 36 inventory
rows, three finite raw endpoint feature pairs, three material reverse-flow
endpoint pairs, zero ordinary F6 fit-eligible rows, and zero admission-review
eligible rows.

Next useful task: either identify non-recirculating pressure anchors or define
a recirculation-modeled apparent-cluster pressure path. Do not fit F6 or
component K from current reverse-flow rows.

Acceptance signal: candidate pressure model improves validation/holdout over
`F3_shah_apparent` with source/property labels, no hidden global multiplier, and
no clipped negative K.

### 6. Final frozen predictive scorecard

Purpose: convert the thesis from method plus blocked/diagnostic evidence into
a cleaner predictive-model assessment.

Current state: final scorecard shell exists, but final frozen M6 scores are not
ready while wall/test-section and related gates remain open.

Next useful task: only after UMX1/TSWFC2/source-property gates are settled,
assemble a frozen candidate and score training, support, holdout/testing, and
external-test rows.

Acceptance signal: one scorecard reports `mdot`, TP/TW temperatures, all-probe
shape, heat balance, pressure balance, uncertainty, split role, admission
status, and source paths without target leakage.

## Exact Next Task Sequence

1. Check active ownership: `TODO-TSWFC2-DISTRIBUTED-WALL-FLUID`,
   `AGENT-549`, `AGENT-519`, and two-tap handoff rows.
2. Do not edit Fluid or launch a score grid until active external Fluid
   ownership is complete or released.
3. Promote source/property label enforcement into a reusable closeout or
   scorecard gate.
4. Refresh Salt1 and holdout/external source/property labels.
5. After TSWFC2 lands, decide whether UMX1 or TSWFC2 is the better next
   predictive smoke lane.
6. Design upcomer onset anchors and F6 non-recirculating pressure anchors as
   design packages before any compute launch.
7. Only after model-form and label gates are settled, assemble the final frozen
   scorecard.
8. Then update the external thesis scaffold chapter prose and appendices.

## Output Contracts For Future Work

Every future thesis-strengthening package should emit:

- `README.md` with decision, counts, and guardrails.
- `summary.json` with machine-readable status.
- CSV tables carrying source paths, split role, runtime-input audit,
  source/property labels, and admission status.
- `.agent/status`, `.agent/journal`, and `imports` closeout.
- For thesis-facing work, an update to the relevant `reports/thesis_dossier`
  current section or a dated note explaining why no prose was updated.

Every scorecard/admission package should include:

```text
Source/property label gate: passed/failed/not applicable.
```

If applicable, no fit/admission candidate row may have blank `property_mode`,
`property_sensitivity_label`, `source_validity_envelope_status`,
`source_use_category`, or `provenance_author_title`.

## Do Not Do

- Do not mutate native CFD/OpenFOAM outputs.
- Do not mutate registry/admission state from planning or diagnostic packages.
- Do not use CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler duty,
  scored-row pressure loss, realized test-section heat, or validation
  temperatures as predictive runtime inputs.
- Do not fit or admit `Nu`, `f_D`, `K`, F6, or component K from recirculating
  rows.
- Do not claim SAM validation.
- Do not report resolved/superseded blockers as open.
- Do not edit external thesis or Fluid files without a fresh board row that
  explicitly claims those paths.

## Next Thesis Writing Step

The best immediate writing task is Chapter 6: convert the admission framework
into prose and tables using AGENT-538/546, the split policy, the blocker
register, and the claim ledger. This chapter can be strong before final M6
results because it explains the rigor that prevents overclaiming.
