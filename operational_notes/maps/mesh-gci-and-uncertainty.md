---
task: AGENT-294
date: 2026-07-13
role: Writer
type: map
status: reference
tags: [mesh-gci, uncertainty, gci]
related:
  - operational_notes/maps/README.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/cfd-runs-and-admission.md
---
# Mesh, GCI & Uncertainty — Map of Content

Tags: #mesh-gci #uncertainty #gci

## What this covers

Grid-convergence (GCI) and mesh-sensitivity of the closure QOIs, plus the
separate time-series / steady-state statistical uncertainty of the CFD monitors.
This hub is the entry point for "how mesh-converged and how statistically settled
are the numbers we fit the 1D model to." Endpoint-monitor GCI, closure-QOI GCI,
and time-series UQ are three distinct threads tracked here.

## Current status

Ethan's coarse/medium/fine mesh family (24 cases) has been readable since
2026-07-09, so the long-standing "no mesh for GCI" blocker is **superseded** — do
not re-report it. The live limitation is now downstream: closure-QOI mesh GCI is
**not publication-ready**. The 2026-07-14 refresh consumes coarse/medium/fine
thermal repair-smoke rows plus prior nonthermal closure decisions: 25 QOI rows,
0 publication-ready rows, 0 fit-admissible thermal rows, and a 16-row thermal
admission table with 11 validation-only diagnostics and 5 blocked rows. Thermal
extraction is now available for selected lower-leg/upcomer triplets, but those
rows remain non-fit because of sign/enthalpy review, heat-balance residuals,
lower-leg Nu availability/admission, downcomer policy, and the guardrail that
internal Nu must not absorb source, wall-storage, passive-loss, or radiation
residuals. Nonthermal closure rows remain blocked by missing triplets or
non-monotone/oscillatory mesh behavior. The separate time-series/steady-state
UQ thread is **worked and trustworthy**.

2026-07-16 AGENT-459 update: final-use Closure-QOI/GCI is now narrowed to the
non-upcomer fit lanes in
`work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/`.
That package reviews `13` final-use non-upcomer GCI rows and finds `0`
publication-ready final-use GCI rows. Upcomer/test-section rows are excluded
from single-stream final-use GCI and kept in the hybrid/onset diagnostic lane.
The next GCI work should run only after branch-local admission decides which
non-upcomer rows remain intended for final fitting.

2026-07-16 AGENT-466 update: the first branch-local admission attempt focused
on the downcomer in
`work_products/2026-07/2026-07-16/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap/`.
It did not promote any row to final-use GCI: the single downcomer Nu candidate
still has `0` mesh/GCI pass rows and is blocked before GCI closeout by
sign/heat-balance and low-recirculation admission. Same-QOI GCI should still be
deferred until a branch-local row survives physical admission.

2026-07-16 AGENT-469 update: the downcomer policy/admission artifact in
`work_products/2026-07/2026-07-16/2026-07-16_downcomer_policy_admission_artifact/`
documents why the downcomer lane cannot admit an ordinary Nu/GCI row. It checks
sign/enthalpy, low-recirculation validity, and same-QOI GCI before Nu fitting:
all `4` same-QOI GCI rows fail, and no ordinary downcomer Nu row is admitted.
The useful nuance is that station-core low-recirculation passes while interface
recirculation and thermal heat-balance evidence fail. AGENT-474 later resolves
the global `closure-qoi-mesh-gci` blocker by final-use disposition/exclusion,
not by admitting this downcomer evidence as fit data.

## Trusted results

- **Time-series / steady-state UQ (WORKED)** — 52 postProcessing dirs; trend +
  CLT SEM + autocorrelation. Steady relative uncertainty 0.001–0.05%; adopt a
  600 s averaging window. `total_Q` flags "not steady" only because its residual
  noise is near-zero. `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/`
- **Salt2 pressure-only medium/fine comparison** — fit-safe (raw
  pressure-gradient) only for `left_lower_leg`, `left_upper_leg`; medium/fine
  Darcy-friction change <10% on those. Momentum-corrected friction is positive
  and medium/fine-consistent on all six spans but must not be conflated with raw
  pressure-gradient friction. `work_products/2026-07/2026-07-13/2026-07-13_salt2_pressure_only_mesh_family_comparison/`
- **Endpoint-monitor GCI** — Salt2 endpoint-monitor rows admitted earlier; this
  lane is separate from and ahead of the closure-QOI lane.

## Open / in-progress / blocked

- **`closure-qoi-mesh-gci` (OPEN, high)** — 14 nonthermal complete triplets
  remain non-monotone/oscillatory, 5 rows are blocked-missing-triplet, 5 thermal
  rows are blocked-sign-review, and 1 thermal row is blocked-downcomer-policy;
  0 rows are publication-ready. AGENT-459 further restricts current final-use
  review to 13 non-upcomer rows and still finds 0 publication-ready rows. This,
  not "no mesh," is the #1 trust limiter.
  Blocks T6, T11, mesh-uncertainty-bounds.
  `.agent/journal/2026-07-13/salt2-closure-qoi-mesh-gci.md`,
  `.agent/journal/2026-07-14/thermal-closure-mesh-gate-refresh.md`,
  `work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci/`,
  `work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/`
- **`refined-mesh-t-reconstruction-corruption` (RESOLVED/SUPERSEDED)** — serial
  reconstructed medium `T` had nonfinite tokens, but OF13 reconstruction works
  and split reconstruction has produced medium, fine, and coarse repair-smoke
  outputs. Do not reopen this as a live blocker. Treat repair-smoke outputs as
  diagnostic until a separate admission gate admits source rows.
  `.agent/journal/2026-07-13/reconstructed-t-repair-diagnosis.md`,
  `work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial/`,
  `work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch/repair_trial_output/`,
  `work_products/2026-07/2026-07-13/2026-07-13_salt2_coarse_thermal_repair_smoke/`
- **Refined NCC interface breaks the OF13 `fvMeshStitcher` at runtime** → needs a
  conformal-first remesh; many med/fine solver logs end on walltime.
  `operational_notes/07-26/09/2026-07-09_salt_mesh_refinement_discovery_plan.md`
- **TODO-MESH-UNCERTAINTY (board row, open)** — intake mesh levels, compute GCI
  where defensible, and explicitly mark QOIs too mesh-sensitive for publication.
  Do NOT fabricate GCI for two-level or non-monotone data.

## Research avenues tried (outcome + provenance)

- **Assemble Salt2 closure-QOI GCI table** → produced 25 candidate rows but 0
  publication-ready; made the blockers explicit and reproducible instead of
  faking convergence. `work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci/`
- **Refresh thermal/closure mesh gate after coarse thermal smoke** → consumed
  coarse/medium/fine thermal smoke plus prior nonthermal closure decisions; 25
  rows, 0 publication-ready, 0 fit-admissible thermal. Added a thermal
  admission memo/table: lower-leg finite HTC/UA and energy rows are
  validation-only, lower-leg Nu is blocked, upcomer finite rows are
  validation-only recirculation/heat-balance diagnostics, and downcomer rows are
  blocked. Main table:
  `work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/refreshed_qoi_mesh_gate_status.csv`
- **Blocker-resolution plan across thermal/GCI, forward model, and
  hydraulic/API gaps** → defines three major areas, nine work packets, ten
  scientific rigor gates, and coverage for all six open blockers without
  promoting smoke outputs or stale blockers.
  `work_products/2026-07/2026-07-14/2026-07-14_blocker_resolution_plan/`
- **Pressure-only mesh-family comparison (skip `T`)** → succeeded; proved fine
  pressure sampling works when `T` is excluded, salvaging two fit-safe spans.
  `work_products/2026-07/2026-07-13/2026-07-13_salt2_pressure_only_mesh_family_comparison/`
- **Reconstruct refined `T` for thermal GCI** → failed; `foamPostProcess`
  rejected reconstructed `T` (`wrong token type … '-'`). Diagnosed as a
  reconstruction artifact; native field is fine. Split-reconstruction workaround
  (AGENT-267) yields smoke, not admitted rows.
  `.agent/journal/2026-07-13/reconstructed-t-repair-diagnosis.md`
- **Run refined meshes as-delivered** → failed; NCC interface breaks the
  `fvMeshStitcher`, logs hit walltime. Conformal-first remesh required.
  `operational_notes/07-26/09/2026-07-09_salt_mesh_refinement_discovery_plan.md`
- **Time-series steady-state UQ** → succeeded; trend + SEM + autocorrelation over
  52 dirs, 600 s window adopted.
  `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/`

## Key artifacts (canonical)

- GCI calculator — `tools/analyze/compute_gci.py`
- Closure-QOI GCI builder — `tools/analyze/build_salt2_closure_qoi_mesh_gci.py`
- Mesh-independence protocol — `operational_notes/06-26/30/2026-06-30_mesh_independence_protocol.md`
- Mesh-family intake plan — `operational_notes/07-26/09/2026-07-09_salt_mesh_refinement_discovery_plan.md`
- Closure-QOI GCI package — `work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci/`
- Thermal/closure mesh gate refresh and admission memo/table — `work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/`
- Branch-local Internal-Nu / final-use GCI unblock queue — `work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/`
- Downcomer Internal-Nu unlock and blocker roadmap — `work_products/2026-07/2026-07-16/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap/`
- Downcomer policy/admission artifact — `work_products/2026-07/2026-07-16/2026-07-16_downcomer_policy_admission_artifact/`
- Pressure-only mesh comparison — `work_products/2026-07/2026-07-13/2026-07-13_salt2_pressure_only_mesh_family_comparison/`
- Time-series / steady-state UQ — `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/`
- Recirculation policy / final hydraulic unblock chain — `work_products/2026-07/2026-07-15/2026-07-15_recirculation_policy_forward_hydraulic_unblock_plan/`
- Presentation uncertainty table — `tools/analyze/build_time_series_uncertainty_story.py`
- Blocker ledger — `.agent/BLOCKERS.md`

AGENT-419 clarifies that current AGENT-409 raw two-tap pressure rows remain
coarse diagnostic evidence until pressure definition, tap orientation,
straight-loss subtraction, and mesh/GCI are admitted. They may be labeled
`K_section_effective_recirculating_diagnostic`; they do not admit true component
`K` or final hydraulic residual attribution.

## Related

- `operational_notes/maps/README.md` — maps index / how to use hubs
- `operational_notes/maps/thermal-closures-and-internal-nu.md` — thermal-QOI admission and internal-Nu guardrails
- `operational_notes/maps/cfd-runs-and-admission.md` — endpoint-monitor admission & steady-state
