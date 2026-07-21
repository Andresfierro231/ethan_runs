# Ethan External Boundary And Setup Reference

Generated: `2026-07-09`
Task: `AGENT-236`
Role: Coordinator / Writer

Tags: #thermal-parity #external-boundary #rcExternalTemperature #patch-role-table
#wallHeatFlux #litrev-synthesis #heat-loss

## Related

- `operational_notes/07-26/10/2026-07-10_NEXT_MEETING_START_HERE.md`
- `operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md`
- `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/README.md`
- `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/README.md`
- `operational_notes/07-26/13/2026-07-13_litrev_synthesis_start_here.md`
- `work_products/2026-07/2026-07-08/2026-07-08_cfd_scenario_contract/README.md`
- `work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/README.md`
- `work_products/2026-07/2026-07-09/2026-07-09_openfoam_boundary_condition_implementation_audit/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/README.md`

## Short Answer

Yes, the Ethan-run external-boundary-condition and setup documentation is now
substantial, but before this package it was fragmented across July 1 and July 8
work products. The most important sources are:

- CFD setup and boundary dictionary audit:
  `work_products/2026-07/2026-07-08/2026-07-08_cfd_scenario_contract/`.
- CFD patchwise thermal contract:
  `work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/`.
- CFD patchwise heat ledger:
  `work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger/`.
- CFD-to-1D heater/cooler comparison policy:
  `operational_notes/07-26/08/2026-07-08_thermal_interface_power_policy.md`.
- 1D setup and confidence note:
  `reports/2026-07/2026-07-01/2026-07-01_local_1d_closure_bakeoff_refresh/2026-07-01_one_d_setup_and_confidence.md`.
- Fixed-mdot replay method and slide-6 interpretation:
  `work_products/2026-07/2026-07-08/2026-07-08_cfd_informed_fixed_mdot_1d_runs/`
  and
  `work_products/2026-07/2026-07-08/2026-07-08_tomorrow_presentation_package/slide6_thermal_replay_analysis.md`.

This report consolidates those sources into one reference. The compact table is
`boundary_setup_summary.csv`; the citation map is `source_index.csv`.

## Reference Files In This Package

- `README.md`: narrative reference and interpretation boundary.
- `boundary_setup_summary.csv`: compact topic-by-topic findings table.
- `source_index.csv`: source map for every major claim.
- `summary.json`: package metadata.

No OpenFOAM extraction, Fluid rerun, or solver-output mutation was performed for
this consolidation.

## Scope And Evidence Boundary

This reference is about the external thermal boundary conditions and setup
contract relevant to the Ethan Salt CFD-to-1D comparison. It primarily covers
the admitted Salt 2/3/4 Jin mainline continuation rows because those are the
current closure/thermal evidence set. Salt 1 remains held pending later
qualification, and corrected-Q perturbation runs remain status or sensitivity
signals until formal gate admission.

This package distinguishes three different things that were easy to mix:

1. The CFD case setup visible in OpenFOAM dictionaries and postprocessed
   `wallHeatFlux`.
2. The current predictive 1D setup in external Fluid.
3. CFD-informed diagnostic replays that intentionally import CFD heat terms to
   isolate thermal-boundary mismatch.

Only the first category is direct CFD setup evidence. The second is the current
1D model state. The third is diagnosis, not a predictive model.

## CFD Setup: What The Ethan Salt Runs Are Doing

### Physical Layer / Insulation Label

The July 8 CFD scenario contract found that readable mainline Salt CFD case
`0/T` boundary files contain a `0.03556 m` layer. That is `1.4 in`, and the
scenario contract labels mainline Salt CFD rows as containing the `1.4 in`
layer. Earlier `0.25 in` or `0.30 in` values in friction or temperature-matching
comparisons are 1D diagnostic/sweep settings, not the CFD case label.

Practical wording:

> The admitted Salt CFD rows should be described as `1.4 in layer present`,
> with surface-emissivity boundary metadata, pending a deeper implementation
> audit of the custom external-temperature boundary condition.

Primary sources:

- `work_products/2026-07/2026-07-08/2026-07-08_cfd_scenario_contract/README.md`
- `work_products/2026-07/2026-07-08/2026-07-08_cfd_scenario_contract/scenario_contract.csv`

### Boundary-Condition Families

The readable mainline Salt case boundary files contain three boundary-condition
families in `0/T`:

- `externalTemperature`
- `rcExternalTemperature`
- `zeroGradient`

For the mainline Salt rows, the scenario contract reports boundary type counts:
`externalTemperature: 10`, `rcExternalTemperature: 36`, and `zeroGradient: 23`.

The thermal contract groups those patches by physical role:

- `heater`: intended heater input.
- `cooler`: intended cooler removal.
- `ambient_wall`: passive ambient exchange.
- `test_section`: explicit quartz/test-section exchange.
- `junction_other`: grouped junction/stub/extension exchange.

This role grouping is the useful way to discuss setup. A single generic label
such as "external temperature boundary" is not enough because the same
case-level setup contains heater, cooler, passive wall, test-section, and
junction roles.

### Emissivity And Radiation

The audited Salt CFD rows preserve emissivity metadata on `rcExternalTemperature`
patches. The scenario contract reports 36 `rcExternalTemperature` patches and
36 emissivity-tagged patches on the mainline rows.

AGENT-277 later strengthened this point with a task-scoped OF13 microcase using
the compiled custom `libRCWallBC.so`: changing only `emissivity` or only `Tsur`
changed realized `wallHeatFlux`. The current interpretation is therefore that
Ethan CFD includes radiative exchange through the custom
`rcExternalTemperature` boundary condition, but the radiative contribution is
not separately exported.

Authoritative per-run values from the AGENT-263 patch table, summarized by
AGENT-287:

| Case | rcExternalTemperature patches | Roles | emissivity | Tsur K | Ta K |
| --- | ---: | --- | ---: | ---: | ---: |
| Salt 2 | 36 | ambient_wall; heater; junction_other; test_section | 0.95 | 299.19 | 299.19 |
| Salt 3 | 36 | ambient_wall; heater; junction_other; test_section | 0.95 | 299.79 | 299.79 |
| Salt 4 | 36 | ambient_wall; heater; junction_other; test_section | 0.95 | 299.97 | 299.97 |

AGENT-277 final-time OF13 microcase deltas:

| Perturbation | delta wallHeatFlux Q W | Interpretation |
| --- | ---: | --- |
| emissivity `0.95 -> 0.10` | -658.64271204 | emissivity affects realized heat flux |
| emissivity `0.95 -> 0.00` | -809.14474124 | removing emissivity changes realized heat flux |
| `Tsur 299.19 K -> 350 K` | 1912.49758926 | surroundings temperature affects realized heat flux |

The same audits still found no `constant/radiationProperties` and no exported
`qr` or `G` field in the audited case roots. The older patchwise heat-ledger
field `radiation_present=False` should be read narrowly as "no separate
OpenFOAM radiation output term was found," not as proof that the boundary
condition has no radiative exchange.

Interpretation:

- Surface emissivity metadata is present and active in the custom boundary
  condition.
- A separate OpenFOAM radiation heat-rate ledger term is not available.
- Do not add a separate radiation correction on top of CFD `wallHeatFlux`.
- Do not describe the CFD as "radiation absent" or "no-radiation parity." The
  precise label is radiative exchange embedded in `rcExternalTemperature`
  `wallHeatFlux`, with no exported separate radiation term.

This matters because the 1D model has a `radiation_on` switch, but that switch
is not equivalent to a CFD `qr` output term.

For 1D agents:

- CFD-informed replays that consume CFD `wallHeatFlux` must not add a separate
  1D radiation term on top of that heat rate.
- Forward/predictive 1D models from physical setup inputs should retain or add
  radiative external-loss capability. A radiation-off run is a diagnostic
  sensitivity, not Ethan-CFD equivalence.

Primary current sources:

- `work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/cfd_emissivity_by_run.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_publication_evidence/wallHeatFlux_delta_summary.csv`
- `.agent/DECISIONS.md`

## CFD Heat Boundary Roles And Numbers

The July 8 patchwise heat ledger uses the OpenFOAM wallHeatFlux convention:
positive is heat into the fluid; negative is heat out of the fluid.

### Heater

The CFD heater row is a heater-input boundary role, but the imposed heater duty
is not identical to realized heat entering the fluid through the heater patch
group.

| Case | Imposed heater duty W | Heater wallHeatFlux into fluid W | Gap W |
| --- | ---: | ---: | ---: |
| Salt 2 | 265.700 | 243.519 | 22.181 |
| Salt 3 | 297.500 | 273.155 | 24.345 |
| Salt 4 | 337.600 | 310.487 | 27.113 |

The comparison policy is to use realized CFD heater `wallHeatFlux` for
CFD-informed 1D comparison, not idealized resistor/electrical duty. The gap is
a boundary/solid/storage/staging caveat until a same-time solid-energy audit
exists.

Primary sources:

- `work_products/2026-07/2026-07-08/2026-07-08_thermal_mismatch_remedy_deep_dive/heater_values.csv`
- `operational_notes/07-26/08/2026-07-08_thermal_interface_power_policy.md`

### Cooler / HX

For the admitted Salt 2/3/4 CFD rows, cooler specified duty and cooler
wallHeatFlux align closely. The CFD cooler removal magnitudes are:

| Case | CFD cooler removal W |
| --- | ---: |
| Salt 2 | 136.351 |
| Salt 3 | 150.770 |
| Salt 4 | 169.227 |

The current 1D predictive-airside-HX baseline removes only about `46-54 W`
through the HX at fixed CFD mdot:

| Case | Fixed-mdot current 1D qhx W | CFD cooler removal W |
| --- | ---: | ---: |
| Salt 2 | 46.292 | 136.351 |
| Salt 3 | 49.663 | 150.770 |
| Salt 4 | 53.472 | 169.227 |

This mismatch is the dominant current external-boundary issue. The fixed-mdot
replay that prescribes CFD cooler duty only reduces mean loop-temperature error
from about `63.75 K` to about `4.46 K` across Salt 2/3/4.

### Test Section

The current external Fluid salt case inputs include a separate `37 W`
test-section source. The CFD patchwise ledger instead sees the test section as
a net sink for the admitted Salt 2/3/4 rows:

| Case | CFD test-section wallHeatFlux W |
| --- | ---: |
| Salt 2 | -5.680 |
| Salt 3 | -10.545 |
| Salt 4 | -16.769 |

The sign and source/sink mismatch should remain explicit. The current 1D
`37 W` test-section source is part of the active Fluid salt contract, but it is
not the same object as CFD realized test-section wallHeatFlux.

### Passive Ambient Walls

Passive wall exchange is grouped under `ambient_wall` in the CFD ledger. The
ledger reconstructs the available resistance stack from wallHeatFlux, wall and
bulk temperatures, boundary layer thickness and conductivity, boundary `h`, and
ambient temperature where available.

Aggregate CFD ambient-wall wallHeatFlux sums:

| Case | ambient_wall wallHeatFlux W |
| --- | ---: |
| Salt 2 | -62.234 |
| Salt 3 | -68.320 |
| Salt 4 | -75.927 |

Resolved ambient temperatures are about `299.19 K`, `299.79 K`, and `299.97 K`
for Salt 2/3/4. Boundary `h` values in the resolved rows span roughly
`3.424-10.060 W/m2-K`, depending on case and patch role.

Interpretation:

- Passive ambient exchange is real and measurable in the ledger.
- It is not yet a simple one-parameter calibration target.
- A global 1D insulation scalar is too blunt for a paper-grade reconstruction
  of the CFD patchwise wall stack.

### Junctions

`junction_other` groups stubs, extensions, and mixed boundary-condition corner
patches. These rows are not bracketed by clean endpoint-temperature spans.

Aggregate CFD junction wallHeatFlux:

| Case | junction_other wallHeatFlux W |
| --- | ---: |
| Salt 2 | -39.128 |
| Salt 3 | -43.235 |
| Salt 4 | -48.485 |

Treat this as diagnostic heat accounting, not a clean segment-level closure
target yet.

## Current 1D Setup: What Fluid Is Doing

The July 1 local 1D closure bakeoff documents the defended current 1D setup:

- Solver lineage:
  `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2`.
- Active mode:
  `predictive_airside_hx`.
- Defended full-coverage scenario:
  `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`.
- Base insulation:
  `1.0 in`.
- Radiation:
  `radiation_on = true`.
- Salt heat inputs:
  heater power plus a separate `37 W` test-section source.
- Cooler:
  predictive air-side HX model, not prescribed CFD cooler duty.

The key limitation is that this defended 1D scenario is not already a global
`1.4 in` physically matched CFD boundary scenario. The readable external Fluid
bundle published base `1.0 in` and `2.0 in` rows plus some hybrid branchwise
multipliers; the July 1 note explicitly says that if the representative CFD
setup is globally `1.4 in`, the defended winner is a setup-mismatched surrogate
until that condition is rerun or explicitly published.

Primary sources:

- `reports/2026-07/2026-07-01/2026-07-01_local_1d_closure_bakeoff_refresh/2026-07-01_one_d_setup_and_confidence.md`
- `reports/2026-07/2026-07-01/2026-07-01_local_1d_closure_bakeoff_refresh/README.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/cases.yaml`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/scenarios.yaml`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`

## Fixed-mdot Diagnostic Replays

The July 8 fixed-mdot replays are diagnostic thermal replays, not fully
predictive hydraulic solves. They hold mdot equal to CFD, solve only thermal
periodicity, and report pressure residual diagnostically.

The focused slide-6 comparison is:

| Replay path | Meaning | Mean `|Tmean error|` |
| --- | --- | ---: |
| `P0` baseline current 1D | Current Fluid thermal contract at CFD mdot | 63.75 K |
| `P1` CFD cooler duty only | Replace predictive HX duty with CFD cooler wallHeatFlux magnitude | 4.46 K |
| `P4` CFD cooler + heater flux | Prescribe CFD cooler duty and CFD heater wall flux | 39.75 K |

The scientific interpretation is that cooler duty is the strongest single
thermal-state lever. Adding heater wall flux at the same time over-corrects
because it reduces the source side while the stronger CFD cooler sink remains
imposed. That result is not a reason to abandon realized heater wallFlux; it is
a warning that source, sink, passive-loss, and thermal-periodicity semantics are
coupled.

## Setup Claims That Are Safe Now

These claims are supported by the current documentation:

- The admitted Salt CFD setup should be described as having a `1.4 in` layer
  present in the wall boundary stack.
- CFD `rcExternalTemperature` patches include active surface-emissivity/Tsur
  radiative exchange embedded in total `wallHeatFlux`, but there is no exported
  separate `qr`/`G` radiation heat term in the current ledger.
- CFD-informed heater comparison should use heater `wallHeatFlux` into the
  fluid, not resistor/imposed duty.
- CFD-informed cooler comparison should use cooler patch `wallHeatFlux` removed
  from the fluid, not the current idealized 1D cooler capacity.
- The current 1D defended predictive scenario is `1.0 in`, radiation-on,
  predictive-airside-HX, with salt heater power plus `37 W` test-section source.
- The current 1D predictive cooler/HX model under-removes heat relative to CFD
  cooler wallHeatFlux by about `90-116 W` across admitted Salt 2/3/4.
- Fixed-mdot replays are thermal-boundary diagnostics, not predictive hydraulic
  validation.

## Claims That Still Need Care

These claims should not be made without further work:

- Do not claim the current 1D defended setup is physically matched to the CFD
  `1.4 in` boundary stack.
- Do not claim radiation is absent in the CFD; say radiative exchange is
  embedded in `rcExternalTemperature` `wallHeatFlux`, but no separate `qr`
  radiation heat term is exported.
- Do not claim full predictive agreement from CFD-informed replays that
  prescribe CFD heater or cooler duties.
- Do not use junction heat or high-recirculation upcomer residuals as ordinary
  segment closure targets.
- Do not use Salt 1 or corrected-Q rows as current nominal setup evidence until
  their gates are explicitly updated.

## Recommended Thesis / Paper Wording

Use wording like this:

> The admitted Salt CFD cases use OpenFOAM thermal boundary patches grouped into
> heater, cooler, passive ambient wall, test-section, and junction roles. The
> audited boundary dictionaries contain a 0.03556 m wall-layer entry, labeled
> here as a 1.4 in layer. The `rcExternalTemperature` patches carry emissivity
> and surroundings-temperature inputs, and microcase evidence shows those inputs
> affect realized `wallHeatFlux`; radiative exchange is therefore embedded in
> total CFD `wallHeatFlux`. No separate `qr` or `G` radiation field was
> available in the retained outputs, so CFD heat ledgers use total
> `wallHeatFlux` and do not add a separate radiation correction. For
> CFD-informed 1D comparison, heater and cooler powers are taken from realized
> CFD fluid-interface `wallHeatFlux`, not from idealized electrical heater duty
> or idealized 1D cooler capacity. Fully predictive 1D comparison remains
> limited by the need to predict heater-to-fluid power and cooler removal from
> geometry and external boundary conditions.

## Next Actions

1. Build or run a physically matched 1D scenario that reconstructs the CFD
   `1.4 in` wall/layer contract and patch-role external boundary network.
2. Continue trying to recover the exact `rcExternalTemperature` source for
   publication-strength source-level support. Current binary and microcase
   evidence already show emissivity/Tsur affect total `wallHeatFlux`; what is
   still missing is a source-level decomposition or separate radiation output.
3. Add a first-class Fluid fixed-mdot or frozen-hydraulics replay mode so
   thermal replays cannot be confused with pressure-root predictive solves.
4. Build predictive heater and cooler submodels. CFD-informed replays are useful
   diagnostics, but thesis/paper-grade forward prediction needs those boundary
   powers predicted rather than imported.
5. Keep mesh/GCI, time-window uncertainty, and admission gates attached to all
   final setup/closure tables.
