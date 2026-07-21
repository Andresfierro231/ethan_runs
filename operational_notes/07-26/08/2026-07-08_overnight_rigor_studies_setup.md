# Overnight Rigor Studies Setup

Date: `2026-07-08`
Task ID: `AGENT-218`
Owner: codex

## Question

Which rigor-strengthening studies can run overnight, and what should be set up
now?

## Answer

Run or monitor overnight:

- Corrected Salt Q admission support: already running jobs `3275448`,
  `3275449`, and `3275560`; formal gate job `3280969` is pending on
  `afterany:3275448,3275449,3275560`.
- Salt 1 nominal continuation: already running job `3282992`.
- Fixed-mdot 1D thermal replay: safe to rerun on a compute node into a new
  output package.
- Thermal mismatch remedy replay: safe to rerun into a new output package.
- Periodic scheduler and monitor snapshots: safe and useful for provenance.

Do not launch blindly tonight:

- Full mesh/GCI uncertainty: needs a scoped mesh-level inventory and builder;
  the existing June 30 GCI artifact is only a one-QOI example.
- Minor-loss coefficient correction: the span/corner control-volume
  contradiction must be resolved before another automated coefficient pass.
- Held-out model-form validation: blocked until corrected Salt and/or Salt 1
  rows are formally admitted.
- Self-consistent Ri validation: useful but needs a same-window CFD-vs-1D Ri
  schema first.

## Setup

Created:

- `work_products/2026-07-08_overnight_rigor_studies_setup/README.md`
- `work_products/2026-07-08_overnight_rigor_studies_setup/study_triage.csv`
- `work_products/2026-07-08_overnight_rigor_studies_setup/run_overnight_rigor_studies.sbatch`

Submission was attempted through `login3.ls6.tacc.utexas.edu` and rejected by
TACC allocation accounting:

```text
ERROR: Insufficient balance for Project (ASC23046) on (ls6) to run job.
Current Balance: 4314 SUs
Requested in queued jobs: 7638 SUs
```

Therefore the overnight batch is staged but not queued.

The Slurm job performs:

1. Initial and hourly `squeue` snapshots for corrected Salt, Salt1, gate, and
   fixed-mdot replay jobs.
2. Read-only corrected Salt preflight audit.
3. Read-only corrected Salt live monitor snapshots, linked to gate job `3280969`.
4. Fresh fixed-mdot 1D replay in a new package subdirectory.
5. Fresh thermal-mismatch remedy replay in a new package subdirectory.

## Immediate Lightweight Results

Ran the read-only pieces that were safe from the current compute-node shell:

- Corrected Salt preflight audit:
  `Audited 14 corrected Salt cases; failures=0`.
- Corrected Salt live monitor:
  `Scanned 14 corrected Salt cases; special scrutiny flags=4`.

The four monitor flags are:

- `salt1_jin_lo10q_corrected`: hold for coordinator review; missing nominal
  mdot reference.
- `salt1_jin_hi10q_corrected`: hold for coordinator review; missing nominal
  mdot reference and early stop after only about `254 s` past restart.
- `salt3_jin_hi5q_corrected`: investigate; fatal/error markers in the log.
- `salt3_jin_hi10q_corrected`: investigate; fatal/error markers in the log.

## Scientific Boundary

This setup strengthens provenance and readiness. It does not admit new data.
The formal corrected-Salt gate and a later Salt1 gate decide whether those runs
can become fit or validation evidence. The replay outputs are still
CFD-interface-informed and must not be described as fully predictive
heater/cooler hardware models.
