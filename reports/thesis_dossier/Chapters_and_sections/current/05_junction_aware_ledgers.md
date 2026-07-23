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

## 2026-07-22 Refresh: Local Ownership Still Wins, Admission Still Fails Closed

Current packet:
`work_products/2026-07/2026-07-22/2026-07-22_thesis_junction_aware_section_refresh/`.

The latest pressure/energy and heat-loss partition contracts sharpen the same
conclusion. The junction/stub thermal lane remains a real local owner:
Salt2-4 train-context rows span `39.128349537` to `48.485215891 W`, while the
independent `val_salt2` row remains external-test evidence at approximately
`40.926087 W`. These values can support a named junction/stub heat-loss lane,
but they still cannot be used as predictive runtime inputs because the source is
realized CFD wall heat-flux evidence.

The pressure lane remains stricter. The current pressure/F6 packet reports
`3` section-effective residual rows but `0` component-`K` admissions, `0` F6
fit rows, `0` admitted F6 rows, and `0` ordinary candidate pairs. The signed
lower-right residuals are negative after current pressure-basis subtraction, so
they are evidence that the extraction basis needs repair, not evidence for a
clipped positive `K` or a hidden multiplier.

The refreshed thesis statement is therefore:

- junction/stub heat belongs in a local thermal ownership lane;
- corner and lower-right pressure residuals belong in a diagnostic local
  pressure lane;
- neither lane is currently an admitted predictive coefficient;
- pressure, heat, and internal convection residuals must stay separated.

This preserves the current guardrail: no realized `wallHeatFlux`, CFD `mdot`,
imposed cooler duty, protected temperature, clipped `K`, global multiplier, or
internal-`Nu` residual absorption is allowed to become a runtime shortcut.

## July 22 Refresh: Keep Junctions As Ownership Lanes

The later July 22 packets strengthen this section without changing its
admission boundary. The updated `fluid+walls` model-form packet still reports
`0` final admitted candidates, `0` final score values, and `0`
source/property release-ready rows. That means the junction-aware ledger is a
model-form and evidence-ownership result, not a new predictive closure.

For thermal accounting, the current heat-loss/source inventory separates
internal convection, wall conduction/contact, insulation/quartz, external
convection, radiation, jacket/cooler, heater/test-section sources, storage,
recirculation exchange, and residual lanes. This reinforces the rule that
junction/stub heat cannot be silently assigned to ordinary pipe wall loss or
hidden in internal `Nu`. The PASSIVE-H2 runtime-contract packet gives a narrow
example of the same discipline: corrected radiation is a named external
boundary contribution of `22.4052516482..25.6530978934 W` over the three train
cases, while the full passive operator spans
`38.6073163603..44.6770586908 W`. It is still a contract for later runtime
implementation, not a released numeric heat-loss input.

For pressure accounting, the current negative-K and low-reverse-anchor packets
confirm that the existing `corner_lower_right` rows should remain
section-effective diagnostics. The July 22 future-anchor refinement still has
`0` replacement-ready pressure rows, `0` same-QOI UQ-ready rows, and `0`
component-K/F6 release rows. The pressure result is therefore not that a corner
coefficient has been recovered. The result is that a throughflow-plus-
recirculation pressure residual lane is needed, and ordinary F6 promotion must
wait for nonrecirculating or low-reverse anchors with same-QOI UQ.

For upcomer and test-section coupling, the July 22 onset and mesh packages keep
the same guardrail. The upcomer onset refresh emits `3` current train rows, all
classified as `recirculation_cell_observed`, with `0` ordinary upcomer
admissions and `0` exchange-coefficient admissions. The mesh uncertainty
packet emits `4` QOI disposition rows and `12` case/QOI sensitivity rows, with
`0` formal GCI-ready rows. These are useful diagnostic constraints on where
local ledger terms belong; they do not release ordinary one-stream `Nu`,
`f_D`, `K`, exchange-cell coefficients, or formal mesh/GCI uncertainty for
predictive admission.

The current paper-safe conclusion is therefore unchanged but sharper:
junction-aware ledgers are necessary because the CFD and reduced-model
diagnostics locate residuals in physical ownership lanes. They are not
sufficient by themselves for admission. A future model can promote one lane
only after the matching source/property, split, runtime-input, same-QOI UQ, and
candidate-freeze gates pass.
