---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/recirculation_onset_metric_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/reverse_flow_topology_proxy.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/s13_exchange_tau_proxy_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/same_qoi_temporal_uq_boundary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_mesh_gci_uq_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility/segment_case_regime_map.csv
tags: [upcomer, recirculation, onset, uq, anchor-design, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-THESIS-STUDY-UPCOMER-ONSET-ANCHOR-DESIGN-AND-RECIRC-FRACTION-UQ-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-study-upcomer-onset-anchor-design-and-recirc-fraction-uq.md
  - imports/2026-07-22_thesis_study_upcomer_onset_anchor_design_and_recirc_fraction_uq.json
task: TODO-THESIS-STUDY-UPCOMER-ONSET-ANCHOR-DESIGN-AND-RECIRC-FRACTION-UQ-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Writer / Reviewer / Tester
type: work_product
status: complete
---
# Upcomer Onset Anchor Design And Recirculation-Fraction UQ

Decision: `diagnostic_onset_evidence_ready_closed_fraction_and_admission_fail_closed`.

This package defines the minimum evidence needed to move from observed upcomer
recirculation diagnostics to an onset/recirculation-fraction map. It preserves
the active S13 sampler boundary: no active sampler output, native CFD output,
production harvest, mesh/GCI rerun, source/property release, or coefficient
admission was touched.

## Current Evidence

Current evidence is strong enough for a diagnostic thesis statement:

- Salt2/Salt3/Salt4 share common-range upcomer velocity figures with max
  downward y-velocity visual bound `0.0770250484347 m/s`.
- Reverse-candidate fractions of the right-leg ROI are:
  - Salt2: `0.157702688614`
  - Salt3: `0.160299790332`
  - Salt4: `0.162167108784`
- Largest reverse-candidate component fractions of the right-leg ROI are:
  - Salt2: `0.0831431649426`
  - Salt3: `0.0849664647214`
  - Salt4: `0.0860171209471`
- S13 current-coarse exchange/tau proxies are finite:
  - Salt2: `mdot_exchange_positive_outward_proxy = 2.68592194714e-05 kg/s`,
    `tau_recirc_proxy = 868.807159089 s`
  - Salt3: `4.23665968058e-05 kg/s`, `547.838912867 s`
  - Salt4: `7.65896288069e-05 kg/s`, `301.390653047 s`
- Temporal same-QOI UQ has been executed diagnostically for four S13 QOI labels,
  but production/admission remains closed.

## Fail-Closed Items

The following remain blocked and must not be silently inferred:

- closed recirculation volume/fraction;
- same-window, same-CV Richardson number;
- medium/fine same-label mesh/GCI;
- production harvest of S13 exchange-cell QOIs;
- ordinary upcomer `Nu/f_D/K/F6`;
- exchange-cell coefficient admission;
- final predictive candidate or protected-row score.

## Package Files

- `recirculation_fraction_definition_contract.csv`
- `diagnostic_onset_evidence_table.csv`
- `nondimensional_regime_context.csv`
- `same_qoi_uq_mesh_gate.csv`
- `ordinary_closure_disable_map.csv`
- `future_anchor_design_matrix.csv`
- `figure_table_targets.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
- `figures/svg/upcomer_onset_evidence_gate.svg`

## Next Gate

The next science unlock is still S13 sampler repair closeout. If the smoke
produces nonempty exact-label medium/fine rows, run the post-sampler mesh/GCI
and production-harvest gate. If it fails or remains blocked, the next compute
design should target near-onset/nonrecirculating anchors with predeclared RAF,
RMF, closed-volume, same-window Ri, and exchange-QOI harvest requirements.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state,
active S13 sampler output, Fluid/external repository, source/property release,
Qwall release, production harvest, coefficient admission, protected scoring,
or final score was changed.
