# CFD Steady-State And Continuation Table

Date: `2026-07-09`
Checked at: `2026-07-09T17:46:28-05:00`
Task: `AGENT-246`

## Purpose

This package summarizes which CFD runs look steady, which should be continued,
and which need repair or investigation before resubmission. It separates:

- time-series stationarity from AGENT-244,
- formal corrected-Q gate admission from AGENT-237/241,
- live Salt1 nominal status from AGENT-242 and the current scheduler/log check.

## Files

- `primary_cfd_continuation_decisions.csv`: compact operational table for
  current mainline, Water validation context, Salt1 nominal, and corrected-Q
  sensitivity rows.
- `all_timeseries_case_rollup.csv`: complete 47-case rollup from the AGENT-244
  time-series summary, with admission/action overlays where known.
- `summary.json`: source list and counts.

## High-Level Decision Table

| Run/group | Steady-state status | Admission status | Continuation decision |
| --- | --- | --- | --- |
| Salt2 nominal mainline | mdot/temperature steady; total_Q drifting | current mainline nominal evidence | Do not continue for hydraulic closure only; thermal refresh optional/caveated. |
| Salt3 nominal mainline | mdot/temperature steady; total_Q drifting | current mainline nominal evidence | Do not continue for hydraulic closure only; thermal refresh optional/caveated. |
| Salt4 nominal mainline | all representative series steady | current mainline nominal evidence | Do not continue now. |
| Salt1 nominal `3282992` | steady in current AGENT-244 window, but still running | pending terminal gate | Continue running to exit, then gate before any closure use. |
| Water1/2/3 validation | mdot quasi-steady; heat drifting | validation context only | Continue only if Water validation becomes an active objective. |
| Water4 validation | mdot quasi-steady; heat steady | validation context only | Continue only if Water validation becomes an active objective. |
| Corrected-Q Salt2 -10Q/+10Q | stationary terminal window but under-advanced | not admitted (`too_short`) | First-wave continuation candidates only; re-gate before any fit. |
| Corrected-Q Salt2 -5Q/+5Q | stationary terminal window but under-advanced | not admitted (`too_short`) | Defer midpoint rows until the +/-10Q bracket proves useful. |
| Corrected-Q Salt4 +/-10Q | stationary terminal window but under-advanced | not admitted (`too_short`) | Defer to second wave after Salt2 +/-10Q admits or reveals gate adjustment. |
| Corrected-Q Salt4 +/-5Q | stationary terminal window but under-advanced | not admitted (`too_short`) | Defer midpoint rows. |
| Corrected-Q Salt3 -10Q/-5Q | stationary low-Q window but under-advanced | not admitted (`too_short`) | Defer; avoid asymmetric Salt3 support until high-Q side is repaired. |
| Corrected-Q Salt3 +5Q/+10Q | not accepted short window | not admitted (`too_short`) | Investigate cancelled/superseded high-Q attempt; rerun/rebuild before gate. |
| Corrected-Q Salt1 -10Q | stationary terminal window but under-advanced | not admitted (`too_short`) | Hold until Salt1 nominal/reference policy resolves; then decide whether to continue. |
| Corrected-Q Salt1 +10Q | short/early monitor-stop window | not admitted (`too_short`) | Repair monitor/reference policy before rerun or continuation. |

## Practical Continue List

Only these are continuation candidates now:

1. `salt1_jin_nominal_continuation_corrected` / job `3282992`: already running;
   let it continue to terminal evidence, then gate.
2. `salt2_jin_lo10q_corrected`: first-wave corrected-Q continuation candidate.
3. `salt2_jin_hi10q_corrected`: first-wave corrected-Q continuation candidate.

Everything else is either already usable for the current mainline purpose,
deferred, optional validation context, or repair-first.

## Important Caveat

A stationary time series is not the same as closure admission. The corrected-Q
rows are explicitly labeled sensitivity/correlation-support only and must not
enter nominal closure fits unless a future formal gate admits them.
