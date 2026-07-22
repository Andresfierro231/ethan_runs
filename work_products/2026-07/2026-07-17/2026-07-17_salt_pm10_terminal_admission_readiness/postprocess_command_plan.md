# PM10 Terminal Admission Command Plan

Do not run terminal admission while `3293924` is still running or `3295438` is
pending/running.

1. Refresh scheduler state:

```bash
ssh login1 sacct -j 3293924,3295438 --format JobIDRaw,JobName,State,ExitCode,Elapsed,NNodes,NodeList%80 -P -n
```

2. If both parent jobs are `COMPLETED`, claim a new extraction/admission task.

3. Repeat the PM5 pattern, but in a new task-owned scratch tree:

- copy terminal Salt2/Salt4 +/-10Q cases to scratch
- reconstruct representative terminal windows
- sample upcomer inlet/mid/outlet planes and wall-band surfaces
- validate `U`, `T`, `rho`, `p_rgh`, `Re`, `Pr`, `Ri`, `Gr`, `Ra`, `Gz`, and `wallHeatFlux`
- parse reverse area/mass fraction, secondary velocity, wall-core Delta T, and steady-window metadata
- publish admission and runtime-leakage tables

4. Do not relaunch the old broken July 14 PM5 script unchanged. Use the AGENT-406
repair lessons: scratch-only reconstruction, explicit field validation, and
diagnostic-only admission until recirculation/sign/mesh gates pass.
