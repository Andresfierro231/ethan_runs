---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_time_series_uncertainty_story/mainline_salt234_uncertainty_components.csv
  - work_products/2026-07/2026-07-13/2026-07-13_time_series_uncertainty_story/paper_uncertainty_bounds_salt234.csv
  - work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution/mesh_gci_gate_for_admitted_candidates.csv
  - work_products/2026-07/2026-07-13/2026-07-13_litrev_property_sensitivity/property_sensitivity_summary.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/sensor_map_contract.csv
  - work_products/2026-07/2026-07-17/2026-07-17_sensor_tp2_restore_tw10_exclude/sensor_policy_scorecard.csv
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv
tags: [thesis-section, current-section, uncertainty, mesh-gci, property-sensitivity, sensor-map, split-policy]
related:
  - TODO-THESIS-ENRICHMENT-RESEARCH-AVENUES
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md
task: AGENT-516
date: 2026-07-17
role: Writer/Reviewer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# Uncertainty Chapter Package

## Chapter Claim

The thesis uncertainty story is not one scalar error bar. It is a set of
separate trust boundaries that must stay visible: time-window uncertainty,
mesh/GCI disposition, property-lane sensitivity, sensor-map uncertainty, split
uncertainty, runtime-leakage uncertainty, recirculation/onset uncertainty, and
wall/test-section heat-placement uncertainty.

The practical rule is simple: uncertainty can qualify a claim, but it cannot
promote a diagnostic coefficient into an admitted predictive coefficient.

## Chapter Skeleton

1. Define the reference target.
   - The target is CFD-derived steady operating evidence, not experiment.
   - Distinguish case admission, terminal window, and final-window statistics.

2. Quantify time-window uncertainty.
   - Report drift, oscillation, corrected SEM, and paper envelopes for mdot,
     fluid temperatures, and wall temperatures.
   - Use the time-window package as the source of steady reference uncertainty.

3. State mesh/GCI disposition.
   - Separate publication-ready GCI from final-use diagnostic disposition.
   - Explain why many closure coefficient rows remain diagnostic even when the
     row is useful for model-form choice.

4. Separate property-lane sensitivity.
   - Report the chosen property mode before fitting or comparing closures.
   - Treat property modes as model choices that move `Re`, `Pr`, `Gz`,
     buoyancy, pressure residuals, and heat-transfer interpretation.

5. State sensor-map uncertainty.
   - TP/TW temperatures are validation targets only.
   - Preserve coordinate/projection caveats and sensor exclusions in score
     tables.

6. State split uncertainty and legal use.
   - Training, support, holdout/testing, external-test, and future rows have
     different evidentiary roles.
   - A row's uncertainty does not override its split role.

7. State model-form uncertainty.
   - Segment-only, junction-aware, and hybrid upcomer models carry different
     structural assumptions.
   - Admission status travels with each coefficient, not just each model.

8. End with claim-use rules.
   - Which claims are thesis-ready, caveated, diagnostic, blocked, or future.

## Uncertainty Source Table

| Source | What it measures | Current thesis use | Key caveat |
| --- | --- | --- | --- |
| Time-window uncertainty | Drift, oscillation, corrected SEM, two-sided SEM intervals, and paper envelopes over terminal steady windows. | Reference-target uncertainty for CFD mdot, probe temperatures, and wall temperature. | Does not explain structural model bias by itself. |
| Mesh/GCI disposition | Whether closure QOI rows have complete mesh triplets, monotonic behavior, GCI status, and final-use decisions. | Admission gate for closure coefficients and a caveat for diagnostic rows. | Many pressure/thermal rows remain not publication-ready or not fit-admissible; report row scope. |
| Property-lane sensitivity | Movement in `Re`, `Pr`, `Gz`, heat residual context, and pressure proxies across property modes. | Model-choice uncertainty before closure fitting. | Do not fit under one property mode and report as property-independent. |
| Sensor map | TP/TW runtime role, score role, 1D projection, native CFD representation, coordinate caveats, and exclusions. | Defines scoreable validation targets and sensor caveats. | Sensors are never runtime inputs; TP2/TW10 require policy-specific handling. |
| Split policy | Legal use of final training, training support, holdout/testing, external, and future rows. | Prevents leakage and controls claim strength. | Score quality cannot retroactively make a holdout/external row trainable. |
| Runtime leakage audit | Whether a model used scored-row CFD outputs at prediction time. | Separates predictive models from diagnostic replays. | A numerically accurate replay can still be non-predictive. |
| Recirculation/onset evidence | Reverse-flow indicators, PM5/PM10 matched-plane evidence, and upcomer onset sparsity. | Structural uncertainty for upcomer and internal coefficient labels. | Ordinary single-stream `Nu`, `f_D`, or `K` names are invalid in recirculating states. |
| Wall/test-section heat placement | Whether source/loss placement reproduces mdot and temperature shape. | Explains the active thermal blocker and negative PB2/PB3 result. | Improving mdot while worsening temperatures is not admission. |

## Time-Window Uncertainty

Use `mainline_salt234_uncertainty_components.csv` and
`paper_uncertainty_bounds_salt234.csv` as the chapter table sources. The table
should report:

- case;
- quantity group: mdot, TP-like fluid probe, TW/wall temperature;
- terminal window length;
- drift over window;
- corrected SEM;
- two-sided 95 percent SEM;
- paper envelope absolute and relative bounds;
- steady verdict.

Thesis wording:

> Final-window statistics provide the uncertainty of the CFD reference target
> over the chosen steady window. They are carried separately from model residuals
> so that a closure error is not hidden inside the steady-state uncertainty
> estimate.

## Mesh/GCI Disposition

Use `mesh_gci_gate_for_admitted_candidates.csv` as the source table. The
chapter should distinguish:

- complete mesh triplet available;
- GCI computed and monotonic;
- publication-ready coefficient;
- final-use diagnostic disposition;
- excluded/reextract/future rows.

Current safe claim:

> Mesh/GCI status is row-specific. The current evidence can support diagnostic
> model-form decisions for several rows, but broad publication-grade pressure or
> internal heat-transfer coefficient admission is not available for every QOI.

Avoid:

```text
Mesh uncertainty is resolved for the thesis.
```

Prefer:

```text
The final-use disposition is resolved for this row family; the coefficient is
diagnostic/admitted/blocked as stated in the row ledger.
```

## Property-Lane Sensitivity

Use `property_sensitivity_summary.csv` and `property_mode_matrix.csv`.
Property choices move nondimensional groups before any closure fit is applied.
The July 13 summary shows, for example, that Jin-viscosity modes change mean
`Re` by roughly 25-30 percent relative to the replication mode and change `Pr`
and `Gz` by larger factors in the Salt2-4 rows.

Chapter rule:

> Property mode is an upstream model decision. Friction, heat-transfer, and
> buoyancy comparisons must state the property lane before interpreting closure
> residuals.

## Sensor-Map Status

Use the sensor-map contract plus the July 17 TP2/TW10 policy scorecard. The
chapter should say:

- TP/TW labels are validation targets only;
- runtime models cannot use validation temperatures;
- provisional coordinate status must be reported;
- TP2 had a path/projection issue in earlier mapping and is handled by the
  later sensor policy;
- TW10 remains excluded/blocked for active-HX shell prediction in the current
  policy context;
- multi-point wall-temperature families should not be flattened without an
  explicit aggregation rule.

## Split Uncertainty

The split controls claim strength:

| Role | Claim strength |
| --- | --- |
| Final training | Can fit admitted terms if runtime and admission gates pass. |
| Training support | Can support trends and sensitivity, with labels preserved. |
| Holdout/testing | Can score a frozen model only. |
| External test | Can score or contextualize a frozen model only; no tuning. |
| Future rows | Cannot support final claims until terminal harvest and admission exist. |

This chapter should state that split uncertainty is not statistical noise. It is
evidentiary uncertainty: what the row is legally allowed to prove.

## Model-Form And Admission Uncertainty

Model form is a dominant uncertainty source:

- Segment-only ledgers can conserve totals while misassigning local losses.
- Junction-aware ledgers preserve local heat and pressure ownership but still
  carry diagnostic pressure K status.
- Hybrid upcomer models are required where recirculation invalidates ordinary
  pipe coefficient labels.
- Wall/test-section candidates currently falsify simple passive hA
  redistribution as a complete answer.

Use the claim ledger and segment atlas as the master references for what can be
claimed. If a coefficient is diagnostic in the atlas, the uncertainty chapter
must not let it appear as admitted later in the results chapter.

## Figure And Table Plan

| Item | Source | Suggested caption |
| --- | --- | --- |
| Table U1: uncertainty source ledger | This section | "Uncertainty sources and their effect on thesis claim strength." |
| Table U2: time-window bounds | `paper_uncertainty_bounds_salt234.csv` | "Final-window uncertainty of CFD reference targets." |
| Table U3: mesh/GCI disposition | `mesh_gci_gate_for_admitted_candidates.csv` | "Closure QOI mesh/GCI final-use disposition." |
| Table U4: property modes | `property_sensitivity_summary.csv` | "Property-lane sensitivity before closure fitting." |
| Table U5: sensor policy | `sensor_policy_scorecard.csv` and `sensor_map_contract.csv` | "Scoreable sensors, exclusions, and coordinate caveats." |
| Figure U1: model-form uncertainty stack | `08_thesis_claim_ledger.md` and `09_fluid_walls_segment_atlas.md` | "From CFD target uncertainty to closure admission uncertainty." |

## Paper-Safe Summary

The uncertainty treatment is deliberately structured rather than scalar. The CFD
reference carries finite steady-window uncertainty; closure rows carry
row-specific mesh/GCI and admission status; property choices move the
nondimensional groups used by friction and heat-transfer laws; TP/TW sensor
locations carry projection caveats; and the train/support/holdout/external split
limits what each row can prove. This separation prevents a closure from being
admitted merely because its residual is small under one property lane, sensor
projection, mesh disposition, or diagnostic replay.
