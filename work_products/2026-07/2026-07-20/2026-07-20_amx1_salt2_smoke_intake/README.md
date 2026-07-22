# AGENT-567 AMX1 Salt2 Smoke Intake

Date: 2026-07-20

Decision: `pass_smoke_only`.

External Fluid task
`impl-2026-07-20-fluid-amx1-axial-mixing-smoke` implemented the AMX1
disabled-by-default axial-mixing API and ran the bounded Salt2 smoke specified
by AGENT-565.

## Result

The AMX1 Salt2 smoke passed the implementation-level gates:

- two campaign rows completed
- one AMX1 row
- all roots accepted and bracketed
- AMX1 row `accepted_for_validation=true`
- AMX1 active segments: `46`
- AMX1 ledger absolute sum: `8.08855832584099 W`
- AMX1 total net: `5.551115123125783e-17 W`
- AMX1 max residual: `0.0 W`

The Salt2 diagnostic metrics are nearly neutral against the AMX1 disabled
baseline: mdot improves slightly, while all/TP/TW RMSE worsen by only
`0.0013` to `0.0043 K`. These deltas are smoke diagnostics only, not an
admission result.

## Blocker Impact

AMX1 is no longer blocked at the Fluid API/root/ledger smoke layer. The broader
`predictive-wall-test-section-submodels` blocker remains high because this row
did not run Salt1-4, did not satisfy source/property release for admission, and
did not compare against the full coupled mdot/TP/TW/all-probe gates.

## Next Step

The next progress study is a bounded Salt1-4 AMX1 nominal comparison using only
the disabled baseline and the same low multiplier `0.05`. Keep it no-grid. Treat
source/property labels and runtime as hard gates. Do not update the blocker
register from Salt2 smoke alone.
