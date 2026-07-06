# Ethan Weekend Run Triage

Generated: `2026-06-22`

## Purpose

Record the exact basis for the June 22 decision to stop the live June 18
continuation wave and the live June 19 Salt bracket jobs instead of letting the
weekend runs continue.

The key question was not whether the runs were still moving physically. They
were. The real question was whether the preserved retained field window was
capable of satisfying the existing late-window closure target.

## Decision

The jobs were stopped.

Reason:

- both campaign roots used `writeInterval 1` with `purgeWrite 5`
- that configuration preserves only the last `5` retained field writes
- the resulting preserved restart-state window is about `4 s`
- the blocker plan was asking for a preserved late window near `20 s`

So the active jobs could still improve endpoint convergence and scalar
histories, but they could not deliver the specific retained-window evidence the
science lane was still missing.

## Queue Actions

Stopped on `2026-06-22 10:31 CDT`:

- `3244950` `ethan_s3j_cont`
- `3244951` `ethan_s2j_cont`
- `3244954` `ethan_s4j_cont`
- `3244957` `ethan_w2_cont`
- `3246561` `ethan_s2j_hiqins`
- `3246564` `ethan_s2j_loqins`
- `3250524` `ethan_s4j_hiqins_r2`
- `3250525` `ethan_s4j_loqins_r2`
- `3250526` `ethan_salt_optpack` before start

## Final Preserved Field Windows

### June 18 continuation wave

| Case | Restart time (s) | Final saved times (s) | Preserved field span (s) |
| --- | ---: | --- | ---: |
| Salt 2 Jin | `2431` | `4871, 4872, 4873, 4874, 4875` | `4` |
| Salt 3 Jin | `2514` | `4804, 4805, 4806, 4807, 4808` | `4` |
| Salt 4 Jin | `5776` | `7683, 7684, 7685, 7686, 7687` | `4` |
| Water 2 | `3980` | `6061, 6062, 6063, 6064, 6065` | `4` |

### June 19 Salt bracket wave

| Case | Restart time (s) | Final saved times (s) | Preserved field span (s) |
| --- | ---: | --- | ---: |
| Salt 2 hiq/hiins | `2431` | `4425, 4426, 4427, 4428, 4429` | `4` |
| Salt 2 loq/loins | `2431` | `4399, 4400, 4401, 4402, 4403` | `4` |
| Salt 4 hiq/hiins retry | `5776` | `5789, 5790, 5791, 5792, 5793` | `4` |
| Salt 4 loq/loins retry | `5776` | `5789, 5790, 5791, 5792, 5793` | `4` |

## Important Boundary

The continuation roots do still preserve some long-running scalar and line
artifacts:

- `postProcessing/total_Q.dat`
- probe files
- `postProcessing/velocity_profiles/**`

Those are useful for convergence notes and endpoint diagnostics, but they do
not replace the retained restart-field window needed for the straight-row
late-window rebuild.

## Next Step

Relaunch only the minimal corrected continuation subset:

- `salt2_jin`
- `salt3_jin`
- `salt4_jin`
- `water2`

The corrected relaunch should keep the same `writeInterval 1` but raise
retention to at least `purgeWrite 30`, so the preserved restart-state window
can actually exceed the `~20 s` target.

Keep the Salt bracket and packed optimum jobs staged but off until the
corrected continuation lane is analyzed.
