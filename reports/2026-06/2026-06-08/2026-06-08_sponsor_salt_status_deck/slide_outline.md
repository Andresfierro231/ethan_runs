# June 8, 2026 Sponsor Deck Outline

## Slide 1: Salt Campaign Status and Decisions

Objective: Open with the three sponsor-relevant decisions.

Title:
`Salt CFD status: what is usable now, what is still provisional, and what should run next`

Key points:
- `Salt 2` is the current validation anchor.
- `Salt 4 Jin` is the active live sensitivity continuation.
- `Salt 1` still needs restart repair plus more evidence before any confident claim.

Footer note:
`Status reflects report artifacts through June 7, 2026 plus live scheduler/log checks on June 8, 2026.`

## Slide 2: Current Salt Run State

Objective: Show the campaign state at one glance.

Use:
`live_status_summary.csv`

Columns to show:
- `salt_test`
- `representative_source_id`
- `current_state`
- `confidence_label`
- `immediate_action`

Talk track:
- `High confidence` means the row is strong enough for relative interpretation now.
- `Medium confidence` means usable with caveats.
- `Low confidence` means not yet a sponsor-safe result claim.

## Slide 3: What Is Usable Now

Objective: Separate practical usability from coded convergence.

Figure:
`reports/2026-06-05_ethan_convergence_and_salt1_campaign/figures/png/eight_case_convergence_dashboard.png`

Key points:
- `Salt 2` and `Salt 3` are effectively steady enough to use now.
- `Salt 4` is usable with caveat.
- `Salt 1` is still not steady enough.

Confidence framing:
- Strong for relative use of Salt 2-4.
- Weak for any final steady-state claim on Salt 1.

## Slide 4: Why Salt 2 Is the Validation Anchor

Objective: Justify why one Salt 2 row should anchor the sponsor narrative.

Figures:
- `reports/2026-06-04_salt2_behavior_package/figures/png/salt2_mdot_compare.png`
- `reports/2026-06-04_salt2_behavior_package/figures/png/salt2_tp_compare.png`

Key points:
- `val_salt_test_2` has the best Salt 2 bulk-probe agreement.
- `val_salt_test_2` also has the best Salt 2 mass-flow agreement.
- All three Salt 2 variants still share a similar ambient-loss bias.

Suggested claim text:
`Salt 2 is the most defensible current validation-style reference because it balances the best TP agreement, the best mdot agreement, and practical late-time steadiness.`

## Slide 5: Live June 8 Continuation Update

Objective: Distinguish completed evidence from active runtime progress.

No required figure. Use a compact text panel.

Use these exact live values:
- `As of 2026-06-08T10:08:00-05:00`
- `Salt 2 continuation 3202708: TIMEOUT on 2026-06-07T11:42:53-05:00 after advancing to about 5292.994285714 s`
- `Salt 4 Jin continuation 3210231: RUNNING, elapsed 2-22:38:23, latest observed solver time about 3896.935643564 s`
- `Salt 4 Jin live log: continuity error remains low and Courant is about 0.099 mean, 0.999 max`

Speaker note:
Describe `3210231` as a healthy live continuation, not yet as a completed result.

## Slide 6: The Mdot Mismatch Is Not Wall-Loss-Only

Objective: Make the current mechanism story clear without overselling it.

Figures:
- `reports/2026-06-05_ethan_wall_loss_resistance_coupling/figures/png/salt_mdot_vs_ambient_loss_error.png`
- `reports/2026-06-05_ethan_wall_loss_resistance_coupling/figures/png/salt_section_pressure_drop_heatmap.png`

Key points:
- Salt 2-4 cluster more tightly in ambient-loss proxy error than in mdot error.
- The upper leg is the dominant pressure-loss section in every salt row.
- This is stronger evidence for coupled resistance plus wall-loss error than for a single wall-loss-only cause.

Suggested claim text:
`The current evidence supports a coupled thermal-hydraulic mismatch story: shared wall-loss bias is present, but the mdot spread still depends strongly on resistance-sensitive variant behavior.`

## Slide 7: Salt 1 Is the Current Risk Case

Objective: Explain why Salt 1 should not be framed as merely "needing a little more runtime."

Use:
Salt 1 rows from `reports/2026-06-05_ethan_convergence_and_salt1_campaign/summary.json`

Key points:
- Salt 1 sits on a much higher residual floor than Salt 2-4.
- Salt 1 also has worse validation error simultaneously.
- Runtime repair succeeded for Jin and one Kirst retry, so the broad launcher problem is no longer the main explanation.
- The current Kirst retry blocker is missing root-level `T` in the staged restart tree.

Confidence framing:
- High confidence that Salt 1 is weaker than Salt 2-4.
- Low confidence that runtime extension alone will fully rescue Salt 1.

## Slide 8: Recommended Next Actions

Objective: End on sponsor-usable decisions.

Recommend now:
- Keep monitoring or complete `Salt 4 Jin 3210231`.
- Repair and retry the `Salt 1 Kirst` staged restart tree.
- Build transient `p_rgh` histories for the upper leg, left leg, and test-section branch.

Do not recommend first:
- Insulation thickening as the first explanatory lever.
- Cp sensitivity before wall-loss and resistance-coupling checks.
- Water-case convergence cleanup as part of this sponsor deck.

Closing line:
`The immediate path to higher-confidence sponsor conclusions is not more broad runtime everywhere; it is finishing Salt 4 Jin, repairing Salt 1 Kirst, and proving whether the current upper-left hydraulic ranking is stable in time.`
