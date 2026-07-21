# CFD Scenario Contract And Observation Table

Date: `2026-07-08`
Task: `AGENT-202`
Role: Coordinator / Implementer / Writer
Owner: codex

## User Questions

The user asked why gate job `3280969` was a problem, requested that the formal
corrected-Salt operating-point gate run after proper terminal jobs complete,
asked whether nominal Jadyn Salt 1 converged or has a usable continuation, and
requested a deep dive on the scientific redo: correct insulation/radiation
classification, canonical observation table, and latest relevant continuation
windows.

## Scheduler Interpretation

`3280969` is acceptable if the currently running live corrected-Salt jobs
`3275448`, `3275449`, and `3275560` are treated as the terminal jobs available
for this compute period. It is pending with dependency
`afterany:3275448:3275449:3275560`.

The earlier concern only applies if the plan requires extra continuation jobs
after those live jobs. Since the user currently has no compute and wants to work
with existing runs, no cancellation was performed.

## Nominal Salt 1

Nominal Salt 1 did end cleanly by the coded global convergence monitor:

- June 18 mainline candidate:
  `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt1_jin/...`
  latest retained time `3756.33125 s`.
- June 25 normal-relaunch base continuation:
  `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/runs/salt1_jin_basecont/...`
  latest retained time `4026.15625 s`.

Interpretation: Salt 1 has a later usable candidate for a qualification pass,
but it should not be promoted automatically into closure fitting. Existing
notes flag weak heat closure and short-window/nominal-reference caveats.

## Scenario Contract Audit

Built:

- `tools/analyze/build_cfd_scenario_contract.py`
- `work_products/2026-07-08_cfd_scenario_contract/**`

Raw findings from audited `0/T` files:

- all audited Salt mainline and corrected-Q roots contain layer `0.03556 m`,
  equal to `1.4 in`;
- other wall-stack layers include `0.006096`, `0.003175`, `0.0022`, and
  `0.001651 m`;
- `rcExternalTemperature` patches carry `emissivity 0.95`;
- no `constant/radiationProperties`, `qr`, or `G` field was found.

Interpretation:

- the actual CFD setup should be labeled as `1.4 in layer present`;
- the `0.25/0.30 in` values are 1D diagnostic matched-temperature settings,
  not the CFD setup;
- radiation should be labeled
  `surface_emissivity_bc_present_no_volume_radiation_field` pending review of
  the custom `rcExternalTemperature` implementation.

## Latest Window Audit

Available retained times from live case trees:

- Salt 1 June 18 mainline: `3756.33125 s`
- Salt 1 June 25 base continuation: `4026.15625 s`
- Salt 2 June 18 mainline: `7915 s`
- Salt 3 June 18 mainline: `7618 s`
- Salt 4 June 18 mainline: `10000 s`

Prior source-contract rows are older for Salt 1/2/3/4. This does not invalidate
older products, but it means they are frozen-window products and must be labeled
as such. A final closure fit should use one declared latest-window contract.

## Observation Table Seed

`closure_observations_seed.csv` contains `132` rows:

- `72` pressure-span term rows;
- `24` patch heat-flux rows;
- `36` time-window QOI rows.

The seed table carries units, source paths, fit/validation eligibility, gate
verdicts, and quality flags. It deliberately holds Salt 1 and corrected-Q rows
out of closure fitting until their separate gates resolve.

## Validation

- `python3.11 tools/analyze/build_cfd_scenario_contract.py`
- `python3.11 -m py_compile tools/analyze/build_cfd_scenario_contract.py`

Both passed.
