---
provenance:
  - work_products/2026-07/2026-07-23/2026-07-23_s13_stationary_window_qwall_mesh_gci/summary.json
tags: [s13, mesh-gci, mesh-independence, stationary-window, start-here, blocker-unlock]
related:
  - work_products/2026-07/2026-07-23/2026-07-23_s13_stationary_window_qwall_mesh_gci/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_mesh_gci_disposition/README.md
  - operational_notes/07-26/22/2026-07-22_PASSIVE_H2_STRICT_SOURCE_ENVELOPE_AND_RELEASE_UQ_CONVERSION.md
task: TODO-S13-STATIONARY-WINDOW-QWALL-MESH-GCI-2026-07-23
date: 2026-07-23
role: Coordinator / Writer
owner: claude
type: operational_note
status: current
---

# Start-here: stationary-window mesh GCI unlock (2026-07-23)

## Why this exists
The item-4 science frontier (S13 closeout / source-property release / low-recirc
anchor / TW-after-TP residual) was scoped: three of four options share ONE master
blocker — missing medium/fine CFD fields at the coarse target physical times.
This note records a methodological unlock that removes that blocker for **steady
QOIs** without any new CFD.

## The unlock
Prior S13 fail-closed the formal GCI on `blocked_unmatched_physical_time_indices`
(coarse continuation windows are at different absolute times than medium/fine
terminal windows). But for a QOI at a statistically **stationary** state the
absolute time is immaterial — the converged value is a property of the (case,
mesh) steady attractor, and comparing across meshes is exactly mesh convergence.
Measured stationarity is decisive: `Q_wall` within-window half-range <= 0.003% on
every mesh.

## Result (existing data only, no new CFD)
- **Q_wall mesh-UQ ADMITTED** for Salt2/3/4: GCI_fine 0.0005% / 0.51% / 0.36%,
  observed order p = 10.2 / 2.06 / 2.02, asymptotic ratio ~1.0. First admissible
  GCI in the project; the loop wall-heat QOI is mesh-independent to <= 0.51%.
- **Recirculation-exchange proxies fail-closed** (GCI 79-768%, asymptotic ratio
  0.51-0.65): the current mesh family does not resolve the recirculation-cell
  exchange transport (real physics limit).

## What it unblocks / what it does not
- Resolves the long-standing "no mesh-independence / GCI bounds" blocker for the
  loop wall-heat QOI.
- Passes the same-QOI UQ `mesh_gci_gate` **for Q_wall only**.
- Tells the TW-after-TP residual-ownership gate: the wall-heat delivery owner is
  mesh-trustworthy, but any owner relying on the exchange proxies is not.
- Does NOT release source/property, does NOT freeze, does NOT score, and is NOT a
  PASSIVE-H2 `qambient` GCI (Q_wall is the seeded exchange-CV wall-heat integral).

## Next sequence
1. Independent review of the stationary-window equivalence argument before it is
   cited as admitted same-QOI mesh-UQ in the thesis.
2. Extend to PASSIVE-H2 `qambient` / loop `mdot`: sample those exact QOIs at the
   coarse/medium/fine stationary windows and rerun the GCI builder (small sampler
   task on existing native fields; no new solve).
3. Exchange-transport QOIs remain blocked pending a finer mesh (new CFD).
4. Option A (PASSIVE-H2-R4 release-proof-minus-UQ) can now consume this GCI as the
   loop-thermal mesh-UQ leg.

## Do-not-do
No solver/sampler/harvest launch from this analysis row, no native/registry/
scheduler/Fluid/thesis mutation, no source/property/Qwall release, no coefficient
admission, no candidate freeze, no scoring, no borrowed GCI or fabricated
monotonicity, no mesh-GCI admission beyond what the asymptotic-range check
supports, no S11/S15/S6 trigger, no commit/push without explicit request.
