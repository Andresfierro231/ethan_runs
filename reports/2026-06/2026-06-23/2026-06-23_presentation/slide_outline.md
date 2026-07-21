# Presentation Slide Outline

Date: `2026-06-23`

This outline is slide-first. Each slide lists the claim, the staged local
figure for deck assembly, whether that figure now exists inside the
presentation package, whether the supporting analysis is done yet, and short
speaker notes. Canonical source paths and assumptions live in:

- `reports/2026-06-23_presentation/figures/figure_manifest.csv`
- focused 1D subsection:
  `reports/2026-06-23_presentation/1d_model_slide_sequence.md`
- presentation-local 1D tables:
  `reports/2026-06-23_presentation/1d_model_results_tables.md`
- presentation-local 1D setup note:
  `reports/2026-06-23_presentation/1d_model_setup_documentation.md`

2026-06-30 refresh: Kirst-named figures remain in the package as legacy support
figures only. Do not present them as current mainline references; use
continuation/latest-window Jin evidence for current primary claims when it is
available.

## Slide 1: Title And Question

- Title: `How Predictive Is The Current CFD-Informed 1D Loop Model?`
- Bullets:
  - We now have a reusable 3D evidence stack for pressure loss, heat loss, and
    bounded closure extraction along the loop.
  - The main test is no longer whether we can write down closures at all.
  - The main test is whether those closures actually predict frozen-state CFD
    and experiment with acceptable error.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/01_title_salt_dashboard_overview.png`
- Figure status: `exists`
- Analysis status: `done`
- Speaker notes:
  - Open with the framing that this week’s gain is an evidence chain, not just
    a prettier plot set.
  - Say explicitly that Salt and Water still remain separate families.

## Slide 2: What We Can Quantify Along The Loop Today

- Bullets:
  - We now quantify streamwise heat loss, azimuthal thermal redistribution, and
    bounded pressure-loss behavior on the repaired branches.
  - The analysis stack is strong enough to localize where losses accumulate and
    where support becomes weak.
  - This is a 3D interpretation backbone, not yet a universal reduced-order
    closure.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/02_loop_heat_loss_comparison.png`
- Figure status: `exists`
- Analysis status: `done`
- Speaker notes:
  - Emphasize that the loop is no longer only a monitor-level object.
  - This figure stays on the completed June 15 campaign path rather than the
    still-active Salt heat-loss breakout lane.

## Slide 3: Pressure Losses Are Quantified, But Only On Bounded Support

- Bullets:
  - Straight-section pressure closure is now quantified from hydro-corrected
    pressure plus buoyancy terms.
  - Repaired straight spans are the strongest hydraulic evidence lane.
  - Feature and branch claims remain narrower than straight-span claims.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/03_bounded_pressure_closure.png`
- Figure status: `exists`
- Analysis status: `done`
- Speaker notes:
  - Make the distinction between direct wall-registered pressure and derived
    apparent friction explicit.
  - The point is not that every branch is solved, but that the straight-lane
    hydraulic closure path is now defensible enough to use conditionally.

## Slide 4: `p_rgh` Is Not Dynamic Pressure

- Bullets:
  - The workspace now separates hydrostatic-corrected pressure `p_rgh` from
    true bulk dynamic pressure `q_dyn = 0.5 rho U^2`.
  - This matters because developing or redeveloping flow changes how pressure
    and velocity-based surrogates should be interpreted.
  - It keeps us from overclaiming that a `p_rgh` profile is itself a dynamic
    loss profile.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/04_prgh_vs_qdyn_salt2_kirst.png`
- Figure status: `exists`
- Analysis status: `done`
- Speaker notes:
  - Use this as a legacy support figure for the `p_rgh` / `q_dyn` distinction,
    not as a current mainline Salt reference.
  - This slide is now better than the older dynamic-only figure because it
    puts the two quantities on the same legwise picture directly.

## Slide 5: Major And Minor Friction Extrapolation Is Partly Ready

- Bullets:
  - Salt straight-section friction is now provisionally defended on a bounded
    Reynolds range and branch class.
  - Feature `K_eff` has been reopened only on a bounded patch-endpoint basis.
  - Current retained feature coverage is `21` fit-used rows out of `45`, with
    `24` rows still excluded by nonpositive path feature excess.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/05_salt_hydraulic_agreement.png`
- Figure status: `exists`
- Analysis status: `partial`
- Speaker notes:
  - Say that “partial” here means the straight lane is usable, while feature
    and cross-family generalization are still limited.
  - If you want the feature story explicitly, cite the reopened provisional
    `K_eff` status rather than calling it solved.

## Slide 6: Internal HTC / Thermal Closures Are Strongest On A Safe Subset

- Bullets:
  - `UA'(x)` is the primary admitted thermal surface on the safe subset.
  - `HTC(x)` is secondary on the same subset.
  - Direct fitted `Nu(Re)` is currently defended only on `left_lower_leg`.
  - `right_leg` and derived `upcomer` remain different closure problems.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/06_salt_branch_usability.png`
- Figure status: `exists`
- Analysis status: `partial`
- Speaker notes:
  - This is where to explain why “we have internal HTC information” is true,
    but only in a bounded sense.
  - Avoid language that implies loop-wide direct `Nu` closure readiness.

## Slide 7: Current Correlation Inventory

- Bullets:
  - Admitted now:
    straight friction fit, `UA'(x)` safe-subset surfaces, secondary `HTC(x)`,
    direct `Nu(Re)` only on `left_lower_leg`, readable fixed cooler `Q`.
  - Comparison only:
    `64 / Re`, Shah redevelopment, Muzychka / Yovanovich entry-`Nu`, local
    loss placeholders.
  - Blocked or provisional:
    Water-family fits, direct `Nu` on `right_leg`, direct `Nu` on derived
    `upcomer`, fully defended feature-volume `K_eff`.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/07_salt_heat_loss_partition.png`
- Figure status: `exists`
- Analysis status: `done`
- Speaker notes:
  - This slide is really the closure-menu slide.
  - The heat-loss partition figure works here because it reminds the audience
    that thermal closure disagreement is still entangled with external losses.

## Slide 8: The Main Result: Current 1D Predictiveness Is Still Poor

- Bullets:
  - We now have a local frozen-CFD-vs-readable-1D scorecard against the June
    22 Salt frozen-state contract plus a bounded presentation-facing bakeoff
    package.
  - Best full-coverage readable scenario:
    `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`.
  - Even that best full-coverage row still misses badly:
    `11.27%` heater-normalized energy error,
    `62.79 K` wall-temperature RMSE,
    `62.69 K` centerline-temperature RMSE,
    `26.69%` mass-flow error.
  - Legacy strict-subset breakdown for that same defended row:
    `Salt 1 Kirst = 16.01% / 65.31 K / 65.24 K / 25.45%`,
    `Salt 2 Kirst = 8.92% / 64.65 K / 64.78 K / 34.41%`,
    `Salt 2 Val = 8.89% / 58.40 K / 58.05 K / 20.21%`
    for `energy / TW RMSE / TP RMSE / mass-flow`.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/08_primary_scenario_metric_heatmap.png`
- Figure status: `exists`
- Analysis status: `done`
- Speaker notes:
  - This is the slide to slow down on.
  - The mean row is useful, but this legacy case split should be described as
    stale support, not the current mainline run set:
    `Salt 1 Kirst` is the worst energy case,
    `Salt 2 Kirst` is the worst mass-flow case,
    and `Salt 2 Val` is the least-bad overall case.
  - The important message is not “1D is useless.”
  - The important message is “the current defended closure bundle is still not
    sufficiently predictive, and now we know by how much.”

## Slide 9: Why The 1D Still Misses

- Bullets:
  - The hybrid/profile-descriptor family is still under-covered on the primary
    frozen set, so it cannot yet be defended as the global winner.
  - Hybrid improves one metric lane only partially:
    best hybrid mean mass-flow error is `19.55%`, but that row has only `1`
    primary comparison case and does not beat the defended baseline on
    temperature.
  - The strongest direct thermal evidence is still only `left_lower_leg`.
  - `upcomer`, `right_leg`, and feature losses still need different treatment
    than the current straight-plus-safe-subset bundle provides.
  - The current readable external replay is also stale relative to the June 22
    closure refresh.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/09_primary_branch_development.png`
- Figure status: `exists`
- Analysis status: `partial`
- Speaker notes:
  - “Partial” here means the error pattern is measured, but the causal
    decomposition by closure family is not yet fully scored.
  - Call out that the upper-side and loop-start probes stay among the worst
    misses.

## Slide 10: What Is Done Versus What Still Needs The Next Hour

- Bullets:
  - Done now:
    local frozen-state 1D scorecard, bounded presentation-facing bakeoff,
    bounded straight-friction support, bounded thermal safe subset,
    and `p_rgh` / `q_dyn` clarification.
  - Current defended full-coverage winner is still the baseline
    `1.0 in` radiation-on row; hybrid rows remain under-covered rather than
    globally preferred.
  - We now know the current failure shape, not just the mean:
    all three primary Salt references stay around `58-65 K` sensor RMSE, while
    energy error splits into one worse `Salt 1` row and two less-bad `Salt 2`
    rows.
  - Still not done:
    the refreshed external `Fluid` replay against the June 22 closure surface.
  - Still future after that replay:
    the broader admitted-versus-comparison correlation bakeoff.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/10_current_1d_gap_summary.png`
- Figure status: `exists`
- Analysis status: `done`
- Speaker notes:
  - Be explicit that the missing item is now the external replay, not the
    local bakeoff.
  - This slide should leave the audience with one clear boundary:
    today’s local negative result is real, but the external refreshed replay
    still has to land before broader 1D closure changes are judged.

## Backup Slide A: Representative Mechanism Comparison

- Bullets:
  - Use this if you need one detailed transport-mechanism picture.
  - It shows the friction and pressure redistribution story on the matched Salt
    representative case.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/A_representative_friction_and_pressure.png`
- Figure status: `exists`
- Analysis status: `done`
- Speaker notes:
  - Good answer if someone asks for a concrete case-level mechanism figure.

## Backup Slide B: Sensor Parity For The Current Best 1D Row

- Bullets:
  - This is the most concrete view of how the current best full-coverage 1D row
    misses the frozen-state CFD sensor field.
  - It is useful if the audience wants the predictive gap shown as actual
    parity, not just summarized metrics.
  - Use it to show that the aggregate miss is broad-field, not one single bad
    probe.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/B_primary_best_sensor_parity.png`
- Figure status: `exists`
- Analysis status: `done`
- Speaker notes:
  - Use this if someone challenges whether the aggregate RMSE numbers hide a
    few bad probes or a broadly wrong field.
  - The current worst recurring examples remain `TP3`, `TP4`, `TP5` on the
    probe side and `TW9`, `TW10`, `TW6` on the wall side.

## Backup Slide C: Legacy Salt 2 Kirst Redevelopment Follow-On

- Bullets:
  - This is the straight-leg redevelopment picture that puts
    `p_rgh(s)`, `q_dyn(s)`, and streamwise wall heat loss `q'(s)` on one
    retained-time case view.
  - It is useful if the audience asks how developing flow and heat loss fit
    into the current bounded straight-friction story.
  - It also keeps the bend/corner limitation explicit:
    endpoint-path feature screening is usable, but full interior feature-path
    closure is still not solved.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/C_salt2_kirst_redevelopment_followon.png`
- Figure status: `exists`
- Analysis status: `done`
- Speaker notes:
  - Use this when someone asks whether the repo now directly measures where
    fully developed assumptions break down.
  - Label it as a legacy mechanism/support view; it should not be used as the
    current primary Salt 2 reference.
  - The safe answer is yes for the straight-leg redevelopment picture, but no
    for a full universal feature-volume closure.

## Backup Slide D: Salt 1-4 Metric Cards

- Bullets:
  - This is the fastest case-by-case view of how the defended 1D row behaves
    across the readable Salt `1-4` progression.
  - It uses the `Jin` progression intentionally, because that is the only
    current readable four-case family span on one consistent defended
    scenario.
  - Use it if the audience asks whether the current miss grows monotonically
    with Salt number or if one metric lane behaves differently than the others.
- Figure:
  - `reports/2026-06-23_presentation/figures/png/D_salt1to4_metric_cards.png`
- Figure status: `exists after figure-pack refresh`
- Analysis status: `done`
- Speaker notes:
  - Energy error on this slide is heater-normalized total-loss mismatch, not a
    separate global residual definition.
  - The useful pattern is that temperature and mass-flow miss generally worsen
    from Salt `1` to Salt `4`, while energy mismatch stays in the same broad
    `8-16%` band.

## Focused 1D Section

If the deck needs a tighter modeling-only subsection instead of the broader
ten-slide story, use:

1. `reports/2026-06-23_presentation/1d_model_slide_sequence.md`
2. `reports/2026-06-23_presentation/1d_model_results_tables.md`
3. `reports/2026-06-23_presentation/1d_model_setup_documentation.md`
