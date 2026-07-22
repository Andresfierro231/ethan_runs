# Selected Corrected Salt Q Status Table

Rows are sourced from `registry/case_registry.csv`; gate/status fields are joined from the completed 3280969 corrected-Q gate and minimal continuation plan. `Latest registered timestep` is scanned from each registered case root, while `Latest log time` is parsed from recent `logs/log.foamRun*` tails when present. Perturbation rows remain sensitivity/correlation-support, not nominal baselines.

| Row        | Gate latest time | Latest registered timestep | Latest log time | Post-restart advance so far | Status                                                                                                           |
| ---------- | ---------------- | -------------------------- | --------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Salt1 -10Q | 6377.610 s       | 6544.000 s                 | 6544.688 s      | 2621.279 s = 43m 41s        | Partial usable window, but gate says too_short; hold until Salt1 policy resolves, then continue if still useful. |
| Salt1 +10Q | 4010.590 s       | 4166.000 s                 | 4166.873 s      | 254.259 s = 4m 14s          | Not accepted; early monitor/End path. Repair/rerun before treating as continuation evidence.                     |
| Salt4 +10Q | 11536.798 s      | 11537.000 s                | 11537.723 s     | 1536.798 s = 25m 37s        | Partial usable window, but gate says too_short; defer behind Salt2 +/-10Q first wave.                            |
