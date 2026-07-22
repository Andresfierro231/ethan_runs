---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/shared_velocity_ranges.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight/recirc_segmentation_case_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/s13_exchange_trend_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/same_qoi_temporal_uq_summary.csv
tags: [thesis, recirculation, onset, s13, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-THESIS-STUDY-RECIRCULATION-FRACTION-ONSET-EVIDENCE-PACKET-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-study-recirculation-fraction-onset-evidence-packet.md
task: TODO-THESIS-STUDY-RECIRCULATION-FRACTION-ONSET-EVIDENCE-PACKET-2026-07-22
date: 2026-07-22
role: Hydraulics/cfd-pp/Writer/Reviewer/Tester
type: work_product
status: complete
---
# Recirculation/Onset Evidence Packet

Decision: `recirculation_onset_packet_started_diagnostic_proxies_available_closed_fraction_and_ri_fail_closed`.

This packet starts the thesis-facing recirculation/onset evidence chain from
existing improved upcomer composite figures, validated cell-VTK topology
preflight rows, and S13 current-coarse exchange/tau diagnostics.

Defensible now:

- common-range y-velocity visual bound rows: `3`
- reverse-flow topology proxy rows: `3`
- S13 exchange/tau current-coarse proxy rows: `3`
- same-QOI temporal UQ summary rows: `4`

Fail-closed now:

- closed recirculation fraction: no admitted closed recirculation volume
- Richardson number: no same-window, same-CV basis in this packet
- medium/fine mesh/GCI: pending scheduler exact-label sampler
- ordinary upcomer `Nu/f_D/K/F6` and exchange-cell coefficient admission

No native solver outputs, registry/admission state, blocker register, or
mesh/GCI disposition were mutated by this evidence packet.
