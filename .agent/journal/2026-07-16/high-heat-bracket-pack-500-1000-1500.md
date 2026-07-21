---
provenance:
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_bracket_pack_manifest.csv
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/scripts/run_salt4_high_heat_bracket_pack.sbatch
  - work_products/2026-07/2026-07-16/2026-07-16_high_heat_no_recirc_probe/bracket_pack_local_preflight.csv
tags: [openfoam, salt4, high-heat, recirculation]
related:
  - .agent/status/2026-07-16_AGENT-475.md
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/README.md
task: AGENT-475
date: 2026-07-16
role: Implementer/Tester/Writer
type: journal
status: submitted
---
# High-Heat Bracket Pack 500 / 1000 / 1500 W

User objective: submit additional Salt4 high-heat OpenFOAM cases at exact total
heater inputs `500 W`, `1000 W`, and `1500 W`, scaling cooling accordingly and
using the corrected OpenFOAM restart-field Q update workflow.

Implementation:

- Added `stage_high_heat_bracket_pack.py` to stage three lightweight case roots.
- Added `run_salt4_high_heat_bracket_pack.sbatch` to copy/patch/preflight the
  restart fields on the compute node and run the three cases as `3 x 64` ranks.
- Root `0/T` patch audit passed for all three cases: all three heater patches
  and all three cooler/sink patches were patched once per case.
- Local root/config preflight passed for all three cases before heavy
  `processors64` copy.
- The launcher repeats the AGENT-471 lesson: patch both visible root `0/T` and
  collated restart `processors64/10000/T`; do not trust root-only edits.

Cooling policy:

Cooling is scaled from the Salt4 nominal parent patch values by
`target_heater_power_W / 337.6 W`.

| Case | Heater total W | Heater patch W | Cooler q04 W | Cooler q05 W | Cooler q06 W |
| --- | ---: | ---: | ---: | ---: | ---: |
| `salt4_q0500w_no_recirc_probe` | `500` | `166.666666667` | `-30.4193117188` | `-189.793507838` | `-30.4193117188` |
| `salt4_q1000w_no_recirc_probe` | `1000` | `333.333333333` | `-60.8386234376` | `-379.587015677` | `-60.8386234376` |
| `salt4_q1500w_no_recirc_probe` | `1500` | `500` | `-91.2579351564` | `-569.380523515` | `-91.2579351564` |

Validation:

- `python3.11 -m py_compile .../stage_high_heat_bracket_pack.py`
- `bash -n .../run_salt4_high_heat_bracket_pack.sbatch`
- `python3.11 .../stage_high_heat_bracket_pack.py`
- `python3.11 tools/analyze/check_corrected_salt_preflight.py --manifest .../high_heat_bracket_pack_manifest.csv --allow-missing-processors`

Submission:

- Submitted from `login1` as Slurm job `3299620`.
- Early scheduler state: `RUNNING` on `c318-018`.
- At closeout it was copying `processors64` for the first case; restart
  preflight files were not expected yet.

Guardrails: no registry mutation, no existing native CFD-output mutation, no
external Fluid edit, and no destructive cleanup.
