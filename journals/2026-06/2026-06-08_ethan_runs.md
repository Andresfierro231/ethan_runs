# Ethan Runs Update

Date: 2026-06-08

## Observed Outputs

- Built a sponsor-facing salt status deck scaffold under `reports/2026-06-08_sponsor_salt_status_deck/` with:
  - `README.md`
  - `slide_outline.md`
  - `live_status_summary.csv`
  - `summary.json`
- Recorded provenance for that package in `imports/2026-06-08_sponsor_salt_status_deck.json`.
- Captured a live June 8 continuation snapshot at `2026-06-08T10:08:00-05:00`:
  - `3202708` (`Salt 2 validation continuation`): `TIMEOUT`, ended `2026-06-07T11:42:53-05:00`
  - `3210231` (`Salt 4 Jin continuation retry 4`): `RUNNING`, elapsed `2-22:38:23`
- Confirmed from the live Salt 4 Jin continuation log that the repaired runtime path is still advancing stably through about `3896.935643564 s`, with:
  - cumulative continuity error about `1.05979532e-4`
  - mean Courant about `0.0992615276`
  - max Courant about `0.99930974`
- Updated `tools/publish/download_results_to_laptop.sh` so the new sponsor deck package is included in the default report pull set.

## Interpretation

- The current reporting stack is already strong enough to support a same-day sponsor deck without generating new CFD figures. The correct move is to reuse the existing June 4-5 salt report packages and layer on a clearly labeled June 8 live-status update.
- The sponsor-safe salt narrative remains:
  - `Salt 2` is the best-supported validation-style anchor.
  - `Salt 4 Jin` is the live continuation worth watching.
  - `Salt 1` is still the risk case and should not be framed as solved by runtime alone.
- The live June 8 Salt 4 snapshot strengthens confidence that the repaired runtime/bootstrap path is operationally healthy. It does not yet justify upgrading Salt 4 Jin from `usable with caveat` to a completed high-confidence result.
- No new case source was imported today, so `registry/case_registry.csv` was referenced for provenance rows but not expanded with a new entry.

## Contradictions / Caveats

- The sponsor deck package intentionally does not refresh all underlying report packages to June 8. It cites the latest established reports and then adds a live-status overlay for the continuation jobs.
- Water rows are still useful only as validation context. They should stay out of the sponsor-facing headline because the current workspace documentation still treats them with convergence-audit restraint.
- Salt 1 runtime/bootstrap is no longer the broad blocker, but Salt 1 Kirst still has a concrete restart-tree defect (`missing root-level T`) that prevents a clean retry claim.

## Suggested Next Actions

- If `3210231` finishes before the presentation, refresh the continuation wording in the sponsor deck package from `live continuation` to the actual final state.
- Repair the Salt 1 Kirst staged restart tree before any new retry after `3211199`.
- Build transient `p_rgh` histories for the upper leg, left leg, and test-section branch before proposing geometry changes or a wall-loss-only explanation.
- Pull the new sponsor deck package to the laptop together with the existing figure bundles if the final slides will be assembled off-cluster.
- Decide whether to present the existing `Nu(x)` plots as the heat-transfer proxy or derive a separately labeled `HTC(x)` product.
- Build transient `Delta p_rgh(t)` or distance-resolved `Delta p(x)` products if the talk needs more than latest-time branch pressure ranking.
