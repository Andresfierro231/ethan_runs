---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_junction_split_heat_ledger_and_model_gate/junction_split_heat_ledger_and_model_gate.md
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state/scientific_review.md
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_predict_val_salt2_external_ledger/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_external_score_junction_corner_progress/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/README.md
tags: [thesis-section, current-section, junction-aware-ledger, structured-losses, pressure-k, heat-loss]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/01_modeling_approach.md
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md
task: AGENT-504
date: 2026-07-17
role: Writer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# Why Segment-Only 1D Models Miss Structured Losses

## Junction-Aware vs Loop-Segment Ledgers

This section motivates a local-role ledger in the final 1D model. The evidence
shows that some thermal and hydraulic residuals are structured around junctions,
stubs, connectors, and recirculating regions. A segment-only model can conserve
the loop total while assigning the wrong physical cause to the residual.

The conclusion is not that every junction coefficient is already admitted. The
conclusion is narrower and stronger: the final 1D model needs local ownership
lanes for junction/stub heat loss, corner pressure residuals, and upcomer
recirculation. Without those lanes, the model is pushed toward one global
correction factor that hides where the CFD says the error lives.

## Model Forms Compared

### Segment-Only Ledger

The segment-only model divides the loop into large physical branches:

- heater or lower leg;
- cooler or upper leg;
- downcomer;
- upcomer;
- lower and upper connecting legs.

This form is useful as a first balance. It can assign pressure drop, heat loss,
and sensor error to the major loop regions. Its weakness is ownership: local
geometric features inside or between the large segments have to be absorbed into
the nearest branch. A junction heat leak may become an apparent passive-pipe
loss. A corner pressure feature may become a branch friction multiplier. A
recirculating upcomer region may be forced into an ordinary pipe-flow
coefficient.

In this form, the model tends toward corrections such as:

$$
\Delta p_{loss}
\approx
\sum_{branches} f_{branch}\frac{L}{D}\frac{1}{2}\rho V^2
+ K_{global}\frac{1}{2}\rho V^2,
$$

and

$$
Q_{loss}
\approx
\sum_{branches} UA_{branch}(T_{drive}-T_{env}).
$$

Those expressions are not wrong as bookkeeping, but they are too coarse for the
current evidence. They do not preserve whether a residual is attached to an
ordinary pipe wall, a cooler neighborhood, a stub, a non-conformal junction, a
corner, or a recirculating test-section/upcomer span.

### Junction-Aware Ledger

The junction-aware model keeps the same loop segmentation but adds explicit
local-role ownership:

- ordinary pipe segment;
- heater entry or heated segment;
- cooler/HX segment;
- passive wall segment;
- junction body;
- stub or connector;
- corner or bend cluster;
- non-conformal interface or transition region;
- residual lane with admission status.

In this form, the heat ledger becomes:

$$
\dot{m}\bar{c}_{p,i}(T_{out,i}-T_{in,i})
= Q_{heater,i}
- Q_{cooler,i}
- Q_{pipe\ wall,i}
- Q_{junction/stub,i}
+ Q_{test,i}
+ Q_{residual,i}.
$$

The pressure ledger similarly separates ordinary distributed loss from local
corner or connector evidence:

$$
\Delta p_{loss}
=
\sum_i f_i\frac{L_i}{D_i}q_i
+ \sum_j K_{corner,j}q_j
+ \Delta p_{junction/stub}
+ \Delta p_{residual}.
$$

The symbols in this equation are ownership slots, not automatically admitted
coefficients. A row can be present in the ledger while remaining diagnostic.
That distinction is central to the thesis.

### Hybrid Upcomer Ledger

The upcomer is a third model form. It should not be treated as ordinary pipe
flow when reverse-flow evidence is material. The defensible structure is a
throughflow path plus a recirculation-cell exchange path:

```text
net loop throughflow
  + recirculation-cell exchange / mixing / penalty lane
```

This prevents upcomer recirculation from being hidden inside ordinary
single-stream `Nu`, `f_D`, or component `K`. It also keeps the test section as a
physical middle-upcomer span with its own source/loss role.

## What The Evidence Shows

### Heat Residuals Shift When Junction/Stub Losses Are Separated

The Salt2-4 mainline junction split shows that junction/stub heat loss is a
real, localized pathway. The split closes against the aggregate heat audit:

| Case | Junction/stub split loss |
| --- | ---: |
| `salt2_mainline` | `39.128350 W` |
| `salt3_mainline` | `43.234691 W` |
| `salt4_mainline` | `48.485216 W` |

These values are not large enough to explain every thermal discrepancy, but
they are large enough that assigning them to ordinary pipe segments would
misidentify the physical location of the loss.

The external `val_salt2` ledger strengthens the point. Its junction/stub split
closes to approximately:

$$
Q_{junction/stub,val\_salt2} = 40.926087\ \mathrm{W}
$$

across four physical buckets. That value is currently external-test evidence,
not a runtime input and not a training reclassification. It is still
thesis-useful because it shows that the local junction/stub lane exists in an
independent validation row.

### Corner Pressure `K` Is Diagnostic, Not Admitted

The pressure evidence is more limited. Corner pressure-drop rows exist and are
directionally useful, but they are not admitted component-`K` closures. The
current `val_salt2` and cross-case pressure reviews report:

- `0` corner-K fit-admitted rows;
- negative local K values after current straight-loss subtraction;
- recirculation, pressure-basis, component-isolation, and mesh/GCI gates still
  failing.

The negative local K result is not a physical claim that corners create pressure
gain. It is a diagnostic warning that the current straight-reference subtraction
over-subtracts the preserved feature drop. The proper conclusion is that corner
losses need a better extraction and admission workflow before they can become
predictive 1D coefficients.

## Thesis Claim

The junction/stub and corner evidence supports the thesis claim that the final
1D model needs local role ledgers. The model should not rely on one global
hydraulic multiplier or one global heat-loss correction. The CFD evidence
contains structured residuals:

- heat residuals associated with junction/stub surfaces;
- corner pressure drops that are visible but not yet admitted;
- upcomer recirculation that invalidates ordinary single-stream pipe
  coefficient labels.

The correct 1D response is to add named ownership lanes and admission status,
not to force every discrepancy into a branch friction factor, branch `UA`, or
global correction factor.

## Paper-Safe Wording

Segment-only 1D models are useful for loop-scale accounting, but the present CFD
evidence shows that they can miss structured local losses. When junction and
stub heat-transfer surfaces are separated from ordinary pipe segments, a
nontrivial heat-loss lane appears: Salt2-4 mainline rows show approximately
`39-48 W` of junction/stub loss, and the independent `val_salt2` ledger reports
approximately `40.93 W` across four junction/stub buckets. This evidence is
strong enough to motivate a named junction/stub heat-loss lane in the final
model, while still preserving runtime-input restrictions on realized CFD wall
heat flux.

The hydraulic evidence is deliberately more conservative. Corner pressure-drop
rows identify structured local pressure features, but current straight-loss
subtraction produces negative local K values and leaves `0` fit-admitted
corner-K rows. The result is therefore diagnostic, not an admitted component-K
closure. Together, the thermal and hydraulic evidence show why the final 1D
model should use local role ledgers with explicit admission status rather than
one global correction factor.
