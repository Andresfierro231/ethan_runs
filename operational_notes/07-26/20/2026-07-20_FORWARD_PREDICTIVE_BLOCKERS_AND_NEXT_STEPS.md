---
provenance:
  - .agent/BLOCKERS.md
  - operational_notes/maps/forward-predictive-model.md
  - work_products/2026-07/2026-07-18/2026-07-18_blocker_research_path_next_step_synthesis/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_blocker_research_path_next_step_synthesis/verified_blockers.csv
  - work_products/2026-07/2026-07-18/2026-07-18_blocker_research_path_next_step_synthesis/research_paths.csv
  - work_products/2026-07/2026-07-18/2026-07-18_blocker_research_path_next_step_synthesis/next_steps_queue.csv
  - work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_stratified_reservoir_blocked_handoff/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_dry_contract/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/README.md
tags: [forward-model, predictive-1d, blocker-synthesis, next-steps, wall-test-section, upcomer-stratification]
related:
  - operational_notes/maps/forward-predictive-model.md
  - .agent/status/2026-07-20_AGENT-552.md
  - .agent/journal/2026-07-20/forward-predictive-blockers-next-steps-documentation.md
  - imports/2026-07-20_forward_predictive_blockers_next_steps_documentation.json
task: AGENT-552
date: 2026-07-20
role: Writer/Coordinator
type: operational_note
status: complete
---
# Forward Predictive Blockers And Next Steps

This note documents the current forward predictive model state from durable repo
evidence. It is scoped to the setup-only model that predicts `mdot` and TP/TW
temperatures without runtime use of CFD `mdot`, realized CFD `wallHeatFlux`,
imposed CFD cooler duty, realized test-section heat, or validation/holdout
temperatures.

## Current Status

The old broad blocker `predictive-heater-cooler-wall-submodels` is superseded.
Heater and cooler/HX now have bounded setup-only submodels:

- Heater: `salt2_fit_constant_heater_efficiency` is admitted in the July 16
  boundary-submodel screen.
- Cooler/HX: `salt2_fit_constant_UA_bulk_drive` is admitted in the July 16
  boundary-submodel screen.

This does not admit final forward-v1. The unresolved forward-model problem is
now local thermal shape and coupled flow/thermal physics, not simply missing
heater or cooler bounds.

## Major Blockers

### 1. Wall / test-section / passive-boundary thermal physics

Blocker ID: `predictive-wall-test-section-submodels`.

This is the primary forward-model blocker. Runtime-legal candidates have been
implemented and solved, but none are admitted. The repeated failure pattern is
specific: candidates often improve `mdot` relative to M3, but worsen TP, TW, and
all-probe RMSE. The persistent scoreable residuals are heated-incline wall
temperature failures, especially TW5/TW6. TP2 and TW10 are separate policy or
extraction exclusions and should not be used to explain away TW5/TW6 failures.

Do not retry passive wall-state selectors or total passive hA scaling as the
primary next lane. The evidence has narrowed the problem toward local
wall-temperature/thermal-shape physics, heater/source placement limits,
explicit test-section wall/fluid coupling, and upcomer axial
mixing/stratification.

### 2. Upcomer mixing, stratification, and recirculation

The upcomer should not be treated as an ordinary single-stream pipe in current
recirculating rows. Ordinary `Nu`, `f_D`, and `K` promotion remains blocked for
the upcomer.

UMX1 is the current top research path because it targets energy-conserving
upcomer exchange/stratification. However, AGENT-544 made UMX1 a
`stop_before_grid` case: the smoke package passed conservation (`9/9`) but only
`3/9` rows passed accepted-root gates, and the tested exchange candidates
worsened scored probe groups relative to the disabled baseline. AGENT-548 then
blocked the stratified-reservoir Fluid edit because another external Fluid row
owned the same files.

The next UMX1 step is therefore an API/root/contract row, not a scoring grid.

### 3. Upcomer onset data sparsity

Blocker ID: `upcomer-onset-data-sparsity`.

The current evidence has observed recirculation points but no admitted
non-recirculating or near-onset anchors. This prevents ordinary coefficient
promotion and limits confidence in any upcomer onset law.

Resolution requires near-onset or non-recirculating CFD anchors with
same-window reverse-flow, pressure, wall/bulk temperature, source/property
labels, and mesh/time uncertainty metrics.

### 4. F6 / two-tap pressure correction

Blocker IDs:

- `two-tap-corner-lower-right-component-isolation-fails`
- `two-tap-corner-lower-right-same-qoi-uq-missing`
- `two-tap-corner-lower-right-material-reverse-flow`
- `f6-friction-re-correction`

The raw endpoint path is no longer missing data in the simple availability
sense, but it is not admissible. Corner/lower-right component isolation fails,
same-QOI uncertainty is missing, and raw endpoint pairs fail the ordinary
recirculation gate. These rows remain diagnostic/component-lane evidence only.

Do not fit F6 from recirculating rows, clip negative K, introduce a hidden
global multiplier, or admit component K from the present two-tap evidence.

### 5. Source/property label enforcement

The final predictive scorecard must not admit rows with missing source-envelope
or property-sensitivity labels. AGENT-546 found `1110` fit/admission candidate
rows and blocked all `1110` in the enforced view until labels and
source/property content permit use.

Required nonblank labels are:

- `property_mode`
- `property_sensitivity_label`
- `source_validity_envelope_status`
- `source_use_category`
- `provenance_author_title`

This is documentation/scoring hygiene, but it is thesis-critical. It prevents
Salt1, perturbation, external, and future rows from being silently treated as
inside-envelope fit evidence.

## Ordered Next Steps

### 1. UMX1 Fluid API/root row

Implement or formally reject a real energy-conserving upcomer
mixing/stratification hook in Fluid. The row must expose declared stratified or
second-stream state, pass runtime legality, preserve split discipline, and pass
accepted-root dry checks before any grid.

Acceptance signal: the API contract has real hook fields, accepted-root dry
behavior, conservation checks, and no mdot-only admission path.

### 2. TSWFC2 as secondary wall/test-section path

Use the TSWFC2 distributed wall/fluid node contract only after UMX1 is
unavailable or fails cleanly. TSWFC2 must remain distinct from the failed
AGENT-526 one-node bulk-to-ambient series-resistance fallback.

Acceptance signal: a dry contract and later smoke row declare distributed
fluid/inner-wall/outer-wall/external states, a per-node heat ledger, split
gates, runtime-forbidden input checks, and temperature-shape scoring against
M3/prior wall-source candidates.

### 3. Upcomer onset anchor design

Design the Q/Re/insulation matrix needed to produce near-onset and
non-recirculating upcomer evidence. This is a design/admission-contract step
first; launch only under a separate compute row.

Acceptance signal: the matrix names cases, expected Re/onset coverage,
same-window reverse-flow metrics, pressure and thermal extraction needs,
mesh/time uncertainty needs, and admission gates.

### 4. F6/two-tap pressure anchor path

Continue F6 work only through non-recirculating pressure anchors or an explicit
throughflow-plus-recirculation pressure closure. Raw endpoint postprocessing and
component review must stay separate from F6 fitting/admission.

Acceptance signal: finite pressure/velocity endpoints plus pressure-basis,
straight-reference, reverse-flow, same-QOI UQ, and source/property gates pass;
then a separate scorecard shows validation/holdout improvement over
`F3_shah_apparent` without hidden multipliers.

### 5. Source/property label refresh before scorecards

Before any final predictive scorecard reports fit, model selection, or
admission, refresh labels for Salt1, perturbation, external, and future rows.

Acceptance signal: no fit/admission candidate row has blank required
source/property labels, and rows outside support are explicitly blocked or
refresh-required.

## Guardrails

- Do not re-report heater/cooler/HX as the broad live blocker; that blocker is
  superseded by the narrower wall/test-section/passive-boundary blocker.
- Do not launch a UMX1 grid from the July 18 smoke outputs.
- Do not tune passive hA, wall-state selectors, friction, source placement, or
  sensor policy to fake upcomer mixing.
- Do not use CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler duty,
  realized test-section heat, validation temperatures, or holdout temperatures
  as predictive runtime inputs.
- Do not promote ordinary upcomer `Nu`, `f_D`, or `K` from recirculating rows.
- Do not admit component K or F6 from the current two-tap corner/lower-right
  endpoint evidence.
- Do not report final forward-v1 admission until the wall/test-section,
  upcomer/onset, F6/hydraulic, and source/property scorecard gates are satisfied.
