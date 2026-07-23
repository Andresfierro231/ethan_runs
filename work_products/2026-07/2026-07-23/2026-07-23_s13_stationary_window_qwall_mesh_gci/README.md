---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_coarse_extraction_gci_uq_chain/direct_sampled_coarse_surface_field_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/aggregated_exact_label_qoi_rows.csv
  - work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_discovery/mesh_case_inventory.csv
  - tools/analyze/compute_gci.py
tags: [s13, mesh-gci, mesh-independence, stationary-window, recirculation, exchange-cell, Q_wall, fail-closed]
related:
  - .agent/status/2026-07-23_TODO-S13-STATIONARY-WINDOW-QWALL-MESH-GCI-2026-07-23.md
  - .agent/journal/2026-07-23/s13-stationary-window-qwall-mesh-gci.md
  - operational_notes/07-26/23/2026-07-23_S13_STATIONARY_WINDOW_QWALL_MESH_GCI.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_mesh_gci_disposition/README.md
task: TODO-S13-STATIONARY-WINDOW-QWALL-MESH-GCI-2026-07-23
date: 2026-07-23
role: Hydraulics / Thermal-modeling / Mesh-GCI / Implementer / Tester / Writer / Reviewer
owner: claude
type: work_product
status: complete
---

# S13 Stationary-Window Q_wall Mesh GCI

Decision: `qwall_mesh_uq_admitted_exchange_proxies_fail_closed_mesh_unconverged`.

This package computes the **first formal, admissible Grid Convergence Index (GCI)**
for the S13 seeded exchange-CV QOIs, using only already-committed native-sampled
data. It resolves the prior `blocked_missing_same_label_coarse_member` /
`blocked_unmatched_physical_time_indices` fail-closed by making the physical-time
equivalence argument **explicit and testable** rather than assumed.

## The methodological unlock

The coarse continuation windows (Salt2 ~7914 s, Salt3 ~7617 s, Salt4 ~9999 s)
are at different *absolute* physical times than the medium/fine terminal windows
(~517 s / ~398 s, etc.), and prior S13 packages declined to treat them as
equivalent. But **the absolute time index is immaterial for a QOI that has
reached a statistically stationary state**: the converged value is a property of
the (case, mesh) steady attractor, so comparing those values across meshes *is* a
mesh-convergence comparison. We quantify stationarity from the three sampled
sub-windows per (case, mesh, qoi) and admit a mesh-GCI only where stationarity
holds **and** the ASME/Roache asymptotic-range check passes. Stationarity is
overwhelming: `Q_wall` window half-range is <= 0.003% of the mean on every mesh.

## Results

Refinement ratios from cell counts (2.167M / 6.744M / 21.78M, ASME h ~ N^(-1/3)):
`r21 = 1.478`, `r32 = 1.460`.

**Q_wall (trusted-wall wallHeatFlux integral) — mesh-UQ ADMITTED, all 3 cases:**

| case | coarse | medium | fine | observed order p | GCI_fine | asymptotic ratio | verdict |
|------|--------|--------|------|------------------|----------|------------------|---------|
| salt_2 | 23.116 | 22.848 | 22.842 | 10.2 (super-conv.) | 0.0005% | 0.999 | monotonic conv. |
| salt_3 | 25.347 | 25.079 | 24.953 | **2.06** | **0.51%** | 0.994 | monotonic conv. |
| salt_4 | 28.123 | 27.922 | 27.826 | **2.02** | **0.36%** | 0.996 | monotonic conv. |

Salt3/Salt4 recover near-textbook second order; Salt2 is super-converged
(fine ~= medium). Asymptotic-range ratios ~1.0 confirm the triplets are in the
asymptotic range. **Q_wall is mesh-independent to <= 0.51% (GCI, fine grid).**

**Recirculation-exchange proxies — FAIL-CLOSED (mesh-unconverged):**
`mdot_exchange`, `tau_recirc`, `wall_core_bulk_temperature_contrast` all show
GCI_fine of 79-768% and asymptotic ratios far from 1 (0.51-0.65), some
monotonic-divergent. The current mesh family does **not** resolve the
recirculation-cell exchange. This is a real physics finding, not a gate technicality.

## What this means

- **Mesh-independence blocker:** the loop wall-heat QOI now has a defensible GCI
  bound (<= 0.51%) from existing data — addressing a long-standing open item
  ("no mesh-independence / GCI bounds yet") without any new CFD.
- **Same-QOI UQ `mesh_gci_gate`:** passes **for Q_wall only**. The exchange QOIs
  remain fail-closed.
- **TW-after-TP residual ownership:** the wall-heat *delivery* is mesh-robust,
  but the recirculation-*exchange transport* is not — so a residual owner that
  depends on the exchange proxies cannot be admitted on this mesh family.

## Scope and honesty caveats

- `Q_wall` here is the **seeded right-leg exchange-CV** trusted-wall wallHeatFlux
  integral, not the whole-loop PASSIVE-H2 outer `qambient`. Its mesh-UQ admission
  is a `mesh_gci_gate` component; it is **not** a PASSIVE-H2 source/property
  release and **not** a candidate freeze.
- The stationary-window equivalence is justified per-QOI by the measured
  within-window half-range; it is applied only to QOIs that pass the stationarity
  threshold (`0.10%`) AND the asymptotic-range check.
- Nothing here is released, frozen, fitted, or scored. No borrowed GCI, no
  fabricated monotonicity.

## Outputs
| file | content |
|------|---------|
| `stationarity_evidence.csv` | per (case, mesh, qoi): window mean, half-range, half-range %, stationary flag |
| `mesh_gci_results.csv` | per (case, qoi): coarse/medium/fine, r21/r32, R, p, GCI_fine/coarse %, asymptotic ratio, verdict, admission |
| `gci_admission_by_qoi.csv` | per-QOI rollup (admitted / fail-closed) |
| `gci_decision.csv` | overall decision + gate status |
| `no_mutation_guardrails.csv` | 16 guardrails, all False |
| `source_manifest.csv` | read-only inputs + existence |
| `summary.json` | machine-readable rollup |

## Reproduce
```
python3.11 tools/analyze/build_s13_stationary_window_qwall_mesh_gci.py
python3.11 -m pytest tools/analyze/test_s13_stationary_window_qwall_mesh_gci.py -q
```

## Next
- Independent review of the stationarity-equivalence argument before it is cited
  as an admitted same-QOI mesh-UQ in the thesis.
- To extend mesh-UQ to the PASSIVE-H2 `qambient` / loop `mdot`, sample those
  exact QOIs at the coarse/medium/fine stationary windows and rerun this GCI.
- The exchange-transport QOIs need a finer mesh family (new CFD) to converge;
  do not admit them on the current meshes.
