---
task: AGENT-294
date: 2026-07-13
role: Writer
type: map
status: reference
tags: [thermal-closure, internal-nu, closure-ledger]
related:
  - operational_notes/maps/README.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
---

# Thermal Closures & Internal Nu — Map of Content

Tags: #thermal-closure #internal-nu #closure-ledger

## What this covers

Salt-side (internal) heat-transfer closures for the TAMU natural-circulation
loop: per-segment HTC / UA' / Nu extracted from CFD, how those diagnostics do
(and do not) feed the 1D Fluid model's internal Nusselt correlation, and the
gates that keep effective Nu diagnostic-only. Scope is the *internal* convective
resistance. External wall / radiation boundary and mesh-uncertainty threads are
tracked in the two related maps.

## Current status

Coarse-mesh patch-based thermal closures on mainline Salt2/3/4 Jin are the only
trusted internal-Nu numbers today, and they carry an explicit coarse-mesh
caveat. The CFD imposes **no** internal Nu correlation — every quoted Nu / HTC /
UA' is a postprocessed diagnostic, not a CFD input. Refined-mesh (medium/fine)
thermal closures are blocked by reconstructed-`T` corruption, and thermal GCI is
blocked with them. Before internal Nu can be *tuned* (not just diagnosed), the
heat-loss / wall-adjacent-T parity problem must be separated out. The largest
current temperature error traces to cooler duty, not to the internal Nu form.

2026-07-14 final admission update: AGENT-319 froze the lower-leg/upcomer/
downcomer thermal gate in
`work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/`.
There are `0` fit-eligible rows, `11` validation-only rows, and `5` blocked rows.
Forward-v1 internal Nu fitting is explicitly not allowed; use only
baseline/literature/default internal Nu behavior until a later gate admits
specific rows.

2026-07-14 upcomer recirculation rule: AGENT-330 documented upcomer
recirculation as an admission/naming rule in
`work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/`.
Current admitted onset evidence has three Salt2-4 diagnostic rows, all
recirculating, with `0` internal Nu fit-admissible rows. Under material
backflow, `Ri_median >= 1`, reverse-flow proxy, or an explicit recirculation
flag, single-stream `Nu`, `f_D`, and `K` labels are invalid; use
section-effective or diagnostic labels. Candidate upcomer onset rows with
matched Re/Pr/Ri/Gz/wall-bulk-Delta-T/reverse-flow metrics remain an extraction
request, not admitted fit evidence.

2026-07-14 extraction contract update: AGENT-339 converted that request into a
therm-reconstr contract in
`work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/`.
It defines matched `upcomer_inlet`, `upcomer_mid`, and `upcomer_outlet` fields,
formulas, acceptance criteria, admission classes, coefficient naming policy, and
the explicit evidence needed to reopen internal-Nu fitting. It is contract-only;
the current fit-admissible upcomer Nu count remains `0`.

2026-07-14 blocker/progress integration update: AGENT-345 documented the major
internal-Nu blockers, assumptions, methods, process, and next executable actions
in
`work_products/2026-07/2026-07-14/2026-07-14_internal_nu_blocker_progress_integration/`.
It does not reopen fitting: current fit-admissible internal-Nu rows remain `0`.
It does make progress actionable by separating matched-plane extraction,
corrected-Q harvest/admission, closure-QOI mesh/GCI gates, boundary residual
ownership, Fluid external-boundary API work, and hydraulic Re-variation gating.

2026-07-15 AGENT-413 update:
`work_products/2026-07/2026-07-15/2026-07-15_blocker_resolution_wave_implementation/`
reviewed the current thermal/internal-Nu rows after the PM5 wall-band unlock.
Result: `16` thermal rows reviewed, `0` fit-admissible rows, `11`
validation-only rows, and `5` blocked rows. Internal-Nu remains blocked from
absorbing heater, cooler/HX, passive wall, radiation, storage, or branch-mixing
residuals.

2026-07-15 AGENT-432 modeling update:
`operational_notes/07-26/15/2026-07-15_sensor_and_sophisticated_modeling_decisions.md`
adds the next thermal/hydraulic modeling direction. The upcomer should be
modeled as throughflow pipe plus recirculating convection-cell exchange, not as
ordinary single-stream pipe heat transfer for current Salt2-4 rows. Boundary
layer development must be quantified by segment using hydraulic
entrance/reset/development terms, thermal entrance/Graetz effects,
wall-adjacent temperature drive, and wall/layer resistance before any
internal-Nu fitting gate is reopened.

2026-07-15 AGENT-435 branch policy:
`operational_notes/07-26/15/2026-07-15_branch_specific_model_forms_and_upcomer_omission_plan.md`
states the immediate analysis rule: omit recirculating upcomer rows from
ordinary single-stream `Nu`, `f_D`, and `K` fits, then proceed on the other
eligible branches with branch-specific model forms and gate status. Upcomer rows
are handed to the hybrid recirculation/onset lane, not dropped from the science.

2026-07-16 AGENT-452 parity gate:
`work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate/`
resolved `thermal-cfd-1d-parity` narrowly as a blocker to predictive thermal
continuation: 7/7 residual owners are separated, setup-only HX/cooler
continuation is runtime-legal, and internal Nu remains reference/baseline or
diagnostic-only with `0` fit-admissible rows. This does not reopen Nu fitting;
it prevents Nu from absorbing heater, cooler/HX, passive wall, radiation,
storage, or recirculation residuals.

2026-07-16 AGENT-455 leg-specific admission update:
`work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution/`
removes the remaining taxonomy ambiguity but does **not** admit Internal-Nu
fitting. `test_section_span` is part of `upcomer_left_vertical`, so
test-section rows are not a separate non-upcomer ordinary-pipe/Internal-Nu fit
lane. The generated gate reviewed `50` leg-specific candidates and found `0`
fit-admissible Internal-Nu rows; `27` upcomer/test-section rows stay in the
hybrid recirculation/onset lane. Distinct future Nu/model lanes are retained for
heater/source, downcomer, cooler/HX, and upcomer, but each still needs its own
branch-local sign/heat-balance/source, residual-owner, recirculation, and
mesh/GCI admission before fitting.

2026-07-16 AGENT-459 branch-local unblock update:
`work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/`
implements that next gate and keeps Internal-Nu fitting closed. It restricts
final-use GCI review to non-upcomer fit lanes and finds `13` final-use
non-upcomer GCI rows, `0` publication-ready final-use GCI rows, `32`
Internal-Nu candidate rows, and `0` fit-admissible Internal-Nu rows. The
generated unblock queue has five lanes: heater source/sign/mesh admission,
downcomer policy/low-recirculation admission, cooler/HX residual separation,
upcomer hybrid/onset classification, and same-QOI final-use mesh/GCI.

2026-07-16 AGENT-466 downcomer-first update:
`work_products/2026-07/2026-07-16/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap/`
implements the first targeted lane from that queue. The downcomer remains the
best first ordinary non-upcomer candidate, but the current row is not admitted:
`1` downcomer Nu candidate, `0` fit-admissible rows, residual-owner partial
`4/5`, sign/heat-balance pass `0/5`, recirculation pass `0/5`, and mesh/GCI pass
`0/5`. The package also records the next studies for heater source/sign,
cooler/HX boundary separation, upcomer hybrid/onset, same-QOI GCI, M3+TS, F6,
wall thermal circuit, segment pressure/thermal models, boundary-layer
development, and thesis upcomer-recirculation writeup. Internal Nu fitting
stays closed.

2026-07-16 AGENT-469 downcomer policy/admission update:
`work_products/2026-07/2026-07-16/2026-07-16_downcomer_policy_admission_artifact/`
implements the publication-style downcomer admission artifact requested after
AGENT-466. It reviews row-level sign/enthalpy, low-recirculation validity, and
same-QOI GCI before any ordinary Nu fit. The station-core velocity evidence
passes low-recirculation, but interface recirculation fails; all `3`
sign/enthalpy rows fail; all `4` same-QOI GCI rows fail; and `0` ordinary
downcomer Nu fit rows are admitted. The downcomer remains a physically valuable
lane, but it is not fit-admissible until the thermal/interface evidence and
publication GCI are repaired or explicitly excluded.

2026-07-17 AGENT-495 upcomer onset data-sparsity update:
`work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress/`
implements the row-level misuse guardrail requested for the
`upcomer-onset-data-sparsity` blocker. The package reviews `68` current
upcomer/test-section rows and finds `36` `recirculation_diagnostic` rows,
`32` rows missing required same-window fields, `0` ordinary `Nu`/`f_D`/
component-`K` fit rows, and `0` non-recirculating or transition anchor
candidates. Current upcomer/test-section rows remain valid hybrid/onset
diagnostics and validity-boundary evidence, not ordinary single-stream
coefficient evidence. The next unlock is a near-onset/non-recirculating anchor
with same-window pressure, wall/bulk Delta-T, wallHeatFlux, onset metrics, and
mesh/time uncertainty.

2026-07-21 new-LitRev extraction update:
`work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/`
adds implementation-facing thermal/recirculation model-form guidance from the
revised LitRev. The throughflow-plus-recirculation/exchange-cell model is the
preferred escalation when persistent local reverse mass/area invalidates one
bulk state, but all coefficients remain unresolved until TAMU CFD/experiment
calibration. The CFD contract also requires enthalpy-weighted bulk temperature,
wall heat flux, `h`, `Nu`, heat-loss-network terms, and source-status labels
before any thermal closure is promoted.

2026-07-21 heat-loss contract alignment:
`work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/`
aligns the LitRev heat-loss-network rows with the current predictive
external-boundary and steady `fluid+walls` model. It is the current contract
table for runtime inputs, forbidden inputs, outputs, and blockers by heat path.
It explicitly keeps residual, radiation, passive wall loss, storage,
cooler/jacket removal, wall conduction, insulation/quartz, and contact/layer
terms out of internal `Nu`.

2026-07-21 phased progress plan:
`operational_notes/07-26/21/2026-07-21_HEATLOSS_PHASED_PROGRESS_PLAN.md`
adds the board-backed sequence for making that contract executable. For this
map, the key ordering is Phase 4: upcomer exchange and non-upcomer single-stream
gates must be evaluated before any internal-`Nu` fitting row can reopen.

## Trusted results

- **Coarse-mesh per-segment HTC / UA' / Nu, Salt2/3/4 Jin** (mainline):
  lower_leg (heater) HTC 252 / 269 / 288, UA' 16.6 / 17.7 / 18.9; upcomer Nu
  3.1 / 4.1 / 5.0; downcomer HTC ~43–44, Nu ~1.74–1.76.
  Source: `work_products/2026-06/2026-06-30/2026-06-30_claude_thermal_htc/`;
  method `operational_notes/06-26/30/2026-06-30_thermal_extraction_spec.md`.
- **Downcomer thermal is physically the simplest non-upcomer candidate**, but
  current AGENT-455 admission keeps it non-fit until downcomer policy,
  sign/heat-balance, branch-local row, and same-QOI mesh/GCI gates pass.
  Source: `operational_notes/06-26/30/2026-06-30_downcomer_closure_analysis.md`.
- **New LitRev model-form extraction** keeps internal Nu separated from heat
  loss and recirculation residuals, and packages future thermal lanes for
  heat-loss contract alignment and throughflow-plus-recirculation exchange-cell
  design. →
  `work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/`
- **Model-form audit**: CFD prescribes no internal Nu; the 1D model closes it
  with a laminar/turbulent pipe-flow correlation (M_i multiplier).
  Source: `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/`.

## Open / in-progress / blocked

- **Refined-mesh thermal closure (medium/fine HTC/Nu)** — BLOCKED by
  reconstructed-`T` `-nan` corruption
  (blocker `refined-mesh-t-reconstruction-corruption`, `.agent/BLOCKERS.md`).
  AGENT-267 split-reconstruction produced smoke rows only (lower_leg HTC 457,
  upcomer HTC 77.9 / Nu 4.28) — **not admitted**. Salt2 fine repair active
  under AGENT-291. Source: `.agent/journal/2026-07-13/reconstructed-t-repair-trial.md`.
- **Thermal GCI** — BLOCKED (blocker `closure-qoi-mesh-gci`); no mesh-uncertainty
  bounds on any thermal QoI yet. See `operational_notes/maps/mesh-gci-and-uncertainty.md`.
- **CFD→1D thermal parity residual ownership** — RESOLVED narrowly by
  AGENT-452: predictive thermal work may continue with separated residual
  owners and setup-only HX/cooler input. Internal Nu fitting remains closed
  until sign/heat-balance, recirculation, mesh/GCI, and source/path gates admit
  true rows. Source:
  `work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate/`.
- **Effective Nu / UA / HTC stay diagnostic-only** until the support / sign /
  bulk-T / mesh-UQ gates pass.

## Research avenues tried (outcome + provenance)

- **Patch-based per-segment extraction (coarse)** → SUCCESS, trusted with
  coarse caveat. `work_products/2026-06/2026-06-30/2026-06-30_claude_thermal_htc/`.
- **Refined-mesh reconstruction for medium/fine Nu** → FAILED (`-nan` corruption);
  split-reconstruction smoke rows not admitted.
  `.agent/journal/2026-07-13/reconstructed-t-repair-trial.md`.
- **Internal-Nu model-form comparison vs literature** → CLARIFYING: confirmed CFD
  has no imposed Nu; largest T-error tied to cooler duty, not internal Nu.
  `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/`.
- **Heat-loss separation / litrev calibration** → IN PROGRESS; prerequisite for
  internal Nu tuning. `work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration/`.

## Key artifacts (canonical)

| What | Path |
|---|---|
| Coarse HTC/UA'/Nu (Salt2/3/4) | `work_products/2026-06/2026-06-30/2026-06-30_claude_thermal_htc/` |
| Extraction method spec | `operational_notes/06-26/30/2026-06-30_thermal_extraction_spec.md` |
| Downcomer closure analysis | `operational_notes/06-26/30/2026-06-30_downcomer_closure_analysis.md` |
| Internal-Nu model-form comparison | `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/` |
| Heat-loss calibration (litrev) | `work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration/` |
| Final thermal admission/internal Nu gate | `work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/` |
| Upcomer recirculation/internal-Nu admissibility | `work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/` |
| Upcomer internal-Nu extraction contract | `work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/` |
| Internal-Nu blocker/progress integration | `work_products/2026-07/2026-07-14/2026-07-14_internal_nu_blocker_progress_integration/` |
| Thermal parity resolution gate | `work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate/` |
| Closure-QOI / leg-specific Internal-Nu resolution gate | `work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution/` |
| Branch-local Internal-Nu unblock queue | `work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/` |
| Downcomer Internal-Nu unlock and blocker roadmap | `work_products/2026-07/2026-07-16/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap/` |
| Downcomer policy/admission artifact | `work_products/2026-07/2026-07-16/2026-07-16_downcomer_policy_admission_artifact/` |
| Upcomer onset data-sparsity progress | `work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress/` |
| LitRev thermal heat-loss contract alignment | `work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/` |
| Heat-loss phased progress plan | `operational_notes/07-26/21/2026-07-21_HEATLOSS_PHASED_PROGRESS_PLAN.md` |
| Blocker-resolution wave / thermal admission refresh | `work_products/2026-07/2026-07-15/2026-07-15_blocker_resolution_wave_implementation/` |
| Recirculation policy / coefficient admission guardrails | `work_products/2026-07/2026-07-15/2026-07-15_recirculation_policy_forward_hydraulic_unblock_plan/` |
| Sensor and sophisticated modeling decisions | `operational_notes/07-26/15/2026-07-15_sensor_and_sophisticated_modeling_decisions.md` |
| Branch-specific model forms / upcomer omission plan | `operational_notes/07-26/15/2026-07-15_branch_specific_model_forms_and_upcomer_omission_plan.md` |
| Refined-T repair trial (blocker log) | `.agent/journal/2026-07-13/reconstructed-t-repair-trial.md` |
| Blocker ledger | `.agent/BLOCKERS.md` |
| Dimensionless-definition audit (T9) | `operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md` |

AGENT-419 adds an explicit internal-Nu guardrail: true single-stream `Nu` is not
fit-admissible when `RAF >= 0.20` or `RMF >= 0.20`; current AGENT-406 PM5 rows
must remain `Nu_section_effective_upcomer_diagnostic` or sign-review
diagnostics, not fitted internal-Nu closure rows.

## Dimensionless-definition conventions (T9 audit)

Lc = nominal bore; TRef = 447 K; solver Nu uses (Tw − TRef); use the section
**MEDIAN** Ri (~O(1)), not the mean (mean ~100× larger, dominated by near-zero
velocity cells). Source: MASTER TODO T9,
`operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md`.

## Related

- `operational_notes/maps/README.md` — maps index
- `operational_notes/maps/thermal-boundary-and-radiation.md` — external wall / radiation BC thread
- `operational_notes/maps/mesh-gci-and-uncertainty.md` — mesh-independence / GCI thread
