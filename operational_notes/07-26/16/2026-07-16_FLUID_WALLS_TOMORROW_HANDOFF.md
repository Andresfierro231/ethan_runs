---
task: AGENT-477
date: 2026-07-16
role: Coordinator/Writer
type: operational_note
status: complete
tags: [fluid-walls, final-1d-model, handoff, steady-state, upcomer-onset, thermal-circuit]
provenance:
  - .agent/BOARD.md
  - .agent/BLOCKERS.md
  - reference/geometry_reference.md
  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md
  - work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_final_use_disposition_closeout/README.md
  - work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/README.md
  - work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate/junction_split_heat_ledger_and_model_gate.md
  - work_products/2026-07/2026-07-16/2026-07-16_m3ts_frozen_candidate_coupled_score/README.md
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/README.md
related:
  - .agent/status/2026-07-16_AGENT-477.md
  - .agent/journal/2026-07-16/fluid-walls-tomorrow-handoff.md
  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md
---
# Fluid+Walls Tomorrow Handoff

## Why This Exists

This note preserves the July 16 coordination state for the final steady-state
1D model form so tomorrow's agents can resume without reconstructing decisions
from chat. The current model target is `fluid+walls`: every segment carries its
own fluid energy balance, wall/material thermal circuit, pressure model,
source/sink role, boundary-layer/development state, recirculation/admission
flags, and uncertainty status.

Do not include storage or transient wall terms in the current model. Those are
future work, not part of the thesis-facing steady-state form being coordinated
now.

## Open First Tomorrow

Read these in order:

1. `.agent/BOARD.md`
2. `.agent/BLOCKERS.md`
3. `reference/geometry_reference.md`
4. `operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md`
5. `work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/README.md`
6. `work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate/junction_split_heat_ledger_and_model_gate.md`
7. `work_products/2026-07/2026-07-16/2026-07-16_m3ts_frozen_candidate_coupled_score/README.md`
8. `work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/README.md`

The geometry anchor is non-negotiable: the physical upcomer is
`left_lower_leg -> test_section_span -> left_upper_leg`, and the test section is
the middle upcomer span. The test section is bare quartz, not an insulated steel
pipe segment.

## Current Model Contract

The segment energy form should stay steady:

```text
d/ds[ mdot cp(T) T ] =
    q'_heater_to_fluid
  - q'_cooler_removed
  - q'_wall_loss
  + q'_other_source_to_fluid
```

The wall model should be implemented as a per-segment thermal circuit:

```text
fluid bulk
  -> internal convection / boundary-layer state
  -> steel wall or quartz wall conduction
  -> insulation or local material layer where present
  -> external convection to ambient
  -> external radiation to surroundings
```

Use CFD setup fields such as geometry, material stack, `h`, `Ta`, `Tsur`,
emissivity, and layer thickness as runtime-legal inputs. Realized CFD
`wallHeatFlux`, CFD `mdot`, imposed cooler duty, and validation temperatures are
diagnostic/scoring evidence only unless a later admission package explicitly
allows them.

For the test section, carry the sign from the balance rather than hard-coding a
source or sink:

```text
q'_test_section_to_fluid =
    q'_electrical_deposition_to_fluid_or_wall
  - q'_quartz_to_ambient_loss
```

The available mainline evidence shows net test-section contribution can be
negative even with electrical input, so the model must allow positive, negative,
or near-zero net contribution.

## What We Have

- Blocker ledger: `.agent/BLOCKERS.md` is the authoritative current state.
  The remaining open blockers are `predictive-wall-test-section-submodels`,
  `upcomer-onset-data-sparsity`, and `f6-friction-re-correction`.
- Closure-QOI/GCI: resolved by AGENT-474 final-use disposition. It reviewed
  `13` non-upcomer final-use rows, admitted `0` publication-GCI rows,
  explicitly excluded `13` rows, and retained `0` extraction-required rows.
  Do not reopen `closure-qoi-mesh-gci` unless a future package creates a new
  final-use QOI lacking admission or exclusion.
- Geometry: mostly admitted and documented. The test-section location is clear
  in `reference/geometry_reference.md`.
- Pressure: diagnostic pressure maps exist for all relevant segments, but
  admitted pressure `K`, `f`, and development coefficients remain incomplete.
- Thermal circuit: the form is documented and setup evidence exists, but the
  `TODO-PREDICT-WALL-THERMAL-CIRCUIT` implementation/admission package is still
  open.
- Source/sink roles: heater, cooler/HX, passive wall, test section, and
  junction roles exist in prior ledgers, but final `fluid+walls` ownership is
  only partial.
- Junction heat: AGENT-473 split Salt2/Salt3/Salt4 into 87 patch rows and
  matched aggregate junction trends closely enough for model gating, but
  validation Salt2 and perturbation split ledgers plus admitted pressure `K`
  remain missing.
- Recirculation flags: AGENT-467 provides recirculation feature/admission
  guardrails and the hybrid upcomer contract. Current recirculating upcomer rows
  are not valid ordinary single-stream `Nu`, `f_D`, or `K` fits.
- Uncertainty: time-window UQ is stronger than closure-QOI coefficient
  uncertainty. Current closure-QOI final-use ambiguity is closed by exclusion,
  not by coefficient admission.

## Active Hazards

- `AGENT-476` is active on board cleanup and generated index refresh. Do not
  modify generated index files or duplicate its board-cleanup work.
- `AGENT-475` is active on the packed Salt4 high-heat bracket (`500 W`,
  `1000 W`, `1500 W`). Check its closeout before proposing or launching another
  onset/probe run.
- `AGENT-471` submitted job `3299610` for the high-heat no-recirculation probe.
  Treat the solver job as external state to inspect, not as something to
  duplicate.
- `AGENT-470` found the frozen M3+TS coupled score path still blocked because
  all bounded Fluid runs timed out. The next action there is a runtime/path fix
  or smaller coupled solve route, not new physical theory.

## Recommended Task Order

1. Re-read `.agent/BOARD.md` and `.agent/BLOCKERS.md`; the active rows are
   changing quickly.
2. Check AGENT-471 and AGENT-475 job/status files before any new CFD-onset
   planning. Do not submit duplicate high-heat probes.
3. Use the `fluid+walls` readiness ledger to identify the shortest missing-data
   path for a thesis-defensible model scorecard.
4. Advance `predictive-wall-test-section-submodels` by fixing the coupled M3+TS
   scoring path or defining a smaller runtime-legal coupled solve; do not use
   realized CFD test-section net heat as a predictive input.
5. Claim `TODO-PREDICT-WALL-THERMAL-CIRCUIT` to turn the thermal-circuit theory
   into segment tables and admitted/blocked fields.
6. Use AGENT-473's junction split gate to decide which junction heat rows can
   enter `fluid+walls` as separate regions rather than hiding them in pipe
   `Nu`.
7. Claim `TODO-UPCOMER-ONSET-CFD-ANCHOR-MATRIX` only after the active high-heat
   probes have reported enough status to avoid duplicate runs.
   AGENT-478 has now provided a ready study package at
   `work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design/`
   with the proposed Salt3 high-Re/high-insulation sentinel, low-Q/low-insulation
   sentinel, `Q x insulation` matrix, required outputs, and uncertainty plan.
8. Claim `TODO-PAPER-FINAL-1D-MODEL-FORM-DOCS` only after shareable results
   exist. Until then, keep paper text framed as model form plus blocker status,
   not as final validation.

## Board Rows To Track

- `TODO-PREDICT-WALL-THERMAL-CIRCUIT`
- `TODO-PREDICT-FLUID-WALLS-READINESS-LEDGER` (complete as of July 16)
- `TODO-PREDICT-TEST-SECTION-HEAT-LOSS`
- `TODO-PREDICT-SEGMENT-EQUATION-CONTRACT`
- `TODO-PREDICT-SEGMENT-PRESSURE-MODELS`
- `TODO-PREDICT-SEGMENT-THERMAL-MODELS`
- `TODO-PREDICT-BOUNDARY-LAYER-DEVELOPMENT-SCORECARD`
- `TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL`
- `TODO-UPCOMER-ONSET-CFD-ANCHOR-MATRIX`
- `TODO-THESIS-UPCOMER-RECIRCULATION-SECTION`
- `TODO-PAPER-FINAL-1D-MODEL-FORM-DOCS`

## Do-Not-Do Guardrails

- Do not mutate native solver outputs.
- Do not use runtime CFD `mdot`, realized `wallHeatFlux`, imposed cooler duty,
  or validation temperatures as predictive inputs.
- Do not include transient wall storage in the current thesis-facing
  steady-state model.
- Do not collapse junction/stub/connector heat loss into a generic pipe `Nu`.
- Do not fit ordinary single-stream `Nu`, `f_D`, or `K` in the recirculating
  upcomer rows.
- Do not edit external Fluid source without a separate external board claim.
- Do not refresh generated documentation indexes while another active task owns
  that path.
