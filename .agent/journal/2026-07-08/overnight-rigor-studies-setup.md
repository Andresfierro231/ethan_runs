# Overnight Rigor Studies Setup

Date: `2026-07-08`
Role: Coordinator / Implementer / Writer
Task ID: `AGENT-218`

## Objective

Identify which closure-rigor follow-up studies can run overnight and set up
bounded jobs that improve provenance or replay evidence without launching
duplicate CFD or mutating solver outputs.

## Current Job State

Observed with `squeue -u andresfierro231`:

- `3282992` `salt1_nom_cont`: running.
- `3275448` `corr_saltq_g1`: running.
- `3275449` `corr_saltq_g2`: running.
- `3275560` `corr_saltq_salt4_all`: running.
- `3280969` `saltq_gate_after`: pending on dependency.
- `3282230`: fixed-mdot replay/background job still running at inspection.

The gate dependency was inspected with:

```bash
squeue -j 3280969 -o "%i %T %M %D %R %E"
```

It reports:

```text
3280969 PENDING ... (Dependency) afterany:3275448(unfulfilled),afterany:3275449(unfulfilled),afterany:3275560(unfulfilled)
```

Interpretation: `3280969` is not waiting on a missing continuation ID. It is
waiting on the current corrected Salt Q production groups. `afterany` is
acceptable if the gate script rejects failed or incomplete run artifacts.

## Setup Completed

- Added `AGENT-218` board row.
- Created `work_products/2026-07-08_overnight_rigor_studies_setup/study_triage.csv`.
- Created `work_products/2026-07-08_overnight_rigor_studies_setup/README.md`.
- Created `work_products/2026-07-08_overnight_rigor_studies_setup/run_overnight_rigor_studies.sbatch`.
- Added operational note
  `operational_notes/07-26/08/2026-07-08_overnight_rigor_studies_setup.md`.

## Submission Attempt

Attempted:

```bash
ssh login3.ls6.tacc.utexas.edu 'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch -t 12:00:00 work_products/2026-07-08_overnight_rigor_studies_setup/run_overnight_rigor_studies.sbatch'
```

TACC rejected the job before submission:

```text
ERROR: Insufficient balance for Project (ASC23046) on (ls6) to run job.
Current Balance: 4314 SUs
Requested in queued jobs: 7638 SUs
```

The batch script is therefore staged but not queued.

## Immediate Lightweight Runs

Ran the read-only pieces locally on compute node `c318-008`:

```bash
python3.11 tools/analyze/check_corrected_salt_preflight.py --audit-out work_products/2026-07-08_overnight_rigor_studies_setup/corrected_salt_preflight/audit.csv --json-out work_products/2026-07-08_overnight_rigor_studies_setup/corrected_salt_preflight/audit.json
python3.11 tools/analyze/monitor_live_corrected_salt.py --output-dir work_products/2026-07-08_overnight_rigor_studies_setup/corrected_salt_monitor/initial --gate-job-id 3280969 --dependency afterany:3275448,3275449,3275560
```

Results:

- Preflight: `Audited 14 corrected Salt cases; failures=0`.
- Monitor: `Scanned 14 corrected Salt cases; special scrutiny flags=4`.
- Flags: Salt1 lo/hi hold for coordinator review; Salt1 hi ended early; Salt3
  hi5/hi10 require investigation due fatal/error markers.

## Overnight Categories

Run/monitor:

- Corrected Salt Q gate support.
- Salt1 continuation monitor.
- Fixed-mdot 1D replay.
- Thermal mismatch remedy replay.

Stage only:

- Full mesh/GCI study.
- Minor-loss coefficient correction.
- Held-out model-form validation.
- Self-consistent Ri validation.

## Caveat

While probing script options, `tools/analyze/build_model_form_bakeoff_from_observations.py`
was invoked with `--help`, but the script has no CLI parser and regenerated its
default package. No native CFD output or solver case tree was touched. The
overnight package avoids using that default output path for its own products.
