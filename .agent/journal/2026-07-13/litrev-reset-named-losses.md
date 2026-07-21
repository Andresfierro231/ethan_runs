# Lit-Rev Reset Named Losses

Date: `2026-07-13`

Task: `TODO-LITREV-RESET-NAMED-LOSSES`

Built reset and named pressure-loss tables with 33 rows each. The package
classifies pressure terms as straight-section, component-K, cluster-K, or
branch-apparent and consumes CFD validity naming limits where available.

Interpretation: pressure residuals should stay localized. No global friction
multiplier is recommended from this package.

Recommended next action: preserve component/cluster/branch-apparent names in
any 1D handoff; do not collapse them into one loop friction factor.

