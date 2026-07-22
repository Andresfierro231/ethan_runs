---
task: AGENT-294
date: 2026-07-13
role: Writer
type: map
status: reference
tags: [pressure-ledger, momentum-budget, minor-loss]
related:
  - operational_notes/maps/README.md
  - operational_notes/maps/friction-closures.md
  - operational_notes/maps/geometry-and-mesh-truth.md
---
# Pressure & Momentum Budget — Map of Content

Tags: #pressure-ledger #momentum-budget #minor-loss

## What this covers
How the CFD streamwise pressure drop across the TAMU molten-salt loop is
decomposed into named physical terms — buoyancy (hydrostatic + density-gradient),
kinetic/dynamic head, distributed straight-pipe friction, development/entry
excess, and minor/feature (bend, junction, cluster) losses — and how those terms
feed the 1D closure ledger. This is the source thread for the de-buoyed friction
factors consumed by the friction-closures map. Companion threads: friction
closures (which `f` forms are fit) and geometry-and-mesh-truth (arc lengths,
lower↔right label swap).

## Current status (one paragraph)
The **pressure-term ledger is complete** (TODO-PRESSURE-TERM-LEDGER, 2026-07-08):
a read-only 18-row (3 cases × 6 spans) decomposition that reproduces the July-1
de-buoyed Salt2/3/4 budget with no buoyancy double-counting (max |residual
fraction| < 0.002). Bend/junction minor-loss K is quantified as upper bounds via
a two-tap NIST-style method. The headline lesson is settled: **per-segment ΔP is
the robust closure metric; mdot is not** (condition-dependent ±27%), and the
dominant 1D error is the thermal boundary (insulation), not hydraulic closures.
AGENT-310 adds a bounded H1 hydraulic scorecard: branch-apparent K improves
forward-v0 mdot as a diagnostic proxy, while keeping straight friction, K rows,
reset/development, and recirculation diagnostics separate. AGENT-503 made the
`val_salt2` pressure-evidence/corner-K blocker explicit: six `val_salt2` branch
pressure rows and twelve current corner rows remain diagnostic with zero
fit-admitted `f_D`/`K` entries. AGENT-523 now turns the named-loss/reset
evidence into an extraction-readiness queue: 33 named pressure rows reviewed,
0 fit-ready, 3 component/cluster repair rows, 6 branch/straight repair rows,
and 24 diagnostic/section-effective rows. AGENT-525 implements the first repair
lane as a two-tap/component contract for the three `corner_lower_right` target
rows, preserving 0 current ordinary admissions and requiring pressure/velocity
basis, straight-reference, component-isolation, recirculation, and same-QOI UQ
gates. AGENT-530 implements that extractor schema from existing evidence:
3 rows emitted, 0 ordinary admissions, 15 failed gates, and a precise raw
postprocessing queue for endpoint pressures, final basis, straight reference,
same-window RAF/RMF/SVF, and same-QOI UQ. One reconciliation gap remains open: an
unexplained ~2× mdot discrepancy at matched-T when CFD friction is imposed.
TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS converted that queue into an exact raw
sampling contract for Salt2/Salt3/Salt4 `corner_lower_right`: lower-leg `s04`
to right-leg `s00` endpoint pressure surfaces, static/`p_rgh`/velocity/density
basis fields, RAF/RMF/SVF definitions, same-QOI mesh/time UQ requirements, and
launch/admission guardrails. It remains a plan only: 0 sampling jobs and 0 F6 or
component-K admissions.
TODO-TWO-TAP-BLOCKER-ROADMAP then turned that contract into an ordered roadmap:
7 blocker/gate rows, 6 research paths, 7 next-step queue rows, and 7 admission
decision rules. The first executable follow-on remains a separate staged-copy
cfd-pp sampler; F6 and component-K admission stay explicitly separated.
TODO-TWO-TAP-STAGED-ENDPOINT-SAMPLER implemented that follow-on sampler package:
3 cases and 6 endpoint cut-plane surfaces are preflight-ready, exact raw-output
schemas and Slurm runner scripts are emitted, and the first concrete blocker is
now documented: the declared NCC endpoint patch names have zero boundary faces
in the reconstructed mesh, so raw sampling must use mesh-station VTK cutting
planes at `lower_leg__s04` and `right_leg__s00`. No sampling job, F6 fit, or
component-K admission was performed.
TODO-LITREV-MODEL-FORM-EXTRACTION-2026-07-21 adds the new-LitRev pressure/corner
dispatch package: pressure rises around corners must be classified as static
recovery, hydrostatic/kinetic basis, source-defined reduced-static coefficient,
section/cluster apparent effect, or unresolved residual before any K admission.
It preserves 0 current F6/component-K admissions.
TODO-LITREV-PRESSURE-CORNER-BASIS-RECOVERY then audits the current
pressure-increasing `corner_lower_right` candidates: all three Salt2/Salt3/Salt4
rows are labeled `section_effective`, with gross static pressure rise explained
as hydrostatic-dominated and the signed negative available residual preserved as
unadmitted pressure-recovery/recirculating-section diagnostic evidence. It
preserves 0 clipped-K, F6, global-multiplier, and component-K rows.
TODO-PRESSURE-CORNER-PUBLICATION-FREEZE-2026-07-21 freezes that result for
publication and future comparison: canonical result rows, stacked-bar figure
data, allowed/forbidden publication claims, and a methods note now live in a
single package. The next pressure work should compare against this freeze rather
than recomputing or rewording the finding from scratch.
TODO-PRESSURE-CORNER-SAME-QOI-SCIENTIFIC-SYNTHESIS-2026-07-21 then hardens the
handoff: what was tried, what worked, what did not, why it failed to admit
coefficients, and the efficient next sequence are now recorded in a single
synthesis package. Its default next executable row is the low-recirculation
anchor harvest, followed by same-QOI time/mesh inventory and raw F6 endpoint
sampling.
TODO-LITREV-LATEST-CFD-SCHEMA-PROMOTION refreshed that low-recirculation unlock
gate with read-only scheduler evidence: high-heat `CAND-001` jobs `3299610` and
`3299620` and corrected-Q continuation `3307441` are all still running, so
there are 0 terminal-ready source cases, 0 sampler releases, and 0 latest-schema
promotions. TODO-PRESSURE-CORNER-PAPER-RESULTS-SECTION completes the parallel
writing track from frozen evidence: paper methods/results/limitations, table
ledger, and caption text are ready for the diagnostic result while coefficient
language remains blocked.
TODO-F6-ENDPOINT-RAW-FACE-SAMPLER implements the F6 raw-face sampler unblock as
a scheduler-ready Stage A handoff: 8 Salt2 medium/fine endpoint-face rows are
ready for staged-copy sampling, 12 coarse endpoint-face rows remain blocked by
source-path/field evidence, and 0 raw sampled rows, F6 fits, component-K
admissions, clipped-K rows, or hidden multipliers exist.

## Trusted results
- **De-buoyed streamwise momentum budget.** Variable-density,
  buoyancy-corrected p_rgh gradients per span yield physical `f` only on fit-safe
  spans (left_lower_leg, left_upper_leg) / isothermal upcomer (~2–2.7);
  single-leg heated/cooled gradients give unphysical negative `f`. Loop closure
  shows minor losses ~30–43% of buoyancy head. →
  `work_products/2026-07/2026-07-01/2026-07-01_claude_momentum_budget/`
- **Pressure-term ledger (18 rows).** Separates p_rgh, dynamic/total-pressure
  proxy, density-gradient buoyancy, distributed loss, development/reset,
  minor/feature loss, recirculation-invalid regions, and residual; reproduces
  the July-1 de-buoyed budget with no double-counting. →
  `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/`
- **Bend/junction minor-loss K (two-tap).** Corner K_apparent 6.22–16.50;
  K_local upper bound 1.07–8.75 after straight-loss subtraction; test-section
  connector K undefined (recirculation). →
  `work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap/`,
  `work_products/2026-07/2026-07-01/2026-07-01_claude_bend_minor_loss/`
- **Metric lesson.** mdot is NOT a robust closure metric (±27%,
  condition-dependent); per-segment ΔP is robust; dominant 1D error is the
  thermal boundary, not hydraulic closures. →
  `reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/`

## Open / in-progress / blocked
- **~2× mdot discrepancy at matched-T with CFD friction** — OPEN. No validated
  mechanism; needs a term-by-term momentum reconciliation against the ledger. →
  `reports/2026-07/2026-07-02/2026-07-02_overnight_synthesis/`
- **Heated/cooled single-leg `f`** — cannot be extracted from single-leg p_rgh
  gradients (goes negative); only the isothermal upcomer `f` is trustworthy.
  Blocks per-leg friction calibration.
- **Test-section connector K** — undefined because the region recirculates;
  cannot be reduced to a single minor-loss coefficient.
- **Tap lengths** — several minor-loss rows use abs(dz) proxy lengths, so
  K_local values remain upper bounds until true centerline tap-to-tap lengths
  are supplied.
- **Pressure-basis and recovery for pressure-increasing corners** — OPEN. The
  new LitRev extraction requires pressure/velocity basis, hydrostatic and kinetic
  corrections, straight/developing subtraction, component isolation, recovery
  length, recirculation metrics, and same-QOI uncertainty before classifying a
  corner row as component `K`; otherwise use `section_K`, `cluster_K`, or
  residual assignment. →
  `work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/`

## Research avenues tried (outcome + provenance)
- **Single-leg de-buoyed p_rgh gradient → f** — PARTIAL. Works on fit-safe /
  isothermal spans (f ~2–2.7); FAILS (negative f) on heated/cooled legs. →
  `work_products/2026-07/2026-07-01/2026-07-01_claude_momentum_budget/`
- **Unified pressure-term ledger** — SUCCESS. Confirms no buoyancy
  double-counting; development_loss is 20–40% of distributed friction on short
  entry spans, minor_loss 5–15% on spans with bends. →
  `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/`
- **Two-tap minor-loss separation (NIST-style)** — SUCCESS as upper bound;
  local dynamic-pressure normalization overestimates true bend loss. →
  `work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap/`,
  `work_products/2026-07/2026-07-08/2026-07-08_minor_loss_separation/`
- **mdot as validation metric** — REJECTED as primary metric; switched to
  per-segment ΔP. →
  `reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/`
- **Lit-rev named-loss reset framing** — apply hydrostatic + kinetic +
  straight-pipe corrections BEFORE extracting f_D or K; name section losses as
  straight / component-K / cluster-K / branch-apparent; do NOT collapse into one
  global friction multiplier. →
  `work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/`
- **H1 hydraulic scorecard** — bounded proxy screen. `F1_heater_only` mean mdot
  error falls by 60.29% without thermal fitting, enough to refresh forward-v1
  scorecard diagnostics but not enough to admit a final localized H1 closure. →
  `work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/`
- **val_salt2 pressure and corner-K diagnosis** — SUCCESS as blocker
  explanation, not as admission. The pressure map is external-test diagnostic
  evidence; six branch rows have zero ordinary `f_D`/`K` fit-admitted entries.
  Twelve corner rows remain zero fit-admitted because centerline straight-loss
  subtraction makes all local K values negative and the rows also fail
  recirculation, pressure-basis, mesh/GCI, and component-isolation gates. →
  `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis/`
- **Named pressure extraction readiness** — SUCCESS as next-work queue, not as
  coefficient admission. Current named pressure evidence has 0 fit-ready rows;
  the next implementable lanes are two-tap/component repair, pressure/velocity
  basis finalization, recirculation masking, same-QOI mesh/time uncertainty, and
  reset-development Fluid API contract. →
  `work_products/2026-07/2026-07-17/2026-07-17_named_pressure_extraction_readiness/`
- **Two-tap component repair contract** — SUCCESS as an extractor contract, not
  as component-K admission. The nearest target rows are the three
  `corner_lower_right` Salt2/3/4 rows; centerline lengths exist, but current
  centerline straight-reference subtraction makes K negative, so a future
  extractor must repair basis, reference, isolation, reverse-flow masks, and
  same-QOI UQ before scoring. →
  `work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract/`
- **Two-tap component repair extractor** — SUCCESS as schema implementation,
  not as coefficient admission. It emits 3 `corner_lower_right` rows with
  supported preserved fields and explicitly blank endpoint-pressure,
  RAF/RMF/SVF, and uncertainty fields where evidence is missing. All 15
  predeclared gate rows fail, yielding the next raw postprocessing queue. →
  `work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/`
- **Two-tap raw endpoint plan** — SUCCESS as a sampling contract, not as raw
  evidence or coefficient admission. It converts the AGENT-530 queue into exact
  pressure/velocity/recirculation/UQ requirements for Salt2/Salt3/Salt4
  `corner_lower_right`, with upstream `lower_leg__s04`, downstream
  `right_leg__s00`, time windows `7915/7618/10000`, required `p`, `p_rgh`,
  `U`, `T_or_rho`, flux/area/normal fields, RAF/RMF/SVF definitions, same-QOI
  UQ contract, and explicit F6/component-K separation. →
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/`
- **Two-tap blocker roadmap** — SUCCESS as a blocker/research/next-step handoff,
  not as raw evidence or coefficient admission. It represents all 7 raw-endpoint
  launch/admission gates, maps them to staged sampling, pressure-basis audit,
  straight-reference/component-isolation audit, recirculation metrics, same-QOI
  UQ, and separated admission/F6 governance, and orders the next 7 implementable
  steps. →
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap/`
- **Two-tap staged endpoint sampler** — SUCCESS as an executable sampler and
  raw-evidence package, not as coefficient admission. It
  validates Salt2/Salt3/Salt4 exact times and fields, records that direct NCC
  patch sampling is empty (`nFaces=0`), emits mesh-station VTK cutting-plane
  scripts and a strict harvest parser, and now contains six harvested raw
  pressure/velocity/recirculation endpoint rows. →
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/`
- **Two-tap endpoint resubmit/harvest** — SUCCESS as raw endpoint harvest, not
  as pressure-basis audit, F6 fit, or component-K admission. Resubmission job
  `3302464` wrote all six staged VTK surfaces; the batch exited `1:0` only
  because the old in-job parser could not read wrapped OpenFOAM VTK
  `POLYGONS`/`FIELD` output. The parser was fixed and local harvest produced
  six sampled rows in `raw_endpoint_pressure_velocity.csv`; next task is
  pressure/velocity basis audit. →
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/RUNNING.md`
- **Two-tap pressure/basis recirculation audit** — SUCCESS as a basis audit and
  blocker clarification, not as coefficient admission. Static-p, `p_rgh`,
  hydrostatic, kinetic, density, velocity, and local dynamic-pressure terms are
  finite for all three `corner_lower_right` pairs, but all fail ordinary
  recirculation (`aggregate_RAF≈0.763`, `aggregate_RMF≈0.500`), so the rows
  remain diagnostic/section-effective and cannot feed F6 or component-K
  admission. →
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/`
- **Two-tap remaining gates and anchor request** — SUCCESS as a full
  non-admission closeout sequence. Component isolation routes all three rows to
  `apparent_cluster_only`; same-QOI UQ is `missing_no_GCI_diagnostic_only`;
  separated admission review keeps all rows diagnostic only; and the
  non-recirculating-anchor package defines future evidence requirements without
  launching work. →
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_separated_admission_review/`
- **Two-tap next context handoff** — SUCCESS as the human start-here for the
  next two-tap task. It records the open-first file list, trusted packages,
  active blockers, assumption register, non-recirculating-anchor sequence, and
  guardrails that keep current rows out of F6/component-K admission. →
  `operational_notes/07-26/18/2026-07-18_TWO_TAP_NEXT_CONTEXT_AND_STEPS.md`
- **F6 legwise pressure-anchor plan** — SUCCESS as a gate-carryforward and
  source/property-labeled contract, not as F6 fitting or admission. It separates
  ordinary straight-leg candidates, non-upcomer reverse-flow diagnostics,
  component/junction rows, and an explicit upcomer recirculation-modeled lane.
  The current contract has 36 leg/slot rows, 3 finite raw endpoint feature
  pairs, 3 finite endpoint pairs blocked by material reverse flow, and 0
  ordinary F6/admission-review eligible rows; any future review must compare
  against `F3_shah_apparent` without a hidden global multiplier. →
  `work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan/`
- **Two-tap non-recirculating anchor plan** — SUCCESS as a planning-only next
  step, not as a sampler, launch, F6 fit, or component-K admission. It evaluates
  `NR-CLR-01` and `NR-ALT-01`, selects Salt4 high-heat/no-recirculation probes
  as the preferred conditional same-topology `corner_lower_right` lane after
  terminal review, keeps current Salt2/Salt3/Salt4 endpoint rows diagnostic,
  and records `no_launch_from_this_row`. →
  `work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/`
- **F6/two-tap non-recirculating staging** — SUCCESS as an AGENT-560 staging
  handoff, still not as a sampler, launch, F6 fit, or component-K admission.
  It preserves `CAND-001` as the preferred conditional Salt4 high-heat/no-
  recirculation `corner_lower_right` source family, but requires terminal
  source cases, a separately claimed staged-copy sampler row, finite endpoint
  fields, aggregate `RAF < 0.01` and `RMF < 0.01`, and same-QOI UQ before any
  ordinary-flow review. →
  `work_products/2026-07/2026-07-20/2026-07-20_f6_two_tap_nonrecirc_staging/`
- **Two-tap recirculating section-effective pressure model** — SUCCESS as a
  model-form and paper-dossier package, not as coefficient admission. It
  reframes the current `corner_lower_right` rows as recirculating
  section-effective pressure-residual evidence: static apparent `K` is
  hydrostatic/buoyancy dominated, `p_rgh` residuals are diagnostic, reverse
  flow remains material, component isolation remains `apparent_cluster_only`,
  and same-QOI UQ remains missing. It emits a residual contract,
  current-row table, UQ sampling contract, paper claim/limitation ledger,
  artifact crosswalk, figure/table manifest, and paper methods/results notes.
  Ordinary `component_K`, F6 promotion, hidden multipliers, and scheduler launch
  remain forbidden. →
  `work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/`
- **Two-tap recirculating residual scorer** — SUCCESS as a diagnostic scorer
  and lower-apparent-K explanation, not as coefficient admission. It shows the
  lower static apparent `K` trend is driven by dynamic-pressure denominator
  growth while the static pressure drop remains hydrostatic/buoyancy dominated;
  it also audits raw endpoint normal flux and marks throughflow `q_ref`
  untrusted until a single-leg orientation/masking audit proves the denominator.
  Current rows remain `diagnostic_only_no_fit_no_admission`; the next useful
  extraction is face-level positive/negative mass flux plus same-QOI residual
  UQ and a separate non-recirculating anchor. →
  `work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/`
- **LitRev pressure-corner basis/recovery audit** — SUCCESS as a sign-safe
  decomposition and label audit, not as coefficient admission. It decomposes the
  current pressure-increasing `corner_lower_right` rows into gross static,
  hydrostatic, kinetic, blocked straight/developing, pressure-recovery
  candidate, and available residual terms. Result: 3/3 rows are
  `section_effective`; hydrostatic head explains the gross static rise; the
  negative available residual is preserved with sign as pressure-recovery /
  recirculating-section diagnostic evidence; 0 clipped-K, F6, global-multiplier,
  or component-K rows. →
  `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/`
- **Pressure-corner publication freeze** — SUCCESS as the canonical comparison
  and writing package for the July 21 finding. It publishes frozen result rows,
  figure data, methods wording, and allowed/forbidden claim ledgers. Result:
  3/3 `section_effective`, 0 component-K, 0 F6, 0 clipped-K, 0 global multiplier.
  Future pressure-plane, UQ, recirculation, low-recirculation-anchor, and
  admission-review rows should cite this package as the benchmark. →
  `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/`
- **Pressure-corner same-QOI scientific synthesis** — SUCCESS as the current
  start-here for efficient continuation, not as admission. It records 5
  attempt/outcome rows, 7 blocker rows, and a 6-step next-evidence sequence.
  Result: the lower-right corner remains `section_effective`/diagnostic;
  0 component-K, cluster-K, F6-fit, clipped-K, or global-multiplier rows. The
  next executable row is low-recirculation anchor preflight/harvest. →
  `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_same_qoi_scientific_synthesis/`
- **Latest CFD schema-promotion terminal refresh** — SUCCESS as a gate refresh,
  not as harvest or admission. Read-only scheduler evidence shows high-heat
  `CAND-001` jobs `3299610`/`3299620` and corrected-Q continuation `3307441`
  still running; 0 terminal-ready cases, 0 sampler releases, and 0 latest-schema
  promotions. PM10 terminal evidence remains context, but the newer `3307441`
  continuation supersedes it for latest corrected-Q schema promotion once
  terminal. →
  `work_products/2026-07/2026-07-21/2026-07-21_litrev_latest_cfd_schema_promotion/`
- **Pressure-corner paper results section** — SUCCESS as manuscript-facing text,
  not as coefficient admission. It publishes methods, results, limitations,
  table-ready claim ledger, and caption text for the frozen diagnostic result:
  3/3 `section_effective`, 0 component-K, 0 cluster-K, 0 F6, 0 clipped-K, and
  0 global multiplier. →
  `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_paper_results_section/`
- **Two-tap face-level q_ref and UQ progress** — SUCCESS as a face-flux
  extraction/audit from already harvested VTK surfaces, not as coefficient
  admission. It parses six `corner_lower_right` endpoint surfaces, computes
  face-level positive/negative/absolute mass flux and `q_ref` diagnostics, and
  confirms the endpoint evidence still has material reverse flow. Same-QOI
  residual UQ remains missing, component isolation remains blocked, and current
  rows stay diagnostic-only for pressure, F6, and two-tap component `K`. →
  `work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/`
- **Pressure/F6/two-tap blocker unlock next steps** — SUCCESS as an
  implementation-ready handoff, not as admission. It converts the current
  reverse-flow, component-isolation, same-QOI UQ, and F6 blockers into two
  evidence lanes: future `CAND-001` same-topology low-reverse endpoint sampling
  for ordinary `K`, and a separate recirculating section-effective
  pressure-residual model lane for lower apparent `K`. Current blockers remain
  open, no scheduler launch is allowed from the package, and no F6/component-K
  admission is performed. →
  `work_products/2026-07/2026-07-20/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps/`
- **F6 non-upcomer branch modeling analysis** — SUCCESS as an ordinary-branch
  candidate screen, not as F6 fitting or admission. It reviews the 36-row F6
  legwise inventory, selects Salt2/Salt3/Salt4 `right_leg` and
  `test_section_span` as the six future ordinary candidates, excludes upcomer,
  corners, junctions, component/cluster rows, and material-reverse-flow rows
  from ordinary single-stream F6, and emits downcomer/right-leg plus
  test-section sampling contracts. All six candidates remain not fit-ready until
  endpoint pairs and same-QOI UQ land. →
  `work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/`
- **F6 endpoint raw-face sampler unblock** — SUCCESS as a Stage A sampler
  handoff, not as raw sampled evidence, F6 fitting, or admission. The package
  repairs the preflight split, emits eight Salt2 medium/fine endpoint-face rows
  for future compute-node staged-copy sampling, preserves twelve coarse
  endpoint-face rows as blocked until source-path repair proves retained times
  and required fields, and writes harvest/gate schemas with 0 sampled rows, 0
  F6 fits, 0 component-K admissions, 0 clipped-K rows, and 0 hidden
  multipliers. →
  `work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/`
- **Negative-K section-effective thesis case dispatch** — SUCCESS as the
  current start-here for the lower-right corner negative-result route, not as
  coefficient admission. It consolidates the LitRev pressure-basis rule, basis
  recovery audit, publication freeze, and section-effective hybrid scorecard
  into one thesis-facing case: stop current component-K attempts, preserve the
  signed negative residual, publish the result as section-effective pressure
  evidence, and use it to motivate `Delta_p_recirc_section`. The rerun
  scorecard evidence remains diagnostic only: Salt2/Salt3/Salt4 residuals
  `-1.25366731683/-1.84957005859/-1.67833900273 Pa`, Salt2-frozen transfer max
  error `0.47046606946166093438399 Pa`, and 0 component-K, cluster-K, F6,
  clipped-K, hidden-multiplier, validation, holdout, or external-test rows. →
  `work_products/2026-07/2026-07-21/2026-07-21_negative_k_section_effective_thesis_case_dispatch/`

## Key artifacts (canonical)
- Momentum-budget output (de-buoyed f per span): `work_products/2026-07/2026-07-01/2026-07-01_claude_momentum_budget/`
- Budget tool: `tools/analyze/derive_streamwise_momentum_budget.py`
- Pressure-term ledger (18 rows): `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/`
- Two-tap minor-loss K: `work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap/`
- Bend minor-loss (July-1 source): `work_products/2026-07/2026-07-01/2026-07-01_claude_bend_minor_loss/`
- H1 hydraulic scorecard: `work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/`
- Segment arc lengths (mesh PCA): `work_products/2026-07/2026-07-01/2026-07-01_claude_segment_friction/`
- Metric lesson / model-form comparison: `reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/`
- ~2× discrepancy synthesis: `reports/2026-07/2026-07-02/2026-07-02_overnight_synthesis/`
- Named-loss reset framing: `work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/`
- val_salt2 pressure/corner-K diagnosis: `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis/`
- Named pressure extraction readiness: `work_products/2026-07/2026-07-17/2026-07-17_named_pressure_extraction_readiness/`
- Two-tap component repair contract: `work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract/`
- Two-tap component repair extractor: `work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/`
- Two-tap raw endpoint plan: `work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/`
- Two-tap blocker roadmap: `work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap/`
- Two-tap staged endpoint sampler: `work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/`
- Two-tap endpoint launch handoff: `work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/RUNNING.md`
- Two-tap pressure/basis recirculation audit: `work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/`
- Two-tap component isolation decision: `work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_isolation_decision/`
- Two-tap same-QOI UQ status: `work_products/2026-07/2026-07-18/2026-07-18_two_tap_same_qoi_uq_status/`
- Two-tap separated admission review: `work_products/2026-07/2026-07-18/2026-07-18_two_tap_separated_admission_review/`
- Two-tap non-recirculating anchor request: `work_products/2026-07/2026-07-18/2026-07-18_two_tap_nonrecirc_anchor_request/`
- F6 legwise pressure-anchor plan: `work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan/`
- Two-tap non-recirculating anchor plan: `work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/`
- Two-tap recirculating section-effective pressure model: `work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/`
- Two-tap recirculating residual scorer: `work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/`
- Two-tap face-level q_ref and UQ progress: `work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/`
- Pressure-corner publication freeze: `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/`
- Pressure-corner same-QOI scientific synthesis: `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_same_qoi_scientific_synthesis/`
- LitRev latest CFD schema promotion: `work_products/2026-07/2026-07-21/2026-07-21_litrev_latest_cfd_schema_promotion/`
- Pressure-corner paper results section: `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_paper_results_section/`
- Pressure/F6/two-tap blocker unlock next steps: `work_products/2026-07/2026-07-20/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps/`
- F6 non-upcomer branch modeling analysis: `work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/`
- F6 endpoint raw-face sampler unblock: `work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/`
- Negative-K section-effective thesis case dispatch: `work_products/2026-07/2026-07-21/2026-07-21_negative_k_section_effective_thesis_case_dispatch/`

## Related
- `operational_notes/maps/README.md` — MOC index
- `operational_notes/maps/friction-closures.md` — consumes the de-buoyed f
- `operational_notes/maps/geometry-and-mesh-truth.md` — arc lengths, lower↔right
  probe-CSV swap (probe CSV is a schematic; use mesh PCA geometry)
