# Pressure Term Ledger — TODO-PRESSURE-TERM-LEDGER, 2026-07-08

## Purpose

Unified per-segment pressure decomposition for Salt 2/3/4 Jin mainline cases
(18 rows = 3 cases × 6 spans). Joins the CFD momentum budget, mesh-PCA arc
lengths, section endpoint pressure/dynamic-head rows, source-window provenance,
and bend minor-loss data into one fit-ready CSV/JSON ledger suitable for
verifying the no-double-counting rule and comparing closure term magnitudes.

## Provenance

| Source | Path | Role |
|---|---|---|
| Momentum budget | `work_products/2026-07-01_claude_momentum_budget/momentum_budget.csv` | De-buoyed friction + buoyancy gradients per span |
| Segment arc lengths | `work_products/2026-07-01_claude_segment_friction/segment_friction.csv` | L_m, D_h_m from mesh PCA |
| Bend K values | `work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_*.csv` | Corner K and abs_loss_pa per bend |
| Section endpoint terms | `work_products/2026-07-01_claude_section_mean_pressure/section_mean_pressure_*.csv` | station endpoints, p_rgh, dynamic head, total-pressure proxy |
| Source windows | `work_products/2026-06-29_ethan_reduction_contract_audit/source_contract_map.csv` | extraction windows and source roots |
| Observation schema | `work_products/2026-07-08_closure_observation_table/closure_observation_schema.csv` | downstream fit/validation contract |

## Key findings

- Budget closure: max |residual_fraction| < 0.002 for all main legs. The
  residual is the momentum-budget identity residual, not a second subtraction
  of development/minor losses that are already embedded in the CFD distributed
  mechanical-loss term.
- f_debuoyed round-trip error < 1e-5 (pure floating-point arithmetic).
- development_loss is 20–40% of distributed_friction for short entry segments
  (x+ ≈ 0.08–0.6), reflecting large Shah vs F1 difference at TAMU loop Re.
- minor_loss_pa is 5–15% of distributed_friction for spans with bends.
- Station endpoint columns now carry p_rgh, dynamic head, and total-pressure
  proxy values so downstream ledger checks do not need a bespoke join.

## Caveats

1. **Bend K values are upper bounds** per AGENT-189 evidence freeze.  The local
   dynamic-pressure normalization in the bend CSV overestimates actual minor
   losses relative to segment-mean conditions.  Use minor_loss_pa only as an
   upper bound for bend dissipation.

2. **development_loss uses Shah–F1 difference** as a proxy for the entry-length
   pressure excess for fresh-entry spans (flow_reset_flag=True).  Non-entry spans
   (test_section_span, left_upper_leg) receive development_loss_pa = 0.0 because
   they inherit already-developed flow from the preceding sub-span.  For entry
   spans, the flat (plug) inlet profile assumption is conservative; the true profile
   after a bend may be partially developed, reducing the actual excess.

3. **Recirculation spans** (left_lower_leg, left_upper_leg) should be treated as
   diagnostic only.  The upcomer has a backflow recirculation cell occupying
   15–33% of the cross-section; the momentum budget extracts an effective f but
   the physical interpretation is ambiguous.

4. **x_plus uncertainty** pending T6 GCI (mesh-independence study).  Currently
   no GCI bounds on L_m or D_h_m; uncertainty is O(mesh spacing / D_h).

5. **Residual formula** uses the physics-correct identity:
      residual = -sigma × distributed - gross - buoyancy
   where sigma = flow_orientation_sigma (±1). This differs from the task
   specification formula (gross - buoyancy - distributed) which is algebraically
   inconsistent with the momentum budget.  See module docstring for derivation.

6. **No buoyancy double counting:** `gh_drho_dxi_pa_m` and
   `buoyancy_contribution_pa` are reported separately as reversible/density
   gradient terms. `f_debuoyed` and `distributed_mechanical_loss_pa_m` are the
   closure-fit hydraulic terms.

## Column descriptions

| Column | Units | Source / Derivation |
|---|---|---|
| source_id | — | Case identifier (Salt 2/3/4 Jin) |
| case_id/run_class/mesh_level | — | Observation-contract metadata |
| source_window_start_s/source_window_end_s | s | Source extraction window |
| span | — | Loop segment name |
| station_start_label/station_end_label | — | Non-fitting section endpoint labels used for the span budget |
| L_m | m | Arc length from mesh PCA (segment_friction.csv) |
| D_h_m | m | Hydraulic diameter from mesh PCA |
| Re | — | Reynolds number from momentum budget |
| rho_kg_m3 | kg/m³ | Section-mean density |
| u_bulk_m_s | m/s | Bulk velocity magnitude |
| q_ref_pa | Pa | 0.5 × rho × u_bulk² |
| x_plus | — | L / (D_h × Re) — entry length parameter |
| p_rgh_start_pa / p_rgh_end_pa | Pa | Endpoint section-mean p_rgh |
| dynamic_head_start_pa / dynamic_head_end_pa | Pa | Endpoint 0.5 rho U_b² |
| total_pressure_proxy_start_pa / total_pressure_proxy_end_pa | Pa | Endpoint p_rgh + dynamic-head proxy |
| dp_rgh_dxi_pa_m | Pa/m | Flow-direction-projected p_rgh gradient |
| gh_drho_dxi_pa_m | Pa/m | Flow-direction-projected density-gradient buoyancy term |
| rho_u_du_dxi_pa_m | Pa/m | Flow-direction-projected inertial term |
| gross_static_dp_pa | Pa | grad_p_rgh × L_m (signed) |
| buoyancy_contribution_pa | Pa | buoyancy_source_grad × L_m |
| distributed_friction_pa | Pa | friction_grad_corrected × L_m (always positive) |
| distributed_mechanical_loss_pa_m | Pa/m | Debuoyed mechanical-loss gradient |
| development_loss_pa | Pa | max(Shah dp_total - F1 dp_total, 0) for entry spans; 0.0 for non-entry spans (flow_reset_flag=False) |
| minor_loss_pa | Pa | abs_loss_pa from bend CSV (0 if no bend) |
| minor_loss_K | — | K_minor_loss from bend CSV (NaN if no bend) |
| minor_loss_upper_bound_flag | bool | True where minor_loss_pa > 0 |
| recirculation_flag | bool | True for left_lower_leg and left_upper_leg |
| flow_reset_flag | bool | True = fresh entry (Shah applicable); False = developed inflow (dev loss = 0) |
| residual_assignment | — | Where the residual is assigned/interpreted |
| buoyancy_counting_policy | — | Guard against fitting buoyancy as friction |
| residual_pa | Pa | Budget residual (see formula above) |
| residual_fraction | — | residual_pa / distributed_friction_pa |
| f_debuoyed | — | Re-derived Darcy f from distributed_friction_pa |
| fit_eligible / fit_use_status | — | Fit-vs-validation eligibility following the closure observation contract |
| admission_note | — | "mainline_salt_jin" for all rows |

## Reproduce

From the ethan_runs repo root:

```bash
python tools/analyze/build_pressure_term_ledger.py
python -m pytest tools/analyze/test_pressure_term_ledger.py -v
```
