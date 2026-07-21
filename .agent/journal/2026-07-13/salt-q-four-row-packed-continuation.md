# Salt-Q Four-Row Packed Continuation

Date: `2026-07-13`

Task: `AGENT-274`

## Observed Output

The previous selected corrected-Q allocation, `3288671`, reached terminal Slurm
state before this task. `sacct -j 3288671 -X` reported `COMPLETED`, elapsed
`3-00:23:10`, start `2026-07-10T12:19:23`, end `2026-07-13T12:42:33`, on
`c318-017`. The only current queue row visible before the new submission was the
interactive allocation `3292998` on `c318-008`.

For `salt4_hi10q`, the final available monitor files in
`jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/salt4_jin_hi10q_corrected/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation/postProcessing`
advanced to written time `12639 s`. The final 600 s window was `12039` to
`12639 s`.

Final-window metrics:

| Quantity | Mean | Latest | Drift | Span |
| --- | ---: | ---: | ---: | ---: |
| `total_Q` | `7.71885485857 W` | `6.99361 W` | `-1.59099 W` | `1.69738 W` |
| `mdot_pipeleg_left_04_test_section` | `-0.0184330308173 kg/s` | `-0.018519071 kg/s` | `-0.00011291196 kg/s` | `0.00044801123 kg/s` |
| `mdot_pipeleg_upper_05_cooler` | `-0.0184335818572 kg/s` | `-0.018520606 kg/s` | `-0.00011310302 kg/s` | `0.00044813782 kg/s` |
| `mdot_pipeleg_lower_05_straight` | `-0.0184325566521 kg/s` | `-0.018521523 kg/s` | `-0.00011556269 kg/s` | `0.0004465576 kg/s` |
| `mdot_pipeleg_right_02_middle` | `-0.018431987885 kg/s` | `-0.018519001 kg/s` | `-0.00011382113 kg/s` | `0.00045049359 kg/s` |

Fluid temperature probes reached a maximum absolute drift of `1.45105 K` and
maximum span of `4.73688 K`; wall temperature probes reached a maximum absolute
drift of `1.52954 K` and maximum span of `4.07394 K`.

## Interpretation

Salt4 +10Q was not steady-state enough for terminal postprocessing. The mdot
signals were moving by about `0.61%` of mean over 600 s with `~2.4%` window
spans, and the thermal probes were still moving at order `1 K`. It should be
included in the next packed continuation rather than treated as complete.

## Action

The selected continuation launcher now packs four cases on one 256-task node:

- `salt2_lo10q`
- `salt2_hi10q`
- `salt4_lo10q`
- `salt4_hi10q`

The launcher retains 64 MPI ranks per case and refuses to start if more than
four cases are configured or if the requested case ranks exceed the Slurm task
allocation.

The selected staged `system/functions` files for `salt2_lo10q`, `salt2_hi10q`,
and `salt4_lo10q` still contained a `Time::stopAtControl::writeNow` action when
preflight was first checked. Those staged case inputs were patched to match the
already-corrected `salt4_hi10q` behavior: the monitor logs that its diagnostic
criterion was met, continues to configured `endTime`, and leaves admission to
the post-run operating-point and time-window UQ gate.

Submission was performed from `login3` because `sbatch` is unavailable on the
interactive compute node. Slurm accepted job `3293441`. Initial queue and step
checks showed:

- `squeue -j 3293441`: `RUNNING`, job name `saltq_sel_cont`, node `c318-011`,
  time limit `5-00:00:00`.
- `squeue -s -j 3293441`: four active `foamRun` steps,
  `3293441.0` through `3293441.3`, plus the batch step.
- Slurm stdout recorded restart patching at `10291`, `9674`, `11655`, and
  `12639`, then launched all four cases at `2026-07-13T13:05:23-05:00` to
  `13:05:24-05:00`.

## Follow-Up

After the new job starts, check `squeue`, then tail the per-case
`logs/log.foamRun_corrected_q` files for successful preflight patching and
runtime advancement. Re-run the corrected-Q convergence/admission gate after
the cases produce late windows.
