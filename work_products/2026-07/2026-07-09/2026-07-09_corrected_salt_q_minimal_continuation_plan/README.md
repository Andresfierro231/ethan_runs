# Corrected Salt Q Minimal Continuation Plan

Date: `2026-07-09`
Task: `AGENT-238`

## 2026-07-13 Coordinator Correction

This package's original `too_short => not admitted` interpretation is
superseded. Current coordinator policy is:

- A converged or stationary terminal-window Salt-Q perturbation row is
  closure-fit admissible.
- The old `too_short` post-restart-advance label remains run-history context
  only for rows that are otherwise converged.
- Current presentation names should omit the staging suffix: use `salt2_lo10q`,
  `salt2_hi10q`, and `salt4_lo10q` for the requested repack rows while retaining
  the source keys in provenance fields.

## Decision

Do not bulk-resubmit the Salt Q campaign.

Rows that are converged/stationary are closure-fit admissible under the July 13
coordinator correction. Rows that are short because they lack a usable terminal
window or have failed/cancelled launch evidence remain repair-first.

## Convergence Answer

Converged/stationary Salt-Q perturbation rows are closure-fit admissible. The
old formal operating-point gate's post-restart advancement requirement no longer
overrides a stationary terminal window.

Practical classification:

- Fully admitted for F5/Ri or F6 refit: stationary/converged terminal-window
  rows, subject to the usual row-quality exclusions.
- Terminal-window stationary but formerly under-advanced: 11 rows.
  These are now admissible if their terminal-window convergence evidence is
  accepted.
- Not accepted as a terminal window: 3 rows.
  Salt1 +10Q, Salt3 +5Q, and Salt3 +10Q need investigation or repair before
  any resubmit.

The completed collector did not report fatal markers in the final audit CSV,
but the Salt3 high-Q rows have only about 20-21 s of post-restart evidence from
a cancelled/superseded attempt. Treat that as an investigate-before-resubmit
condition, not as a continuation-ready terminal window.

## Minimal First Wave

Continue only two rows first:

- `salt2_lo10q` (`salt2_jin_lo10q_corrected` source key)
- `salt2_hi10q` (`salt2_jin_hi10q_corrected` source key)
- `salt4_lo10q` (`salt4_jin_lo10q_corrected` source key), added July 13 to pair
  with the already-running Salt4 +10Q row once capacity allows.

Rationale:

- They are clean partial rows: full 300 s late monitor windows, correct mdot
  direction, no special-scrutiny flag, and no Salt1 reference-policy issue.
- They form the smallest symmetric corrected-Q bracket around one nominal Salt
  case, which is the least expensive way to test whether corrected-Q rows can
  unlock a real F5/Ri or F6 refit attempt.
- They have higher leverage than the +/-5% rows.
- They avoid the Salt3 high-Q failed/cancelled rows and the Salt1 weak-reference
  boundary.

This first wave is closure-fit admissible once the row is converged/stationary;
the source-key provenance still records the repaired staging path.

## Resubmit Recommendations

Submit now: no scheduler submission was performed by this task. If the next
task is explicitly authorized to launch work, the recommended repack rows are:

- `salt2_lo10q`
- `salt2_hi10q`
- `salt4_lo10q`

Do not resubmit now:

- Salt2 +/-5Q and Salt4 +/-5Q: defer as midpoint/linearity support only.
- Salt4 +/-10Q: defer until Salt2 +/-10Q proves the continuation/gate settings.
- Salt3 -10Q and -5Q: defer because the high-Q side is not usable yet.
- Salt1 -10Q: hold for Salt1 nominal/reference policy.
- Salt1 +10Q, Salt3 +5Q, Salt3 +10Q: investigate or repair before any resubmit.

## Deferred Rows

- Salt4 +/-10Q: wave 2 only after Salt2 +/-10Q admits or proves the continuation
  setup is practical.
- Salt2 +/-5Q and Salt4 +/-5Q: wave 3 only if admitted +/-10Q rows need midpoint
  support for nonlinearity/local-slope checks.
- Salt3 -10Q and -5Q: defer because the matching high-Q rows failed; avoid an
  asymmetric Salt3 response surface unless deliberately justified.
- Salt1 -10Q: hold until Salt1 nominal/reference-mdot policy is resolved.

## Investigate Before Resubmission

- Salt1 +10Q: repair/verify the diagnostic-only convergence-monitor policy and
  Salt1 reference policy before any rerun or continuation.
- Salt3 +5Q and +10Q: investigate the cancelled/superseded high-Q attempts and
  confirm no BC, launch, or patched-field issue before rerunning from the
  corrected restart.

## Gate Target Warning

The current formal operating-point gate uses `tau_thermal=5000 s` and
`min_tau_advance=3`, so it expects about `15000 s` post-restart advancement.
The existing corrected-Q campaign targets about `6000 s`. Before launching even
the two-row wave, either:

1. set a continuation target that can satisfy the current gate, or
2. document a reviewed change to the gate policy.

Without one of those, a resubmitted row can consume allocation and still return
`too_short`.

## Output Tables

- `minimal_continuation_plan.csv`: per-row decision and wave.
- `convergence_resubmit_recommendations.csv`: direct answer to which rows are
  admitted, continuation-ready, deferred, or investigate-before-resubmit.
- `no_submit_checklist.md`: safeguards against accidental bulk resubmission.

## Closure Boundary

Corrected-Q perturbation rows remain sensitivity/correlation-support evidence.
They are not nominal baselines. They must not enter F4/F5/F6/T13 closure fits,
model-form bakeoffs, or publication-grade validation tables until the exact row
has explicit formal gate evidence: `operating_point_verdict=requalified`.
