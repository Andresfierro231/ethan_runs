# Literature Review Lessons and Research Pathways

Date: `2026-07-13`

Task: `AGENT-282`

Source reviewed:
`/scratch/09748/andresfierro231/projects_scratch/papers/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL`

## Purpose

This note extracts lessons learned, model forms, and concrete things to try
from the HITEC closure literature review. Provenance is by author and title
because numeric citation labels will change. The source literature-review repo
was treated as read-only.

Tags: #litrev-synthesis #closure-ledger #source-envelope #property-sensitivity
#cfd-to-1d #heat-loss #minor-loss #research-pathways

## Start Here

Use this package when deciding what the literature review implies for the next
CFD-to-1D closure tasks. The fastest reading order is:

1. `README.md` sections `Main Takeaway`, `Highest-Value Near-Term Work`, and
   `Things To Try`.
2. `litrev_to_current_evidence_crosswalk.csv` for the current tried/demoted/
   untried status of each model family after the July 14 gate packages.
3. `untried_litrev_model_forms.csv` for the prioritized model-form backlog.
4. `rejected_or_demoted_litrev_shortcuts.csv` for shortcuts that must stay out
   of current claims.
5. `research_pathways.csv` for board-ready task ideas and acceptance gates.
6. `summary.json` for a compact machine-readable index.

## Related

- `operational_notes/07-26/13/2026-07-13_litrev_synthesis_start_here.md`
- `operational_notes/07-26/10/2026-07-10_NEXT_MEETING_START_HERE.md`
- `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/README.md`
- `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_heat_loss_path/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/README.md`
- `.agent/BOARD.md` rows `TODO-LITREV-SOURCE-ENVELOPE`,
  `TODO-LITREV-PROPERTY-SENSITIVITY`, `TODO-LITREV-RESET-NAMED-LOSSES`,
  `TODO-LITREV-HEAT-LOSS-CALIBRATION`, and
  `TODO-LITREV-CFD-VALIDITY-DIAGNOSTICS`.

## Main Takeaway

The literature review does not support one global friction coefficient, one
global Nusselt number, or one global heat-loss UA for the TAMU HITEC loop. It
supports a branchwise closure ledger. The useful unit is a branch or section
with explicit reset history, local properties, source envelope, pressure basis,
velocity basis, heat-transfer state, heat-loss path, and residual.

The most important modeling move is to keep reference limits, active closures,
diagnostic gates, sensitivity models, method sources, and unresolved residuals
separate. A match in total mass flow or total heat removal is not enough if the
match hides hydrostatic terms, fitting losses, heat loss, or property error in
the wrong coefficient.

## Completion Update: Current Model-Form Status

Added by `AGENT-352` on 2026-07-14. This section completes the original
summary by crosswalking the literature-review recommendations against the
current Ethan evidence stack. It does not mutate the source literature-review
repo and it does not admit any new model by itself.

The current state is more specific than "try the LitRev ideas":

- The branchwise ledger architecture is now the controlling rule for pressure,
  heat transfer, boundary conditions, and residuals.
- Several literature ideas have been tried and demoted rather than left open:
  localized fixed-K alone worsened mdot and remains diagnostic; fully developed
  friction/Nu defaults are reference-only; global `f`, `Nu`, `K`, and `UA`
  shortcuts are rejected.
- Several ideas are partly executed but still gate-blocked: F6 `phi(Re)` needs
  admitted Re-variation rows; component/cluster `K` needs fit-admissible tap or
  plane evidence; setup-only HX/wall/radiation needs first-class Fluid boundary
  dictionaries; internal Nu needs mesh/sign/heat-balance and recirculation
  validity gates.
- The upcomer result is a positive scientific finding, not just a failed Nu fit:
  current Salt2-4 upcomer evidence is recirculating, so single-stream `Nu`,
  `f_D`, and `K` labels are invalid there.
- Corrected-Q and matched upcomer plane extraction are pending/admission-gated
  evidence sources; they must not be consumed as closure-fit rows until their
  terminal/admission packages say so.

Use these new tables before proposing another model form:

| Table | Purpose |
| --- | --- |
| `litrev_to_current_evidence_crosswalk.csv` | One row per LitRev model family with current tried status, evidence class, Ethan evidence path, and next action. |
| `untried_litrev_model_forms.csv` | Prioritized backlog of forms that are not tried or still incomplete, with required gates. |
| `rejected_or_demoted_litrev_shortcuts.csv` | Guardrail list of shortcuts that are rejected, demoted, or future-only. |

### Tried / demoted / untried summary

| Family | Current status | What this means |
| --- | --- | --- |
| Property modes | tried diagnostic/sensitivity | Property sensitivity exists; keep replication and updated-property modes separate before fitting residuals. |
| Fully developed friction and Nu | demoted to reference | Report these as reference columns, not active default closures. |
| H1 localized fixed K | tried negative diagnostic | Localized fixed-K-only scoring worsens mdot; H1 remains proxy-only until reset/development and admitted K evidence exist. |
| F6 `phi(Re)` friction | partially tried / blocked | F6 is the next bounded hydraulic candidate, but only after admitted Re-variation rows exist. |
| Component/cluster `K` | partially tried / blocked | Current component/cluster K has zero fit-admissible rows; raw connector extraction and admission are still needed. |
| Internal Nu | tried admission rule / blocked for fitting | No internal Nu row is fit-admissible today; recirculating upcomer evidence invalidates single-stream coefficient labels. |
| Chen 2017 mixed Nu | conditional / not active | Use only where source-envelope and CFD validity gates admit branch overlap. |
| Heater source fraction | tried diagnostic | Heater-source split-screen exists; C1 is the next default, while one-scalar variants remain proxy-screen candidates. |
| Cooler/HX UA and wall/radiation | partially tried / blocked | Task matrix and guardrails exist; setup-only Fluid boundary/HX/wall/radiation implementation remains open. |
| CFD validity diagnostics | partially tried / pending extraction | Matched upcomer extraction workflow is submitted; admission-grade parsed rows are pending job completion. |
| Transients and ROM | not tried / future method | Keep as future pathways unless thesis scope expands and validation artifacts exist. |

### Current evidence classes

Use these words consistently when carrying LitRev ideas forward:

- `predictive`: setup-only model input/output evidence admitted for prediction.
- `calibrated`: fitted on declared training data with validation/holdout
  boundaries.
- `diagnostic`: useful for understanding physics or screening, but not a
  closure-fit row.
- `reference`: limiting formula or comparator only.
- `sensitivity`: source-bounded variation for uncertainty or ranking.
- `blocked`: cannot be promoted until stated gates clear.
- `future_method`: valid research direction but not current closure evidence.

## Lessons Learned

1. Fully developed formulas are references, not defaults.

   Use `f_D = 64/Re` and fully developed `Nu` only as reference outputs unless
   branch-specific development evidence exists. This comes from the review's
   use of Shah and London, "Laminar Flow Forced Convection Heat Transfer and
   Flow Friction in Straight and Curved Ducts", Shah, "A Correlation for
   Laminar Hydrodynamic Entry Length Solutions for Circular and Noncircular
   Ducts", and Muzychka and Yovanovich, "Pressure Drop in Laminar Developing
   Flow in Noncircular Ducts: A Scaling and Modeling Approach".

2. Properties are closure choices.

   Density, viscosity, heat capacity, and thermal conductivity must be carried
   as named property modes because they move `Re`, `Pr`, `Gr`, `Ra`, `Ri`,
   `Gz`, buoyancy head, entrance length, `h`, and residuals. The review points
   to Sohal et al., "Engineering Database of Liquid Salt Thermophysical and
   Thermochemical Properties", Jin et al., "Accurate Viscosity Measurement of
   Nitrates/Nitrites Salts for Concentrated Solar Power", Parida and Basu, "On
   the Specific Heat Capacity of HITEC-Salt Nanocomposites for Concentrated
   Solar Power Applications", Santini et al., "Measurement of Thermal
   Conductivity of Molten Salts in the Range 100-500 C", Nunes et al.,
   "Molten Salts as Engineering Fluids - A Review: Part I. Molten Alkali
   Nitrates", and Serrano-Lopez et al., "Molten Salts Database for Energy
   Applications".

3. Replication mode and improved-property mode must stay separate.

   Reis, Seo, and Hassan, "Molten Salt Flow Visualization to Characterize
   Boundary Layer Behavior and Heat Transfer in a Natural Circulation Loop",
   records the TAMU-style experimental property usage and friction convention.
   Jin viscosity and Parida/Basu heat capacity are useful candidates or
   sensitivities, but they are not what the Reis/Jadyn model used. Mixing those
   modes would break provenance.

4. Fittings are both losses and reset features.

   Bends, reducers, expansions, contractions, quartz transitions, and tees
   should not be represented as universal constants. They need `K(Re, geometry,
   split, pressure_basis, velocity_basis, development, recovery)`, and they
   also reset downstream hydraulic and sometimes thermal development. This is
   supported by Lin et al., "State-of-the-Art Review on Measurement of Pressure
   Losses of Fluid Flow Through Pipe Fittings", Al-Tameemi and Ricco,
   "Pressure-Loss Coefficient of 90 deg Sharp-Angled Mitre Elbows", Patino-
   Jaramillo et al., "Laminar Flow and Pressure Loss in Planar Tee Joints:
   Pressure Loss Coefficients", and Salehi et al., "Experimental Determination
   and Computational Fluid Dynamics Predictions of Pressure Loss in
   Close-Coupled Elbows (RP-1682)".

5. Internal heat transfer is a branch-state problem.

   Each branch needs `Re`, `Pr`, `Gr`, `Gr_star`, `Ri`, `Ra`, `Gz`,
   orientation, heating/cooling sign, thermal reset distance, and
   invalid-single-stream flags. Muzychka and Yovanovich, "Laminar Forced
   Convection Heat Transfer in the Combined Entry Region of Non-Circular
   Ducts", gives the forced developing form. Everts and Meyer, "Laminar
   Hydrodynamic and Thermal Entrance Lengths for Simultaneously
   Hydrodynamically and Thermally Developing Forced and Mixed Convective Flows
   in Horizontal Tubes", gives diagnostic entrance-length gates. Chen et al.,
   "Characteristics of the laminar convective heat transfer of molten salt in
   concentric tube", is the best current low-Re molten-salt mixed-convection
   candidate, but only if the TAMU branch envelope overlaps its range.

6. HITEC-specific does not automatically mean TAMU-active.

   Chen et al., "Flow and Mixed Convection Heat Transfer of Hitec Salt in
   Multi-Sided Heating Pipes", Yang et al., "Performance Evaluation of Flow
   and Mixed Convective Heat Transfer of Hitec Salt in Inclined Tube with
   Single Surface Heating", and Tian et al., "Numerical analysis of turbulent
   mixed convection heat transfer of molten salt in horizontal tubes with
   uniformly cooled heat flux", are useful for nonuniform heating, inclination,
   secondary-flow, and cooling diagnostics. Their square-tube, turbulent, or
   horizontal-cooling assumptions should not be silently promoted into low-Re
   circular-pipe TAMU closures.

7. Heat loss is a network, not a cleanup multiplier.

   VDI Heat Atlas supports the resistance-network architecture: internal
   convection, wall conduction, contact/fouling, insulation, external natural
   convection, radiation, cooling jacket, heater efficiency, passive loss, and
   residual. Reis, Seo, and Hassan, "Consequences of Molten Salt
   Solidification in a Natural Circulation Flow Visualization Loop Due to
   Heater Failure", supports keeping active cooling, heater behavior, passive
   loss, storage, and failure transients distinct.

8. CFD-to-1D reductions must be named by what the planes actually isolate.

   Use hydrostatic, kinetic, and straight-pipe corrections before extracting
   `f_D,Delta_p`, `K_component`, `K_cluster`, or `K_section`. If a CFD span
   contains inseparable redevelopment, local disturbance, and recovery, call it
   a section apparent loss, not a universal fitting coefficient. This follows
   Lin et al., "Measurement Methods and Techniques for Pressure Losses in Pipe
   Fittings", and Csizmadia and Hos, "CFD-Based Estimation and Experiments on
   the Loss Coefficient for Bingham and Power-Law Fluids Through Diffusers and
   Elbows".

9. ROM is a pathway, not current validation.

   Manthey et al., "Reduced Order Modeling of a Natural Circulation System by
   Proper Orthogonal Decomposition", Vergari et al., "Reduced Order Modeling
   Approach for Parametrized Thermal-Hydraulics Problems: Inclusion of the
   Energy Equation in the POD-FV-ROM Method", Star et al., "A POD-Galerkin
   Reduced Order Model of a Turbulent Convective Buoyant Flow of Sodium Over a
   Backward-Facing Step", and Acierno et al., "Development and Application of
   Reduced-Order Models for Thermal-Fluid Dynamics in Molten Salt Reactors",
   support a future workflow only after full-order models, snapshots,
   stabilization, and withheld validation exist.

## Model Forms to Carry Forward

| Family | Model form to keep | Source-status use | Provenance by author/title | Immediate test |
| --- | --- | --- | --- | --- |
| Pressure ledger | `dp_static = dp_hyd + dp_kin + dp_dist_dev + dp_minor + dp_reset + dp_transient + dp_res` | Architecture | Shah, "A Correlation for Laminar Hydrodynamic Entry Length Solutions for Circular and Noncircular Ducts"; Muzychka and Yovanovich, "Pressure Drop in Laminar Developing Flow in Noncircular Ducts"; Lin et al., "Measurement Methods and Techniques for Pressure Losses in Pipe Fittings" | Recompute every CFD/1D section with separate hydrostatic and kinetic terms. |
| Property modes | `P0` replication, `P1/P2/...` updated and sensitivity modes | Direct plus sensitivity | Reis, Seo, and Hassan, "Molten Salt Flow Visualization..."; Sohal et al., "Engineering Database..."; Jin et al., "Accurate Viscosity Measurement..."; Santini et al., "Measurement of Thermal Conductivity..." | Run mass-flow and temperature predictions under at least replication, full Sohal/Janz, Jin-viscosity, midrange-Cp, and low/high `k` modes. |
| Fully developed friction | `f_D,FD,ref = 64/Re` | Reference only | Shah and London, "Laminar Flow Forced Convection Heat Transfer and Flow Friction..." | Output as a diagnostic side column; do not use as active default. |
| Developing pressure loss | `fRe(L+)` from reset distance | Source-bounded active candidate | Muzychka and Yovanovich, "Pressure Drop in Laminar Developing Flow in Noncircular Ducts..." | Compare no-reset, conservative-reset, and aggressive-reset cases against CFD section pressure losses. |
| Pressure-derived section loss | `f_D,Delta_p` or `K_Delta_p` after corrections | Measured/CFD-informed | Lin et al., "Measurement Methods and Techniques..."; Csizmadia and Hos, "CFD-Based Estimation..." | Build section tables named `straight`, `component`, `cluster`, or `branch_apparent`. |
| Minor losses | `K(Re, geometry, split, pressure_basis, velocity_basis)` | Source-bounded, measured, CFD, or unresolved | Lin et al., "State-of-the-Art Review..."; Patino-Jaramillo et al., "Laminar Flow and Pressure Loss in Planar Tee Joints..." | Create a TAMU fitting inventory with part geometry, pressure basis, velocity basis, and candidate source status. |
| Forced developing `Nu` | Combined-entry local/average `Nu` | Source-bounded active candidate if buoyancy weak | Muzychka and Yovanovich, "Laminar Forced Convection Heat Transfer in the Combined Entry Region..." | Test against fully developed reference and CFD `Nu_i` section outputs. |
| Low-Re molten-salt mixed `Nu` | Chen 2017 `Nu` with `Gz`, `GrPrD/L`, and viscosity ratio | Conditional source-bounded closure | Chen et al., "Characteristics of the laminar convective heat transfer of molten salt in concentric tube" | Compute TAMU branch overlap for `Re`, `Pr`, `Gr`, `Gz`, `L/D`, and boundary condition before use. |
| Nonuniform heating diagnostics | Heating pattern, vortex/secondary-flow flags | Diagnostic/source-bounded | Chen et al., "Flow and Mixed Convection Heat Transfer of Hitec Salt in Multi-Sided Heating Pipes"; Shen et al., "Convective Heat Transfer of Molten Salt in Receiver Tube with Axially and Circumferentially Non-Uniform Heat Flux" | Record heater surface pattern and compute wall-temperature/heat-flux reconstruction fields. |
| Inclination | `g_parallel = g sin(theta)`, `g_perpendicular = g cos(theta)` | Diagnostic | Yang et al., "Performance Evaluation of Flow and Mixed Convective Heat Transfer of Hitec Salt in Inclined Tube..." | Add axial/transverse buoyancy components to branch metadata. |
| Heat-loss network | `R_int + R_wall + R_contact + R_ins + (R_ext || R_rad)` plus jacket path | Architecture | VDI Heat Atlas; Reis, Seo, and Hassan, "Consequences of Molten Salt Solidification..." | Fit jacket/passive/radiation/contact terms separately before touching internal `Nu`. |
| CFD invalidity flags | reverse area fraction, reverse mass fraction, secondary velocity fraction | Method/diagnostic | Patino-Jaramillo et al., "Laminar Flow and Pressure Loss in Planar Tee Joints: Numerical Simulations and Flow Analysis"; Podila et al., "Modelling of Heat Transfer in a Molten Salt Loop Using Computational Fluid Dynamics" | Add plane-level recirculation diagnostics to CFD extraction. |
| ROM | POD/POD-FV/C-ROM with state variables and validation metrics | Future method source | Manthey et al., "Reduced Order Modeling..."; Vergari et al., "Reduced Order Modeling Approach..."; Acierno et al., "Development and Application..." | Do not claim ROM prediction until snapshot envelope and withheld validation exist. |

## Things To Try

### Tier 1: Do First

1. Build the TAMU branch nondimensional envelope.

   For every branch and source/sink segment, compute min/mean/max `Re`, `Pr`,
   `Gr`, `Gr_star`, `Ri`, `Ra`, `Gz`, `Bo` where relevant, `L/D`, reset
   distance, orientation, heating/cooling sign, and property mode. This is the
   gate for nearly every source-bounded claim. Provenance: Chen et al.,
   "Characteristics of the laminar convective heat transfer of molten salt in
   concentric tube"; Tian et al., "Numerical analysis of turbulent mixed
   convection..."; Everts and Meyer, "Laminar Hydrodynamic and Thermal
   Entrance Lengths...".

2. Run a property-mode sensitivity package before fitting closures.

   Compare replication properties, full Sohal/Janz density/viscosity, Jin
   viscosity, `cp = 1424/1560/Sohal`, and Santini/constant `k` cases. Report
   movement in mass flow, `Re`, `Pr`, `Gz`, buoyancy head, heat residual, and
   pressure residual. Provenance: Reis, Seo, and Hassan, "Molten Salt Flow
   Visualization..."; Sohal et al., "Engineering Database..."; Jin et al.,
   "Accurate Viscosity Measurement..."; Santini et al., "Measurement of
   Thermal Conductivity...".

3. Build a reset-distance map.

   Assign hydraulic and thermal reset points at bends, reducers, quartz
   transitions, heater starts, cooling-jacket starts, wall-material changes,
   and CFD-identified separation zones. Test no-reset, source-based reset, and
   aggressive reset variants. Provenance: Shah, "A Correlation for Laminar
   Hydrodynamic Entry Length Solutions..."; Muzychka and Yovanovich,
   "Pressure Drop in Laminar Developing Flow..."; Everts and Meyer, "Laminar
   Hydrodynamic and Thermal Entrance Lengths...".

4. Convert existing CFD section pressure data into named losses.

   Extract `dp_hyd`, `dp_kin`, `dp_straight`, `f_D,Delta_p`, and `K_Delta_p`.
   Name each row `straight_section`, `component_K`, `cluster_K`, or
   `branch_apparent` based on plane placement. Provenance: Lin et al.,
   "Measurement Methods and Techniques for Pressure Losses in Pipe Fittings";
   Csizmadia and Hos, "CFD-Based Estimation...".

5. Separate cooler/jacket heat removal from passive loss.

   Use coolant-side energy balance where available. If not available, fit
   `UA_jacket` only over a stated envelope and keep passive convection,
   radiation, insulation/contact, and heater efficiency separate. Provenance:
   VDI Heat Atlas; Reis, Seo, and Hassan, "Consequences of Molten Salt
   Solidification...".

### Tier 2: Next Modeling Studies

6. Test Chen 2017 as a low-Re molten-salt mixed-convection candidate.

   Only run it for branches whose `Re`, `Pr`, `Gr`, `Gz`, `L/D`, geometry, and
   boundary condition overlap the Chen source envelope. Otherwise keep it as a
   sensitivity comparison. Provenance: Chen et al., "Characteristics of the
   laminar convective heat transfer of molten salt in concentric tube".

7. Build a branchwise internal HTC bakeoff.

   Compare `Nu_FD_ref`, Muzychka-Yovanovich forced developing `Nu`, Chen 2017
   source-bounded mixed `Nu`, CFD-derived `Nu_i`, and section-effective `h_i`.
   Score not only temperature error but also residual movement and physical
   assignment. Provenance: Shah and London, "Laminar Flow Forced Convection...";
   Muzychka and Yovanovich, "Laminar Forced Convection Heat Transfer...";
   Chen et al., "Characteristics...".

8. Create the TAMU fitting inventory and source-status map.

   For each fitting, record type, part number if known, geometry, diameter or
   area ratio, bend radius or miter flag, flow split, velocity basis, pressure
   basis, source candidate, and `K_source_status`. Use unresolved rows to drive
   CFD or measurement. Provenance: Lin et al., "State-of-the-Art Review...";
   Patino-Jaramillo et al., "Laminar Flow and Pressure Loss in Planar Tee
   Joints: Pressure Loss Coefficients"; Salehi et al., "Experimental
   Determination...".

9. Add invalid-single-stream diagnostics to every CFD reduction.

   Track reverse-flow area fraction, reverse mass fraction, secondary velocity
   fraction, recirculation region count/location, and skewed wall heat flux.
   Use these flags to decide when a section coefficient is only
   section-effective. Provenance: Patino-Jaramillo et al., "Laminar Flow and
   Pressure Loss in Planar Tee Joints: Numerical Simulations and Flow
   Analysis"; Chen et al., "Flow and Mixed Convection Heat Transfer of Hitec
   Salt in Multi-Sided Heating Pipes"; Yang et al., "Performance Evaluation..."

10. Bound radiation before declaring it small.

    Use surface temperature, surroundings temperature, exposed area, emissivity
    sensitivity, and view-factor assumptions. If the data are missing, carry
    `epsilon` and view factor as sensitivity, not as zero. Provenance: VDI Heat
    Atlas; Santini et al., "Measurement of Thermal Conductivity..." for the
    general warning that high-temperature molten-salt thermal measurements are
    sensitive to experimental heat paths.

### Tier 3: Experimental and Longer Pathways

11. Add targeted pressure measurements around fitting clusters.

    Use multi-tap or carefully placed upstream/downstream taps, with
    hydrostatic, dynamic, and straight-pipe corrections. Focus first on quartz
    transitions, reducer/expansion clusters, and close-coupled bends. Provenance:
    Lin et al., "State-of-the-Art Review..."; Lin et al., "Measurement Methods
    and Techniques...".

12. Add wall-temperature and surface-temperature instrumentation.

    Internal HTC and passive loss cannot be separated with centerline or bulk
    probes alone. Wall and outer-surface temperatures let the model distinguish
    internal convection, wall conduction, insulation/contact, external
    convection, and radiation. Provenance: Shen et al., "Convective Heat
    Transfer of Molten Salt in Receiver Tube with Axially and Circumferentially
    Non-Uniform Heat Flux"; VDI Heat Atlas.

13. Use CFD as a closure extraction tool, not a final answer by itself.

    CFD products should include mesh evidence, CHT flags, plane placement,
    pressure-basis naming, heat-flux maps, reverse-flow diagnostics, and
    section validity limits. Provenance: Podila et al., "Modelling of Heat
    Transfer in a Molten Salt Loop Using Computational Fluid Dynamics";
    Csizmadia and Hos, "CFD-Based Estimation...".

14. Keep natural-circulation transient work conditional.

    Activate startup, relaxation, oscillation, or freezing models only if the
    thesis scope includes time-dependent behavior. Then add wall/salt storage,
    heater failure states, and stability metrics. Provenance: Welander,
    "On the Oscillatory Instability of a Differentially Heated Fluid Loop";
    Creveling et al., "Stability Characteristics of a Single-Phase Free
    Convection Loop"; Vijayan and Austregesilo, "Scaling Laws for Single-Phase
    Natural Circulation Loops"; Reis, Seo, and Hassan, "Consequences of Molten
    Salt Solidification...".

15. Treat ROM as an archive-design requirement now.

    Even if ROM is future work, start storing the fields it would need:
    velocity, pressure, temperature, wall heat flux, wall temperature,
    `Delta_p_loss`, section `K`, `Nu_i`, heat-loss terms, reverse-flow metrics,
    property mode, heater setting, and jacket setting. Provenance: Manthey et
    al., "Reduced Order Modeling..."; Vergari et al., "Reduced Order Modeling
    Approach..."; Acierno et al., "Development and Application...".

## Research Pathways

| Pathway | Question | Products | Decision Gate |
| --- | --- | --- | --- |
| Source-envelope gate | Which literature correlations actually overlap the TAMU branches? | Branch nondimensional envelope table and source-overlap flags | No source-bounded closure becomes active until overlap is computed. |
| Property-to-closure propagation | How much of the current mismatch is property-driven? | Property sensitivity tables for mass flow, `Re`, `Pr`, `Gz`, pressure, heat residual | Do not calibrate friction or heat loss until property sensitivity is quantified. |
| Hydraulic reset/development | Are branch losses dominated by redevelopment rather than fully developed friction? | Reset map, developing `fRe(L+)` bakeoff, section `f_D,Delta_p` comparison | If residual localizes near reset features, fit cluster/section loss, not global friction. |
| Fitting and quartz transitions | Which fittings need source audit, CFD, or measurement? | Fitting inventory, `K_source_status` map, cluster-loss candidates | Unsupported geometry goes to residual or CFD/measurement priority list. |
| Branchwise HTC | Which thermal closure best explains wall/bulk temperature without hiding heat loss? | `Nu_FD_ref`, forced developing, mixed candidate, CFD `Nu_i`, residual comparison | HTC is not accepted if it improves temperature by corrupting heat-loss residual. |
| Heat-loss calibration | What heat leaves through jacket, passive convection/radiation, heater leakage, and storage? | Resistance-network calibration table and heat residual ledger | No global UA unless labeled as envelope-specific calibration. |
| CFD extraction | What 1D terms can be extracted from CFD with defensible names? | Pressure/heat-transfer section tables plus invalid-single-stream diagnostics | Universal coefficient only if geometry and plane isolation justify it. |
| Experimental upgrade | Which measurements most reduce model uncertainty? | Pressure tap plan, wall/surface/coolant temperature plan, uncertainty estimate | Prioritize measurements that separate ledger terms, not those that only improve total fit. |
| Transient extension | Is startup/freezing/oscillation in scope? | Storage terms, heater failure states, stability indicators | Keep transient literature out of steady closure unless activated. |
| ROM extension | Can CFD/1D data be compressed without losing closure physics? | Snapshot protocol, state vector, validation metrics, stabilization flag | ROM prediction deferred until FOM, snapshots, stabilization, and withheld validation exist. |

## Highest-Value Near-Term Work

1. Build the branch nondimensional envelope and source-overlap table.
2. Run the property-mode sensitivity matrix.
3. Produce a reset-distance map and developing-pressure-loss bakeoff.
4. Convert CFD pressure spans into named section/component/cluster losses.
5. Build the fitting inventory and unresolved `K` source-status table.
6. Calibrate cooling-jacket/passive/radiation heat paths separately.
7. Add invalid-single-stream diagnostics to CFD postprocessing.

## Source Files Used

- `chapters/01_executive_summary.tex`
- `chapters/02_physical_context.tex`
- `chapters/03_hitec_property_models.tex`
- `chapters/04_friction_apparent_friction.tex`
- `chapters/05_developing_heat_transfer.tex`
- `chapters/06_minor_losses_quartz_transition.tex`
- `chapters/07_heat_loss_radiation_cooling.tex`
- `chapters/08_source_audit_findings.tex`
- `chapters/09_recommended_baseline_model.tex`
- `chapters/10_sensitivity_study_matrix.tex`
- `chapters/11_dissertation_safe_claims.tex`
- `chapters/12_assumptions_future_work.tex`
- `chapters/13_implementation_schemas_revision_ledger.tex`
- `chapters/14_final_integration_cfd_postprocessing.tex`
- `chapters/15_second_major_enrichment_and_rom.tex`
- `chapters/16_final_source_audited_revision.tex`
- `appendices/O_rom_methodology_details.tex`
- `appendices/P_unresolved_and_rejected_register.tex`
- `appendices/Q_final_closure_gate_audit.tex`
- `data/claims_ledger.csv`
- `data/correlation_table.csv`
- `data/implementation_ready_recommendations.csv`
- `data/modeling_decision_memo.csv`
- `data/source_audit_master.csv`
- `data/audit_outputs/HITEC_source_validity_envelope_prompt2E.csv`
- `bibliography/references.bib`

## Boundaries

No solver outputs, scheduler state, registry rows, external publication
repositories, or literature-review source files were modified. This package is
a synthesis and planning artifact, not a claim that any new model has been
validated.
