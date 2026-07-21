# CFD Postprocessing / Closure Rigor Deep Dive

Date: `2026-07-07`
Role: Coordinator / Writer
Task: `AGENT-188` strengthening pass applied `2026-07-07`

## Executive Assessment

The major unlock is not one more fitted coefficient. The major unlock is a
clean observation-to-closure contract that separates:

1. what the 3D CFD directly shows;
2. what can be reduced into a physically meaningful 1D term;
3. what is only an apparent/residual diagnostic;
4. what still needs more CFD, mesh uncertainty, or literature support.

The current stack is now good enough to produce a coherent Salt-only picture:
mesh-derived geometry, section-mean pressure, enthalpy-flux thermal quantities,
per-leg friction multipliers, bend/minor-loss screens, upcomer recirculation
metrics, and run-status gates exist. It is not yet good enough to claim broad
portable correlations. The strongest near-term scientific product is a rigorous
CFD-informed decomposition and model-form comparison, not a universal `f(Re)`
or `Nu(Re)` law.

## Non-Negotiable Operational Contract

This section is the hard guardrail for all downstream pressure-drop, friction,
and thermal-driver work. If a later script or model form cannot satisfy these
conditions, it must write `fit_admissible=no` and explain why.

### A. No Buoyancy Double Counting

The 1D model already carries the reversible buoyancy driving head separately in
`buoyancy_pressure()`. Therefore:

- a friction closure must not add a second buoyancy force or pressure head;
- F4 / mixed-convection friction may only modify the irreversible mechanical
  resistance or effective wall-shear term;
- any F4 implementation must state whether its target is:
  - de-buoyed Darcy friction, `f_corrected`, from the CFD momentum budget;
  - a residual multiplier relative to F1/F3;
  - or a purely diagnostic apparent resistance.

The preferred F4 target is the de-buoyed CFD momentum-budget quantity in
`work_products/2026-07-01_claude_momentum_budget/momentum_budget.json` and
`.csv`, not the raw signed apparent-friction rows in
`work_products/2026-07-01_claude_segment_friction/segment_friction.csv`. The
raw signed rows are useful diagnostics, but rows carrying pressure-recovery or
negative-apparent-friction flags must not be used as Darcy-friction fit targets.

### B. Pressure Ledger Before Closure Claims

No new closure-grade pressure claim should be made from raw `p_rgh` slopes alone.
The required object is a loop-station / span ledger that explicitly decomposes
observed pressure behavior into:

- static / modified pressure: `p`, `p_rgh`;
- dynamic head: `0.5*rho*u^2`;
- total pressure proxy: `p + 0.5*rho*u^2`;
- density-gradient buoyancy contribution;
- distributed mechanical loss;
- entrance / redevelopment contribution;
- local feature / minor-loss contribution;
- recirculation or invalid-single-stream flags;
- residual / unmodeled term.

For straight spans, the starting balance is the flow-direction-projected
section-mean form already used by the July 1 momentum budget:

```text
friction_loss_per_length
  = -d(p_rgh)/dxi - gh * d(rho)/dxi - rho*u*du/dxi
```

where `xi` is the measured flow direction, not necessarily loop-order `s`. The
ledger must carry all terms, sign conventions, station endpoints, and quality
flags; it must not collapse them into one apparent `f` column without the
intermediate terms.

### C. Admission And Gate Policy

Rows may enter closure fitting only when all admission conditions are explicit
and satisfied:

- `run_class=mainline_continuation` or a named sensitivity/perturbation class;
- `operating_point_verdict=requalified` for corrected perturbations;
- `closure_fit_admissible=yes`;
- `needs_special_gate_scrutiny=False`;
- no unresolved coordinator-review flag;
- source fields, time window, geometry source, and extraction method recorded.

Corrected Salt Q rows remain excluded until the formal gate emits
`operating_point_verdict=requalified`. For corrected Salt Q specifically, any row
with `needs_special_gate_scrutiny=True` is held even if another column appears
favorable. No flagged row is closure-fit admissible without coordinator review.

### D. Current F4 Status Must Be Named Precisely

As of the AGENT-187 pass, `F4_leg_class` exists in the Fluid friction closure
library. It is an admitted-data, leg-class OLS multiplier fitted from mainline
Salt 2/3/4 de-buoyed momentum-budget rows. It is useful as a pressure-resistance
model-form comparison.

It is not yet a Richardson-number mixed-convection friction law. The Ri-corrected
F4 remains a separate future task because wall-bulk `Delta T`, median section
Ri, and streamwise gravity projection still need to be assembled and audited.

### E. Richardson-Number Convention

Any Ri-based friction or heat-transfer fit must record the exact definition. The
current project convention is:

- use section median Ri where field-derived Ri is available; do not use mean Ri
  as the characteristic value because low-velocity cells can dominate it;
- for inclined spans, carry a streamwise projection such as
  `Ri_streamwise = Ri_median * cos(theta_from_gravity)` or the equivalent signed
  gravity-projection convention, with the angle source recorded;
- record the `Delta T` basis, property basis, length scale, and temperature at
  which properties were evaluated;
- do not mix field-output Ri and reconstructed wall-bulk Ri in one fit without a
  conversion/audit column.

## Thermal-Driver Caveat For Journal-Grade Interpretation

The July 2 driver-side diagnostic is a major scientific caveat for any
mass-flow-rate claim. The relevant provenance is:

- `.agent/journal/2026-07-02/driver-side-thermal-overheat-finding.md`;
- `work_products/2026-07-02_overnight/driver_thermal_compare.py`;
- `work_products/2026-07-02_overnight/driver_thermal_compare.json`.

That diagnostic solved the 1D model with per-leg CFD friction multipliers under
`predictive_airside_ins_1.0in_rad_1` and compared Salt 2/3/4 loop temperatures
against CFD bulk-temperature references. The raw result was:

| Case | Source | `mdot` kg/s | Main Re | Mean T K | Loop `Delta T` K |
| --- | --- | ---: | ---: | ---: | ---: |
| Salt 2 | CFD | 0.01318 | 68 | 450.3 | 12.1 |
| Salt 2 | 1D | 0.011896 | 154.3 | 512.25 | 8.19 |
| Salt 3 | CFD | 0.01497 | 88 | 463.7 | 12.2 |
| Salt 3 | 1D | 0.013500 | 211.4 | 527.40 | 8.29 |
| Salt 4 | CFD | 0.01698 | 120 | 479.2 | 12.3 |
| Salt 4 | 1D | 0.015242 | 285.9 | 545.40 | 8.58 |

Raw observation: under that scenario, the 1D loop was about `62-66 K` hotter
than the CFD reference and had a smaller loop `Delta T` despite using CFD-informed
per-leg friction. Interpretation: the residual mass-flow/Re discrepancy cannot
be assigned only to hydraulic friction closures. The model's thermal driver,
heat-loss path, ambient/cooler contract, or scenario matching may be contributing
first-order error. This caveat must accompany any statement that a new friction
form "improves" or "does not improve" mass-flow predictivity.

Journal-grade statement boundary:

- It is defensible to say that CFD-informed friction improves the pressure-loss
  distribution it is calibrated to.
- It is not defensible to claim a portable hydraulic correlation from mdot error
  alone while the thermal state is mismatched by roughly `60 K`.
- Before using mdot as the primary validation metric for a friction model, rerun
  the comparison with case-matched heater power, cooler/ambient boundary
  conditions, insulation/radiation settings, and a heat-source/sink ledger.

## Salt 1 Qualification Assessment

Salt 1 should remain provisional for closure fitting. It is not simply "bad" or
"far from steady" in every metric, but it is weaker than Salt 2/3/4 and needs a
dedicated qualification pass before it becomes normal training data.

Observed nominal Salt 1 continuation evidence:

- Source: `work_products/2026-06-30_claude_continuation_convergence/salt1_jin/time_convergence.json`
  and `time_convergence_monitors.csv`.
- The gate reports `case_verdict=stationary`, `hydraulic_verdict=stationary`,
  and `thermal_verdict=stationary`.
- Hydraulic monitors over the trailing window have drift fractions of about
  `0.76-0.78%` and amplitude fractions of about `0.79-0.80%`.
- Gross wall duty is very flat over its retained duty window.
- The heat-closure metric is weaker: `heat_closure_net_over_gross =
  -0.020783865833194637`, about `-2.08%`, versus Salt 2/3/4 notes reporting heat
  closure around `0.04-0.07%` and `0.01%`.
- The same convergence artifact records the caveat: "Salt 1 Jin retained window
  is short; treat any steady claim as weaker."

Observed corrected Salt 1 perturbation evidence:

- `salt1_jin_hi10q_corrected` moved in the expected direction but ended via the
  solver convergence monitor after only about `254 s` past restart, about `4.24%`
  of its target extension.
- `salt1_jin_lo10q_corrected` moved in the expected direction and had about
  `1724 s` of monitor span in the AGENT-185 independent direction check.
- The preliminary gate records that Salt 1 has no formal nominal mdot comparator
  in the same CFD reference table used for Salt 2/3/4, so formal Salt 1 gating
  cannot be treated equivalently without a Salt 1 nominal-reference decision.

Recommended Salt 1 next steps:

1. Keep Salt 1 out of F4/Ri coefficient fitting and out of closure-grade
   validation tables unless a row-level `fit_use_status=provisional_sensitivity`
   is explicitly intended.
2. Build a Salt 1 qualification package that compares nominal restart mdot,
   heat-balance residual, gross duty, wall duty, and late-window pressure/thermal
   QoIs against the Salt 2/3/4 standard.
3. Decide whether the `-2.08%` heat imbalance and short retained window are
   acceptable for sensitivity-only use or require an extended nominal Salt 1 Jin
   continuation.
4. If Salt 1 is needed for coefficient fitting, stage a fresh extension rather
   than mutating existing case trees, run long enough to pass the same thermal
   and operating-point gates, and regenerate the pressure/thermal ledger from
   the admitted final window.

## Major Unlocks

### 1. Pressure Decomposition Into 1D Terms

Current pressure work can show pressure structure, but closure-grade pressure
terms require a stricter decomposition:

- distributed major loss;
- reversible buoyancy / density-gradient contribution;
- local feature/minor losses;
- entrance / redevelopment losses;
- recirculation or cell-dominated invalid-single-friction regions;
- residual / unmodeled terms.

The most important next implementation is a loop-station pressure ledger with
columns for `p_rgh`, dynamic head, total pressure, local density/buoyancy term,
mechanical loss per length, feature masks, and quality flags. This should become
the input to all future friction and minor-loss claims.

Why this matters: raw `p_rgh` slopes are not pure friction in the heated/cooling
legs. The July 1 honesty audit explicitly warns that variable-density
non-isothermal legs require buoyancy correction before interpreting slopes as
Darcy friction.

Pressure-ledger minimum schema:

- `case_id`, `source_id`, `run_class`, `job_id`, `time_window_start_s`,
  `time_window_end_s`, `operating_point_verdict`, `closure_fit_admissible`,
  `needs_special_gate_scrutiny`;
- `span`, `station_start`, `station_end`, `feature_mask`, `geometry_source`,
  `centerline_source`, `flow_direction_sigma`, `theta_from_gravity_deg`;
- `p_rgh_start_pa`, `p_rgh_end_pa`, `rho_start_kg_m3`, `rho_end_kg_m3`,
  `u_start_m_s`, `u_end_m_s`, `dynamic_head_start_pa`,
  `dynamic_head_end_pa`, `total_pressure_proxy_start_pa`,
  `total_pressure_proxy_end_pa`;
- `dp_rgh_dxi_pa_m`, `gh_drho_dxi_pa_m`, `rho_u_du_dxi_pa_m`,
  `distributed_mechanical_loss_pa_m`, `development_loss_pa`,
  `minor_loss_pa`, `residual_pa`, `residual_fraction`;
- `f_lam_64_over_re`, `f_debuoyed`, `f_debuoyed_over_flam`,
  `f_fit_target_status`, `ri_definition`, `ri_median`, `ri_streamwise`,
  `x_plus`, `flags`.

Pressure-ledger acceptance criteria:

1. The loop-summed straight-span identity must close to roundoff with the
   retained terms before residual/minor-loss interpretation is promoted.
2. The ledger must explicitly identify where the residual is assigned: feature
   loss, development, recirculation/invalid single-stream, or unresolved.
3. No row with negative raw apparent friction may be silently dropped; it must
   either be corrected through the buoyancy/mechanical balance or remain as a
   flagged diagnostic.
4. The ledger must reproduce the July 1 de-buoyed straight-span momentum-budget
   values for Salt 2/3/4 before it is used for any new F4/minor-loss claim.
5. The code must be read-only with respect to native solver outputs and must
   write CSV/JSON plus a README containing equations, sign conventions, source
   paths, and row-admission rules.

### 2. Observation Table And Model-Form Contract

The postprocessing outputs are valuable but fragmented. The next durable unlock
is a common `closure_observations.csv` plus model-form specs. Every candidate
model should consume the same observation table, so adding F4 buoyancy friction,
entry-length correction, per-leg lookup, or upcomer-cell terms does not require
new bespoke glue.

Minimum observation axes:

- source/case/provenance;
- mesh level;
- time window and convergence gate;
- span/station/feature identity;
- geometry source;
- pressure method;
- thermal method;
- quality/admission flag;
- quantity/value/units;
- fit/validation eligibility.

### 3. Heat Source/Sink Ledger

Gross heater powers and intended cooler sinks are available and are adequate for
run sanity checks and case-level heat ledgers. They are not yet a fully resolved
resistance-path decomposition.

Current heat partition artifacts are explicitly audit-style. They distinguish
heater duty, cooling branch removal, ambient proxy, noncooling ambient proxy,
junction loss indicators, and net residual. They do not yet split internal
convection, wall conduction, external convection, and external radiation into a
closed resistance network.

Therefore:

- setup-level heat inputs are sufficiently characterized for current run
  validation;
- closure-level heat sources/sinks are not fully characterized for a final
  mechanistic thermal model;
- the next thermal unlock is a patchwise heat-ledger by BC type and physical
  path, with explicit sign convention and energy-balance residual.

### 4. Time-Dependent Data Use

Time-dependent data is useful, but not mainly for fitting transient correlations
yet. Use it first for rigor:

- convergence and false-steady detection;
- operating-point movement after perturbations;
- late-window stationarity of mdot, wall duty, heat residual, and pressure terms;
- uncertainty bands from time-window sensitivity;
- identifying slow thermal drift, recirculation intermittency, or feature loss
  variability.

Do not use transient data as extra independent training points unless the system
is known to be quasi-steady at each sample or the model is explicitly transient.
Early transient windows are correlated snapshots of one relaxation path, not
independent steady closure data.

Operational rule: time-dependent samples must be curated as quasi-steady
observations with uncertainty, not as raw extra rows. A worker may promote a
time window into a closure observation only after tagging the window state and
uncertainty explicitly.

Required time-window states:

- `stationary`: drift and oscillation are small enough that the window mean is a
  defensible steady observation.
- `quasi_stationary`: drift is bounded but time oscillations or slow residual
  relaxation are visible; the window mean may be used only with a temporal
  uncertainty band and downgraded fit weight.
- `moving_not_plateaued`: the run is still relaxing toward a new operating
  point; use for monitor/status plots and relaxation-time estimates only.
- `oscillatory_not_steady`: net drift may be small, but limit-cycle or persistent
  oscillations are too large for a single steady mean; report oscillation
  envelope and period, not a closure-fit point.
- `short_or_early_terminated`: insufficient post-restart advance, too few
  samples, or solver ended early; examples include rows like
  `salt1_jin_hi10q_corrected` unless a special review admits them.
- `transient_model_only`: acceptable only for an explicitly transient model with
  equations and validation targets stated up front.

Minimum quasi-steady observation schema:

- `case_id`, `source_id`, `run_class`, `job_id`, `window_id`,
  `window_start_s`, `window_end_s`, `advance_since_restart_s`,
  `advance_fraction_of_target`, `n_samples`, `write_interval_s`;
- `qoi_name`, `qoi_units`, `mean`, `std`, `min`, `max`,
  `peak_to_peak`, `rms_fluctuation`, `coefficient_of_variation`;
- `drift_slope_per_s`, `drift_over_window`, `drift_fraction_of_mean`;
- `lag1_autocorr`, `integrated_autocorrelation_time_s` if available,
  `effective_sample_size`, `autocorr_corrected_standard_error`;
- `block_count`, `block_duration_s`, `block_mean_std`,
  `block_mean_standard_error`;
- `dominant_period_s` and `cycles_in_window` when oscillations are detectable;
- `uncertainty_random`, `uncertainty_oscillation`, `uncertainty_drift`,
  `uncertainty_total`, `uncertainty_method`;
- `window_state`, `fit_use_status`, `independence_group_id`,
  `notes`, `source_paths`.

Uncertainty rule for time oscillations:

- Do not reduce a coherent oscillation to a tiny standard error by counting every
  solver write as an independent sample.
- Report at least three temporal uncertainty components:
  1. random/autocorrelation uncertainty from effective sample size;
  2. oscillation envelope or block-to-block variability;
  3. drift uncertainty across the window.
- For closure fitting, use a conservative total temporal uncertainty such as the
  root-sum-square of those components, with a floor based on the oscillation
  envelope when a persistent cycle is present. If the oscillation envelope is
  physically meaningful, report it separately rather than hiding it inside a
  standard error.

Independence rule:

- Multiple windows from the same relaxation path are not independent closure
  training rows. They must share an `independence_group_id` and either be
  collapsed into one admitted quasi-steady observation or be handled with a
  hierarchical/blocked weighting scheme.
- A "new equilibrium" requires both operating-point movement from the restart
  state and re-plateauing. Passing through a target mdot during relaxation is
  not closure evidence.
- If a worker wants to use transient samples directly, the worker must open a
  transient-model task and define the governing transient model, observables,
  likelihood/error model, and validation targets before fitting.

Relationship to existing tooling:

- `tools/analyze/assess_time_convergence.py` already reports drift,
  peak-to-peak amplitude, lag-1 autocorrelation, effective sample size, and
  autocorrelation-corrected standard error. This is the minimum baseline, not
  the final UQ standard.
- The next tool should extend that baseline with block means, oscillation-period
  diagnostics, explicit window states, conservative total temporal uncertainty,
  and independence grouping.

### 5. Literature-Review Lessons

The literature review already supports several important decisions:

- fully developed friction/Nu are references, not defaults;
- entry/development corrections should be considered explicitly;
- mixed convection and buoyancy can reshape both friction and heat transfer;
- upcomer/downcomer branch policy should be conditioned on recirculation,
  Richardson/Rayleigh/Graetz groups, and reset distance;
- `Muzychka-Yovanovich` remains a conservative internal HTC baseline;
- `Sieder-Tate`, `Shah/London`, Jackson/Cotton/Axcell, Everts/Meyer-style
  mixed-convection work should inform screening and candidate forms, not be
  pasted in blindly as validated HITEC/TAMU correlations.

The next literature expansion should be targeted, not broad:

1. laminar mixed-convection pressure-drop/friction in inclined/vertical pipes;
2. developing laminar friction, including Hagenbach/Shah-style entrance
   corrections and reset distances after bends;
3. laminar bend/minor losses at low Re and curved close-coupled features;
4. conjugate or external-loss resistance models for insulated heated loops;
5. natural-circulation loop stability / transient relaxation only if transient
   data becomes a model target.

### 6. Remaining Analysis Blockers

The important blockers are:

- no mesh/GCI uncertainty for f, Nu, UA', recirculation, or K;
- corrected Salt perturbations must finish and pass operating-point gates before
  entering closure fits;
- feature/minor-loss extraction still needs a robust two-tap total-pressure
  path with adjacent straight-friction subtraction;
- heat ledger is not yet a resolved patchwise resistance decomposition;
- upcomer correlation still lacks cell-off and max-cell points;
- `F4_leg_class` now exists as a data-driven leg-class multiplier, but the
  Richardson-number mixed-convection F4 is not yet implemented as a physics
  model;
- common observation/model-spec interface is missing;
- Salt 1 remains provisional: nominal monitors are stationary, but the retained
  window is short, heat closure is about `-2.08%`, and corrected Salt 1
  perturbation rows need special gate scrutiny;
- Water remains provisional/readiness-only relative to Salt.

## What We Can Do Well Now

- Identify and document run status, convergence, and false-steady issues.
- Preserve provenance and distinguish mainline continuations from invalid
  perturbations.
- Build mesh-derived geometry and avoid the old schematic-probe geometry error.
- Extract section-mean pressure and dynamic head with better geometry.
- Extract thermal HTC/UA'/Nu with enthalpy-flux bulk temperature and sign caveats.
- Quantify upcomer recirculation and downcomer passive behavior.
- Inject per-leg friction into the 1D model and show that pressure distribution
  improves even when mdot predictivity remains condition-dependent.

## What Still Needs Work For Scientific Rigor

1. Create a pressure-term ledger and decompose the loop into buoyancy, major,
   minor, development, and residual terms.
2. Promote patchwise heat-source/sink accounting into a resistance-path ledger.
3. Treat time windows as uncertainty and gate evidence, not extra independent
   steady points by default.
4. Implement and score model forms through a common observation table.
5. Add literature-supported candidate forms one at a time with domain guards.
6. Carry mesh/discretization uncertainty before paper-grade coefficient claims.
7. Keep closure language honest: calibration now, correlation only after domain
   expansion and uncertainty bounds.

## Recommended Worker Tasks

1. `pressure_term_ledger`: build the loop-station pressure decomposition table.
   Must reproduce the July 1 Salt 2/3/4 de-buoyed momentum-budget rows, carry
   the no-double-counting guard, and emit CSV/JSON/README.
2. `patchwise_heat_ledger`: classify and sum heater/cooler/ambient/junction
   patch duties by BC type and physical path.
3. `time_window_uncertainty`: rerun key QoIs over multiple late windows and
   report drift/variance/gate status.
4. `litrev_targeted_forms`: extract mixed-convection friction and developing
   laminar forms into candidate equations with domain guards.
5. `observation_table_contract`: define and populate the first
   `closure_observations.csv` for Salt 2/3/4 Jin.
6. `minor_loss_two_tap`: implement bend/reducer two-tap total-pressure loss with
   adjacent straight-loss subtraction.
7. `salt1_steady_qualification`: decide whether Salt 1 needs a fresh nominal
   extension before any closure-fit use; if not, document exactly why
   sensitivity-only use is acceptable.
8. `ri_corrected_f4`: build a wall-bulk `Delta T` / median-Ri calibration table
   and implement a true Ri-based F4 only after the pressure ledger is in place.

## Bottom Line On Heat Sources And Sinks

We are good enough for sanity checking and case-level heat-budget reporting. We
are not yet done for mechanistic thermal closure. The heater powers and balanced
cooler sink targets are clear; gross wall duty stationarity is checkable; but
the physical partition into internal transfer, wall conduction, external
convection/radiation, cooler removal, parasitic ambient loss, and junction loss
still needs a patchwise ledger and residual accounting.

## Confirmed Existing Script Inventory

Checked `2026-07-07` from the repo root. The current workspace already contains
useful CFD postprocessing scripts for the main categories we care about. The
important distinction is that these are not all equally ledger-ready.

Run-state / convergence / live sanity:

- `tools/analyze/build_postprocessing_run_status_inventory.py`
- `tools/analyze/assess_time_convergence.py`
- `tools/analyze/reconcile_freeze_windows.py`
- `tools/analyze/check_corrected_salt_preflight.py`
- `tools/analyze/monitor_live_corrected_salt.py`
- `tmp/2026-07-06_overnight_postprocess_jobs/collect_corrected_salt_status.py`

Heat input / heat balance / thermal closure:

- `tools/analyze/build_ethan_steady_state_heat_flow_audit.py`
- `tools/analyze/build_ethan_case_heat_summary.py`
- `tools/analyze/build_ethan_salt_family_heat_loss_breakout.py`
- `tools/analyze/build_ethan_salt_thermal_closure_hardening.py`
- `tools/analyze/build_ethan_salt_thermal_closure_hardening_v3.py`
- `tools/analyze/build_ethan_water_thermal_closure_readiness.py`
- `tools/extract/sample_segment_htc_uaprime.py`

Mean pressure / pressure features / hydraulic evidence:

- `tools/extract/sample_section_mean_pressure.py`
- `tools/extract/sample_leg_centerline_major_loss.py`
- `tools/extract/sample_bend_minor_loss.py`
- `tools/extract/sample_feature_minor_loss_budget.py`
- `tools/analyze/build_ethan_salt_pressure_closure_breakout.py`
- `tools/analyze/build_ethan_salt_pressure_drop_predictivity.py`
- `tools/analyze/build_ethan_pressure_feature_support_note.py`
- `tools/analyze/build_ethan_prgh_vs_dynamic_profiles.py`
- `tools/analyze/build_ethan_dynamic_pressure_profiles.py`
- `tools/analyze/derive_segment_friction.py`
- `tools/analyze/derive_streamwise_momentum_budget.py`

Per-leg friction / closure-to-1D / model-form trials:

- `tools/analyze/build_ethan_streamwise_friction_package.py`
- `tools/analyze/build_ethan_dense_streamwise_friction_package.py`
- `tools/extract/sample_streamwise_friction_dense_faces.py`
- `tools/extract/sample_streamwise_friction_patch_averages.py`
- `tools/analyze/build_ethan_1d_closure_bakeoff.py`
- `tools/analyze/build_incremental_model_form_comparison.py`
- `tools/analyze/build_next_1d_model_forms.py`
- `tools/analyze/build_rom_model_form_fits_and_1p4_boundary.py`
- `tools/analyze/cfd_closure_bundle.py`

Branch behavior and supporting geometry:

- `tools/extract/build_mesh_centerlines.py`
- `tools/extract/sample_upcomer_convection_cell.py`
- `tools/extract/sample_downcomer_recirculation.py`
- `tools/analyze/build_ethan_upcomer_recirculation_evidence.py`
- `tools/analyze/mixed_convection_reversal.py`

Mesh/GCI support:

- `tools/analyze/compute_gci.py`
- Prior de-risk attempt: `.agent/journal/2026-07-02/mesh-self-generation-gci.md`

Assessment: yes, we have scripts that can do useful CFD postprocessing today.
The missing layer is not basic extraction capability. The missing layer is a
set of auditable ledgers and common observation contracts that make the outputs
fit-ready, uncertainty-aware, and resistant to double counting.

## Script Documentation And Workflow Integration Audit

Checked `2026-07-07`.

### Run State / Convergence

Scripts:

- `tools/analyze/build_postprocessing_run_status_inventory.py`
- `tools/analyze/assess_time_convergence.py`
- `tools/analyze/check_corrected_salt_preflight.py`
- `tools/analyze/monitor_live_corrected_salt.py`

Documentation quality: good to excellent. `assess_time_convergence.py` is the
strongest: it documents the scientific method, thresholds, autocorrelation
handling, operating-point gate, caveats, and usage. `build_postprocessing_run_status_inventory.py`
and `check_corrected_salt_preflight.py` have clear purpose statements and CLIs.
`monitor_live_corrected_salt.py` is operationally useful but thinner; its logic
is in code rather than a full method docstring.

Workflow integration: strong for current corrected-Salt operations. These tools
are already tied to AGENT-181/185/192 style workflows and have tests for the
newer preflight/live-monitor paths. Remaining need: fold outputs into the common
observation/admission contract instead of leaving them as separate status CSVs.

### Heat Audits / Thermal Closure

Scripts:

- `tools/analyze/build_ethan_steady_state_heat_flow_audit.py`
- `tools/analyze/build_ethan_case_heat_summary.py`
- `tools/analyze/build_ethan_salt_family_heat_loss_breakout.py`
- `tools/extract/sample_segment_htc_uaprime.py`

Documentation quality: mixed. `sample_segment_htc_uaprime.py` is excellent: it
states formulas, enthalpy-flux bulk temperature, sign convention, caveats, usage,
mesh/GCI limitations, radiation exclusion, and what is gated. The older heat
audit/report builders have CLI descriptions and generated report context but
weak top-level scientific-method docstrings.

Workflow integration: useful but fragmented. Heat summaries and heat-loss
breakouts are well used in reports; HTC/UA'/Nu extraction is technically solid
for the cases it supports. Missing piece: a patchwise heat-source/sink ledger
that joins heater/cooler/passive/junction duties, enthalpy changes, wall fluxes,
and residuals with one sign convention.

### Mean Pressure / Hydraulic Evidence

Scripts:

- `tools/extract/sample_section_mean_pressure.py`
- `tools/extract/sample_leg_centerline_major_loss.py`
- `tools/analyze/derive_segment_friction.py`
- `tools/analyze/derive_streamwise_momentum_budget.py`

Documentation quality: very good overall. `sample_section_mean_pressure.py`,
`derive_segment_friction.py`, and `derive_streamwise_momentum_budget.py` have
strong method documentation, equations, sign conventions, confidence boundaries,
and usage. `sample_leg_centerline_major_loss.py` is more of an older workflow
extractor and is less self-contained.

Workflow integration: strong as diagnostic evidence, not yet ledger-grade. These
scripts already feed section means, friction diagnostics, and the July 1
de-buoyed momentum budget. Missing piece: unify them into one pressure-term
ledger before fitting or assigning residuals to major/minor/development terms.

### Minor Losses / Features

Scripts:

- `tools/extract/sample_bend_minor_loss.py`
- `tools/extract/sample_feature_minor_loss_budget.py`
- `tools/analyze/summarize_corner_pressure_drops.py`

Documentation quality: uneven. `sample_bend_minor_loss.py` has a strong
scientific docstring for feature total-pressure loss and K factors. `summarize_corner_pressure_drops.py`
documents sign convention and its reuse of existing feature CSVs. `sample_feature_minor_loss_budget.py`
is older scaffold code with weaker method documentation.

Workflow integration: partial. Existing tools are good for feature diagnostics
and presentation summaries. They are not yet the requested robust two-tap
minor-loss workflow because adjacent straight distributed losses are not
subtracted consistently and local dynamic-pressure normalization still needs to
be made explicit in a ledger-compatible output.

### Per-Leg Friction / 1D Trials

Scripts:

- `tools/analyze/build_ethan_1d_closure_bakeoff.py`
- `tools/analyze/build_incremental_model_form_comparison.py`
- `tools/analyze/build_next_1d_model_forms.py`
- `tools/analyze/cfd_closure_bundle.py`

Documentation quality: moderate. `build_incremental_model_form_comparison.py`
is well framed as additive and read-only. `build_ethan_1d_closure_bakeoff.py`
has a clear CLI description but relies on report context for interpretation.
`build_next_1d_model_forms.py` and `cfd_closure_bundle.py` are usable but thinly
documented relative to their scientific importance.

Workflow integration: moderate to strong. These scripts have already produced
useful 1D comparison packages and closure bundles. Missing piece: make all
model-form comparisons consume the same `closure_observations.csv`, separate
fit/validation rows, and score pressure distribution, mdot, and thermal mismatch
separately.

### Upcomer / Downcomer Behavior

Scripts:

- `tools/extract/sample_upcomer_convection_cell.py`
- `tools/extract/sample_downcomer_recirculation.py`
- `tools/analyze/build_ethan_upcomer_recirculation_evidence.py`

Documentation quality: good. `sample_upcomer_convection_cell.py` and
`sample_downcomer_recirculation.py` clearly explain why recirculation metrics
exist, how they are computed, what nondimensional fields are or are not
available, and why upcomer/downcomer should not share one closure. The evidence
builder is less self-documenting but has a clear CLI and report-package role.

Workflow integration: useful for regime diagnosis, not complete for correlation.
The upcomer/downcomer tools support the current branch-policy conclusion. The
missing workflow is an onset/regime table that joins recirculation metrics,
Ri/Ra/Re/Pr, wall-bulk Delta T, time-window quality, mesh uncertainty, and
fit-admission status.

## Mesh/GCI Intake Note

User note, recorded `2026-07-07`: Ethan said he would put mesh/GCI material in
the modern runs area on TACC, likely:

```text
~/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/
```

Inspection from this account found:

- `~/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/` exists.
- It contains `salt/` and `water/`.
- `salt/` was modified on `2026-07-07` and contains `coarse/`, `medium/`, and
  `fine/`.
- The `salt/coarse`, `salt/medium`, and `salt/fine` directories currently deny
  traversal to this account because they are mode `drwx--S---` under owner
  `ethanrozak`.
- Therefore the likely mesh/GCI upload location exists, but the files are not
  inspectable until Ethan grants group execute/read permission or stages a
  readable copy.

Recommended intake action: ask Ethan to run a permission fix or copy into a
group-readable staging directory. Do not import or claim mesh/GCI evidence until
we can list exact case paths and record provenance.

## Draft Board-Ready Agent Briefs

These should probably become board rows during the board-cleaning pass. Until
then, treat them as coordinator-drafted scopes. Each one should end with a
dated `work_products/**` package plus `.agent/status/...` and a journal note.

### `pressure_term_ledger`

Role: Implementer / Tester / Writer.

Objective: build a read-only pressure ledger that separates reversible buoyancy,
distributed mechanical loss, development/reset effects, feature/minor losses,
recirculation-invalid regions, and residual before any fitting.

Required reading before coding:

- this note, especially `Pressure Ledger Before Closure Claims`;
- `.agent/journal/2026-07-01/T1b-momentum-budget-debuoyed-friction.md`;
- `.agent/journal/2026-07-01/T1-mesh-centerlines-geometry-refix.md`;
- `.agent/journal/2026-07-01/3d-closure-into-1d-predictivity-trial.md`;
- `reports/2026-07/2026-07-01/2026-07-01_postprocessing_rom_honesty_audit/README.md`;
- `work_products/2026-07-01_claude_momentum_budget/**`;
- relevant source scripts: `derive_streamwise_momentum_budget.py`,
  `sample_section_mean_pressure.py`, `sample_leg_centerline_major_loss.py`.

Deliverables:

- `pressure_term_ledger.csv` and `.json`;
- `pressure_term_ledger_README.md` with equations, sign convention, source paths,
  and row-admission policy;
- reproduction check against July 1 Salt 2/3/4 de-buoyed momentum-budget rows;
- list of rows that remain residual-only or invalid for single-stream friction.

Acceptance criteria:

- raw `p_rgh` slopes are never used as friction without buoyancy correction;
- `buoyancy_pressure()` is not double counted as a friction term;
- every span has explicit source time, geometry, station endpoints, and flags;
- negative apparent friction rows are explained, corrected, or retained as
  flagged diagnostics rather than silently dropped.

### `observation_table_contract`

Role: Coordinator / Implementer / Writer.

Objective: define the canonical `closure_observations.csv` schema consumed by
pressure, thermal, time-window, and 1D model-form tasks.

Required reading:

- this note, especially `Observation Table And Model-Form Contract`;
- `.agent/journal/2026-06-30/3d-to-1d-field-reduction-methods.md`;
- `.agent/journal/2026-06-19/coordinator-writer-litrev-to-1d-modeling-handoff.md`;
- `reports/2026-06/2026-06-18/2026-06-18_ethan_salt_closure_correlation_package/README.md`;
- `reports/2026-07/2026-07-01/2026-07-01_postprocessing_rom_honesty_audit/README.md`;
- existing package schemas in `work_products/2026-06-30_claude_segment_friction/`,
  `work_products/2026-06-30_claude_thermal_htc/`, and
  `work_products/2026-07-01_claude_momentum_budget/`.

Deliverables:

- schema document with required columns, units, allowed enums, and provenance
  fields;
- seed `closure_observations.csv` for admitted Salt 2/3/4 Jin mainline rows only;
- validation script that fails rows missing source paths, time windows, units,
  mesh level, or fit-admission flags.

Acceptance criteria:

- one row represents one observable, not one arbitrary case summary;
- fit eligibility and validation eligibility are separate fields;
- time windows and mesh level are mandatory;
- sensitivity/perturbation rows cannot enter unless their gate status is
  explicit.

### `targeted_litrev_forms`

Role: Writer / Implementer.

Objective: convert literature findings into candidate equations with domain
guards, required inputs, and expected failure modes. This task should not merely
summarize papers.

Required reading:

- `.agent/journal/2026-06-19/coordinator-writer-litrev-to-1d-modeling-handoff.md`;
- `.agent/journal/2026-06-22/writer-reviewer-litrev-htc-audit.md`;
- `operational_notes/06-26/30/2026-06-30_next_scope_branch_closures_and_cfd_design.md`;
- AGENT-186 outputs under `work_products/2026-07-07_f_lit_forms/**`;
- implemented friction forms in
  `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`.

Deliverables:

- `candidate_forms.csv` with equation, source, inputs, nondimensional groups,
  branch applicability, validity range, and exclusion criteria;
- priority ranking for pressure, heat-transfer, upcomer, minor-loss, and
  transient forms;
- explicit list of forms not implemented because constants or primary-source
  definitions are not verified.

Acceptance criteria:

- primary-source citation or explicit secondary-source caveat for every formula;
- no equation is added to code unless its constants, units, and validity range
  are verified;
- the output says which forms are references, which are candidate closures, and
  which are only sanity checks.

### `minor_loss_two_tap`

Role: Implementer / Tester.

Objective: extract bend/reducer/junction minor losses using two-tap total
pressure, subtract adjacent straight distributed loss, and normalize with local
bulk dynamic pressure.

Required reading:

- `.agent/journal/2026-07-01/3d-closure-into-1d-predictivity-trial.md`;
- `operational_notes/06-26/25/2026-06-25_ethan_corner_pressure_drop_math.md`;
- reports and outputs from `2026-06-25_ethan_corner_pressure_drop_summary`;
- `sample_bend_minor_loss.py`, `sample_feature_minor_loss_budget.py`,
  `summarize_corner_pressure_drops.py`.

Deliverables:

- feature-level `minor_loss_two_tap.csv`;
- corrected `K_local` and diagnostic `K_apparent` columns;
- adjacent straight-loss subtraction audit;
- README stating where the result is an upper bound.

Acceptance criteria:

- no global loop dynamic pressure normalization for local `K` unless also
  labeled diagnostic;
- feature windows do not overlap straight-span fit windows without accounting;
- rows near recirculation or separation get quality flags;
- output can be joined to the pressure ledger by case, feature, and station.

### `model_form_bakeoff`

Role: Implementer / Reviewer.

Objective: compare closure model forms using the same observation table and a
predeclared scoring method, without changing the target data per model.

Required reading:

- `.agent/journal/2026-07-01/3d-closure-into-1d-predictivity-trial.md`;
- `.agent/journal/2026-07-02/per-leg-friction-implementation-and-predictivity.md`;
- `reports/2026-07/2026-07-02/2026-07-02_overnight_synthesis/README.md`;
- AGENT-187 F4 outputs under `work_products/2026-07-07_f4_buoyancy_friction/**`;
- `build_ethan_1d_closure_bakeoff.py`, `build_incremental_model_form_comparison.py`,
  and external Fluid closure files.

Deliverables:

- scored bakeoff table for baseline, per-leg, literature, F4_leg_class, and any
  admitted Ri/F4 candidate;
- pressure-distribution score, mdot score, thermal-state mismatch score, and
  complexity/overfit warning;
- holdout or leave-one-case-out result where possible.

Acceptance criteria:

- mdot is not the only score while thermal state is mismatched;
- pressure distribution and thermal boundary mismatch are reported separately;
- model forms are compared on the same admitted observations;
- fitted and validation rows are visibly separated.

### `upcomer_onset`

Role: Writer / Implementer.

Objective: determine when the upcomer should be modeled as ordinary pipe
friction versus a buoyancy/recirculation-cell regime.

Required reading:

- `operational_notes/06-26/30/2026-06-30_next_scope_branch_closures_and_cfd_design.md`;
- `.agent/journal/2026-07-01/T1-mesh-centerlines-geometry-refix.md`;
- existing `work_products/2026-07-01_claude_allspan_convection/**`;
- `build_ethan_upcomer_recirculation_evidence.py`;
- `mixed_convection_reversal.py`;
- targeted mixed-convection literature from `targeted_litrev_forms`.

Deliverables:

- upcomer regime table with Re, Pr, Gr/Ra/Ri, wall-bulk Delta T, flow reversal
  or recirculation metrics, and fit-admission status;
- proposed onset criterion and uncertainty/unknowns;
- recommended CFD design points for cell-off and max-cell envelopes.

Acceptance criteria:

- upcomer rows are not forced into standard Darcy-friction fits when
  recirculation metrics say the single-stream assumption is invalid;
- the proposed criterion says whether it is evidence-based, literature-based,
  or a design hypothesis awaiting CFD;
- new CFD recommendations are minimal and targeted.

### `mesh_uncertainty`

Role: Coordinator / Implementer / Tester.

Objective: convert Ethan's new mesh levels into an auditable mesh/GCI package
for f, pressure ledger terms, HTC/UA'/Nu, recirculation metrics, and feature K.

Required reading:

- `.agent/journal/2026-07-02/mesh-self-generation-gci.md`;
- `operational_notes/07-26/01/2026-07-01_T6_gci_blocker_ethan_request.md`;
- `tools/analyze/compute_gci.py` and `test_compute_gci.py`;
- source case provenance under Ethan's modern-runs mesh directories once
  permissions allow inspection.

Deliverables:

- import/intake manifest with exact Ethan source paths and timestamps;
- mesh-level inventory: coarse/medium/fine, cell counts, geometry differences,
  solver version, boundary-condition differences, and latest usable time;
- QOI comparison table by mesh level;
- GCI or honest two-level/failed-GCI statement for each QOI;
- list of QOIs still too mesh-sensitive for publication claims.

Acceptance criteria:

- no GCI value is fabricated if only two levels or non-monotone convergence are
  available;
- OpenFOAM non-conformal-interface issues from AGENT-171 are checked explicitly;
- mesh uncertainty is propagated as a qualifier on closure observations, not
  buried in a separate appendix;
- exact file paths are recorded before any imported data is copied or analyzed.
