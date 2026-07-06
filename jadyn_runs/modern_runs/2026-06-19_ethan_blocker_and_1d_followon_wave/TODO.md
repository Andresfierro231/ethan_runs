# TODO

- [x] Create a fresh campaign root separate from the AGENT-072-owned June 18 wave.
- [x] Select the bounded Salt-only bracket cases from current defended fit participation.
- [x] Stage Salt 2 Jin high-Q / high-insulation child.
- [x] Stage Salt 2 Jin low-Q / low-insulation child.
- [x] Stage Salt 4 Jin high-Q / high-insulation child.
- [x] Stage Salt 4 Jin low-Q / low-insulation child.
- [x] Submit all four jobs.
- [x] Record job IDs in `campaign_manifest.csv`.
- [x] Record the submission in the import manifest, status file, and raw journal.
- [x] Recheck queue health after submission.
- [x] Preserve the failed Salt 4 staging artifacts instead of overwriting them.
- [x] Harden the generic continuation launcher against incomplete staged trees.
- [x] Rebuild the failed Salt 4 staged children from the static continuation parent.
- [x] Relaunch only the failed Salt 4 jobs with new job IDs.
- [x] Stage the deferred Salt 3 Jin midpoint pair.
- [x] Release the Salt 3 midpoint hold and submit both midpoint children after the June 22 user request widened the bracket scope.
- [x] Raise all staged bracket children to `purgeWrite 21`.
- [x] Cancel the unbalanced June 22 relaunches once the strict
  `|Q_in - Q_lost| < 2 W` gate was imposed.
- [x] Rebuild the six bracket roots in place to baseline insulation plus
  residual-balanced cooling-branch sinks.
- [x] Repack the six balanced bracket cases as two `3 x 64` Salt nodes.
- [ ] Find and prove a readable cooler-side mutation path before the next heater/cooler-focused boundary DOE.
- [ ] Design the next Salt follow-on around heater/cooler boundary behavior, recirculation onset, and development-length sensitivity rather than insulation tuning alone.
- [ ] Inspect the runtime and memory behavior of the new packed balanced nodes
  (`3251883`, `3251884`) before reusing the same `3 x 64` layout on larger
  Salt scenario waves.
- [x] Queue a `normal`-partition follow-on for the balanced high-Q pack as job
  `3253880` behind the live `3251883` node, using `2` normal nodes to preserve
  the existing `3 x 64` layout under the `128`-CPU normal-node geometry.
- [x] Cancel live dedicated high-Q balanced job `3251883` so `3253880` can
  proceed in the normal queue without waiting on the original dedicated node.
- [x] Capture the June 23 retained-window checkpoint package so the current
  Salt scenario lanes can be analyzed as a bounded snapshot.
- [x] Recover the mistakenly canceled low-Q and high-Q continuation paths as
  jobs `3254179` and `3254181`.
- [ ] Remove or archive the abandoned partial local copy at
  `runs/salt2_jin_hiq_balq/` once it is no longer needed as a scratch
  byproduct of the aborted fresh-copy staging attempt.
