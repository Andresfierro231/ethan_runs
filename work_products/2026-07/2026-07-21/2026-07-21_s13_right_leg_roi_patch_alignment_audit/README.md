---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv/component_topology_forensics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv/component_boundary_escape_by_patch.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/wall_core_band_contract.csv
tags: [s13, upcomer-exchange, roi, geometry-seed, fail-closed]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition/release_decision.csv
task: TODO-S13-RIGHT-LEG-ROI-PATCH-ALIGNMENT-AUDIT-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Tester / Writer
type: work_product
status: complete_fail_closed
---
# S13 Right-Leg ROI Patch Alignment Audit

This package audits whether the reverse-flow cell-center ROI and trusted
right-leg wall patches describe the same physical S13 region.

Decision: `complete_fail_closed_geometry_seed_required`.

Dominant reverse-flow components in Salt2/Salt3/Salt4 have zero trusted
right-leg wall patch contact. The only wall-contact alternate components are
absent for Salt2 and tiny for Salt3/Salt4, where they touch unreleased
`ncc_pipeleg_right_03_upper_end` boundary faces. A source-bounded S13 CV should
therefore not be released from the velocity-only dominant component rule.

Next executable unlock is a predeclared geometry-backed right-leg/upcomer seed
tied to `pipeleg_right_01_lower`, `pipeleg_right_02_middle`, and
`pipeleg_right_03_upper`, followed by a rerun of source-bounded CV release.

No native-output mutation, scheduler action, surface extraction, sampler,
harvest, Fluid edit, threshold relaxation, new mask admission, exchange-cell
admission, S11/S12/S15/S6 trigger, or internal-Nu residual absorption was
performed.
