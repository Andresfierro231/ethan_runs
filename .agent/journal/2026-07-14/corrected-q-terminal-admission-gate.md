---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_terminal_admission_gate/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_terminal_admission_gate/corrected_q_terminal_gate_rows.csv
tags: [journal, salt-q-perturbation, admission, live-job]
related:
  - .agent/status/2026-07-14_AGENT-320.md
  - imports/2026-07-14_corrected_q_terminal_admission_gate.json
task: AGENT-320
date: 2026-07-14
role: Coordinator/Writer
type: journal
status: complete
---
# Corrected-Q Terminal Admission Gate

Observed: Slurm job `3293924` remains `RUNNING` on `c318-016`, and all four
`foamRun` steps are still `RUNNING`. The launch stdout still shows the repaired
contract and preflight success.

Latest solver times seen:

- `salt2_lo10q`: `10644.337423 s`
- `salt2_hi10q`: `10014.348066 s`
- `salt4_lo10q`: `11951.598958 s`
- `salt4_hi10q`: `12885.023364 s`

Interpretation: this is not a terminal harvest. All four rows remain blocked
pending terminal state and operating-point convergence/admission evidence.

No duplicate corrected-Q job was launched. No native solver outputs were
modified.
