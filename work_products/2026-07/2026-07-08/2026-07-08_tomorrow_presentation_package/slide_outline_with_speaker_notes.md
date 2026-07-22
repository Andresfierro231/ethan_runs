# July 9 Presentation Outline With Speaker Notes

Generated: `2026-07-09T15:46:04+00:00`
Task: `AGENT-219`

## Presentation Thesis

The strongest defensible story is not a final closure coefficient. It is that
the CFD evidence has now been decomposed into pressure, heat, and regime terms
with explicit provenance, residuals, admission boundaries, and next actions for
turning the 1D model into a predictive surrogate.

## Slide 1 - Why the 1D model cannot be one tuned friction factor

**Use figure:** optional title slide, no required figure.

**Bullets**

- Goal: make the 1D model predictive against CFD, not merely tuned to mass flow.
- Today's evidence separates pressure, heat-path, and recirculation-regime terms.
- Claim boundary: this is a rigorous decomposition story, not a final coefficient story.

**Speaker notes**

Start by setting expectations. The project is now past the stage where one
global multiplier is the right scientific object. The data show several coupled
effects: buoyancy and pressure decomposition, thermal-boundary mismatch, and an
upcomer recirculation regime. The value of today's work is that these terms are
being separated so that future 1D closure terms have identifiable targets.

## Slide 2 - Evidence contract and admission boundary

**Use figure:** none required; use a compact table if the deck needs one.

**Bullets**

- Salt 2/3/4 Jin mainline rows are the current admitted evidence set.
- Corrected Salt rows are status-only until the gate requalifies them.
- All current QOIs still carry `coarse_no_gci`; mesh/GCI remains a publication gate.
- CFD setup audit: Salt CFD uses a 1.4 in layer and emissivity metadata, but no exported `qr` radiation field.

**Speaker notes**

This slide is the guardrail. The analysis is useful because every row is labeled
by its admission status. Salt 2/3/4 are the current mainline rows for closure
decomposition. Corrected Salt may become valuable, but right now it is not fit
evidence. That distinction keeps tomorrow's claims conservative and defensible.

## Slide 3 - Pressure decomposition: raw p_rgh is not friction

**Use figure:** `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/mechanical_pressure_terms_by_span.svg`

**Optional support figure:** `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/pressure_decomposition_by_span.svg`

**Bullets**

- July 8 pressure ledger has 18 Salt 2/3/4 span rows.
- The primary slide chart shows loss-scale mechanical terms only: de-buoyed
  distributed friction, development/reset estimate, and bend-loss upper bound.
- Signed `p_rgh` density-gradient terms are excluded from the main chart because
  they are reversible source/cancellation terms, not pressure losses.
- Direction context: `right_leg` is the downcomer; `left_lower_leg`,
  `test_section_span`, and `left_upper_leg` are the upcomer path.
- 12 rows are fit-eligible; 6 recirculation-invalid rows are excluded from
  single-stream friction fitting.

**Speaker notes**

The key point is that pressure loss is not being read directly from a raw static
or `p_rgh` slope. The ledger separates what is observed directly from what is
inferred as mechanical loss or residual. This is the pressure backbone for a
predictive 1D model.

Important correction: the earlier decomposition figure was too easy to misread
because it placed signed `p_rgh` density-gradient source terms beside
irreversible losses. That made the upper leg look like it carried a huge
pressure loss, when its de-buoyed distributed friction is actually around
6-7 Pa, comparable to the lower leg and smaller than the right-leg/downcomer
friction in Salt 3/4. The support figure can still be used to explain why raw
`p_rgh` is not friction, but the main slide should use the mechanical chart.

Geometry context matters. The right leg is the downcomer, so flow is downward
with gravity. The left-side path, made from `left_lower_leg`,
`test_section_span`, and `left_upper_leg`, is the riser/upcomer path and flows
up against gravity. Those directions are essential when interpreting signed
`p_rgh` and density-gradient terms; they are not standalone loss coefficients.

## Slide 4 - Heat accounting: the boundary condition is first-order

**Use figure:** `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/heat_source_sink_by_patch_group.svg`

**Bullets**

- Patchwise heat ledger reconciles imposed duties, wallHeatFlux, enthalpy
  changes, cooler sink, passive losses, and sign conventions.
- Cooler imposed duty and wallHeatFlux are closely aligned in CFD.
- Heater imposed duty is not identical to realized heater wallHeatFlux.
- Test section appears as a net sink in wall-flux accounting.

**Speaker notes**

The thermal boundary cannot be treated as a minor correction. The heat ledger
shows that the setup-level power and the realized fluid-side heat transfer are
not always the same object. This matters for 1D model comparison because the 1D
state can look wrong for thermal reasons even if the pressure closure is moving
in the right direction.

## Slide 5 - Segment enthalpy residuals expose where thermal closure is weak

**Use figure:** `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/heat_enthalpy_residual_by_segment.svg`

**Bullets**

- Span endpoint temperatures now support segment-level heat residuals.
- Non-junction absolute heat residuals are about 36.7 W to 162.7 W.
- Upcomer residuals are diagnostic because recirculation violates ordinary
  single-stream assumptions.
- Cooler residuals remain caveated because current endpoints partially bracket
  the cooler.

**Speaker notes**

This is the bridge from a heat-source table to a closure target. The residuals
are not all fit targets yet, but they tell us where the thermal model is missing
physics or where the CFD reduction needs better bracketing.

## Slide 6 - Fixed-mdot thermal replay: cooler/HX path is the biggest lever

**Use figure:** `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/figures/fixed_mdot_thermal_replay_error.svg`

**Bullets**

- AGENT-211 ran fixed-mdot thermal replays at CFD mdot.
- Baseline mean temperature error is about 64 K.
- Prescribing CFD cooler duty alone drops mean temperature error to about 4.5 K.
- Prescribing both CFD cooler duty and CFD heater wall flux over-corrects the
  mean temperature by about 40 K because the source contract changes too.
- No replay path passes the strict thermal gate yet; this is diagnosis, not a
  final predictive thermal model.

**Speaker notes**

This slide answers the thermal-state mismatch question directly. The strongest
single issue is the cooler/HX heat-removal path. We can make the thermal state
much closer by prescribing the CFD cooler duty, but that is not yet predictive.
The current-1D baseline means the existing Fluid salt thermal contract at fixed
CFD mdot: current heater/source contract, predictive air-side HX, internal
ambient/passive-loss model, radiation setting retained, no CFD heat ledger
injected, and no pressure-root mdot solve. The cooler-plus-heater replay is a
useful warning: importing more CFD heat terms is not automatically better
inside the current source/loss semantics. The next model must predict cooler
removal from geometry and boundary conditions rather than importing it from CFD.
Use `slide6_thermal_replay_analysis.md` for the detailed scientific
interpretation and baseline definition.

## Slide 7 - Friction-form screen: F3 Shah is the current mdot baseline

**Use figure:** `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/friction_form_mdot_error.svg`

**Optional support:** `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/friction_per_leg_pressure_drop.svg`

**Bullets**

- Fully developed F1 overpredicts mdot by about 9.7% to 18.0%.
- F3 Shah apparent narrows mdot error to about -0.9% to 3.7%.
- F4 leg-class over-stiffens the loop at about -24.7% to -23.2% mdot error.
- Mdot agreement alone is not enough; pressure distribution and thermal state
  must be scored separately.

**Speaker notes**

This is a useful result but not the final answer. F3 Shah apparent is the best
current mdot baseline, and that makes physical sense because the flow is not
fully developed. But a model that gets only total mass flow right can still get
the wrong pressure distribution or thermal state.

## Slide 8 - Minor losses: corrected K is smaller, but corners are not the full story

**Use figures:** `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/figures/minor_loss_k_apparent_vs_local.svg` and `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/figures/minor_loss_separation_phi.svg`

**Bullets**

- Two-tap reduction separates diagnostic `K_apparent` from corrected/local
  `K_local`.
- `K_local` is much lower after subtracting adjacent straight-loss contribution,
  but still an upper-bound estimate.
- Corner bends explain only about 8-12% of span-level pressure drop in the main
  pipe spans.
- Residual pipe-only phi remains about 1.34-1.90 after corner attribution.

**Speaker notes**

This slide is the pressure-breakdown nuance. We should not throw all residual
pressure into bend K values. The current evidence says corners matter, but they
do not explain the dominant excess above F3 Shah. That points toward secondary
flow, bend redevelopment, buoyancy-driven cross-section structure, or model-form
terms that remain distributed rather than purely local.

## Slide 9 - F5/Ri screen failed honestly; T13 is the path to separation

**Use figures:** `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/f5_ri_screen_coefficients.svg` and `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/figures/t13_re_sweep_plan.svg`

**Bullets**

- Current admitted dataset has only three Salt operating points.
- F5/Ri coefficients are zero/deactivated in the present screen.
- Re and Ri are too collinear in the current dataset to separate mechanisms.
- T13 proposes Q sweep from Salt 3 anchor to reach roughly Re 160, 220, 305, and
  possibly 428.

**Speaker notes**

This is a good negative result. The framework for Ri correction exists, but the
current data do not support a real fitted Ri law. T13 is valuable because it
pushes the loop across the missing Re range and may separate recirculation onset,
development effects, and buoyancy effects.

## Slide 10 - Upcomer: this is a recirculation-cell regime

**Use figure:** `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/upcomer_backflow_vs_re.svg`

**Bullets**

- All admitted Salt 2/3/4 upcomer points classify as recirculation-cell observed.
- Backflow fraction decreases with Re but remains nonzero at Salt 4.
- Upcomer rows should be validation/regime diagnostics, not ordinary pipe-friction fit rows.
- Need additional points near Re 150-250 to locate onset.

**Speaker notes**

This is where the 1D model needs a regime boundary. The upcomer cannot be
treated as an ordinary single-stream pipe span while the CFD shows a
recirculation cell. We either exclude it from ordinary friction fitting or build
a separate recirculation/regime term.

## Slide 11 - What is moving and what is still blocked

**Use figure:** `work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/corrected_salt_gate_status.svg`

**Bullets**

- Corrected Salt perturbations are useful status signals, not closure evidence yet.
- Mesh/GCI uncertainty is still missing for publication-grade coefficient claims.
- Time-window uncertainty still needs a dedicated package.
- Raw two-tap reducer/junction extraction and station-resolved development
  analysis remain high-value follow-ups.

**Speaker notes**

This slide prevents overclaiming. The work is in a much stronger state than it
was yesterday, but the gate and uncertainty tasks are real. The right message is
that we know which claims are ready for tomorrow and which ones are still in
progress.

## Slide 12 - Close: what can be done today versus what remains thesis work

**Use figure:** optional summary table.

**Bullets**

- Ready for tomorrow: pressure decomposition, heat accounting, thermal residuals,
  friction mdot screen, minor-loss support figures, upcomer regime, gate status.
- Can be started immediately: mesh/GCI intake, time-window uncertainty,
  raw two-tap feature extraction, station-resolved development analysis.
- Thesis/paper direction: common observation schema, separate objective scores,
  predictive heater/cooler boundary models, and regime-aware upcomer treatment.

**Speaker notes**

End with the path forward. The next version of the 1D model should be judged on
multiple objective columns, not just mass flow. The pieces are now laid out:
pressure terms, heat terms, recirculation flags, and uncertainty requirements.
