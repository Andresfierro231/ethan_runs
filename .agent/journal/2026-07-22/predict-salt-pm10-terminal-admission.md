---
provenance:
  - tools/analyze/build_salt_pm10_terminal_admission.py
  - work_products/2026-07/2026-07-22/2026-07-22_predict_salt_pm10_terminal_admission/summary.json
task: TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION
date: 2026-07-22
role: cfd-pp / Scheduler / Thermal-modeling / Hydraulics / Upcomer-onset / Implementer / Tester / Writer
type: journal
status: complete
tags: [journal, pm10, terminal-admission, holdout, recirculation, pressure]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_predict_salt_pm10_terminal_admission
---

# Salt PM10 terminal admission disposition

## Attempted

Claimed the open PM10 terminal-admission TODO and consumed the existing
readiness, scheduler, terminal drift, steady-window, split-policy, and upcomer
recirculation packages. Built a task-owned script and tests to assemble a
read-only disposition packet rather than editing artifacts by hand.

## Observed

`3293924` is terminal as `TIMEOUT`; its `foamRun` steps were cancelled at the
wall limit. The dependent harvester `3295438` is terminal as `COMPLETED`.
`squeue` showed no live rows for either job on 2026-07-22.

The July 20 terminal drift classification passes all four PM10 rows. The Salt2
rows show late-window mdot drift of `0.007906%` and `0.101132%`; the Salt4 rows
show `0.052102%` and `-0.486409%`. The representative steady-window stats mark
mdot as `steady` for all four rows.

The same representative stats mark `total_Q` as `not steady (drifting)` for all
four rows, with relative drift near `8.5%` to `9.6%`. That is the important
thermal caveat: terminal mdot/temperature evidence is usable diagnostically, but
heat/source release is not justified.

The PM10 upcomer package classifies all four rows as `strong_recirculation`.
Reverse area fractions are about `0.77` to `0.79`, reverse mass fractions are
near `0.50`, and secondary velocity fractions are about `0.74` to `0.77`.

## Inferred

The right disposition is not "still blocked by live jobs" and not "admitted for
final scoring." The scheduler blocker is gone, terminal evidence exists, and
the rows can support future-holdout planning plus recirculation/onset thesis
evidence. They still cannot train, select, score a current final model, release
runtime inputs, or release source/property corrections.

## Contradictions or Caveats

The older readiness packet had `blocked_scheduler_unknown` because scheduler
queries were intentionally disabled. The current read-only `sacct`/`squeue`
check supersedes that scheduler ambiguity for this row.

The solver job ended by timeout, not clean solver completion. The harvester did
complete, and the existing terminal classification passed strict log and drift
gates, so this packet treats the cases as terminal evidence with caveats rather
than failed/unusable runs.

## Next Useful Actions

1. Feed `pm10_recirc_onset_summary.csv` into the recirculation-fraction/onset
   thesis evidence packet.
2. Build pressure ladder and streamwise pressure-map tables for PM10 without
   fitting protected rows.
3. Build a separate heat-loss/source ledger before any thermal/source release;
   current `total_Q` drift forbids release.
