---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/f6_onset_scorecard.csv
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_probe_manifest.csv
tags: [openfoam, salt4, high-heat, recirculation]
related:
  - .agent/status/2026-07-16_AGENT-471.md
  - imports/2026-07-16_high_heat_no_recirc_probe.json
task: AGENT-471
date: 2026-07-16
role: Implementer/Tester/Writer
type: journal
status: submitted
---
# High-Heat No-Recirculation Probe

User objective: choose and launch a much-higher-heater-input CFD case that may
remove or bracket upcomer recirculation, while keeping the model scientifically
honest and likely to converge.

Prediction: `1012.8 W` total heater input, implemented as `337.6 W` on each of
the three lower heater patches. This is `3.0 x` Salt4 nominal and `2.73 x` the
current `371.36 W` maximum. The basis is deliberately conservative: +/-5% and
+/-10% perturbations still show material reverse flow, so `2x` current max is
not a confident no-recirculation target. The `q3x` case is a bracket/probe.

Cooler change for convergence: scaled the three fixed cooler/sink `Q` patches
by the same `3.0 x` factor:

- `pipeleg_upper_04_reducer = -61.6173578176 W`
- `pipeleg_upper_05_cooler = -384.445729477 W`
- `pipeleg_upper_06_reducer = -61.6173578176 W`

Leaving the cooler at the old value would create a large net positive heat
input and make any eventual state hard to interpret.

Implementation:

- Added reproducible staging script:
  `jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/scripts/stage_high_heat_probe.py`.
- Added Slurm launcher:
  `jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/scripts/run_salt4_q3x_no_recirc_probe.sbatch`.
- Staged lightweight case inputs only on the current node; the Slurm job copies
  `processors64`, patches restart `T`, and runs restart-level preflight on the
  compute node.
- Disabled the weak `convergenceMonitor` `writeNow` stop path while preserving
  diagnostic monitor output.
- Submitted from `login1` after local `sbatch` was unavailable on `c318-009`.

Validation:

- `python3.11 -m py_compile .../stage_high_heat_probe.py`
- `bash -n .../run_salt4_q3x_no_recirc_probe.sbatch`
- `python3.11 .../stage_high_heat_probe.py`
- Root/config preflight passed with missing processors allowed before compute
  copy: `work_products/2026-07/2026-07-16/2026-07-16_high_heat_no_recirc_probe/local_preflight.csv`.
- `summary.json` parsed with `python3.11 -m json.tool`.

Submission:

- Job id: `3299610`.
- Early state: `RUNNING` on `c318-017`.
- At first check, job was copying `processors64`; no `foamRun` log existed yet.

Guardrails: no existing native CFD outputs, registry/admission state, external
Fluid files, or active AGENT-469/470 paths were mutated.
