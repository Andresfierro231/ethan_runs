# Water Provisional And Corrected Salt Gate

Date: `2026-07-07`
Task: `AGENT-181`
Role: Coordinator / Implementer / Writer

## Context

The user requested that the July 6 Water outputs be used for provisional
reporting while preserving the caveat that Water came from a timeout/frozen
final window. The same request asked for a reusable corrected-Salt preflight
checker, a rerun of the operating-point gate after Salt finishes, and continued
exclusion of false-steady perturbations from closure fitting.

## Observed Output

- Water postprocess job `3278452` completed and wrote July 6 Water run-status
  outputs under
  `work_products/2026-07-06_overnight_postprocess_jobs/water_postprocess_after_3265970/`.
- Water source job `3265970` is `TIMEOUT`. The four Water monitor rows are
  `quasi_stationary` overall/hydraulic and `stationary` thermal, but they are
  provisional because they come from a timeout endpoint.
- The July 6 consolidated closure table contains no Water closure rows. It can
  not be used as Water closure-fit evidence.
- Corrected Salt parent jobs `3275448`, `3275449`, and `3275560` were still
  running at the July 7 check.
- The earlier Salt gate job `3278453` was `CANCELLED` before writing outputs.

## Implementation

Added the reusable read-only checker:

- `tools/analyze/check_corrected_salt_preflight.py`
- `tools/analyze/test_check_corrected_salt_preflight.py`

The checker reads the corrected-case manifest, derives target heater patch Q
and cooler patch Q values, and validates:

- `case_config.yaml` heater power and heater Q;
- root `0/T` target patch counts and values;
- latest `processors64/<time>/T` target patch counts and values;
- collated `decomposedBlockData` processor byte-frame integrity.

The live corrected-Salt audit found `14/14` cases passing, with 64 processor
blocks and zero frame errors for every case:

- `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/corrected_salt_preflight_audit.csv`

Prepared a replacement post-run gate wrapper:

- `tmp/2026-07-07_corrected_salt_gate/run_corrected_salt_gate_after_live_jobs.sbatch`

Submitted it through `login3`:

- `3279646` `saltq_gate_0707`
- dependency: `afterany:3275448:3275449:3275560`

Added the reusable live sanity monitor:

- `tools/analyze/monitor_live_corrected_salt.py`
- `tools/analyze/test_monitor_live_corrected_salt.py`

The monitor writes CSV/JSON/README under:

- `work_products/2026-07-07_corrected_salt_live_monitor/`

It records job IDs, Slurm partition/state/dependency, latest solver times,
fatal/error scans, mdot movement checks, and an admit/hold/investigate
recommendation. Current output scanned 14 cases and found four rows with
`needs_special_gate_scrutiny=True`:

- `salt1_jin_lo10q_corrected`: missing nominal Salt 1 mdot reference.
- `salt1_jin_hi10q_corrected`: missing nominal Salt 1 mdot reference and
  convergence/solver `End` after `254.259 s` past restart, only `4.24%` of the
  target extension.
- `salt3_jin_hi5q_corrected`: canceled job `3275450`, fatal/error markers,
  `21.476 s` past restart.
- `salt3_jin_hi10q_corrected`: canceled job `3275450`, fatal/error markers,
  `19.876 s` past restart.

## Report Package

Created:

- `reports/2026-07/2026-07-07/2026-07-07_water_provisional_and_corrected_salt_gate/README.md`
- `reports/2026-07/2026-07-07/2026-07-07_water_provisional_and_corrected_salt_gate/summary.json`
- `imports/2026-07-07_water_provisional_and_corrected_salt_gate.json`

The report separates observed Water monitor status, inferred provisional use,
and non-admissible closure/ROM uses.

Added Water language audit artifacts:

- `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/water_provisional_language_audit.csv`
- `work_products/2026-07-07_water_provisional_and_corrected_salt_gate/water_provisional_language_audit.json`

The audit checked six artifacts and found the timeout/frozen-window caveat,
closure-fit block, and ROM-correlation block present in all six.

## Admission Boundary

False-steady perturbations remain excluded from closure fitting and ROM
correlation fitting. Corrected Salt rows remain inadmissible until the
replacement gate writes `run_status/run_status_inventory.csv` and any row
intended for fitting has `operating_point_verdict=requalified`.

No corrected Salt row with `needs_special_gate_scrutiny=True` is closure-fit
admissible without coordinator review, even if a later formal gate appears to
requalify it.

Water July 6 outputs are provisional monitor-status evidence only until a later
package provides explicit Water closure extraction with the timeout caveat.

## Validation

- `python -m pytest tools/analyze/test_check_corrected_salt_preflight.py`:
  `3 passed`.
- `python -m pytest tools/analyze/test_monitor_live_corrected_salt.py tools/analyze/test_check_corrected_salt_preflight.py`:
  `8 passed`.
- `python -m py_compile tools/analyze/check_corrected_salt_preflight.py tools/analyze/test_check_corrected_salt_preflight.py`:
  passed.
- `python -m py_compile tools/analyze/monitor_live_corrected_salt.py tools/analyze/check_corrected_salt_preflight.py`:
  passed.
- `bash -n tmp/2026-07-07_corrected_salt_gate/run_corrected_salt_gate_after_live_jobs.sbatch`:
  passed.
- `python tools/analyze/check_corrected_salt_preflight.py ...`: audited `14`
  cases, `0` failures.
- `python tools/analyze/monitor_live_corrected_salt.py --no-scheduler ...`:
  scanned `14` cases, `4` special-scrutiny flags.
- `squeue -j 3275448,3275449,3275560,3279646`: replacement gate pending on
  dependency; parent jobs running.

## Evening Supersession: Gate Cancellation and Salt 1 Review

Later on `2026-07-07`, the gate plan above was superseded. A dependency-gated
continuation submission for `corr_saltq_g1` after `3275448` was attempted from
`login3`, but Slurm rejected it because project `ASC23046` had `4633` SUs
remaining and `4688` SUs already requested by running/waiting jobs. No
continuation job ID was created. Because the old gate would have run after the
original live jobs rather than after the desired extensions, gate jobs `3279638`
and `3279646` were canceled. `sacct` reports both with state
`CANCELLED by 890970` and no start time.

Coordinator review of `salt1_jin_hi10q_corrected` found a clean solver stop,
not a crash. The log reports
`*** convergenceMonitor: CONVERGED at iteration 640600` at
`Time = 4010.590361446s`, followed by `End`. The case `controlDict` still had
`stopAt endTime` and `endTime 9756.33125`, while `system/functions` contains a
coded `convergenceMonitor` with `rtol = 0.0001` that calls
`stopAt(writeNow)` when global `Tmean`, `Tsigma`, `Umean`, and residual checks
pass. Interpretation: Salt 1 high-Q only advanced `254.259 s` because the weak
global monitor declared convergence and forced a clean early write/stop.

Salt 1 corrected-Q rows remain non-admissible for closure fitting. They require
a coordinator-approved Salt 1 nominal mdot reference and, if still needed, a
continuation/rerun with the convergence monitor disabled or made
non-terminating, followed by operating-point movement checks and quasi-steady
time-window UQ. The current continuation submission remains blocked until
allocation balance frees up or a different approved allocation is used.
