# No-Submit Checklist

This package is a plan only. Before any scheduler action, confirm:

- Do not run `scripts/submit_corrected_jobs.sh`; it groups all manifest rows and
  is a bulk-resubmit path.
- Do not submit the original four-case packed groups unchanged.
- Submit at most the selected wave-1 rows first:
  - `salt2_jin_lo10q_corrected`
  - `salt2_jin_hi10q_corrected`
- Use a per-row or explicitly two-row launcher manifest, not the full
  `corrected_case_manifest.csv` grouping.
- Re-run preflight patch audits immediately before any launch.
- Confirm the continuation target can satisfy the formal operating-point gate
  or explicitly document a reviewed gate-policy change before launch.
- After wave 1 exits, run the same formal gate path and stop. Do not launch
  wave 2 until the wave-1 gate result is known.
- Keep every future admitted row labeled
  `sensitivity/correlation-support`; none becomes a nominal baseline.

