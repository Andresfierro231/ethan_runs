# 2026-06-30 OpenFOAM Parallel Scaling Study

This campaign root holds the benchmark wrapper and generated outputs for the
Salt 2 Jin OpenFOAM parallel scaling pilot.

The production source continuation tree is read-only input. Benchmark jobs
stage clones under `work/` and write parsed outputs under `results/`.

Initial pilot:

- source case: June 18 Salt 2 Jin continuation
- source restart time: latest `processors64` time, observed as `7915`
- decomposition method: `scotch`
- rank counts: `32`, `64`, `128`, `256`
- scheduler: `NuclearEnergy`, account `ASC23046`
- requested window: 2026-06-30 20:00 CDT to 2026-07-01 08:00 CDT

Follow-up runs should add a controlled `hierarchical` comparison and then
repeat the best candidates on a Water case.

Scheduled follow-up:

- script: `scripts/run_salt2_method_io_followup.sbatch`
- target window: 2026-07-01 20:00 CDT to 2026-07-02 08:00 CDT
- default rank count: `64` unless manually changed before start
- variants:
  - `scotch_prod_io`: `scotch`, `writeInterval 1`, compression off
  - `scotch_sparse_io`: `scotch`, `writeInterval 1000`, compression off
  - `scotch_sparse_compressed`: `scotch`, `writeInterval 1000`, compression on
  - `hierarchical_sparse_io`: `hierarchical`, `writeInterval 1000`,
    compression off
