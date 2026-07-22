# Salt 1 Corrected-Q Coordinator Review

Generated: `2026-07-07`

## Question

Why did `salt1_jin_hi10q_corrected` advance only about `254 s` after restart,
and can Salt 1 corrected-Q rows be admitted?

## Raw Observations

- Manifest row:
  - case: `salt1_jin_hi10q_corrected`
  - parent restart: `3756.33125 s`
  - target end: `9756.33125 s`
  - q ratio: `1.10`
- Solver log:
  - starts as corrected Salt job `3275448` from restart `3756.33125 s`;
  - reaches `Time = 4010.590361446 s`;
  - reports `*** convergenceMonitor: CONVERGED at iteration 640600`;
  - then writes `End` and `Finalising parallel run`;
  - no fatal/error marker was found for this case.
- Advance:
  - `4010.590361446 - 3756.33125 = 254.259111446 s`;
  - this is `4.24%` of the intended `6000 s` extension.
- `system/controlDict`:
  - `stopAt endTime`;
  - `endTime 9756.33125`;
  - therefore the solver did not stop because it reached configured `endTime`.
- `system/functions` convergence monitor:
  - checks volume-weighted `Tmean`, `Tsigma`, and `Umean`;
  - uses `rtol = 0.0001`;
  - when `qoiOK && resOK`, calls `mesh().time().stopAt(Time::stopAtControl::writeNow)`.

## Interpretation

`salt1_jin_hi10q_corrected` ended early because the coded convergence monitor
declared convergence and forced `stopAt(writeNow)`. This was a normal solver
`End`, not a crash.

That convergence criterion is not sufficient for corrected-Q closure admission:
it only checks global volume means and residuals. It does not prove operating
point re-equilibration from the parent restart, does not use the missing Salt 1
nominal mdot reference, and does not ensure enough post-perturbation thermal
relaxation time.

## Coordinator Decision

Salt 1 corrected-Q rows remain held. No Salt 1 corrected row is closure-fit
admissible without a later coordinator decision that supplies a defensible Salt
1 nominal mdot reference and re-runs/extends the corrected perturbation with a
gate that cannot stop solely on the weak global convergence monitor.

## Next Action

If Salt 1 corrected perturbations are needed, stage a targeted Salt 1 rerun or
continuation with the convergence monitor disabled or made non-terminating, then
gate on operating-point movement plus quasi-steady time-window UQ rather than
global volume-mean flatness alone.
