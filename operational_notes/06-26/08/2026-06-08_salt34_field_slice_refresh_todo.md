# TODO: Salt 3/4 Field Slice Refresh

Updated: `2026-06-08T13:46:21-05:00`

Status as of `2026-06-22`:

- The Salt 3/4 slice refresh itself is complete and no longer needs follow-up.
- The first two bullets remain optional presentation/product choices, not
  render-pipeline blockers.
- The `ExitCode=11` item is now a documented ParaView caveat rather than an
  unknown blocker; artifact existence plus status JSON are the accepted success
  criteria for this render family.

- [ ] Decide whether to publish the existing `Nu(x)` plots as the presentation-facing heat-transfer proxy or build a separately labeled `HTC(x)` derivation.
- [ ] Build transient `Delta p_rgh(t)` or distance-resolved `Delta p(x)` products if the presentation needs more than latest-time branch ranking.
- [ ] Investigate why ParaView render jobs keep returning `ExitCode=11` after successful artifact writes.
