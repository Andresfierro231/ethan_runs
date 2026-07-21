# 2026-07-10 CFD-1D Thermal Parity Roadmap

Tags: #thermal-parity #external-boundary #internal-nu #patch-role-table
#rcExternalTemperature #energy-contract

## Related

- `operational_notes/07-26/10/2026-07-10_NEXT_MEETING_START_HERE.md`
- `operational_notes/07-26/10/2026-07-10_end_of_day_todo.md`
- `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md`
- `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/README.md`
- `work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/README.md`

## Purpose

This note records the agreed direction for the next thermal-modeling push:
make the 1D model match the CFD thermal boundary/source contract as closely as
possible, then use the remaining section-by-section heat-transfer mismatch to
study internal thermal development, stratification, and effective wall-adjacent
temperature.

This is separate from the generic end-of-day operations note. It is the
scientific roadmap for the next thermal parity study.

## Core Understanding

The 3D OpenFOAM CFD and the 1D Fluid model are similar only at a high level:
both reject heat to an ambient environment through a wall/insulation boundary.
They are not currently equivalent in the details of that outer thermal circuit.

Current interpretation:

- CFD uses patch-level OpenFOAM thermal boundary conditions such as
  `rcExternalTemperature`, `externalTemperature`, and `zeroGradient`.
- The CFD boundary dictionaries carry patch-specific external `h`, ambient /
  surroundings temperatures, wall/layer metadata, and emissivity/Tsur metadata.
- The 1D model currently computes external natural convection internally and
  can also add radiation through its own switch.
- The next parity mode should replace the 1D external closure with the CFD
  boundary-condition contract wherever possible.

The point of the parity mode is not to overfit temperatures. It is to remove
avoidable boundary-condition mismatch so the remaining disagreement isolates
the internal-flow thermal problem.

## Decisions Locked In

### Patch-Level Exactness Is The Target

We should match the CFD boundary condition at patch level as far as feasible,
then document any reduction to segment-level equivalents.

Reason:

- Temperature-probe comparisons depend on local thermal history and local
  boundary roles.
- Segment averages may be acceptable for a first diagnostic run, but paper-grade
  interpretation needs to know what each patch represents.
- Every patch should be mapped to a role: heater, cooler, passive ambient wall,
  test section, junction/stub/other, or zero-gradient/NCC connector.

Feasibility:

- Feasible as a documentation and extraction problem: the patch names and `0/T`
  dictionaries exist.
- Feasible as a first 1D diagnostic if patch rows can be collapsed into
  segment-level equivalent conductances and heat terms.
- Harder as a predictive 1D model if the patch layout needs sub-segment
  temperature states near probe locations. That is likely a second step.

### Realized Versus Imposed Heat Terms Must Stay Separate

Use both, but do not mix their meanings.

- For diagnosis, use realized CFD `wallHeatFlux` by patch/role. This answers:
  "If the 1D model is given the same realized heat source/sink terms, where
  does it still disagree?"
- For setup documentation, record imposed OpenFOAM boundary inputs. This
  answers: "What was the CFD case instructed to do?"

The gap between imposed and realized terms is itself evidence. For example,
heater imposed duty and heater wallHeatFlux are not identical in the current
Salt rows, while cooler specified duty and realized cooler wallHeatFlux are
much closer.

### Radiation / Emissivity Must Be Audited, Not Assumed

Working policy:

- Do not leave 1D radiation on just because the 1D baseline has it.
- Audit whether the OpenFOAM `rcExternalTemperature` implementation actually
  uses `emissivity` and `Tsur` in the heat-flux calculation.
- If it does, reproduce that term in 1D parity mode.
- If it does not, or if no heat-rate term can be separated, keep 1D radiation
  off and document that CFD surface-emissivity metadata is present but not a
  separate exported radiation ledger.

This audit should inspect both dictionaries and the actual OpenFOAM boundary
condition implementation used in the run environment, not only the presence of
metadata fields.

### Matching Targets, In Order

Use this order to avoid overfitting:

1. Total heat balance.
2. Branch/section heat loss and gain.
3. Station/probe temperatures.
4. Wall temperatures.

The first two are energy-contract tests. The last two are more sensitive to
internal stratification, probe placement, local wall gradients, and mesh/probe
support.

### Internal Thermal Model Direction

Preferred scientific direction:

- Predict development length and thermal profile evolution where possible.
- Use boundary-layer/developing-flow theory to estimate an effective
  wall-adjacent temperature or mixing factor.
- Treat an effective internal HTC/Nu that varies with development as a fallback
  or intermediate diagnostic, not the first-choice physical story.

Practical direction:

- Build diagnostic mode first.
- Use diagnostic mode to identify which sections require an internal
  development correction.
- Then build a predictive mode informed by literature-review models and CFD
  observations, with fit/validation separation.

## Why The Internal Problem Is Hard

In 3D, the fluid temperature near the wall can differ strongly from the
cross-section-average temperature. Developing thermal boundary layers,
inclined-leg buoyancy, bends, and recirculation can produce stratified flow.

The 1D model has one bulk temperature per segment state. If heat loss is driven
by a wall-adjacent temperature rather than the cross-section mean, then a
standard `q = UA * (T_bulk - T_ambient)` form can be wrong even when the
external wall/insulation boundary condition is correct.

Therefore, the next model should separate:

- external resistance parity,
- imposed/realized source-sink parity,
- internal wall-adjacent temperature or internal resistance,
- and local probe/station temperature comparison.

## Proposed Study Ladder

### Study 1: Boundary Dictionary Audit

Goal:
Create a patch-level table of all thermal boundary patches for the current
mainline CFD rows.

Required outputs:

- patch name
- case/source id
- boundary type
- physical role
- area if available
- parent 1D segment/span
- `h`, `Ta`, `Tsur`, emissivity
- layer thicknesses and conductivity coefficients
- imposed heat term if present
- realized wallHeatFlux if available
- whether the patch is admissible for passive ambient comparison, heater
  comparison, cooler comparison, test-section comparison, or diagnostic only

### Study 2: rcExternalTemperature Implementation Audit

Goal:
Answer whether `emissivity` and `Tsur` affect the OpenFOAM wall heat flux.

Required outputs:

- source file or compiled-library provenance for `rcExternalTemperature`
- formula used by the boundary condition
- whether radiation is present as a heat-flux contribution
- whether any radiation contribution can be separated from total wallHeatFlux
- exact parity instruction for 1D radiation: off, included, or inseparable

### Study 3: 1D External-BC Parity Mode

Goal:
Run 1D with the same external wall/layer boundary contract as CFD.

Requirements:

- Replace 1D natural-convection external `h` with CFD patch/segment equivalent
  `h`.
- Use CFD ambient/surroundings temperature consistently.
- Use CFD wall/layer resistance metadata.
- Turn off 1D radiation unless Study 2 proves an equivalent CFD radiation term
  is active.
- Record any patch-to-segment averaging formula.

### Study 4: Source/Sink Parity Mode

Goal:
Compare imposed-input and realized-wallFlux versions.

Two modes:

- `setup_documentation_mode`: use imposed CFD heater/cooler/test-section inputs.
- `diagnostic_realized_mode`: use realized CFD wallHeatFlux by role.

The second mode is not predictive, but it is the cleanest way to isolate
internal thermal-development mismatch after source/sink mismatch is removed.

### Study 5: Section Heat-Loss Decomposition

Goal:
Compare where heat leaves or enters the loop in CFD versus 1D.

Priority sections:

- upcomer
- test section
- downcomer/right leg
- heater-side branches
- cooler/HX branch
- junction/stub/other groups

Outputs:

- total heat balance
- branch/section heat gain/loss
- residual by section
- flags for recirculation, sign instability, poor bulk-temperature support, or
  missing patch coverage

### Study 6: Internal Thermal-Development Diagnostic

Goal:
Determine whether each section needs:

- standard bulk-temperature HTC,
- a wall-adjacent temperature model,
- a developing-length correction,
- an effective internal HTC multiplier,
- or a recirculation/stratification-specific treatment.

This should be diagnostic first and predictive second.

### Study 7: Predictive Internal Model

Goal:
Build a predictive internal thermal closure using the literature review plus
admitted CFD evidence.

Candidate directions:

- developing laminar thermal boundary layer model,
- Graetz-number or entry-length model,
- mixed-convection/Richardson-number correction,
- stratified wall-adjacent temperature factor,
- branch-class model for upcomer/downcomer/test section,
- effective HTC multiplier only where a physical profile model is not yet
  defensible.

## What To Submit / Run

Do not submit a new thermal-parity compute job tonight.

Current scheduler state from `sacct` during this note:

- `3282992` Salt1 nominal is still running.
- `3288671` selected corrected-Q packed job is still running for Salt1 -10Q and
  Salt1 +10Q, while Salt4 +10Q failed.

Operational submissions already covered by the end-of-day note:

- Wait for `3282992` terminal evidence before any Salt1 nominal admission.
- Wait for surviving `3288671` steps to exit before post-continuation gates.
- Repair Salt4 +10Q corrected time precision before any single-row resubmit.

Thermal-parity next submissions should wait until at least Study 1 and Study 2
produce clear setup contracts. The first runnable thermal task should be a
read-only audit/extraction package, not a new CFD job.

## Concrete TODOs For Next Work

1. Claim a new task for `thermal_boundary_patch_role_table`.
2. Build the patch-level boundary dictionary table from current mainline Salt
   rows, preserving patch names and physical roles.
3. Audit the `rcExternalTemperature` implementation and write the exact heat
   flux formula.
4. Define patch-to-1D-segment reduction rules with areas/resistances, not only
   string matching.
5. Draft the 1D parity-mode specification before editing Fluid.
6. Implement diagnostic 1D parity mode only after the specification is reviewed.
7. Run total heat balance first, then branch heat-loss comparison.
8. Use station/probe and wall-temperature comparisons only after energy-contract
   parity is understood.
9. Use the revamped literature review to choose predictive internal-development
   model candidates.
10. Keep diagnostic realized-wallFlux modes clearly separate from predictive
    imposed/setup modes in all plots and labels.

## End-Goal Statement

The end goal is a predictive 1D model whose external wall, insulation,
ambient, heater, cooler, and test-section boundary contracts are consistent
with CFD, while the internal thermal-development model accounts for the fact
that the 3D wall-adjacent fluid temperature may not be represented by the 1D
cross-section-average bulk temperature.

That is the key modeling challenge: match net heat transfer to the environment
without hiding the internal physics inside an overfit global HTC.
