# Lit-Rev TODO Campaign Index

Date: `2026-07-13`

Task: `AGENT-288`

## Purpose

This package ties together the five implemented `TODO-LITREV-*` rows created
from AGENT-282/285. It is the next-agent entry point for the literature-review
closure-rigor campaign.

## Reading Order

1. `../2026-07-13_litrev_source_envelope/README.md`
   - Start here before promoting any source-bounded model form.
   - Key tables: `branch_source_envelope.csv`, `source_overlap_flags.csv`.

2. `../2026-07-13_litrev_property_sensitivity/README.md`
   - Use before fitting pressure or heat residuals.
   - Key tables: `property_mode_matrix.csv`,
     `property_sensitivity_summary.csv`.

3. `../2026-07-13_litrev_cfd_validity_diagnostics/README.md`
   - Use before naming any CFD-extracted `f_D`, `K`, or `Nu`.
   - Key tables: `cfd_single_stream_validity.csv`,
     `coefficient_naming_limits.csv`.

4. `../2026-07-13_litrev_reset_named_losses/README.md`
   - Use before exporting pressure losses to 1D.
   - Key tables: `reset_distance_map.csv`,
     `named_pressure_loss_table.csv`.

5. `../2026-07-13_litrev_heat_loss_calibration/README.md`
   - Use before any internal HTC/Nu or heat-loss calibration.
   - Key tables: `separated_heat_loss_ledger.csv`,
     `heat_closure_admission.csv`.

## Decision Matrix

| Gate | Current Result | Decision |
| --- | --- | --- |
| Source envelope | 90 branch/property rows and 360 source-overlap rows. | Chen 2017 can only be considered where `inside`; Tian 2024 remains reference-only for laminar TAMU rows; unknown/outside rows are not active closure evidence. |
| Property sensitivity | 90 branch/property rows and 15 summary rows. | Do not fit friction, heat-loss, or Nu residuals until replication and updated-property lanes are declared. |
| CFD validity | 18 section rows and 54 naming-limit rows. | Universal `f_D`, `K`, or `Nu` names are rejected where the section is recirculating, reverse-flow affected, or diagnostic-only. |
| Reset/named losses | 33 reset rows and 33 named pressure-loss rows. | Keep straight-section, component-K, cluster-K, and branch-apparent losses separate; no global friction multiplier is recommended. |
| Heat-loss calibration | 207 heat-path rows and 18 admission rows. | Internal Nu cannot absorb jacket, passive convection, radiation metadata, heater-efficiency, wall/storage, or residual heat terms. |

## Scientific Guardrails

- Use author/title provenance from the package rows; do not rely on citation
  numbers.
- Treat fully developed friction and Nusselt forms as references unless the
  source-envelope, reset, and validity gates admit active use.
- Keep CFD-derived coefficients section-effective unless plane isolation and
  single-stream assumptions are documented.
- Radiation in current thermal packages is metadata-bounded inside realized
  `wallHeatFlux`; do not double-count it as a separate 1D loss term.
- Missing exact reverse-flow area/mass or secondary velocity metrics should
  trigger bounded compute-node extraction, not a silent transferable coefficient
  claim.

## Recommended Next Action

Use this campaign as the closure-gate layer for the forward predictive model
work. The next implementation should consume these outputs before choosing
active friction, minor-loss, heat-loss, or internal-HTC terms.

