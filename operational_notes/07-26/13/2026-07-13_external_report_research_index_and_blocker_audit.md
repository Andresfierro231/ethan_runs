# External Report Research Index & Blocker Audit — Map of Content

Date: `2026-07-13`
Task: `AGENT-289`
Role: Coordinator / Writer

Tags: #external-report #research-index #map-of-content #blocker-audit #provenance
#cfd-to-1d #thermal-parity #rcExternalTemperature #radiation #mesh-gci
#salt-q-perturbation #forward-model #litrev-synthesis #closure-ledger
#reconstruction-repair #uncertainty #thesis-source

## What this is

A durable, Obsidian-style hub tying together the 2026-07-13 external report with
the wider project record. It is the recommended **single entry point** for writing
the master's thesis and for any agent trying to find where a topic lives. The full
narrative, tables, blocker audit, consolidated TODO backlog, and research-avenue
record are in the companion journal entry:

- **Main external report →** `.agent/journal/2026-07-13/coordinator-writer-external-report-and-blocker-audit.md`

## One-paragraph status

We are building a branchwise-closure 1D model of the TAMU molten-salt loop that
predicts CFD mdot and temperature distribution, following a *thermal-parity-before-
predictive-fitting* order. The current production friction closure is
`F3_shah_apparent`; thermal closures are trustworthy on the coarse mesh but carry
no discretization-error bound; the cooler/HX boundary is the first-order thermal
error (baseline Tmean error 63.75 K → 4.46 K when CFD cooler duty is imposed). The
two live frontiers are the forward-predictive `TODO-PRED-*` chain and mesh/GCI
uncertainty.

## Blocker audit — headline result

Three classic "blockers" are **stale/false** and should be scrubbed from
`CLAUDE.md` and the MASTER TODO:

1. **OF12 `reconstructPar` segfault** — resolved by the OF13 env (2026-07-01).
2. **"No mesh for GCI, waiting on Ethan"** — Ethan's coarse/medium/fine family is
   readable since 2026-07-09; the real blocker is closure-QOI GCI quality +
   conformal remesh + reconstructed-`T` repair.
3. **"CFD has no radiation"** — superseded 2026-07-13; `rcExternalTemperature`
   includes radiative exchange (emissivity 0.95, Tsur ~299 K), verified by
   microcase.

**Genuinely-open blockers:** closure-QOI mesh GCI, refined-mesh `T` corruption,
thermal CFD↔1D parity / internal-development model, upcomer onset data sparsity,
predictive heater/cooler/wall-layer submodels, Fluid external-boundary API gap.
Full evidence table: journal §3.2.

## Topic map (where each theme lives)

| Topic | Tag | Primary artifacts |
|---|---|---|
| Thermal boundary / radiation | #rcExternalTemperature #radiation | `2026-07-13_cfd_radiative_boundary_correction.md`; `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/`, `.../2026-07-13_cfd_radiative_boundary_guidance/`; `.agent/DECISIONS.md` |
| Fixed-mdot parity / forward model | #forward-model #thermal-parity | `2026-07-13_forward_predictive_model_research_plan.md`; `work_products/.../2026-07-13_predictive_heat_loss_path/`, `.../2026-07-13_patch_boundary_fixed_mdot_1d_parity/`, `.../2026-07-13_cfd_bc_no_radiation_1d_parity/` |
| Friction closures | #closure-ledger | `reports/2026-07/2026-07-09/2026-07-09_friction_correlation_math_reference/`; `2026-07-08_friction_ri_failure_and_path_forward.md`; F1/F3/F4/F5/F-lit work_products under `2026-07-07` |
| Thermal closures / internal Nu | #closure-ledger | `work_products/2026-06-30_claude_thermal_htc/`; `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/` |
| Mesh / GCI | #mesh-gci | `2026-07-09_salt_mesh_refinement_discovery_plan.md`; `work_products/.../2026-07-13_salt2_closure_qoi_mesh_gci/`, `.../2026-07-13_reconstructed_t_repair_diagnosis/` |
| Salt-Q perturbation runs | #salt-q-perturbation | `2026-07-13_salt_q_admission_policy_and_short_names.md`, `2026-07-13_salt_q_four_row_packed_continuation.md`, `2026-07-13_stopped_sbatch_steady_state_decisions.md` |
| Upcomer recirculation / onset | #closure-ledger | `2026-06-30_upcomer_convection_cell_model.md`; `work_products/2026-07/2026-07-08/2026-07-08_upcomer_onset/` |
| Pressure / momentum budget | #closure-ledger | `work_products/2026-07-01_claude_momentum_budget/`; `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/` |
| Literature synthesis / gates | #litrev-synthesis | `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/`; five `work_products/.../2026-07-13_litrev_*/`; `2026-07-13_litrev_synthesis_start_here.md` |
| Uncertainty / presentation | #uncertainty | `work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/`; AGENT-272/273 presentation tables |
| Geometry / mesh truth | — | `work_products/2026-07-01_claude_mesh_centerlines/`; `reference/geometry_reference.md` |

## How to use for the thesis

1. Start at the journal §1 (themes) and §5 (research-avenue record with outcomes).
2. Use §4 (consolidated TODO backlog) to see what is done vs open vs blocked.
3. Use §3.2 (blocker audit) so you do not re-report solved problems as open.
4. Follow the topic map above into the per-topic `work_products`/`reports`
   packages, each of which carries its own README + summary.json provenance.

## Related

- `.agent/journal/2026-07-13/coordinator-writer-external-report-and-blocker-audit.md`
- `operational_notes/07-26/10/2026-07-10_NEXT_MEETING_START_HERE.md`
- `operational_notes/07-26/13/2026-07-13_litrev_synthesis_start_here.md`
- `operational_notes/07-26/13/2026-07-13_forward_predictive_model_research_plan.md`
- `operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md`
- `.agent/BOARD.md`
- `.agent/DECISIONS.md`
