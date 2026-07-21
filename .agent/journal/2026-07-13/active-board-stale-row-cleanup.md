# Active Board Stale Row Cleanup

Date: `2026-07-13`

Task: `AGENT-278`

## Objective

Clean up six stale board rows that were still marked active even though their
original ownership was completed, superseded, or no longer backed by a complete
status handoff.

## Evidence Checked

- `.agent/BOARD.md`
- `.agent/status/2026-07-04_AGENT-178.md`
- `.agent/status/2026-07-07_AGENT-181.md`
- `.agent/status/2026-07-09_AGENT-242.md`
- Later status files: `AGENT-237`, `AGENT-241`, `AGENT-261`, `AGENT-268`,
  `AGENT-269`, and `AGENT-274`
- `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/`
- `work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/`
- `work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_publication_evidence/`

## Observations

- `AGENT-178` completed the corrected Salt-Q quarantine/staging/relaunch
  foundation and was superseded by later corrected-Q gate, naming, admission,
  and packed-launch tasks.
- `AGENT-181` completed reusable preflight/live-monitor tooling and provisional
  language audits. Its old dependency-gated submission path is no longer current.
- `AGENT-242` completed the intended live Salt1 nominal snapshot as an exclusion
  decision while job `3282992` was non-terminal; `3282992` was later cancelled
  and documented by `AGENT-268`.
- `AGENT-267` has no status file despite the board claim, but the repair-trial
  package exists and records clean reconstructed `T` plus successful section and
  segment extraction. It is complete as a repair smoke, not as closure
  admission.
- `AGENT-276` has no claimed status/journal/import files and only two CSVs in
  its work-product directory. The promised fixed-mdot replay results, README,
  metadata, and correction outputs were not found.
- `AGENT-277` has no claimed status/journal/import files. Its output package
  exists; `publication_evidence_decision.json` says `microcase_confirmed=true`,
  while README still says the microcase was not confirmed. That needs a future
  cleanup/review before publication use.

## Action Taken

Removed `AGENT-277`, `AGENT-276`, `AGENT-267`, `AGENT-242`, `AGENT-181`, and
`AGENT-178` from the Active table. Added a `Retired From Active On 2026-07-13`
block with per-row dispositions and reopen guidance.

## Follow-Up

- Reopen `AGENT-276` as a new dated task if no-radiation fixed-mdot replay
  results are still required.
- Reopen `AGENT-277` as a new dated cleanup/review task to reconcile README,
  status, journal, import manifest, and publication decision before citing it as
  publication-grade evidence.
