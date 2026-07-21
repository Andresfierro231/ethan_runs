# 3D-to-1D Field-Reduction Methods

Date: 2026-06-30
Task: AGENT-161
Role: Coordinator / Writer

## User Request

Write a paper-ready explanation of how OpenFOAM 3D field data are reduced to
1D profiles and closure quantities. Explicitly address whether native model
`cellZones`, `faceZones`, and `cellSets` are used and whether they simplify the
workflow.

## Source Review

Primary sources read:

- `reports/2026-06/2026-06-29/2026-06-29_ethan_reduction_contract_audit/README.md`
- `reports/2026-06/2026-06-17/2026-06-17_ethan_streamwise_transport_math_reference/README.md`
- `reports/2026-06/2026-06-17/2026-06-17_ethan_streamwise_transport_math_reference/MATH_COMPANION.md`
- `operational_notes/06-26/30/2026-06-30_cfd_to_1d_segment_map.md`
- `operational_notes/06-26/30/2026-06-30_cfd_1d_closure_workflow.md`
- `tools/case_analysis_profiles.py`
- `tools/extract/sample_section_mean_pressure.py`
- `tools/analyze/derive_segment_friction.py`
- `tools/extract/sample_segment_htc_uaprime.py`

Observed native OpenFOAM sets/zones in the Salt 2 Jin continuation case:

- `constant/polyMesh/cellZones`: 33 cell zones, including junction/region
  topology.
- `constant/polyMesh/faceZones`: 4 face zones, all mdot-style monitor planes.
- `constant/polyMesh/sets`: `mdot_pipeleg_left_04_test_section`,
  `mdot_pipeleg_lower_05_straight`, `mdot_pipeleg_right_02_middle`,
  `mdot_pipeleg_upper_05_cooler`, and `piv_slab`.

Interpretation: zones/sets are useful and should be preserved as metadata, but
they are not by themselves a complete streamwise 1D reduction basis. The
paper-grade profile path combines them with repaired station labels, wall patch
lists, flow-direction hints, and cut-plane masking.

## Deliverable

Report package:

`reports/2026-06/2026-06-30/2026-06-30_3d_to_1d_field_reduction_methods/`

