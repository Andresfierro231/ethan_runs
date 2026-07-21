---
task: AGENT-294
date: 2026-07-13
role: Writer
type: map
status: reference
tags: [forward-model, predictive-1d, thermal-parity]
related:
  - operational_notes/maps/README.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/literature-synthesis-and-gates.md
---
# Forward Predictive Model — Map of Content

Tags: #forward-model #predictive-1d #thermal-parity

## What this covers

The thread that tries to **predict mdot and sensor temperatures from the
heater/cooler physical setup ALONE** — CFD mdot and realized CFD
`wallHeatFlux` are forbidden and not runtime inputs. This is the
thesis-strength forward model:
setup inputs in, `mdot` + TP/TW temperatures out. Everything about *how* the
loop is closed (friction, thermal Nu, mesh/UQ) feeds this hub but lives in its
own map; here we track the end-to-end predictive assembly and its gates.

## Current status

We can run a forward 1D model, but we **cannot yet make a thesis-strength
prediction**. Six things are unresolved: the cooler/HX boundary, heater
transfer efficiency, the test-section source/loss contract, wall-layer
temperature mapping, radiation separability, and the thermal uncertainty gates.
The current predictive input contract and a pressure-rooted forward-v0
(imposed-cooler) mode exist and pass their audits, but every CFD-informed replay
is a **diagnostic**, not a fully predictive claim: predictive modes must not
consume CFD mdot, realized CFD `wallHeatFlux`, or validation temperatures at
runtime.

2026-07-17 canonical split update: AGENT-481 supersedes the older final
predictive split that held out Salt4 nominal. The canonical final predictive
model should train/calibrate across the admitted Salt1-4 nominal envelope:
`salt1_nominal`, `salt2_jin_nominal`, `salt3_jin_nominal`, and
`salt4_nominal`. Testing/holdout must come from perturbation rows, external
validation rows, and new CFD: current holdout/testing rows are Salt2 +/-5Q
after PM5 extraction repair; `val_salt2` is external-test only after a matching
section heat-loss/admission ledger; Salt2/Salt4 +/-10Q are future holdout
candidates after live job `3293924` and harvester `3295438` finish and terminal
admission lands; the AGENT-478 Salt3 Q x insulation matrix is the new-CFD
holdout/onset design. Source:
`work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/`.

2026-07-18 TP/TW forensics update: AGENT-536 produced
`work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/`.
Open it before launching another wall/test-section Fluid grid. It ranks TW5 as
the top scoreable sensor failure and TW heated-incline as the top role/segment
failure, keeps all tested candidate families non-admitted, blocks a duplicate
AGENT-526 one-node wall/fluid series-resistance rerun, and turns the evidence
into a contract-first requirement matrix. The next lane remains `UMX1`
energy-conserving upcomer exchange/stratification after a static Fluid
API/root/split audit; `TSWFC2` distributed wall/fluid nodes are secondary.
AGENT-541 added the TSWFC2 dry contract in
`work_products/2026-07/2026-07-18/2026-07-18_tswfc2_dry_contract/`: it requires
distributed axial fluid/inner-wall/outer-wall/external states, a per-node heat
ledger, setup-only runtime inputs, frozen sensor gates, source/property labels,
and an explicit distinction from AGENT-526's failed one-node series-resistance
fallback before any Fluid implementation or scoring grid.

2026-07-18 UMX1 smoke update: AGENT-544 produced
`work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/` using the
AGENT-540 Fluid API. Runtime legality and split discipline pass; UMX
conservation passes `9/9` rows; accepted-root gate fails with only `3/9` rows
passing in bounded fast-scan smoke. Salt2 passes all three fixed UMX candidates,
while Salt3/Salt4 fail accepted-for-validation due finite but too-large
temperature periodicity errors. Decision: `stop_before_grid`; no UMX1 admission,
no broad multiplier grid, and no full UMX1 campaign until the Salt3/Salt4 root
blocker is diagnosed. Salt1 remains explicitly blocked pending schema promotion
before any final-training admission row consumes it. The same package also
blocks the predeclared exchange family on score behavior: both exchange
multipliers worsen `all_experimental`, `tp`, `tw`, and `umx_focus_segments` MAE
versus `UMX1_disabled_baseline` on Salt2/Salt3/Salt4, so future UMX1 progress
needs a separately claimed Fluid-edit row for a richer setup-only
stratification/source state before scoring again.

2026-07-18 UMX1 stratified-reservoir handoff: AGENT-548 attempted to start that
Fluid-edit follow-up but found an active external Fluid ownership blocker.
`../cfd-modeling-tools/.agent/BOARD.md` row
`impl-2026-07-18-fluid-tswfc2-distributed-wall-fluid-api` owns the exact Fluid
files UMX1 would need (`solver.py`, `config_loader.py`, README, and focused
tests). AGENT-548 therefore did not edit Fluid and instead published
`work_products/2026-07/2026-07-18/2026-07-18_umx1_stratified_reservoir_blocked_handoff/`
with a decision-complete API contract, assumptions register, implementation
sequence, validation plan, and blocker evidence for the next non-overlapping
Fluid-edit row.

2026-07-18 source/property scorecard update:
TODO-FINAL-SCORECARD-SOURCE-PROPERTY-LABELS regenerated the final predictive
scorecard shell at
`work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/`
so `case_partition_contract.csv` and `prediction_join_shell.csv` carry AGENT-538
source-validity envelope and property-mode sensitivity labels. The split intent
is preserved in `split_fit_allowed` / `split_model_selection_allowed`, but final
`fit_allowed` and `model_selection_allowed` are now label-gated: Salt1,
perturbation, external, and future rows remain blocked or diagnostic until a
row-specific source/property refresh exists.

2026-07-18 source/property enforcement update: AGENT-546 produced
`work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/`.
Use it as the current audit gate before any future closure scorecard reports
fit or admission. It scanned post-litrev scorecard/admission/fit/gate CSVs from
July 13-18, detected `1110` fit/admission candidate rows, found `1028` original
rows missing at least one required source/property label, and built an enforced
view with `0` blank required labels. The enforced view is deliberately strict:
all `1110` candidate rows remain blocked until source/property labels and their
own label content permit use. Required nonblank labels are `property_mode`,
`property_sensitivity_label`, `source_validity_envelope_status`,
`source_use_category`, and `provenance_author_title`.

2026-07-20 documentation update: AGENT-552 added a concise current-state handoff
at `operational_notes/07-26/20/2026-07-20_FORWARD_PREDICTIVE_BLOCKERS_AND_NEXT_STEPS.md`.
Use it when the goal is to brief or restart the forward predictive model thread.
It records that heater and cooler/HX are no longer the broad live blocker:
AGENT-454 superseded `predictive-heater-cooler-wall-submodels` after admitting
the setup-only heater-efficiency and cooler/HX UA candidates. The active
forward-model blockers are now the narrower wall/test-section/passive-boundary
thermal-shape blocker, upcomer stratification/onset sparsity, F6/two-tap
pressure anchoring, and scorecard source/property label enforcement. The
recommended order is UMX1 Fluid API/root repair first, TSWFC2 distributed
wall/fluid nodes second, upcomer onset anchor design, F6/two-tap pressure
anchors, and source/property label refresh before any final scorecard.

2026-07-20 TSWFC2 smoke update: AGENT-553 produced
`work_products/2026-07/2026-07-20/2026-07-20_tswfc2_smoke_scenario/`.
The single Salt 2 bounded four-node TSWFC2 scenario passed smoke only:
`root_status=accepted`, pressure and temperature roots bracketed,
`accepted_for_validation=True`, `mdot=0.022190917 kg/s`, and temperature
periodicity error `8.847e-10 K`. The active TSWFC2 ledger has four rows, all
four expected node IDs, node-count sum `4`, summed absolute external/inner-wall
heat `43.743240 W`, and max residual `0.0 W`. This is not a score grid, fit,
model-selection result, source/property update, or scientific admission change;
it only confirms the Fluid API can execute the prepared TSWFC2 scenario with
finite accepted roots and nonzero ledgers.

2026-07-20 blocker-unlock runbook update: AGENT-556 produced
`work_products/2026-07/2026-07-20/2026-07-20_forward_blocker_unlock_runbook/`.
AGENT-555 was already occupied by a PM10 documentation task, so follow-up
contracts are shifted to AGENT-557 through AGENT-561. The external Fluid row
`impl-2026-07-20-fluid-umx1-tswfc2-smoke-followup` is now completed, AGENT-553
TSWFC2 smoke is the executable starting point, and AGENT-554 source/property
gate tooling is available. The immediate next action is AGENT-557: a bounded
TSWFC2 nominal scorecard using the four-node setup only, with no broad grid,
no runtime leakage, strict source/property labels, and admission only if mdot,
TP, TW, all-probe, and TW5/TW6 gates pass versus M3 and prior wall/source
candidates. Later follow-ups are UMX1 intake, upcomer onset anchor design,
F6/two-tap nonrecirculating staging, and blocker-register review after evidence
lands.

2026-07-20 TSWFC2 bounded scorecard update: AGENT-557 produced
`work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/`.
The single AGENT-553 four-node TSWFC2 candidate solved all Salt1-4 nominal
cases with accepted pressure/temperature roots, but it is not admitted and did
not unlock `predictive-wall-test-section-submodels`. Salt2-4 all regress
versus M3 in mdot, TP, TW, and all-probe RMSE; Salt1 lacks an M3 comparator in
the cited table. Source/property gates also block admission: Salt1 still lacks
row-specific branch source-envelope labels, while Salt2-4 retain conservative
mixed/outside and diagnostic/no-fit labels. Decision:
`not_admitted_no_grid_expansion`. Do not rerun the same four-node TSWFC2
candidate as a blocker-unlock attempt without a new physical change or release
gate; continue with UMX1 intake and/or source/property/onset work.

2026-07-20 UMX1 Fluid intake update: AGENT-558 produced
`work_products/2026-07/2026-07-20/2026-07-20_umx1_fluid_intake_decision/`.
The completed external Fluid follow-up clears the immediate UMX1
Salt3/Salt4 root blocker at smoke level: `umx1_bracket_smoke_v1` has `12/12`
accepted rows and zero rejected rows, with zero upcomer reservoir energy
residual in the reviewed segment ledgers. This does not make UMX1
scorecard-ready. The best exchange variant still trails the radiation-on
baseline (`70.242831 K` versus `69.693542 K` all-sensor RMSE), radiation-off
rows remain much worse, and the combined UMX1+TSWFC2 smoke accepts roots but
scores poorly (`97.990763 K` all-sensor RMSE). Decision:
`blocked_not_scorecard_ready_no_grid`. Use the now-working UMX1 root path only
after a new setup-only physical candidate, source/property release gate, or
upcomer onset/stratification anchor is documented.

2026-07-20 upcomer onset anchor design update: AGENT-559 produced
`work_products/2026-07/2026-07-20/2026-07-20_upcomer_onset_anchor_design/`.
It closes the design row as `design_complete_no_launch_from_this_row`: there
are still `0` ordinary upcomer `Nu`, `f_D`, or component-`K` rows admitted, the
three current Salt2/Salt3/Salt4 points remain recirculating diagnostics, active
matched-plane extraction job `3305547` should be consumed before duplicate
compute, and high-heat jobs `3299610`/`3299620` remain monitor/terminal-harvest
gated in cited evidence. The next order is PM10 matched-plane QOI admission,
then high-heat terminal harvest, then only the two Salt3 sentinel anchors, with
the nine-row Q-by-insulation matrix deferred until sentinel failure.

2026-07-20 AMX1 axial-mixing dry-contract update: AGENT-565 produced
`work_products/2026-07/2026-07-20/2026-07-20_amx1_axial_mixing_dry_contract/`.
This is the current bounded path for trying to unlock
`predictive-wall-test-section-submodels` without retreading failed TSWFC2 or
UMX1 exchange-only variants. The recommended first form is
`AMX1a_axial_mixing_segment_diffusion_v1`: conservative adjacent-pair axial
thermal exchange across `left_lower_vertical`, `test_section`, and
`left_upper_vertical`, followed only later by optional UMX1 reservoir exchange.
The decision is `fluid_patch_required_before_smoke`: current Fluid supports
UMX1 exchange and TSWFC2 distributed wall/fluid nodes, but no
`axial_mixing_mode`, `axial_mixing_multiplier`, target parent list, or
axial-mixing ledger contract exists. Next action is a separately claimed
external Fluid row adding disabled-by-default AMX1 API/ledgers/tests, then a
Salt2 smoke only with finite accepted roots and nonzero conservative ledgers.
No Salt1-4 scorecard, external/holdout scoring, fit/model selection, or
blocker-register change should run before that smoke passes.

2026-07-21 heat-loss phased progress plan:
`operational_notes/07-26/21/2026-07-21_HEATLOSS_PHASED_PROGRESS_PLAN.md`
is the current sequence for correcting heat-loss accounting before another
final predictive claim. It adds board rows for baseline release, external
BC/radiation integration, split heat-loss evidence, wall/test-section scoring,
upcomer exchange/internal-`Nu` gating, and frozen scorecard handoff. For forward
model work, do Phase 0 through Phase 2 before any new wall/test-section
scorecard and do Phase 5 only after a runtime-legal candidate exists or a
negative result is frozen.

2026-07-21 first key studies wave:
`work_products/2026-07/2026-07-21/2026-07-21_predictive_first_key_studies_wave/`
consolidates the first S0-S3 predictive-model studies. It releases the
baseline control surface, external-BC contract/handoff, split heat-loss
evidence, and pressure source-envelope release gate. It does not edit Fluid,
score a model, fit, select, admit, or create a final freeze. The next repo-local
scientific gate is `TODO-HEATLOSS-PHASE-3-WALL-TEST-SECTION-MODEL-SCORE`; the
external source-implementation gate remains `TODO-FLUID-EXTERNAL-BC-DICT` and
requires exact external Fluid ownership before edits.

2026-07-21 upcomer exchange preflight update:
`work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_evidence_preflight/`
is the current no-solver decision package before any Phase 4B sampler. It
classifies `V_recirc`, `mdot_exchange`, `tau_recirc`, same-window
`T_main`/`T_recirc`, wall/core temperature, pressure residual basis, energy
residual, and same-QOI UQ. Result: diagnostic RAF/RMF/SVF and energy-residual
rows are useful for recirculation-guard and residual-attribution writing, but
no exchange-state variable is admission-grade; `sampler_allowed_now=false`,
`phase4b_ready=false`, and `phase5_trigger=not_triggered`. Next work should be
a separately claimed terminal-harvest or narrowly scoped sampler row only after
the exact source family and QOI contract are fixed.

2026-07-21 terminal/source readiness update:
`work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_terminal_source_readiness/`
is the current no-solver follow-on to the exchange preflight. Read-only
scheduler/accounting checks found corrected-Q continuation `3307441` and
high-heat jobs `3299610`/`3299620` still running; older harvester `3295438`
completed but is superseded for latest corrected-Q evidence by `3307441`.
Decision: `terminal_harvest_ready_now=false`, `scoped_sampler_needed_now=false`,
`phase4b_ready=false`, and `phase5_trigger=not_triggered`. The next action is
read-only terminal monitoring, then a separate terminal harvest/admission row
after success; if those sources become formally unusable, only then claim a
sampler-design row.

2026-07-20 AMX1 Salt2 smoke update: AGENT-567 ingested external Fluid task
`impl-2026-07-20-fluid-amx1-axial-mixing-smoke` and produced
`work_products/2026-07/2026-07-20/2026-07-20_amx1_salt2_smoke_intake/`.
The new Fluid AMX1 API/root/ledger path is smoke-unlocked: the Salt2 smoke had
two rows, one AMX1 row, all accepted/bracketed roots, `46` AMX1-active
segments, summed AMX1 ledger magnitude `8.088558 W`, total net
`5.55e-17 W`, and max residual `0.0 W`. This is not an admission or scorecard.
Salt2 diagnostic deltas versus the AMX1-disabled baseline are nearly neutral:
mdot shifts from `0.020258706` to `0.020238015 kg/s`, while all-probe RMSE
changes from `65.098442` to `65.101804 K`. The blocker remains high until a
separately claimed bounded Salt1-4 AMX1 nominal comparison passes mdot, TP, TW,
all-probe, runtime, split, and source/property gates. Runtime is a real gate:
the two-row smoke took `191.398 s`, with the AMX1 row taking `111.057 s`.

2026-07-20 AMX1 Salt1-Salt4 bounded comparison update: AGENT-568 ingested
external Fluid task
`impl-2026-07-20-fluid-amx1-salt1-4-bounded-comparison` and produced
`work_products/2026-07/2026-07-20/2026-07-20_amx1_salt1_4_bounded_comparison_intake/`.
The bounded comparison ran exactly two scenario forms across Salt1-Salt4:
disabled baseline plus low AMX1 `segment_diffusion_v1` at multiplier `0.05`.
It completed `8/8` rows `ok`; all pressure and temperature roots were accepted
and bracketed; all four AMX1 rows had `46` active segments, nonzero ledgers,
near-zero total net, and `0.0 W` max ledger residual. The audit decision is
`bounded_comparison_complete_diagnostic_only`, not a scorecard or admission.
The blocker remains high: mdot and velocity errors improved in every Salt case,
but all temperature RMSE families worsened slightly in every Salt case. Largest
increases were Salt4 all-RMSE `+0.004420 K`, TP-RMSE `+0.001782 K`, TW-RMSE
`+0.005546 K`, and TW-without-TW10 RMSE `+0.005648 K`. Runtime also remains a
real gate: total campaign `753.931202 s`, solve time `726.891243 s`, max
scenario duration `477.721667 s`. Next progress should revise AMX1 form before
any score grid: localized/directional/gradient-clipped exchange or coupling to
passive-boundary heat imbalance, with Salt2 smoke first and Salt1-Salt4 bounded
comparison only after roots and conservative ledgers pass.

2026-07-20 AMX1 localized-form smoke update: AGENT-569 ingested external Fluid
task `impl-2026-07-20-fluid-amx1-localized-form-smoke` and produced
`work_products/2026-07/2026-07-20/2026-07-20_amx1_localized_form_smoke_intake/`.
The Salt2-only smoke ran five rows: disabled baseline, prior broad-control
AMX1, lower-vertical-only, test-section-only, and upper-vertical-only. It
completed `5/5` rows `ok`; all roots were accepted/bracketed; all AMX1 forms
had nonzero conservative ledgers. The audit decision is
`localized_smoke_complete_diagnostic_only`, with no score grid,
Salt1-Salt4 expansion, fitting, model selection, or admission. No localized
form is ready for Salt1-Salt4. The closest forms were `upper_vertical_only`
and `lower_vertical_only`: both improved mdot/velocity and TW metrics, but
both still worsened all-probe and TP RMSE. Upper-vertical-only deltas were
all-RMSE `+0.000101928 K`, TP-RMSE `+0.000993433 K`, TW-RMSE
`-0.000279829 K`, and TW-without-TW10 RMSE `-0.000390558 K`. Lower-vertical-only
deltas were all-RMSE `+0.000110606 K`, TP-RMSE `+0.001006495 K`, TW-RMSE
`-0.000273024 K`, and TW-without-TW10 RMSE `-0.000381800 K`. Runtime:
total campaign `528.803825 s`, solve time `503.636152 s`, max scenario
duration `112.448520 s`. Next AMX1 progress should stay Salt2-only and test
lower multipliers or a disabled-by-default gradient-clipped variant around the
upper/lower vertical-only forms before any Salt1-Salt4 rerun.

2026-07-21 predictive execution-path update:
TODO-PRED-ENDTOEND-SCORE produced
`work_products/2026-07/2026-07-21/2026-07-21_predictive_model_execution_path/`.
Use it as the shortest current plan from the steady `fluid+walls` target and
LitRev model-form ladder to a final setup-only scorecard. The staged path is:
baseline current model, external BC dictionary, pressure source-envelope/basis
lane, heat-loss network lane, recirculation guard/hybrid lane, then frozen
scorecard. It explicitly separates train/calibration, development
validation/support, blind holdout, external test, and future score-only claims.
No model was run, no coefficient was fit, and no new closure was admitted.

2026-07-21 starter implementation update:
TODO-PRED-FINAL-MODEL-STARTER-IMPLEMENTATION-2026-07-21 produced
`work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/`
and added `tools/analyze/build_predictive_final_model_starter.py`. This
implements the stage-0/study-queue surface from the execution plan: baseline
contract, runtime/split gate audit, residual-lane readiness, next-study queue,
freeze-readiness matrix, and release guardrails. Result:
`starter_implemented_final_freeze_still_blocked`; runtime/split gate failures
are `0`, fit/model-selection rows after source/property gate are `0`, and no
solver, scheduler, Fluid edit, fitting, model selection, or admission occurred.

2026-07-13 coordination update: AGENT-296 consolidated the post-parallel-agent
state and next maximum-progress plan in
`work_products/2026-07/2026-07-13/2026-07-13_predictive_parallel_progress_and_next_plan/`.
The recommended next order is full `solve_case` confirmation, hydraulic
correction, one-scalar HX/cooler freeze, external BC dictionary work, Salt2
thermal mesh/sign gate, sensor map, and only then forward-v1 split scoring.

2026-07-13 implementation update: AGENT-297 built the repo-local external-BC
bridge package in
`work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/`.
It produces a 24-row Fluid-ready external-boundary dictionary, split-aware HX
and boundary scorecards, hydraulic guardrail summaries, and a precise Fluid
patch plan. External `../cfd-modeling-tools/**` source remained read-only, so
the next implementation step is a writable Fluid lane for
`ambient_loss_model = external_boundary_table`.

2026-07-14 readiness update: AGENT-315 built
`work_products/2026-07/2026-07-14/2026-07-14_forward_model_readiness_after_h1_proxy/`
after the forward-v0 solve_case confirmation and AGENT-308 H1 proxy evidence.
The note keeps the current scorecard non-final: solve_case confirmation is
admitted for forward-v0 (`6/6` pass rows), the H1 proxy is directionality-only
(`F1` mean mdot error `0.002144 kg/s` and still positive on every Salt row),
thermal admission remains blocked (`0` fit-admissible rows). Its
`salt_2=train`, `salt_3=validation`, `salt_4=holdout` split is now historical
method-development context, superseded for final predictive policy by AGENT-481.

2026-07-14 final-gate update: AGENT-317..321 produced the current final
forward-v1 gate in
`work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/`.
The decision is `blocked_no_go_final_forward_v1_not_admitted`. Fluid now has a
localized fixed-K hook, but no calibrated H1/reset rerun; thermal/internal Nu
has `0` fit rows; corrected-Q job `3293924` remains live; boundary/HX/wall
model support is not final.

2026-07-14 heat-loss placement update: AGENT-356 produced
`work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/`.
Use it for tomorrow-presentation and thesis discussion of where the current
best predictive-style model loses heat. The comparison uses `solve_case`
`F1_heater_only` and shows aggregate heat balance is close by cancellation:
pipe legs over-lose heat while junction/stub connector regions under-lose heat.
It remains diagnostic/model-form evidence because imposed cooler duty is still
consumed.

2026-07-14 parity-contract update: AGENT-365 produced
`work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/`.
Use it as the repeatable external-BC/source-contract and thermal-profile
diagnosis package for the heat-release study. It ties the best-predictive
leg discrepancy to h/Ta/Tsur/emissivity/layer setup rows, source/sink roles,
and wall-shell drive diagnostics under the older Salt2 train / Salt3 validation
/ Salt4 holdout split. It does not rerun Fluid and does not promote imposed
cooler duty to predictive HX. Re-score future final candidates under the
AGENT-481 Salt1-4 training plus perturbation/external/new-CFD holdout policy.

2026-07-15 row-admission update: AGENT-407 produced
`work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger/`.
Use `row_admission_ledger.csv` as the canonical row-family ledger for
forward-v1 thermal/HX/internal-Nu evidence. The only predictive candidate lane
is setup-legal HX/cooler (`salt2_fit_constant_UA_bulk_drive` preferred; F1+HX1
kept as secondary reconciliation evidence). Realized `wallHeatFlux`, imposed
cooler duty, and negative-source test-section rows are diagnostic only.
Internal Nu has `0` admitted fit rows and remains blocked by missing
wallHeatFlux plus wall-bulk/Gz/onset anchors.

2026-07-15 setup-predictive heat-loss implementation update: AGENT-418 produced
`work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant/`.
Fluid now has an active `outer_closure_mode: external_boundary_table` path that
uses setup-only h/Ta/Tsur/emissivity dictionaries, a junction/stub/connector
coverage multiplier, and bulk/pipe-outer-wall/outer-surface drive selectors in
the actual passive heat-loss calculation. This is an implementation unlock, not
final admission: it still needs declared split fitting/scoring and external
test ledgers before forward-v1 promotion.

2026-07-15 M3 successor / test-section policy update: AGENT-430 records the
user modeling requirement that M3 must not mean "delete the test section." The
current `M3_cfd_heater_cooler_pressure_root` row remains useful only as a
diagnostic ablation: it shows that removing the present CFD test-section
compatibility term lowers TP/TW RMSE but worsens mdot error. The predictive
target is a setup-only M3 successor, `M3+TS`: pressure-root mdot solve plus
heater model, cooler/HX model, and an explicit distributed test-section
heat-loss model. That model must not consume realized CFD test-section net heat,
CFD `wallHeatFlux`, CFD mdot, imposed CFD cooler duty, or validation
temperatures at runtime.

2026-07-15 segment-resolved equation policy update: AGENT-431 records that the
pressure-root shorthand must not be read as a global `dp_drive(mdot)` and
`dp_loss(mdot)` closure. Buoyancy drive is an integral over
`rho(T(s),p,s) g dz(s)` and therefore depends on the thermal field and loop
position; `mdot` influences it through the coupled thermal solve. Pressure loss
is a sum of segment-local distributed, reset/development, local-K,
junction/branch, and recirculation/onset terms. Different model forms are
expected in heater, cooler/HX, downcomer, upcomer, test section, lower/upper
legs, and junction/stub/connector regions.

2026-07-15 sensor / sophisticated-modeling update: AGENT-432 records the user
decision that TP2 should be restored to the 1D path and aggregate scoring once
projection/source-segment/finite-output gates pass, while TW10 stays excluded
until a forward model emits an active-HX shell-state temperature. It also adds
explicit TODOs for an upcomer pipe-flow plus recirculation-cell hybrid model and
for a segment-by-segment boundary-layer development scorecard.

2026-07-15 branch-specific model-form update: AGENT-435 records that the
current recirculating upcomer must be omitted from ordinary single-stream
`Nu`, `f_D`, and `K` fits. Ordinary-pipe analysis should proceed on other
branches only where local regime/admission gates support it, with different
model forms by branch. The upcomer remains in a separate hybrid recirculation
and onset lane.

2026-07-16 boundary-submodel admission update: AGENT-454 produced
`work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/`.
The broad `predictive-heater-cooler-wall-submodels` blocker is superseded:
heater (`salt2_fit_constant_heater_efficiency`) and cooler/HX
(`salt2_fit_constant_UA_bulk_drive`) pass held-out runtime-legal admission
gates. The remaining open boundary blocker is
`predictive-wall-test-section-submodels`: wall/test-section/passive-boundary
physics still lacks a setup-only physical loss model fit on Salt2 and scored on
Salt3/Salt4.

2026-07-16 test-section heat-loss admission update: AGENT-458 produced
`work_products/2026-07/2026-07-16/2026-07-16_predictive_test_section_heat_loss_model/`.
This implements `TODO-PREDICT-TEST-SECTION-HEAT-LOSS` as a strict setup-only
Salt2-fit screen. The blocker remains open: the two physical candidates
(`TS1_salt2_fit_hA_constant_drive_deltaT` and
`TS2_salt2_fit_constant_loss_W`) were runtime-legal within that older
Salt2-only screen but underpredict Salt3/Salt4 heat loss and lack
solver-coupled M3+TS mdot/TP/TW scores. Re-score any carried-forward
test-section form under the AGENT-481 Salt1-4 final-training policy. Next work
should implement or run the external-boundary / resistance-network M3+TS path,
not promote realized-loss replay diagnostics.

2026-07-16 coupled M3+TS implementation update: AGENT-461 produced
`work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/`.
Fluid now has role-local `external_boundary_role_rows`, so the upcomer
`ambient_wall` and `test_section` subspans can replace the parent upcomer
ambient-loss approximation without realized CFD heat evidence. The package
emits Salt2/Salt3/Salt4 role-row scenario contracts. A later compute-node
`--run-fluid` pass completed 9/9 coupled rows with accepted roots. The blocker
remains open because no candidate has both an admitted coupled gate and
held-out heat-loss gates; the next action is model admission work, not rerunning
the same command.

2026-07-17 cooler model test-plan update: AGENT-480 produced
`operational_notes/07-26/17/2026-07-17_COOLER_MODEL_COMPREHENSIVE_TEST_PLAN.md`.
Use it as the handoff for `TODO-PREDICT-COOLER-REMOVAL`. It defines the
two-candidate campaign for constant-UA effectiveness/NTU and segmented
distributed-UA cooler models under the older Salt2 train / Salt3 validation /
Salt4 holdout development split. AGENT-481 supersedes that split for final
predictive scoring: cooler candidates should ultimately be retrained across
Salt1-4 nominal rows and tested against perturbation/external/new-CFD holdout
rows, while preserving one fitted scalar, runtime-input legality, duty-only
scorecard, coupled Fluid scorecard, required tests, and failure/acceptance
criteria.

2026-07-17 cooler removal implementation update: AGENT-482 produced
`work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model/`.
The constant-UA effectiveness/NTU candidate reproduces the prior split-legal
duty screen with one Salt2-fit scalar: Salt3 validation error `2.869104004 W`
and Salt4 holdout error `7.502618613 W`, with runtime audit pass. AGENT-492
later diagnosed the `45 s` coupled timeout as a bound-selection problem and
reran `--run-fluid --timeout-seconds 180`: `12/12` Fluid rows completed with
elapsed times `69.97005505-136.4293815 s`. The completed coupled rows still do
not admit the cooler/wall path because mdot and TP/TW errors remain large.

2026-07-17 cooler timeout + wall-circuit study update: AGENT-492 produced
`work_products/2026-07/2026-07-17/2026-07-17_cooler_fluid_timeout_and_wall_circuit_study/`.
The future production timeout recommendation for the AGENT-482 cooler score is
`273 s` per row, based on a posthoc 2x slowest completed row. The best new
passive-boundary model-form candidate is
`PB1_total_hA_heater_power_drive_p1`: one Salt2-trained passive drive, setup hA
summed over passive roles, and predeclared linear heater-power drive scaling.
It passes passive-total static validation/holdout gates (`0.04197824857 W` and
`0.8485115954 W`) but is not admitted; local test-section candidates still fail
percent gates, and blocker closure still requires coupled M3+TS+cooler scoring
with separate passive-total and local test-section review.

2026-07-17 wall/test-section coupled admission update: AGENT-494 produced
`work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission/`.
It promotes `PB1_total_hA_heater_power_drive_p1` into explicit PB1+cooler
scenario contracts while keeping local test-section TS6/TS7 component gates
separate from passive-total cancellation. The coupled review is now complete:
12/12 PB1+HX lumped/segmented Fluid rows completed with accepted roots, PB1
static passive-total gates pass, and the runtime audit stays legal. The blocker
still remains `keep_open` because 0 candidates are admitted; all validation and
holdout coupled gates fail vs M3. The pattern is specific: mdot error improves
against M3, but all-probe/TW RMSE worsens sharply, so the next useful model
needs local wall-temperature, wall-shape, or test-section distribution physics
rather than another passive-total hA scaling pass. The submitted background
job `3300338` is retained as first-attempt scheduler provenance; job `3300339`
completed the bounded compute-node run that backs the final package outputs.

2026-07-17 wall/test-section distribution ladder update: AGENT-498 produced
`work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/`.
It advances the AGENT-494 failure mode from passive-total heat loss to local
heat placement. The dry-run package defines two Salt2-trained local distribution
candidates (`PB2_salt2_local_shape_passive_hA_p1` and
`PB3_upcomer_test_section_attenuated_shape_p1`), emits segment/probe regression
audits, and produces 12 runtime-legal coupled scenario contracts. Background
coupled replay completed 12/12 Fluid rows with accepted roots, but 0/4
candidates are admitted. The regenerated current-candidate probe evidence
contains 204 localization rows, 136 validation/holdout deltas, and 80
role/segment summaries; comparable probe gates are 106 fail vs M3 and 14 pass,
with the largest regressions on Salt4 TW heated-incline sensors. The result
preserves the AGENT-494 pattern: mdot error improves versus M3, but
all-probe/TW RMSE remains far worse than M3. The blocker therefore remains open
and is now narrowed beyond passive external hA redistribution toward local
wall-temperature drive, heater/source placement, axial mixing/upcomer thermal
stratification, or test-section wall/fluid coupling.

2026-07-17 wall/passive/test-section admission closeout: AGENT-507 produced
`work_products/2026-07/2026-07-17/2026-07-17_wall_passive_test_section_admission_closeout/`.
It verifies the requested PB1 path is complete: `PB1_total_hA_heater_power_drive_p1`
was taken into coupled M3+TS+cooler scoring, and local test-section/distribution
behavior was assessed separately. The closeout reviews `24` completed coupled
rows and `8` candidate gate rows. No candidate is admitted. Runtime is no longer
the blocker; the remaining blocker is local thermal-field physics: wall
temperature drive, heater/source placement, axial mixing/upcomer stratification,
or explicit test-section wall/fluid coupling.

2026-07-17 heater-source redistribution update: AGENT-511 produced
`work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score/`.
It tested the heater/source-placement branch using Fluid's existing
`tw4_to_tp3_three_span` source API, with a Salt2-only one-parameter lambda scan
crossed with PB2 wall distribution and admitted cooler mechanics. Slurm job
`3300966` completed `27/27` coupled rows. The Salt2 fit selected `lambda=0.00`,
the upstream endpoint (`tw4_to_tw5=0.60`, `tw5_to_tw6=0.30`, `tw6_to_tp3=0.10`).
No candidate is admitted: mdot improves versus M3 on Salt3/Salt4, but TP, TW,
and all-probe RMSE are much worse than M3 for both lumped and segmented cooler
crosses. The result narrows the open blocker away from heater-source
redistribution alone and toward the next Fluid features: upcomer mixing/
stratification and explicit test-section wall/fluid coupling.

2026-07-17 wall-temperature-drive candidate update: AGENT-513 produced
`work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate/`.
It tested the AGENT-507 wall-temperature-drive next step by keeping the Salt2
PB2 local distribution shape and changing only the upcomer `ambient_wall` and
`test_section` role-row drive selector to Fluid-solved wall states. A bounded
compute-node coupled run completed `9/9` rows with runtime audit pass and `0`
admitted candidates. WTD1 pipe-outer-wall drive improves mdot versus M3 by
about `15.77 pct` validation and `13.14 pct` holdout, but worsens all-probe
RMSE by about `35.44 K` validation and `42.97 K` holdout and worsens TW RMSE by
about `42.46 K` validation and `48.67 K` holdout. WTD2 outer-surface drive is
worse on both mdot and temperature. The blocker remains open and is now narrowed
away from passive drive selectors toward heater/source redistribution, explicit
test-section wall/fluid coupling, or upcomer axial mixing/recirculation physics.

2026-07-17 parallel wall thermal-circuit study closeout: AGENT-522 produced
`work_products/2026-07/2026-07-17/2026-07-17_wall_thermal_circuit_study/`
and completed Slurm job `3301052` (`ag522_wall_circuit`) on
`NuclearEnergy-dev` in `00:05:37`. It imports completed AGENT-511 heater-source
evidence read-only (`27/27` coupled rows, `0` admitted, selected Salt2 lambda
`0`) and scores two new non-duplicative lanes: heated-incline wall-state drive
and test-section-only wall/fluid coupling. The job completed `24/24` coupled
rows with `--parallel-workers 8`, emitted `408` probe localization rows, and
admitted `0/8` candidates. The blocker remains open: HIW/TSC variants can
improve mdot, but TP/TW/all-probe gates still fail vs M3, with the worst
regressions on Salt4 heated-incline TW5/TW6. The next lane should move beyond
passive wall-state drive selectors toward axial mixing/upcomer stratification,
sensor-map correctness, or explicit wall/fluid thermal storage/coupling.

2026-07-16 frozen M3+TS candidate score update: AGENT-470 produced
`work_products/2026-07/2026-07-16/2026-07-16_m3ts_frozen_candidate_coupled_score/`.
The frozen role-row candidates are still runtime-legal, but not admitted:
`3` candidates reviewed, `0` admitted, and a bounded compute-node
`--run-fluid --timeout-seconds 45` pass produced `9` coupled rows with `9/9`
`timeout_after_45s` and `0` completed Fluid scores. The next M3+TS blocker is
not runtime leakage; it is solver/root runtime convergence or replacement by a
setup-only candidate that can complete coupled Salt2/Salt3/Salt4 scoring.

2026-07-16 leg-specific Internal-Nu admission update: AGENT-455 produced
`work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution/`.
This corrects the modeling taxonomy for the forward segment chain:
`test_section_span` is part of the upcomer, not a separate ordinary non-upcomer
fit leg. It also confirms that current forward work still has `0`
fit-admissible Internal-Nu rows and `0` publication-ready Closure-QOI/GCI rows.
Use distinct future lanes for heater/source, downcomer, cooler/HX, and
upcomer hybrid/onset, but keep baseline/literature/default internal Nu until
branch-local sign/heat-balance/source, residual-owner, recirculation, and
mesh/GCI gates admit rows.

## Trusted results

- **Cooler/HX is the first-order lever.** Fixed-mdot baseline mean-abs Tmean
  error 63.746 K drops to 4.456 K (−59.29 K, 93.0%) when CFD cooler duty is
  imposed. Source: `work_products/2026-07/2026-07-13/2026-07-13_predictive_heat_loss_path/` (AGENT-270).
- **Heater is not 1:1.** No-radiation parity gives heater realized/imposed ratio
  0.918. Source: `work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/` (AGENT-279).
- **Input contract is strict and passing.** Setup inputs vs calibrated params vs
  validation targets vs diagnostic-only CFD evidence are separated with 0
  violations (TODO-PRED-INPUT-CONTRACT, refreshed AGENT-292).
- **Final predictive split updated.** AGENT-481 supersedes the old
  salt_2 train / salt_3 validation / salt_4 holdout policy for final thesis
  prediction. Final training spans Salt1-4 nominal rows; holdout/testing comes
  from Salt2 +/-5Q after PM5 repair, `val_salt2` after external-test ledger
  admission, Salt2/Salt4 +/-10Q after terminal harvest/admission, and new CFD
  such as the Salt3 Q x insulation matrix.
- **Best current heat-loss placement diagnosis is leg-resolved.**
  `F1_heater_only` over-loses heat in lower leg, upcomer/test-section, cooling
  branch, and downcomer, but under-loses heat in junction/stub connector
  regions. Source:
  `work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/`
  (AGENT-356). This is not final predictive-HX validation because imposed
  cooler duty is still a runtime shortcut.
- **M2/M3 test-section tradeoff is diagnostic, not a deletion policy.**
  AGENT-424 reports M2 (`CFD heater + test-section net + cooler`) at
  `10.397%` mean mdot error and `26.972 K` all-probe RMSE, while M3
  (`CFD heater + cooler only`) has `16.826%` mdot error and `18.023 K` RMSE.
  Interpret this as evidence that the current negative test-section
  compatibility term is not final. The next model should replace it with a
  setup-only distributed loss model, not omit the test-section physics.

## Open / in-progress / blocked

Task chain (see `.agent/BOARD.md`), in intended sequence:

1. `TODO-PRED-INPUT-CONTRACT` — COMPLETE (strict forward input contract).
2. `TODO-PRED-FORWARD-V0` — COMPLETE (pressure-rooted, heater input + imposed
   cooler duty → mdot + sensors; heater-only Tmean err 4.609 K but overpredicts
   mdot by ~0.0055 kg/s vs CFD).
3. `TODO-PRED-HX-FIT` — COMPLETE_PROTOCOL_BLOCKED (model form delivered; no fit
   without declared split — now unblocked by validation-split).
4. `TODO-PRED-HEATER-TEST-CONTRACT` — COMPLETE (heater-only source contract; defer
   calibrated `eta_heater` / test-section loss to validation).
5. `TODO-PRED-WALL-LAYER` (+ `TODO-PRED-WALL-SHELL-SAMPLE`) — COMPLETE E0; E1/E2
   run but do not close the passive heat-loss gap.
6. `TODO-PRED-HYDRAULIC-GATE` — COMPLETE (fit-safe pressure rows = left_lower_leg,
   left_upper_leg; forward-v0 overpredicts mdot every Salt row).
7. `TODO-PRED-THERMAL-MESH-GATE` — OPEN (blocked on thermal GCI, Salt2-first).
8. `TODO-PRED-SENSOR-MAP` — OPEN (TP/TW coords provisional).
9. `TODO-PRED-VALIDATION-SPLIT` — COMPLETE.
10. `TODO-PRED-ENDTOEND-SCORE` — OPEN (final scorecard, train vs held-out).

Also: `TODO-PREDICT-HEATER-FLUID-FRACTION` (eta_heater model) and
`TODO-PREDICT-COOLER-REMOVAL` (predictive UA / ε-NTU, replace imposed duty) are
OPEN/HIGH. `TODO-PREDICT-TEST-SECTION-HEAT-LOSS` is also OPEN/HIGH and required
before an M3-like successor can be treated as predictive: it must build
`Q_test_section_loss_model` from setup geometry, h/Ta/Tsur/emissivity/coverage,
and/or wall/layer resistance terms.

New segment-resolved modeling sequence:

1. `TODO-PREDICT-SEGMENT-EQUATION-CONTRACT` — OPEN/HIGH. Freeze the coupled
   pressure/thermal equation contract and per-region model slots.
2. `TODO-PREDICT-SEGMENT-PRESSURE-MODELS` — OPEN/HIGH. Score segment-local
   pressure drive/loss forms without fitting true `f_D`/`K` from recirculating
   rows.
3. `TODO-PREDICT-SEGMENT-THERMAL-MODELS` — OPEN/HIGH. Score segment-local
   heater, cooler, test-section, passive-boundary, wall/layer, junction, and
   optional admitted-radiation heat terms.
4. `TODO-PREDICT-COUPLED-SEGMENT-M3TS-SCORECARD` — OPEN/HIGH. Run the coupled
   setup-only M3+TS candidate against diagnostic M2/M3 metrics under the
   train/validation/holdout contract.
5. `TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE` — OPEN/HIGH. Restore TP2 as a
   post-solve score target on the right-downcomer/bottom-horizontal junction
   path after finite/projection gates pass; keep TW10 excluded until active-HX
   shell temperature is modeled.
6. `TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL` — OPEN/HIGH. Replace single-stream
   upcomer assumptions in recirculating rows with a throughflow pipe plus
   recirculation-cell exchange candidate.
7. `TODO-PREDICT-BOUNDARY-LAYER-DEVELOPMENT-SCORECARD` — OPEN/HIGH. Quantify
   hydraulic and thermal development effects by segment on `mdot`, TP, TW,
   Tmean, and loop-Delta-T errors.
8. `TODO-BRANCH-SPECIFIC-ORDINARY-PIPE-SCORECARD` — OPEN/HIGH. Omit the
   current recirculating upcomer from ordinary-pipe coefficient fits and score
   branch-specific forms on the other eligible branches.

Current blockers (`.agent/BLOCKERS.md`): `thermal-cfd-1d-parity` is resolved
narrowly by AGENT-452 as a blocker to predictive thermal continuation because
thermal residual owners are separated and internal Nu remains out of residual
cleanup. AGENT-454 supersedes `predictive-heater-cooler-wall-submodels`; the
remaining boundary-model blocker is `predictive-wall-test-section-submodels`.
The Fluid external-boundary API gap is resolved at the implementation-hook
level, but wall/test-section/passive-boundary campaign validation/admission is
still open. Forward-thread register (B1–B10):
`work_products/2026-07/2026-07-13/2026-07-13_forward_predictive_model_research_plan/blocker_register.csv`
— B1 cooler/HX, B2 heater efficiency, B3 test-section source/sink, B4 wall-layer,
B5 radiation, B6 thermal mesh, B7 hydraulic fit-safety, B8 sensor location,
B9 validation split, B10 Fluid external-boundary API.

## Research avenues tried (outcome + provenance)

- **Impose CFD cooler duty in fixed-mdot replay** → confirms cooler/HX is
  first-order (63.746 K → 4.456 K). Diagnostic, not predictive (uses CFD duty).
  `.../2026-07-13_predictive_heat_loss_path/` (AGENT-270).
- **No-radiation heater+cooler parity, fixed-mdot** → heater ratio 0.918;
  radiation-off is a sensitivity only (CFD `rcExternalTemperature` embeds
  radiative exchange, so no separate 1D radiation term). AGENT-279 / AGENT-287.
- **Wall-bulk vs near-wall drive (E0/E1/E2)** → N2 hA/Ta (wall-drive) replay
  22.650 K vs N1 bulk 4.934 K; E1/E2 run after wall-shell sampling but do not
  close the passive-loss gap. TODO-PRED-WALL-LAYER / -WALL-SHELL-SAMPLE.
- **Pressure-rooted forward-v0 for mdot** → overpredicts mdot for every Salt row
  (F1 mean +0.005478 kg/s vs CFD); friction/minor-loss tuning needed before
  thermal fitting. TODO-PRED-FORWARD-V0 / TODO-PRED-HYDRAULIC-GATE.
- **HX UA / ε-NTU fit** → model form + protocol ready, but was blocked with 0
  declared validation rows; split now defined. TODO-PRED-HX-FIT.
- **Diagnostic M3 ablation** → lower TP/TW RMSE but worse mdot when the CFD
  test-section net term is removed. This does not imply the test section has
  zero heat loss; it motivates `M3+TS`, a setup-only successor with modeled
  distributed test-section loss. TODO-PREDICT-TEST-SECTION-HEAT-LOSS.

## Key artifacts (canonical)

- Research plan + registers: `work_products/2026-07/2026-07-13/2026-07-13_forward_predictive_model_research_plan/`
  (`README.md`, `input_readiness_matrix.csv`, `blocker_register.csv`,
  `research_plan.md`, `task_backlog.csv`).
- Plan note: `operational_notes/07-26/13/2026-07-13_forward_predictive_model_research_plan.md`.
- Human handoff (start here): `operational_notes/07-26/13/2026-07-13_CURRENT_CLOSURE_AND_PREDICTIVE_MODEL_START_HERE.md`.
- Cooler/HX lever: `work_products/2026-07/2026-07-13/2026-07-13_predictive_heat_loss_path/`.
- No-radiation parity: `work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/`.
- Runtime guardrail decision: `.agent/DECISIONS.md` (2026-07-08).
- Parallel next-plan handoff:
  `work_products/2026-07/2026-07-13/2026-07-13_predictive_parallel_progress_and_next_plan/`
  (AGENT-296).
- External-BC implementation bridge:
  `work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/`
  (AGENT-297).
- Forward-model readiness after H1 proxy:
  `work_products/2026-07/2026-07-14/2026-07-14_forward_model_readiness_after_h1_proxy/`
  (AGENT-315).
- Final forward-v1 gate and coordination:
  `work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/`,
  `work_products/2026-07/2026-07-14/2026-07-14_forward_v1_parallel_coordination/`
  (AGENT-317..321).
- Forward-v1 gate checklist and scorecard input waitlist:
  `work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/forward_v1_gate_checklist.csv`,
  `work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/scorecard_inputs_waiting_on_agents.csv`,
  `work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/internal_nu_dependency_blockers.csv`.
- TSWFC2 distributed wall/fluid dry contract:
  `work_products/2026-07/2026-07-18/2026-07-18_tswfc2_dry_contract/`
  (AGENT-541).
- Final predictive scorecard shell with source/property label propagation:
  `work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/`
  (TODO-FINAL-SCORECARD-SOURCE-PROPERTY-LABELS update to AGENT-509 shell).
  Current decision remains `blocked_no_go_final_forward_v1_not_admitted`; H1
  proxy, imposed cooler duty, and diagnostic thermal rows are not final
  predictive closure evidence. After the upcomer recirculation/internal-Nu
  update, `Nu_section_effective_upcomer_diagnostic` is diagnostic/validation-only
  and cannot be consumed as trainable closure data; cfd-pp onset candidates and
  therm-reconstr matched-plane extraction are required before any internal-Nu
  fit gate can reopen.
- Scientific-closure / forward-v1 execution dashboard:
  `work_products/2026-07/2026-07-14/2026-07-14_scientific_closure_forward_v1_execution_dashboard/`.
  Start with `workstream_execution_dashboard.csv`,
  `gate_landing_requirements.csv`, `thesis_evidence_register.csv`, and
  `forward_v1_refresh_queue.csv` when choosing the next gate-moving task.
- Best-predictive heat-loss discrepancy study:
  `work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/`.
  Open `presentation_brief.md` for tomorrow's meeting, then
  `best_predictive_leg_heat_loss_discrepancy.csv`,
  `model_change_recommendations.csv`, and
  `repeatability_and_refinement_guide.md` for model-refinement work.
- External-BC thermal-profile parity study:
  `work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/`.
  Open `presentation_brief.md`, `section_heat_loss_comparison.csv`,
  `thermal_profile_drive_comparison.csv`, and `external_bc_segment_equivalents.csv`
  when refining 1D heat-release placement and wall-adjacent drive assumptions.
- Forward-v1 row admission ledger:
  `work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger/`.
  Open `row_admission_ledger.csv`, `hx_candidate_reconciliation.csv`,
  `internal_nu_fit_rows.csv`, and `README.md` before promoting any thermal/HX
  row into a forward-v1 scorecard.
- Blocker-resolution wave implementation:
  `work_products/2026-07/2026-07-15/2026-07-15_blocker_resolution_wave_implementation/`.
  AGENT-413 adds a direct Fluid `hx_ua_multiplier` hook for setup-only
  predictive HX scoring, refreshes the blocker register, and records that final
  forward-v1 remains `blocked_no_go_final_forward_v1_not_admitted` until F6,
  thermal/internal-Nu, and HX/boundary scorecards admit rows.
- Setup-predictive Fluid heat-loss variant:
  `work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant/`.
  Open `fluid_variant_contract.csv`, `dry_run_segment_loss_demonstration.csv`,
  and `README.md` before using external-boundary setup dictionaries in a
  forward score.
- M3 successor / test-section heat-loss requirement:
  `operational_notes/07-26/15/2026-07-15_m3_successor_test_section_heat_loss_requirement.md`.
  Open this before claiming `TODO-PREDICT-TEST-SECTION-HEAT-LOSS`; it records
  that M3-like forward work must model test-section heat loss rather than omit
  the test section.
- Segment-resolved pressure/thermal modeling plan:
  `operational_notes/07-26/15/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.md`.
  Open this before claiming the segment equation, pressure, thermal, or coupled
  M3+TS scorecard TODOs; it expands the pressure-root shorthand into
  temperature/density/elevation drive and segment-local loss/heat terms.
- Sensor and sophisticated modeling decisions:
  `operational_notes/07-26/15/2026-07-15_sensor_and_sophisticated_modeling_decisions.md`.
  Open this before restoring TP2, changing TW10 scoring, implementing the
  upcomer pipe-cell hybrid, or scoring boundary-layer development effects.
- Branch-specific model forms and upcomer omission plan:
  `operational_notes/07-26/15/2026-07-15_branch_specific_model_forms_and_upcomer_omission_plan.md`.
  Open this before fitting or scoring ordinary `Nu`, `f_D`, or `K` forms; it
  records that recirculating upcomer rows are excluded from ordinary-pipe fits.
- Recirculation policy and final forward/hydraulic unblock chain:
  `work_products/2026-07/2026-07-15/2026-07-15_recirculation_policy_forward_hydraulic_unblock_plan/`.
  Open `recirculation_policy_decision_table.csv`,
  `coefficient_label_admission_policy.csv`,
  `current_evidence_recirculation_classification.csv`, and `README.md` before
  promoting AGENT-406 PM5 or AGENT-409 raw two-tap evidence. Current rows are
  diagnostic-only and do not unlock final forward-v1.
- Setup-only HX/cooler scorecard unlock:
  `work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock/`.
  Preferred lane `salt2_fit_constant_UA_bulk_drive` passes the bounded
  candidate screen (Salt3 validation `2.869 W`, Salt4 holdout `7.503 W`,
  runtime violations `0`) and may feed the final scorecard as setup-only HX
  evidence, but final forward-v1 remains blocked by hydraulic/internal-Nu/
  recirculation/mesh gates.
- Predictive boundary-submodel admission:
  `work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/`.
  Heater and cooler/HX submodels are admitted as setup-only boundary evidence;
  the remaining open boundary blocker is wall/test-section/passive-boundary
  heat loss, tracked as `predictive-wall-test-section-submodels`.
- M3+TS frozen candidate coupled score:
  `work_products/2026-07/2026-07-16/2026-07-16_m3ts_frozen_candidate_coupled_score/`.
  Runtime audit remains setup-only, but `3` frozen candidates have `0` admitted
  rows. The bounded compute-node run produced `9/9` solver timeouts after
  `45 s`, so the next work is solver/root convergence or a replacement
  setup-only wall/test-section candidate with completed coupled scoring.
- TP2 1D model evidence:
  `work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence/`.
  TP2 now passes source/projection, finite-row, runtime-forbidden, and
  fit-forbidden gates as a validation-only score target. The aggregate sensor
  count can move from `5 TP + 10 TW` to `6 TP + 10 TW` when using the restored
  TP2 policy; TW10 remains blocked and final forward-v1 remains a separate
  admission gate.
- Leave-Salt3-out heater-source redistribution score:
  `work_products/2026-07/2026-07-17/2026-07-17_heater_source_leave_salt3_out_score/`.
  AGENT-529 corrects the AGENT-511 split by fitting/model-selecting lambda on
  Salt1/Salt2/Salt4 only, holding out Salt3, and carrying Salt2 +/-5Q plus
  `val_salt2` as blind score-only rows. Slurm jobs `3301102` and `3301155`
  completed `67/67` Fluid rows. Strict selection remains blocked because every
  Salt4 train-grid row has `root_status=rejected`; diagnostic finite-row
  lambda `1.0` fails Salt3 vs M3 by mdot, TP, TW, and all-probe gates. Next
  blockers: repair Salt4 root status, add Salt1 PB2 external-boundary role
  rows, and add executable blind-row adapters.
- Weekend next-model handoff:
  `operational_notes/07-26/17/2026-07-17_WEEKEND_NEXT_MODEL_HANDOFF_PLAN.md`.
  AGENT-533 documents the current blocker list and recommends the next
  non-overlapping model lane: `UMX1` energy-conserving upcomer
  exchange/stratification with one fitted scalar, after auditing the updated
  Fluid branch for a real API hook. The secondary lane is `TSWFC2`, a
  distributed test-section wall/fluid node model, but only after confirming
  AGENT-526's one-node series resistance result and avoiding a duplicate rerun.
  AGENT-541 now provides the no-solver TSWFC2 dry contract; implementation or
  smoke scoring still requires a separate row after the UMX1 API result is
  known.
- Fluid temperature-periodicity bracket repair audit:
  `work_products/2026-07/2026-07-18/2026-07-18_fluid_temperature_periodicity_bracket_repair/`.
  TODO-FLUID-TEMP-PERIODICITY-BRACKET-REPAIR shows the UMX1 Salt3/Salt4
  accepted-root failures are caused by the current Fluid temperature scan upper
  bound, not by a reason to relax root gates: Salt2 rows are already bracketed
  (`3/9`), all Salt3/Salt4 rows recover roots above the current upper bound
  (`6/9`), and `0` rows remain unbracketed before the audit ceiling. The Fluid
  source patch is deferred while external `solver.py` is owned by active
  TSWFC2 work; use `fluid_patch_contract.csv` to add bounded adaptive expansion
  in `solve_temperature_periodicity()`, then rerun strict UMX1 smoke validation.
  Handoff note:
  `operational_notes/07-26/18/2026-07-18_FLUID_TEMPERATURE_PERIODICITY_BRACKET_REPAIR_HANDOFF.md`.
- Downcomer Internal-Nu unlock and blocker roadmap:
  `work_products/2026-07/2026-07-16/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap/`.
  Use `future_studies_and_blockers.csv` as the current compact queue for
  non-overlapping next studies. It keeps downcomer Nu blocked, documents all
  four open blockers, and prioritizes coupled M3+TS scoring plus downcomer
  physical admission without changing the predictive runtime-input contract.
- AMX1 lower-multiplier Salt2 smoke intake:
  `work_products/2026-07/2026-07-20/2026-07-20_amx1_lower_multiplier_smoke_intake/`.
  The Fluid campaign `amx1_salt2_lower_multiplier_smoke_v2` completed `7/7`
  Salt2 rows `ok` and passed finite-root plus conservative-ledger gates, but no
  upper/lower vertical-only multiplier cleared the paired progression gate.
  Every AMX1 row still worsened `all_rmse_K` and `tp_rmse_K`; closest was
  `upper_vertical_only_m010` with `max_positive_core_delta=0.00019863866604197256 K`.
  Next useful AMX1 work is a disabled-by-default gradient-clipped localized
  exchange smoke, Salt2-only before any Salt1-Salt4 bounded comparison.
- AMX1 gradient-clipped Salt2 smoke intake:
  `work_products/2026-07/2026-07-21/2026-07-21_amx1_gradient_clipped_smoke_intake/`.
  The Fluid campaign `amx1_salt2_gradient_clipped_smoke_v1` completed `3/3`
  Salt2 rows `ok` and passed finite-root plus conservative-ledger gates. The
  cap reduced the all-probe/TP regression magnitude, but neither clipped
  upper/lower vertical-only `m010` form cleared the paired progression gate.
  Closest was `upper_vertical_only_m010_clip0050` with
  `max_positive_core_delta=0.00005769407099620594 K`, still worsening
  `all_rmse_K` and `tp_rmse_K`. Do not expand this form to Salt1-Salt4; either
  revise AMX1 physics beyond strength limiting or shift priority back to
  setup-only wall/test-section/passive-boundary candidates.
- AMX1 parent-cell physics-revision Salt2 smoke intake:
  `work_products/2026-07/2026-07-21/2026-07-21_amx1_physics_revision_smoke_intake/`.
  The Fluid campaign `amx1_salt2_physics_revision_smoke_v1` completed `3/3`
  Salt2 rows `ok` and passed finite-root plus conservative-ledger gates. This
  was a real AMX1 form change from adjacent-pair diffusion to parent-scale
  lower/upper cell exchange, but both upper/lower vertical-only `m010` forms
  still worsened `all_rmse_K` and `tp_rmse_K`. Closest was
  `upper_vertical_parent_cell_m010` with
  `max_positive_core_delta=0.0003254933205099064 K`, worse than the clipped
  pairwise result. Do not expand AMX1 without new CFD structure evidence;
  shift primary effort to setup-only wall/test-section/passive-boundary
  candidates.
- +/-5Q corrected-Q and hydraulic tap-length forward-v1 delta:
  `work_products/2026-07/2026-07-14/2026-07-14_forward_v1_pm5_hydraulic_delta/`.
  Records 4 terminal-harvested +/-5Q perturbation rows, 0 independent training
  expansion rows, 12 resolved hydraulic tap-length rows, and 0 fit-admissible
  component/cluster K rows. This is progress evidence, not final forward-v1
  admission.
- Live blocker/task state: `.agent/BLOCKERS.md`, `.agent/BOARD.md`.

## Related

- `operational_notes/maps/README.md` — map index.
- `operational_notes/maps/thermal-boundary-and-radiation.md` — external BC,
  `rcExternalTemperature`, radiation inseparability (feeds B4/B5).
- `operational_notes/maps/literature-synthesis-and-gates.md` — lit-rev pre-score
  gates referenced by the input contract and forward-v0.
- `reports/thesis_dossier/README.md` — living weekly-presentation and thesis
  synthesis hub; update only when the forward-model story, blockers, or
  thesis-facing claims change.
