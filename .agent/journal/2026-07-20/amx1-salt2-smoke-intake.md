# AGENT-567 Journal: AMX1 Salt2 Smoke Intake

Task: AGENT-567

Date: 2026-07-20

## Context

AGENT-565 closed with `fluid_patch_required_before_smoke`: the AMX1 axial
mixing form was decision-complete, but Fluid lacked the API, conservative
ledger, and scenario support needed to run even a Salt2 smoke. This row
implemented the follow-on intake after external Fluid task
`impl-2026-07-20-fluid-amx1-axial-mixing-smoke` landed.

## Observed Evidence

The external Fluid row added AMX1 `segment_diffusion_v1`, ran
`amx1_salt2_smoke_v1`, and produced
`results/diagnostics/amx1_salt2_smoke_v1/amx1_smoke_audit/`.

The audit result is `pass_smoke_only`:

- rows scanned: `2`
- AMX1 rows: `1`
- all roots pass: `true`
- AMX1 ledgers nonzero: `true`
- AMX1 ledgers conservative: `true`
- AMX1 active segments: `46`
- AMX1 ledger absolute sum: `8.08855832584099 W`
- AMX1 total net: `5.551115123125783e-17 W`
- AMX1 max residual: `0.0 W`

Runtime is acceptable for smoke but notable: total elapsed time was
`191.398239 s`, and the AMX1 row took `111.057331 s`.

## Interpretation

AMX1 is now unlocked at the API/root/ledger smoke level. It is not yet a
scientific unlock for `predictive-wall-test-section-submodels`. Salt2 diagnostic
deltas are nearly neutral versus the AMX1-disabled baseline: mdot improves
slightly, all/TP/TW RMSE worsen by only a few millikelvin, and no admission gate
was evaluated.

## Next Useful Action

Run a separately claimed bounded Salt1-4 AMX1 nominal comparison using only the
disabled baseline and the same low `0.05` multiplier. Keep source/property
labels and runtime as hard gates. Do not run a broad grid, external/holdout
score, fit/model selection, or blocker-register update from Salt2 smoke alone.
