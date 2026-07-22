---
provenance:
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_probe_manifest.csv
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/root_patch_audit.csv
tags: [openfoam, salt4, high-heat, recirculation]
related:
  - .agent/status/2026-07-16_AGENT-471.md
  - .agent/journal/2026-07-16/high-heat-no-recirc-probe.md
task: AGENT-471
date: 2026-07-16
role: Implementer/Tester/Writer
type: work_product
status: submitted
---
# High-Heat No-Recirculation Probe

AGENT-471 staged and submitted a Salt4 `q3x` continuation probe to test whether
a much-higher-throughflow operating point can bracket the observed upcomer
recirculation onset.

Key output: `heat_input_prediction.csv`.

Submitted Slurm job: `3299610`.

AGENT-475 added and submitted the packed `500 W`, `1000 W`, and `1500 W`
Salt4 bracket as Slurm job `3299620`. Local root/config preflight passed; the
job performs restart-field patch/preflight after copying `processors64`.
