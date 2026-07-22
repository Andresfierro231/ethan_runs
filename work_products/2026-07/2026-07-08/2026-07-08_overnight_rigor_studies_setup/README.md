# Overnight Rigor Studies Setup

Date: `2026-07-08`
Task: `AGENT-218`

## Purpose

This package triages the rigor-strengthening studies from the closure-fit
review and sets up only the parts that can run overnight without launching new
native CFD or mutating solver outputs.

## What Can Run Overnight

1. Corrected Salt Q admission support.
   The corrected Salt Q jobs are already running and the formal gate job is
   already pending:
   - `3275448` `corr_saltq_g1`
   - `3275449` `corr_saltq_g2`
   - `3275560` `corr_saltq_salt4_all`
   - `3280969` `saltq_gate_after`, dependency
     `afterany:3275448,3275449,3275560`

   The overnight job only monitors and snapshots this state; the formal gate
   remains the admission authority.

2. Salt 1 nominal continuation monitoring.
   `3282992` `salt1_nom_cont` is already running. It can run overnight, but its
   output is not closure evidence until it passes a late-window convergence and
   scenario-contract gate.

3. Fixed-mdot 1D thermal replay.
   The existing replay script can run on a compute node without editing the
   external Fluid source. It writes a fresh copy under
   `fixed_mdot_replay/` and keeps hydraulic pressure residuals diagnostic-only.

4. Thermal mismatch remedy replay.
   The existing remedy builder can rerun into `thermal_mismatch_replay/` for a
   timestamped overnight copy of the current four-path replay analysis.

## What Should Not Be Launched Blindly Tonight

- Full mesh/GCI uncertainty: the current GCI artifact is only a one-QOI example.
  A full mesh study needs a scoped builder and mesh-level source inventory.
- Minor-loss coefficient revision: the control-volume contradiction must be
  resolved before an automated correction is meaningful.
- Held-out model-form validation: blocked until corrected Salt and/or Salt 1
  rows are formally admitted.
- Ri validation: useful next task, but needs a common same-window CFD-vs-1D Ri
  schema first.

## Launch Status

Prepared command:

```bash
sbatch -t 12:00:00 work_products/2026-07-08_overnight_rigor_studies_setup/run_overnight_rigor_studies.sbatch
```

Submission was attempted through `login3.ls6.tacc.utexas.edu` on
`2026-07-08`, but TACC rejected the job before submission:

```text
ERROR: Insufficient balance for Project (ASC23046) on (ls6) to run job.
Current Balance: 4314 SUs
Requested in queued jobs: 7638 SUs
```

The script remains ready to submit after queued/running encumbrance clears or
the allocation issue is resolved.

Monitor with:

```bash
squeue -j <jobid>
tail -40 work_products/2026-07-08_overnight_rigor_studies_setup/slurm-rigor_overnight-<jobid>.out
tail -40 work_products/2026-07-08_overnight_rigor_studies_setup/slurm-rigor_overnight-<jobid>.err
```

## Expected Outputs

- `study_triage.csv`
- `job_environment.txt` if the batch job is later accepted
- `corrected_salt_preflight/audit.csv`
- `corrected_salt_preflight/audit.json`
- `corrected_salt_monitor/**`
- `fixed_mdot_replay/**` if the batch job is later accepted
- `thermal_mismatch_replay/**` if the batch job is later accepted
- `snapshots/*_squeue.txt` if the batch job is later accepted
- `logs/*.log` if the batch job is later accepted

## Initial Lightweight Outputs

Run immediately from the current compute-node shell:

- Corrected Salt preflight audit:
  `Audited 14 corrected Salt cases; failures=0`.
- Corrected Salt live monitor:
  `Scanned 14 corrected Salt cases; special scrutiny flags=4`.

Initial flags:

- Salt1 low/high corrected-Q rows remain coordinator-review only because the
  monitor lacks a nominal mdot reference; Salt1 high also ended early.
- Salt3 high-Q corrected rows show fatal/error markers and require
  investigation.
- Other Salt2/Salt3 low-Q/Salt4 rows are still `hold_running_wait_for_formal_gate`.

## Interpretation Boundary

The overnight package strengthens provenance and readiness. It does not admit
new closure rows by itself, does not make F4/F5/F6 publication-grade, and does
not launch new CFD. The formal corrected-Salt gate and future Salt1 gate decide
what becomes validation evidence.
