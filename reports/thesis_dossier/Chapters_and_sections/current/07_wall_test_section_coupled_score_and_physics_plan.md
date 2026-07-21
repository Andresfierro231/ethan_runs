---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/coupled_scorecard.csv
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/coupled_delta_vs_m3.csv
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/candidate_admission_review.csv
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/runtime_input_audit.csv
  - .agent/status/2026-07-17_AGENT-498.md
  - .agent/journal/2026-07-17/wall-test-section-distribution-ladder.md
tags: [thesis-section, current-section, paper-ready, forward-model, wall-circuit, test-section, source-shape]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
  - predictive-wall-test-section-submodels
  - AGENT-498
  - AGENT-511
  - AGENT-513
task: AGENT-514
date: 2026-07-17
role: Writer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# Coupled Wall/Test-Section Score And Source-Shape Plan

## Paper Claim

The coupled M3+test-section+cooler scorecard shows a useful negative result.
Adding a Salt2-trained passive wall/test-section heat-placement distribution to
the admitted cooler model removes most of the mass-flow error on Salt3 and
Salt4, but it does not reproduce the temperature field. The candidate family is
therefore not admitted as a closure model. Its value is diagnostic: it separates
the remaining blocker from total heat-removal magnitude and points toward
source placement, wall-temperature drive, axial mixing, and upcomer/test-section
coupling as the next physical mechanisms to test.

This is paper-useful because it is a controlled falsification. The candidates
were runtime-legal, solver-coupled, and scored against held-out rows without
using held-out CFD outputs as runtime inputs. They failed despite improving
mass flow, so the failure is not a timeout artifact and not a simple lack of
cooler coupling.

## Evidence Package

The result comes from `AGENT-498`, package:
`work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/`.

Primary tables:

| File | Use in paper |
| --- | --- |
| `coupled_scorecard.csv` | Absolute mdot, TP, TW, and all-probe coupled performance for each candidate/case. |
| `coupled_delta_vs_m3.csv` | Held-out Salt3/Salt4 deltas versus the M3 comparator. |
| `candidate_admission_review.csv` | Final admission table: runtime gate, validation gate, holdout gate, decision, blockers. |
| `runtime_input_audit.csv` | Leakage audit proving the score used setup/Salt2-fit inputs only. |
| `scenario_contracts.csv` | Serialized Fluid runtime scenarios for replay/provenance. |
| `segment_heat_placement_audit.csv` | Static heat-placement evidence behind the Salt2-trained wall shapes. |

Execution provenance:

- Latest coupled run: foreground compute-node `srun` step `3299312.2`.
- Command: `srun -N1 -n1 python3 tools/analyze/build_wall_test_section_distribution_ladder.py --run-fluid --timeout-seconds 273`.
- Coupled rows: `12/12` completed.
- Fluid roots: all accepted.
- Candidate admissions: `0/4`.
- Decision for `predictive-wall-test-section-submodels`: keep open.

## Model Forms Tested

All candidates combine a local wall/test-section distribution with an admitted
cooler model. The wall/passive term is trained only from Salt2 information; the
cooler multiplier is the Salt2-fit cooler coefficient from the cooler-removal
model package. Salt3 is validation and Salt4 is holdout.

| Candidate family | Wall/test-section idea | Cooler idea |
| --- | --- | --- |
| `PB2_salt2_local_shape_passive_hA_p1_PLUS_HX_LUMPED_UA_NTU` | Redistribute passive hA by a Salt2-trained segment/role shape. | Lumped UA/NTU cooler. |
| `PB2_salt2_local_shape_passive_hA_p1_PLUS_HX_SEGMENTED_UA_NTU_N16` | Same PB2 wall distribution. | Segmented N16 UA/NTU cooler. |
| `PB3_upcomer_test_section_attenuated_shape_p1_PLUS_HX_LUMPED_UA_NTU` | PB2 plus Salt2 wall-layer-derived attenuation on upcomer ambient/test-section roles. | Lumped UA/NTU cooler. |
| `PB3_upcomer_test_section_attenuated_shape_p1_PLUS_HX_SEGMENTED_UA_NTU_N16` | Same PB3 wall distribution. | Segmented N16 UA/NTU cooler. |

The tested mechanisms do not use validation or holdout `wallHeatFlux`, mdot,
probe temperatures, wall-shell temperatures, imposed cooler duty, or realized
test-section heat as runtime inputs. They use setup external-boundary rows,
Salt2-only wall shape, and the Salt2 cooler coefficient.

## Admission Gate

For a candidate to be admitted, it must pass both held-out cases:

1. Salt3 validation mdot absolute percent error must be no worse than M3.
2. Salt3 validation all-probe RMSE must be no worse than M3.
3. Salt3 validation TW RMSE must be no worse than M3.
4. Salt4 holdout mdot absolute percent error must be no worse than M3.
5. Salt4 holdout all-probe RMSE must be no worse than M3.
6. Salt4 holdout TW RMSE must be no worse than M3.
7. Runtime-input audit must pass.

This gate deliberately rejects candidates that solve only mass flow while
destroying temperature shape. That behavior is exactly what happened.

## Quantitative Result

Negative mdot delta is better. Negative all-probe and TW deltas would be better.
Every candidate improves mdot error but worsens all-probe and TW RMSE.

| Candidate | Salt3 validation delta vs M3 | Salt4 holdout delta vs M3 | Decision |
| --- | --- | --- | --- |
| `PB2 + lumped HX` | mdot `-15.64535145 pct`; all-probe `+35.4599137 K`; TW `+42.39586766 K` | mdot `-12.85262822 pct`; all-probe `+43.11664296 K`; TW `+48.71908999 K` | not admitted |
| `PB2 + segmented HX N16` | mdot `-15.65114081 pct`; all-probe `+35.470608 K`; TW `+42.41122425 K` | mdot `-12.85715657 pct`; all-probe `+43.12306786 K`; TW `+48.72979409 K` | not admitted |
| `PB3 + lumped HX` | mdot `-11.30109382 pct`; all-probe `+36.0150509 K`; TW `+44.50322797 K` | mdot `-17.50605109 pct`; all-probe `+41.25189604 K`; TW `+48.6768088 K` | not admitted |
| `PB3 + segmented HX N16` | mdot `-11.29531994 pct`; all-probe `+36.02976758 K`; TW `+44.52254535 K` | mdot `-17.51055099 pct`; all-probe `+41.26196237 K`; TW `+48.69140384 K` | not admitted |

In absolute terms, the best validation all-probe RMSE is still about `53.21 K`
versus M3 `17.749 K`. The best holdout all-probe RMSE is about `58.22 K`
versus M3 `16.971 K`. TW errors show the same pattern. The wall/passive
redistribution family therefore fixes a hydraulic symptom while making the
temperature field substantially less credible.

## Interpretation

The result narrows the open blocker. Total external heat-removal capacity and
passive hA distribution are not sufficient explanations for the remaining
M3+test-section+cooler failure. If they were sufficient, a Salt2-trained local
distribution should have improved the held-out temperature probes when it
improved mass flow. Instead, mdot and temperature metrics move in opposite
directions.

The most likely missing physics is not another scalar wall-loss multiplier. The
next candidates should change where and how heat enters, leaves, mixes, or
couples to the upcomer/test-section region:

- heater source redistribution along the lower-leg/test-section path;
- wall-temperature-drive formulation instead of passive hA cancellation;
- axial mixing or exchange in the upcomer where recirculation breaks
  single-stream assumptions;
- explicit test-section wall/fluid coupling rather than treating the segment as
  a passive hA bucket.

The paper should state this as a falsified candidate class, not as a failed
project. The negative result is scientifically useful because it prevents an
overclaim: a model can match mdot and still fail as a predictive thermal model.

## Suggested Paper Text

The following paragraph can be used directly after the coupled scorecard table.

> We next tested whether the remaining wall/test-section blocker could be
> resolved by redistributing passive external heat exchange while retaining the
> admitted cooler model. Two Salt2-trained wall-distribution candidates were
> coupled to lumped and segmented cooler models and scored on Salt3 validation
> and Salt4 holdout cases. All twelve coupled Fluid solves completed with
> accepted roots. The candidates reduced mass-flow error relative to M3 on both
> held-out cases, but all-probe and wall-temperature RMSE increased by
> approximately 35-49 K. We therefore did not admit the candidate family. This
> result indicates that the remaining error is dominated by temperature-shape
> physics rather than by total passive heat-removal magnitude alone.

Use the table above, or a condensed version, as the supporting numerical table.
Do not call PB2/PB3 predictive closures; call them diagnostic falsification
experiments.

## Figure And Table Recommendations

Recommended paper table:

- rows: four PB2/PB3 plus cooler candidates;
- columns: Salt3 mdot delta, Salt3 all-probe delta, Salt3 TW delta, Salt4 mdot
  delta, Salt4 all-probe delta, Salt4 TW delta, admission decision;
- caption: "Negative mdot delta indicates improvement relative to M3; negative
  temperature deltas would indicate improvement. All candidates improve mdot
  while degrading temperature metrics."

Recommended figure:

- x-axis: mdot delta vs M3;
- y-axis: all-probe delta vs M3;
- marker color: Salt3 validation or Salt4 holdout;
- marker shape: PB2/PB3 wall family;
- shaded quadrant: admitted-improvement quadrant where both deltas are negative.

Expected visual result: all points lie in the "mdot better, temperature worse"
quadrant. That makes the negative result easy to defend.

## Next-Step Physics Plan

The next work should be staged as predeclared candidate families, not open-ended
tuning. Salt2 remains the fit row for these candidate screens; Salt3 validation
and Salt4 holdout must not be used for fitting or model selection.

### 1. Heater Source Redistribution

Hypothesis: the model injects heater power into the wrong axial location or too
compact a region, which can make mdot plausible while shifting the TP/TW shape.

Current board hook: `AGENT-511`.

Candidate examples:

- split the heater source over a lower-leg-to-test-section span using the
  existing `tw4_to_tp3_three_span` Fluid API;
- fit one Salt2 redistribution parameter or a predeclared small set of shape
  options;
- keep cooler model fixed to the admitted Salt2 cooler candidate;
- keep wall/test-section passive model fixed while testing source placement.

Required outputs:

- source-shape definition table;
- runtime-input audit;
- coupled mdot/TP/TW scorecard;
- delta-vs-M3 table;
- admission review;
- failure localization by sensor group.

Falsification criterion: reject the source redistribution candidate if mdot
improves but all-probe/TW remains worse than M3 on either Salt3 or Salt4.

### 2. Local Wall-Temperature Drive

Hypothesis: passive hA scaling fails because the driving temperature is wrong;
the model should use a local wall/outer-surface drive rather than a bulk or
global cancellation drive in upcomer/test-section roles.

Current board hook: `AGENT-513`.

Candidate examples:

- change upcomer/test-section role-row drive selector to pipe outer-wall or
  outer-surface drive;
- use setup-only wall-layer parameters and Salt2-fit drive coefficients;
- keep PB2/PB3 passive totals as diagnostic comparators but do not rerun them
  as new candidates unless the drive equation changes.

Required outputs:

- drive-equation contract;
- sign and unit audit;
- runtime-input audit forbidding Salt3/Salt4 wall-shell temperatures;
- coupled scorecard with the same mdot/all-probe/TW gates.

Falsification criterion: reject the drive candidate if it only improves one
sensor family by importing a held-out wall-temperature surrogate or if it fails
the same held-out coupled gates.

### 3. Axial Mixing And Upcomer Exchange

Hypothesis: the upcomer/test-section path is not a single advecting stream in
the CFD-relevant regimes. A reduced model needs an exchange or mixing term to
represent recirculation, stratification, or delayed thermal communication.

Candidate examples:

- add a two-lane upcomer model with throughflow and recirculation-cell exchange;
- add an axial dispersion or effective mixing term only where recirculation
  flags support it;
- use recirculation diagnostics as regime guards, not as direct fitted
  validation inputs.

Required evidence before admission:

- Salt2-fit exchange parameter or predeclared literature/geometry value;
- validation/holdout score on Salt3/Salt4;
- no ordinary single-stream `Nu`, `f_D`, or `K` fit through recirculating rows;
- uncertainty table for the onset/regime flag.

Falsification criterion: reject if the exchange term improves TP/TW by
compensating with nonphysical heat or if it cannot be bounded by independent
recirculation evidence.

### 4. Upcomer/Test-Section Wall/Fluid Coupling

Hypothesis: the test section needs an explicit wall/fluid coupling state rather
than a passive bucket, because source, quartz wall, external loss, and fluid
advection are not colocated.

Candidate examples:

- add a local wall node for the test-section/upcomer segment;
- solve a steady wall balance with heater/test-section source, internal
  convection, wall conduction, and external loss;
- constrain the model with setup geometry/materials and Salt2-fit coefficients
  only.

Required outputs:

- wall-state residual equations;
- allowed setup inputs and forbidden score-row inputs;
- convergence/root-status table;
- mdot/TP/TW/all-probe scorecard;
- component heat-balance residual table.

Falsification criterion: reject if the wall node requires held-out wall-shell
temperature or realized held-out wallHeatFlux as a runtime input.

## Sequencing

Recommended order:

1. Finish heater source redistribution (`AGENT-511`) because it directly tests
   the source-location hypothesis with existing Fluid API support.
2. Finish wall-temperature-drive candidate (`AGENT-513`) because it tests the
   passive-drive hypothesis without inventing a new state variable.
3. If both fail, build an axial mixing/upcomer exchange candidate with an
   explicit regime guard.
4. If source and drive both show partial improvements but still fail TW, add a
   wall/fluid coupling state for the test-section/upcomer region.
5. After each candidate, update the same compact paper table: candidate,
   runtime legality, Salt3 deltas, Salt4 deltas, admission status, and physical
   interpretation.

Do not choose the next candidate by looking for the best Salt3/Salt4 score
after many variants. The scientific plan is to predeclare small candidate
families, run the coupled scorecard once, and report failures as narrowing
evidence.

## Minimum Acceptance Criteria For Any Next Candidate

Each future source/temperature-shape package must include:

- a named physical hypothesis;
- a one-row equation contract that can be cited in the paper;
- a runtime-input audit;
- train/validation/holdout split statement;
- mdot, TP, TW, and all-probe metrics;
- delta-vs-M3 table;
- admission status table with admitted, validation-only, diagnostic-only, and
  blocked categories where relevant;
- root/convergence status for coupled Fluid solves;
- explicit statement of whether `predictive-wall-test-section-submodels` stays
  open or can be narrowed/resolved.

This keeps the thesis defensible even if no final wall/test-section closure is
admitted: each failed candidate becomes a documented scientific constraint on
the remaining model-form space.
