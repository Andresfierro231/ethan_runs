# Closure Observation Update Recommendations

Do not edit the July 8 `closure_observations.csv` from this quality-gate pass.
Future observation-table work should consume `mesh_case_catalog.csv`,
`mesh_quality_gate.csv`, and `gci_candidate_matrix.csv` as qualifiers.

Recommended mapping:

- keep existing coarse Salt 2/3/4 Jin mainline rows as current central closure
  evidence until coarse source reconciliation is complete;
- attach `mesh_status=mesh_family_candidate` to rows whose mesh family exists
  but lacks a defensible GCI;
- attach `mesh_status=mesh_gci_ready` only after a later task computes and
  validates GCI from a complete, monotone, admitted triplet;
- keep `fit_use_status=held_for_mesh_uq` for mesh-family rows until the GCI
  package decides whether they update central values or only uncertainty bands;
- keep every Kirst row excluded from current mainline fits unless a dated task
  explicitly re-admits Kirst.

The next closure-correlation retry should wait until Salt 2 Jin coarse
reconciliation and Salt 4 Jin continuation/quality gating are resolved.
