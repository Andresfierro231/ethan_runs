# Ri Definition Audit

Raw observations:

- Ri/Ra/Re values came from `work_products/2026-07-01_claude_allspan_convection/upcomer_convection_cell_<source_id>.csv`.
- The source files provide section-level `Ri_section_median`, `Ri_streamwise_median`, `Ra_section_median`, `Re_section_median`, and `Pr_section_median` for all six Salt 2/3/4 spans.
- The calibration table uses the median of the section medians per span, not section means.
- Delta-T fields came from `work_products/2026-07-01_claude_thermal_downcomer/segment_htc_uaprime_<source_id>.csv` where span mapping was explicit. The upcomer thermal row maps to three spans, so those rows carry a shared thermal basis.

Interpretation:

- The Ri basis is sufficient for a candidate screen because every admitted Salt 2/3/4 span has a median section Ri and streamwise projection.
- This is still not a validated portable F4 law: each physical fit group has only three coupled operating points and no independent validation case.
- Corrected Salt Q rows remain held because the formal operating-point gate has not requalified them; rows with `needs_special_gate_scrutiny=True` remain non-admissible.

Definition contract:

- `Ri_median`: median across section-level `Ri_section_median` values.
- `Ri_streamwise`: median across section-level `Ri_streamwise_median` values.
- `Ra`: median across section-level `Ra_section_median` values.
- `Pr`: median across section-level `Pr_section_median` values.
- `length_scale_basis`: hydraulic diameter.
- `property_basis`: field artifact local section properties for Ri/Ra/Re; Jin viscosity from rho/EOS-derived temperature for de-buoyed momentum rows.
