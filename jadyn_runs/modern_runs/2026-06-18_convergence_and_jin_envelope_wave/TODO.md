# TODO

- [x] Stage Salt 1 Jin continuation copy from the latest existing continuation candidate.
- [x] Stage Salt 2 Jin continuation copy from the staged modern source case.
- [x] Stage Salt 3 Jin continuation copy from the staged modern source case.
- [x] Stage Salt 4 Jin continuation copy from the latest existing continuation candidate.
- [x] Stage Water 1-4 continuation copies from the staged modern source cases.
- [x] Submit 4 Salt Jin continuation jobs.
- [x] Submit 4 Water continuation jobs.
- [x] Record all job IDs in `campaign_manifest.csv`.
- [x] Repack the active Salt 2/3/4 continuations onto one node as job `3250777`.
- [x] Repack the Water 1/2/3/4 continuations onto one node as pilot job `3250776`.
- [x] Raise all active continuation cases in this wave to `purgeWrite 21`.
- [ ] Update `imports/2026-06-18_ethan_convergence_and_jin_envelope_wave.json`.
- [ ] Update `.agent/status/2026-06-15_AGENT-072.md` with the submitted wave.
- [ ] Update `.agent/journal/2026-06-18/coordinator-implementer-transport-analysis-and-paper-handoff.md`.
- [ ] Update `journals/2026-06/2026-06-18_ethan_runs.md`.
- [ ] Day-1 queue/health check.
- [ ] Day-2 first-clean-write check.
- [ ] Day-3 convergence classification checkpoint.
- [ ] Build the gated Jin-only Salt DOE child scaffolds after clean parent writes.
- [x] Inspect the Water `4 x 64` packed pilot for runtime stability, memory pressure, and retained-write behavior before reusing that layout.
- [x] Queue a `normal`-partition Water follow-on behind the live packed pilot as
  job `3253879` using `2 x 128`-CPU normal nodes to preserve the existing
  `4 x 64` case layout.
- [x] Cancel live dedicated Water job `3250776` so `3253879` can proceed in
  the normal queue without waiting on the original dedicated node.
- [x] Capture the June 23 retained-window checkpoint package so the current
  Salt and Water late windows can be analyzed as a bounded snapshot.
- [x] Recover the mistakenly canceled Water follow-on as `3254180` so the
  background continuation path stays live after the checkpoint pass.
- [ ] Before any fixed-`Q` Salt DOE child submission, write the parent
  reference-state heat ledger and derive the child cooling-branch sink so the
  documented signed heat residual stays near zero.
- [ ] Finalize the temporary Salt checkpoint copy under
  `tmp/2026-06-23_salt_last20_checkpoint/` once the background copy finishes
  and the local manifest is written.
