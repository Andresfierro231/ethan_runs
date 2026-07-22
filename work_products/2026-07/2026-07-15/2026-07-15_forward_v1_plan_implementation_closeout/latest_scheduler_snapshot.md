# Latest Read-Only Scheduler Snapshot

Captured: 2026-07-15T08:14:58-0500

No scheduler mutation was performed.

## squeue

Command:

```bash
squeue -u andresfierro231 -h -o "%i|%P|%j|%T|%M|%R"
```

Output:

```text
3295438|NuclearEnergy|saltq_s24_sel_harv|PENDING|0:00|(Dependency)
3293924|NuclearEnergy|saltq_sel_cont|RUNNING|1-15:11:01|c318-016
3295991|NuclearEnergy-dev|hyd_stage|PENDING|0:00|(Dependency)
3295990|NuclearEnergy-dev|hyd_stage|PENDING|0:00|(Dependency)
3295989|NuclearEnergy-dev|hyd_stage|PENDING|0:00|(Dependency)
3295120|NuclearEnergy-dev|idv75667|RUNNING|21:28:30|c318-008
```

## sacct

Command:

```bash
sacct -j 3293924,3295438,3295989,3295990,3295991,3295901,3295968,3295120 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList -n -P
```

Output:

```text
3293924|saltq_sel_cont|RUNNING|0:0|1-15:11:02|c318-016
3293924.batch|batch|RUNNING|0:0|1-15:11:02|c318-016
3293924.0|foamRun|RUNNING|0:0|1-15:10:39|c318-016
3293924.1|foamRun|RUNNING|0:0|1-15:10:39|c318-016
3293924.2|foamRun|RUNNING|0:0|1-15:10:39|c318-016
3293924.3|foamRun|RUNNING|0:0|1-15:10:39|c318-016
3295120|idv75667|RUNNING|0:0|21:28:31|c318-008
3295120.batch|batch|RUNNING|0:0|21:28:31|c318-008
3295120.0|bash|FAILED|1:0|00:02:23|c318-008
3295120.1|bash|FAILED|1:0|00:03:42|c318-008
3295120.2|bash|COMPLETED|0:0|00:02:17|c318-008
3295438|saltq_s24_sel_harv|PENDING|0:0|00:00:00|None assigned
3295901|upc_pm5q|CANCELLED by 890970|0:0|00:00:00|None assigned
3295968|upc_pm5q|CANCELLED by 890970|0:0|00:00:00|None assigned
3295989|hyd_stage|PENDING|0:0|00:00:00|None assigned
3295990|hyd_stage|PENDING|0:0|00:00:00|None assigned
3295991|hyd_stage|PENDING|0:0|00:00:00|None assigned
```
