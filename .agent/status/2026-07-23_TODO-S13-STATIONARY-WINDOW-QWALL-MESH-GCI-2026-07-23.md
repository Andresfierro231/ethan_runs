# TODO-S13-STATIONARY-WINDOW-QWALL-MESH-GCI-2026-07-23 Status

Date: `2026-07-23`
Role: Hydraulics / Thermal-modeling / Mesh-GCI / Implementer / Tester / Writer / Reviewer
Owner: claude

## Scope
Test whether a stationary-terminal-window mesh GCI can resolve the S13
`blocked_unmatched_physical_time_indices` / `missing_same_label_coarse_member`
fail-closed for steady QOIs, using only existing native-sampled data, and admit
mesh-UQ only where the ASME asymptotic-range check earns it.

## Completed
- Verified terminal-window stationarity for the coarse/medium/fine Jin meshes:
  `Q_wall` within-window half-range <= 0.003% of the mean on every (case, mesh).
- Built `tools/analyze/build_s13_stationary_window_qwall_mesh_gci.py` (reads the
  committed coarse + medium/fine QOI rows + mesh cell counts; runs
  `tools/analyze/compute_gci.py`) and its test (6 tests, all pass).
- Result: **Q_wall mesh-UQ ADMITTED for Salt2/3/4** — GCI_fine 0.0005% / 0.51% /
  0.36%, observed order p = 10.2 / 2.06 / 2.02, asymptotic ratios 0.999 / 0.994 /
  0.996. First formal, admissible GCI in the project; loop wall-heat is
  mesh-independent to <= 0.51%.
- Recirculation-exchange proxies (`mdot_exchange`, `tau_recirc`,
  `wall_core_contrast`) FAIL-CLOSED (GCI 79-768%, asymptotic ratio 0.51-0.65,
  some divergent) — genuinely mesh-unconverged on this mesh family.
- Kept source/property release, freeze, and score at False; 16 guardrails False.
- Wrote README, import manifest, operational_notes note, this status, journal.

## Current State
The `mesh_gci_gate` component of same-QOI UQ now **passes for Q_wall** via a
defensible stationarity argument, resolving the long-standing mesh-independence
blocker for the loop wall-heat QOI. The exchange-transport QOIs remain
mesh-unconverged (a real physics limit, not a gate technicality). Nothing was
released, frozen, or scored.

## Follow-up
1. Independent review of the stationary-window equivalence argument before it is
   cited as admitted same-QOI mesh-UQ in the thesis (Codex appears active again).
2. To extend mesh-UQ to PASSIVE-H2 `qambient` / loop `mdot`, sample those exact
   QOIs at the coarse/medium/fine stationary windows and rerun this GCI (small
   sampler task on existing native fields).
3. The exchange-transport QOIs need a finer mesh (new CFD) to converge; do not
   admit them on the current meshes.
4. Then option A (PASSIVE-H2-R4 release-proof-minus-UQ) remains available; this
   GCI supplies the mesh-UQ leg for the loop-thermal QOI class.
