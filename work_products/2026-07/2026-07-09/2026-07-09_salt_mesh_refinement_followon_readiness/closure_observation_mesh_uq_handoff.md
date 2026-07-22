# Closure Observation Mesh-UQ Handoff

Do not update `closure_observations.csv` from this pass.

Observed result:

- Mesh-UQ-ready rows: `0`.
- Numeric GCI rows are screening diagnostics unless `publication_ready=yes`.
- Existing July 8 closure observations should remain `mesh_status=coarse_no_gci`
  and current `fit_use_status` values until a later task has admitted mesh-UQ
  bands.

Recommended next action:

1. Reconcile mainline coarse endpoint values with the external coarse mesh-family
   source before using Salt 2 GCI bands.
2. Decide whether Salt 4 medium/fine need continuation or can be admitted by a
   stronger full-history evidence gate.
3. Extract medium/fine pressure and thermal closure QoIs before attempting GCI
   for debuoyed friction, apparent friction, Nu, or HTC.
4. Only then update closure observations with explicit mesh uncertainty fields.
