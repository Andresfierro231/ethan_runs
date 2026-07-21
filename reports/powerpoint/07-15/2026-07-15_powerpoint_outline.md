---
provenance:
  - operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md
  - reports/thesis_dossier/Chapters_and_sections/2026-07-14_upcomer_recirculation_internal_nu_story.md
  - reports/thesis_dossier/Chapters_and_sections/2026-07-14_thesis_presentation_story_sync.md
  - reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_scientific_closure_forward_v1_execution_dashboard/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_forward_v1_pm5_hydraulic_delta/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/paper_ready_analysis.md
  - work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/presentation_brief.md
  - work_products/2026-07/2026-07-14/2026-07-14_fluid_reset_development_api/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan/README.md
tags: [thesis-dossier, weekly-presentation, powerpoint-outline, forward-v1, admission-gate, blocker-audit]
related:
  - reports/thesis_dossier/README.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-364
date: 2026-07-14
role: Thesis/Presentation/Writer
type: report
status: complete
---
# PowerPoint Outline For 2026-07-15 Meeting

Audience: advisor/research-group update.

Core message: today converted broad CFD/1D activity into an admission-gated
story. We made real progress, but the trustworthy conclusion is not "the final
predictive model is done." It is: we now know which rows and model forms can be
trusted, which are diagnostic only, and which gates must land before final
prediction claims.

Suggested length: 14 main slides plus 4 optional backup slides.

## Attached Deck And Generated Figures

Added by `AGENT-367` on 2026-07-14.

- PowerPoint deck with figures attached:
  `reports/powerpoint/07-15/2026-07-15_powerpoint_deck.pptx`.
- Reproducible figure/deck package:
  `work_products/2026-07/2026-07-14/2026-07-14_powerpoint_figures_and_deck/`.
- Build script:
  `tools/analyze/build_2026_07_15_powerpoint_deck.py`.
- Speaker notes remain in this outline; the generated PowerPoint embeds
  rendered slide images with the new figures.

## TODO For July 15 Result Refresh

- Before presenting, revamp the PowerPoint if any new July 15 landed result
  changes admission, blocker, scorecard, split-policy, figure, or thesis-claim
  status.
- Open first: `.agent/BOARD.md`, `.agent/BLOCKERS.md`, the newest
  `reports/thesis_dossier/` update, and any completed July 15 work products
  from `cfd-pp`, `therm-reconstr`, `internal-Nu`, `hydraulics`,
  `forward-pred`, or `BC-modeling`.
- Specifically check for updates from matched pressure/upcomer plane harvest,
  forward-v1 gate refresh, heater/HX/wall boundary modeling, Salt training or
  perturbation split policy, and thermal/profile parity packages.
- Update both the outline and the generated deck; rerun
  `python3.11 tools/analyze/build_2026_07_15_powerpoint_deck.py` after
  changing figure inputs or slide text.
- Preserve strict wording: `predictive`, `calibrated`, `diagnostic`,
  `reference`, `blocked`, and `pending`; do not promote new rows into training
  or closure fitting unless a dated admission gate explicitly does so.

## Slide 1: Title

**Title:** From CFD Replay To Admission-Gated 1D Prediction

**Bullets**

- TAMU molten-salt natural-circulation loop
- July 15, 2026 weekly update
- Focus: what changed, what is trustworthy, what remains blocked, and what we
  should do next

**Figure**

- Use a clean loop schematic if available.
- Better figure useful: one simplified loop diagram with labeled lower leg,
  upcomer/test section, cooling branch, downcomer, and junction/stub regions.

**Speaker Notes**

Open with the thesis goal: build a setup-only 1D model that predicts loop
`mdot` and temperatures from physical inputs, using CFD as high-fidelity
reference evidence. Emphasize that today was mainly about separating predictive
evidence from diagnostic replay and blocked closure fits.

## Slide 2: The Scientific Question

**Title:** What We Are Trying To Prove

**Bullets**

- Can a 1D model predict CFD loop mass flow without using CFD `mdot` at runtime?
- Can it predict branch/sensor temperatures without using realized CFD
  `wallHeatFlux` or validation temperatures at runtime?
- Which CFD-derived quantities are admissible closures, and which are only
  diagnostic section-effective evidence?
- Current answer: forward-v1 remains blocked, but the gate map is now much
  cleaner.

**Figure**

- Simple input/output block diagram:
  setup inputs -> Fluid 1D model -> `mdot`, pressure losses, temperatures.
- Add red "not runtime inputs" labels on CFD `mdot`, realized `wallHeatFlux`,
  and validation temperatures.

**Speaker Notes**

This slide sets the overclaim boundary. A replay that uses realized CFD heat
flux can be useful, but it is not final prediction. The presentation should
come back to this contract on every result slide.

## Slide 3: Evidence Ladder Used Today

**Title:** How We Classified Today's Evidence

**Bullets**

- Predictive: setup-only inputs, scored on held-out targets.
- Calibrated: fitted on declared training data with validation/holdout limits.
- Diagnostic: explains physics or screens model forms, but not a closure-fit
  row.
- Reference: limiting formulas such as fully developed `f_D` or `Nu`.
- Blocked/pending: needs a named admission gate before use.

**Figure**

- Make a five-level evidence ladder or traffic-light table.
- Better figure useful: one row per result lane: CFD admission, hydraulics,
  heat loss, internal Nu, forward-v1.

**Speaker Notes**

This is the language discipline we need for the thesis. Most of today's
numbers are valuable, but many are diagnostic rather than predictive. That is
not a weakness; it prevents us from fitting the wrong physics into the wrong
coefficient.

## Slide 4: One-Day Progress Snapshot

**Title:** What Changed Today

**Bullets**

- Corrected +/-5Q rows: `4` terminal-harvested rows processed, `0`
  independent training expansion rows.
- Hydraulics: `12` centerline tap rows resolved, `0` fit-admissible
  component/cluster `K` rows.
- Fluid API: separate reset/development `K` input now exists, but H1 is still
  not admitted.
- Internal Nu: current upcomer regime is recirculating; single-stream `Nu`,
  `f_D`, and `K` labels are invalid there.
- Heat loss: aggregate heat balance can look close while heat is lost in the
  wrong physical locations.

**Figure**

- Gate-status dashboard from
  `work_products/2026-07/2026-07-14/2026-07-14_scientific_closure_forward_v1_execution_dashboard/workstream_execution_dashboard.csv`.
- Better figure useful: compact dashboard with rows for CFD admission,
  hydraulics, boundary/HX, internal Nu, forward-v1, and thesis claim.

**Speaker Notes**

Frame this as disciplined narrowing. Today did not magically admit the final
model, but it turned many vague blockers into precise pass/fail gates and
made several tempting shortcuts unsafe to use.

## Slide 5: Current CFD Evidence And Split Discipline

**Title:** Which CFD Rows Can Support Claims?

**Bullets**

- Current main split remains: Salt2 = training, Salt3 = validation, Salt4 =
  holdout.
- Corrected +/-5Q rows are terminal-harvested perturbation evidence, not new
  independent training rows.
- Salt2 +/-5Q: train-family sensitivity/admission evidence pending split
  policy.
- Salt4 +/-5Q: holdout-family sensitivity/admission evidence; not for model
  selection.
- Do not promote a row from "steady" to "fit-admissible" without source,
  boundary, and split labels.

**Figure**

- Use or redraw from
  `work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_split_admission_matrix.csv`.
- Better figure useful: split matrix with rows Salt2 -5Q, Salt2 +5Q,
  Salt4 -5Q, Salt4 +5Q and columns terminal, closure-fit admissible,
  independent training allowed, allowed use.

**Speaker Notes**

The key point is that corrected-Q is no longer just "pending" in the same way:
four +/-5Q rows have been harvested and processed. But they still cannot be
silently added to training because they are perturbation-family evidence.

## Slide 6: Observed Flow/Temperature Ordering

**Title:** Mainline CFD Shows A Clean Monotonic Ordering

**Bullets**

- Salt2: `|mdot| = 0.013199343 kg/s`, probe `T = 448.425 K`.
- Salt3: `|mdot| = 0.014981961 kg/s`, probe `T = 462.106 K`.
- Salt4: `|mdot| = 0.017080866 kg/s`, probe `T = 477.977 K`.
- Mainline Salt2/3/4 show monotonic `|mdot|` increase with temperature.
- This is observational evidence, not a causal fit: temperature, heater power,
  cooler power, and boundary settings co-vary.

**Figure**

- Existing figure:
  `work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/figures/mdot_vs_probe_temperature.svg`.
- Backup figures:
  `mdot_vs_heater_power.svg`, `mdot_vs_cooler_power.svg`,
  `bc_role_heat_breakdown_by_case.svg`.

**Speaker Notes**

This is a good presentation plot because it is simple and data-grounded. Be
careful with language: with only three admitted mainline rows and covarying
settings, this supports an observed ordering, not a fitted flow-temperature
law.

## Slide 7: Boundary Conditions Are Confounded With Operating Point

**Title:** Flow Trends Cannot Be Read As One-Coefficient Physics

**Bullets**

- Initial temperature, probe temperature, heater power, cooler power, and
  external boundary coefficients change together by Salt case.
- Old Q perturbations are false-steady provenance: observed mdot moves were
  far below expected operating-point movement.
- Corrected +/-5Q rows are sensitivity/admission evidence, not independent
  train/validation/holdout rows yet.
- CFD `rcExternalTemperature` includes radiation in total `wallHeatFlux`; no
  separate exported `qr` term exists.

**Figure**

- Existing figure:
  `work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/figures/q_perturbation_expected_vs_observed_mdot_move.svg`.
- Better figure useful: a small causal/confounding diagram connecting Salt
  case -> temperature, heater, cooler, external h -> `mdot`.

**Speaker Notes**

This slide justifies why the model needs a branchwise ledger instead of a
global friction or heat-loss multiplier. It also removes two stale mistakes:
do not use old false-steady perturbations as physical response rows, and do
not add a separate radiation term on top of CFD wall heat flux.

## Slide 8: Heat-Loss Placement Result

**Title:** Aggregate Heat Balance Hides Wrong-Location Heat Loss

**Bullets**

- Best current predictive-style model: `F1_heater_only`.
- Aggregate model loss is close but not enough:
  - Salt2 model `265.701 W` vs CFD realized `243.393 W`.
  - Salt3 model `297.501 W` vs CFD realized `272.869 W`.
  - Salt4 model `337.601 W` vs CFD realized `310.408 W`.
- Pipe legs over-lose heat in the current model.
- Junction/stub/horizontal connector regions under-lose heat most strongly.
- Diagnostic forced-CFD replay exists: `15` rows across Salt2/3/4 force each
  1D segment net heat path to the CFD-realized `wallHeatFlux` location with
  `0 W` segment residual by construction.
- Do not call that replay predictive; it consumes realized CFD `wallHeatFlux`.

**Figure**

- Better figure needed: grouped bar chart from
  `work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/best_predictive_leg_heat_loss_discrepancy.csv`.
- X-axis: lower leg, upcomer/test-section, cooling branch, downcomer, junction.
- Bars: model total loss vs CFD realized loss; annotate model-minus-CFD.
- Optional addendum table:
  `work_products/2026-07/2026-07-15/2026-07-15_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan/diagnostic_forced_replay_case_summary.csv`.

**Speaker Notes**

This should be one of the central slides. The model can look reasonable in
total because errors cancel: too much heat removed in pipe legs, too little in
junction/stub regions. The thesis-safe claim is model-form diagnosis, not
final predictive HX validation, because imposed cooler duty is still consumed.
The forced-CFD replay is a useful upper-bound/diagnostic: it proves exact
location matching if CFD outputs are allowed, and therefore defines what the
setup-only model must learn without consuming those outputs.

## Slide 9: Boundary/HX/Wall Model Implication

**Title:** Next Thermal Model Needs Physical Boundary Lanes

**Bullets**

- Separate heater realized fraction, cooler/HX removal, passive wall loss,
  radiation metadata, storage, and residual.
- Current recommended sequence: heater fraction first, then setup-only
  cooler/HX UA/effectiveness, then wall/external/radiation dictionaries.
- Realized CFD `wallHeatFlux` and cooler duty are score targets, not runtime
  predictive inputs.
- Junction/stub heat-loss coverage is now an explicit model-refinement target.

**Figure**

- Better figure needed: thermal ledger schematic with lanes:
  heater -> fluid, cooler/HX -> coolant/sink, wall conduction, external
  convection, radiation metadata, storage/residual.
- Use the leg discrepancy chart from Slide 8 as a visual anchor if no separate
  schematic is available.

**Speaker Notes**

This is where to translate the heat-loss result into next work. The point is
not "multiply UA until it matches." The point is to move losses into physically
named lanes and keep diagnostic wallHeatFlux out of setup-only runs.

## Slide 10: Hydraulics Progress And Limits

**Title:** Hydraulics Is Cleaner, But Not Yet Admitted

**Bullets**

- Localized fixed-K alone worsened mdot and stays diagnostic.
- Tap-length refresh resolved `12` centerline rows, but component/cluster `K`
  has `0` fit-admissible rows.
- Fluid now supports separate `reset_development_k_by_segment` input.
- H1 remains not launchable as a faithful closure until admitted pressure
  evidence exists.
- F6 `phi(Re)` remains the bounded next candidate after admitted Re-variation
  rows land.

**Figure**

- Better figure needed: pressure-loss ledger diagram:
  straight friction + reset/development + component K + cluster K + buoyancy +
  residual.
- Optional table from
  `work_products/2026-07/2026-07-14/2026-07-14_forward_v1_pm5_hydraulic_delta/thesis_pm5_hydraulic_progress_table.csv`.

**Speaker Notes**

The key nuance is that implementation progress and scientific admission are
different. The Fluid API bridge is useful and real, but it does not by itself
make H1 calibrated. F6 is attractive precisely because it is bounded and can
be tested once Re-variation evidence is admitted.

## Slide 11: Upcomer Recirculation Is A Scientific Result

**Title:** Current Upcomer Regime Is Not Ordinary Pipe Flow

**Bullets**

- Admitted Salt2-4 upcomer observations are recirculating.
- Re_upcomer spans `71.125-134.883`.
- Backflow fraction remains material: `0.277778` down to `0.171875`.
- Ri_median remains above one: `1.497987-2.633785`.
- Single-stream `Nu`, `f_D`, and `K` labels are invalid in this regime.

**Figure**

- Better figure needed: upcomer plane schematic with reverse-flow region,
  forward-flow region, and labels for reverse area/mass fraction, bulk
  temperature, wall temperature, local heat flux, Re, Pr, Ri.
- When available, replace schematic with matched plane extraction from AGENT-344
  or AGENT-357/363 successor packages.

**Speaker Notes**

Do not say only "Nu is blocked." The better story is that we learned the
current upcomer regime is recirculating, which changes what coefficients can
be named and fitted. This is a physics/admission result.

## Slide 12: Internal Nu / Thermal Closure Admission

**Title:** Why Internal Nu Fitting Remains Closed

**Bullets**

- Current internal-Nu admission gate has `0` fit-admissible rows.
- Recirculating upcomer rows are diagnostic/regime evidence, not ordinary-pipe
  Nu closure rows.
- Nu/HTC cannot absorb heater realization, cooler/HX duty, passive wall loss,
  radiation, storage, branch mixing, hydraulic residuals, or sign residuals.
- Reopen fit only after matched plane metrics and ordinary/transition anchors
  exist.

**Figure**

- Better figure needed: "residual ownership" diagram showing which residuals
  are forbidden from being hidden inside Nu.
- Optional table from internal-Nu dependency blockers in the forward-v1
  scorecard package.

**Speaker Notes**

This slide protects the thesis. A fitted Nu from these rows would be
mathematically easy but physically wrong. The admission rule is a result:
some CFD reductions should produce diagnostic section-effective quantities,
not trainable coefficients.

## Slide 13: Forward-v1 Scorecard

**Title:** Current Final Forward-v1 Decision: No-Go, But Actionable

**Bullets**

- Current decision: `blocked_no_go_final_forward_v1_not_admitted`.
- Blocking gates include terminal/split admission, matched upcomer metrics,
  F6/Re-variation, setup-only boundary outputs, and internal-Nu reopen/no-fit
  refresh.
- What is admitted now: input hygiene, current Salt2/Salt3/Salt4 split,
  diagnostic/proxy evidence, and residual guardrails.
- Do not refresh final forward-v1 until at least one upstream gate lands.

**Figure**

- Use
  `work_products/2026-07/2026-07-14/2026-07-14_scientific_closure_forward_v1_execution_dashboard/gate_landing_requirements.csv`.
- Better figure useful: gate funnel with "landed", "diagnostic", "pending",
  and "blocked" badges.

**Speaker Notes**

No-go is the correct scientific result today. It says the model has a
controlled path to admission rather than silently mixing diagnostic replay into
predictive validation.

## Slide 14: Tomorrow / Next Work

**Title:** What Should Happen Next

**Bullets**

- Harvest matched pressure/upcomer plane metrics when active jobs finish; keep
  them diagnostic until admitted.
- Build the heat-loss leg bar chart and use it to drive boundary/HX/wall
  implementation.
- Implement setup-only boundary dictionaries for heater fraction, cooler/HX,
  wall/external convection, and radiation metadata.
- Implement a setup-predictive heat-loss variant using junction/stub coverage,
  wall/shell temperature drive, external h/Ta/Tsur/emissivity/layers, and
  setup-only HX/cooler; use
  `work_products/2026-07/2026-07-15/2026-07-15_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan/predictive_heat_loss_variant_plan.csv`
  as the work packet list.
- Treat `val_salt_test_2_coarse_mesh` as a future heat-loss test only after an
  AGENT-350-style section heat-loss replay/admission package exists.
- Run F6 only after admitted Re-variation evidence exists.
- Plan candidate upcomer cases near Re `150`, `200`, and `250` if current
  rows do not bracket onset.

**Figure**

- Better figure needed: two-column next-work roadmap:
  "Evidence gates" and "Model implementation gates."

**Speaker Notes**

Close with concrete decisions for the group. The strongest next move is not
another global fit. It is to land the pending extraction/admission gates and
turn the heat-loss diagnosis into setup-only boundary model implementation.

## Backup Slide A: Real Blockers Only

**Title:** Current Blockers, Without Stale Items

**Bullets**

- Open: closure-QOI mesh/GCI.
- Open: thermal CFD-to-1D parity/internal-development model.
- Open: predictive heater/cooler/wall-layer submodels.
- Open: upcomer onset data sparsity.
- Open: Fluid external-boundary API gap.
- Open: F6/Re friction correction validation.
- Do not report as open: OF12 reconstruction, no mesh for GCI, CFD-no-radiation
  parity, refined reconstructed-`T` corruption.

**Figure**

- Compact blocker table from `.agent/BLOCKERS.md`.

**Speaker Notes**

Use this only if discussion turns to blockers. It is important because stale
blockers make the project look less organized than it is.

## Backup Slide B: Literature Review Model-Form Crosswalk

**Title:** What The LitRev Says To Try Or Avoid

**Bullets**

- Branchwise ledger is the controlling architecture.
- Fully developed `f_D` and `Nu` are reference-only.
- Global `f`, `Nu`, `K`, and `UA` shortcuts are rejected/demoted.
- F6, setup-only HX/wall/radiation, and matched upcomer extraction remain the
  active next pathways.

**Figure**

- Use
  `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/litrev_to_current_evidence_crosswalk.csv`.
- Better figure useful: three-column table "tried/demoted", "partly tried",
  "not tried yet."

**Speaker Notes**

This slide connects today to the literature review. The literature did not
tell us to choose one magic coefficient; it told us to preserve branch state,
development, boundary, and source-envelope distinctions.

## Backup Slide C: Flow/Temperature Response Details

**Title:** Mainline Correlations Are Descriptive Only

**Bullets**

- Probe-temperature ordering: n=`3`, Pearson r=`0.999991`, R2=`0.999982`.
- Slope vs probe temperature: `0.000131371925 kg/s/K`.
- Heater power also co-varies: r=`0.999809`.
- Cooler setup power co-varies: r=`0.999664`.
- Treat as operating-point context, not a standalone closure law.

**Figure**

- Existing figures:
  - `mdot_vs_probe_temperature.svg`
  - `mdot_vs_heater_power.svg`
  - `mdot_vs_cooler_power.svg`

**Speaker Notes**

This is a useful backup if someone asks why we cannot fit a simple correlation
to the three mainline points.

## Backup Slide D: Exact Claim Boundaries

**Title:** Say / Do Not Say

**Bullets**

- Say: forward-v0 execution works; final forward-v1 is currently no-go.
- Do not say: the predictive model is admitted.
- Say: heat-loss placement diagnosis identifies wrong-location losses.
- Do not say: final predictive HX is validated.
- Say: upcomer recirculation invalidates single-stream coefficient labels.
- Do not say: Nu is merely blocked.
- Say: +/-5Q rows are sensitivity/admission evidence.
- Do not say: +/-5Q rows expand training today.

**Figure**

- Plain two-column "Say / Avoid" table.

**Speaker Notes**

This slide can be used as a speaking guardrail while building the final deck.
It keeps the narrative rigorous while still showing that substantial progress
was made.
