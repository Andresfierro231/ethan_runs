# Salt1 Cancel And Corrected-Q Node Repack

Date: `2026-07-13`
Task: `AGENT-268`

## Current State

User-approved stops are complete:

- Normal Salt1 job `3282992` is cancelled.
- Salt1 -10Q corrected step `3288671.0` is cancelled.
- Corrected-Q allocation `3288671` remains running on `c318-017`.
- Salt4 +10Q corrected step `3288671.5` remains running.
- Salt1 +10Q corrected step `3288671.1` remains running.

Do not cancel `3288671` as a whole unless the intent is to stop all remaining
corrected-Q work on that allocation.

## Capacity Read

The corrected-Q allocation has 256 CPUs. With `3288671.1` and `3288671.5`
running as 64-rank steps, roughly two 64-rank step slots should be available
for repacking if the allocation launcher remains usable.

## Best Next Runs

Best candidates for the available node capacity:

- `salt2_jin_lo10q_corrected`
- `salt2_jin_hi10q_corrected`

These should be presented as `salt2_lo10q` and `salt2_hi10q`. They are the July
9 minimal first-wave rows and remain useful in the July 13 latest-time refresh.
They give the smallest useful symmetric Salt2 bracket and avoid the Salt1
reference-policy issue.

Second-tier candidates:

- Salt2 +/-5Q, if the first pair starts cleanly and capacity remains useful.

Hold:

- Salt3 +5Q and +10Q until their short/cancelled high-Q attempts are diagnosed.
- Additional Salt4 midpoint rows until the +/-10Q bracket is useful.
- Bulk corrected-Q resubmission.

## Admission Correction

Current coordinator policy is that a converged/stationary Salt-Q perturbation
row is closure-fit admissible. The older `too_short` post-restart-advance label
is context only and should not block closure fitting by itself.

## Links

- Status: `../../../../.agent/status/2026-07-13_AGENT-268.md`
- Journal: `../../../../.agent/journal/2026-07-13/salt1-cancel-and-corrected-q-node-repack.md`
- Manifest: `../../../../imports/2026-07-13_salt1_cancel_and_corrected_q_node_repack.json`
