# Water 2 Left-Lower-Leg Hydraulic Audit

This note audits the remaining Water 2 `left_lower_leg` contradiction using only existing package outputs.

## Decision

- recommended status: `resolved_exclude`
- confidence: `high`
- branch-level interpretation: Resolved exclusion. Water 2 left_lower_leg does not show evidence of a stable branchwise pressure-drop reversal. All retained times keep a positive branch-end cumulative direct p_rgh drop, one retained time carries a unique alignment-sign flip relative to the modal branch orientation, and the remaining sign changes in the branch-mean direct gradient are weak-signal finite-difference cancellations rather than robust reversals.

## Per-Time Findings

- `3976.0 s`: direct mean `0.302821942893` Pa/m, shear mean `1.546564341159` Pa/m, cumulative direct end `0.037398961649` Pa, alignment `-1.0`, issue `alignment_registration_flip`.
- `3977.0 s`: direct mean `-0.067879200742` Pa/m, shear mean `1.581597619228` Pa/m, cumulative direct end `0.050271579845` Pa, alignment `1.0`, issue `weak_signal_local_cancellation`.
- `3978.0 s`: direct mean `0.055051980705` Pa/m, shear mean `1.620425387516` Pa/m, cumulative direct end `0.072468764350` Pa, alignment `1.0`, issue `weak_signal_small_direct_gradient`.
- `3979.0 s`: direct mean `-0.024917505351` Pa/m, shear mean `1.609220972409` Pa/m, cumulative direct end `0.045015535089` Pa, alignment `1.0`, issue `weak_signal_local_cancellation`.
- `3980.0 s`: direct mean `-0.085315442832` Pa/m, shear mean `1.594471985093` Pa/m, cumulative direct end `0.042201315507` Pa, alignment `1.0`, issue `weak_signal_local_cancellation`.

## Interpretation Boundary

The audit supports exclusion, not promotion. The row is no longer treated as an unresolved sign mystery if the branch-end cumulative direct drop remains positive in every retained time and the only alignment anomaly is confined to one retained window. That still does not make the branch fit-ready.
