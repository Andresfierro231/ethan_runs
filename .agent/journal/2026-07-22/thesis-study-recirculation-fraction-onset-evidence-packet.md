---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet/evidence_availability_gate.csv
  - work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures/output_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight/recirc_component_summary.csv
tags: [journal, thesis-study, recirculation, upcomer, onset, s13]
related:
  - .agent/status/2026-07-22_TODO-THESIS-STUDY-RECIRCULATION-FRACTION-ONSET-EVIDENCE-PACKET-2026-07-22.md
  - imports/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet.json
task: TODO-THESIS-STUDY-RECIRCULATION-FRACTION-ONSET-EVIDENCE-PACKET-2026-07-22
date: 2026-07-22
role: Hydraulics / cfd-pp / Writer / Reviewer / Tester
type: journal
status: complete
---
# Recirculation/Onset Evidence Packet

## Attempted

Built a refreshed thesis-facing evidence packet using only existing rendered
upcomer figures, validated cell-VTK topology preflight rows, S9 onset guard
rows, S13 limited sampled-field evidence, and same-QOI temporal UQ summaries.

## Observed

The improved common-range y-velocity figure package provides three Salt2/Salt3
/Salt4 figure rows for this packet and a common y-component range of
`-0.0770250484347` to `0.0770250484347 m/s`. This is a visual/render bound, not
an exact per-cell extrema table.

The validated cell-VTK segmentation preflight reports reverse-flow candidate
fractions of the right-leg ROI of about `0.158` to `0.162` for Salt2/Salt3/Salt4.
It also reports `blocked_fragmented_velocity_topology` for all three cases; the
largest component is only about `0.527` to `0.530` of the reverse candidates.

S13 current-coarse exchange/tau proxy rows are available for Salt2/Salt3/Salt4.
The same-QOI temporal UQ summary is available for the four S13 QOIs, but the
medium/fine exact-label rows are still pending.

## Inferred

The strongest current claim is a diagnostic onset/recirculation evidence claim:
the figures, topology proxies, and exchange/tau proxies justify disabling
ordinary one-stream upcomer closure claims in this region. They do not yet
justify a closed recirculation fraction, Ri claim, exchange-cell coefficient,
or same-label mesh/GCI statement.

## Caveats

The reverse-flow candidate fraction is not a closed control-volume
recirculation fraction. The maximum downward velocity reported here is a
common-render visual bound. S13 exchange/tau values are current-coarse
diagnostics; they remain blocked from production/admission until exact-label
medium/fine rows and a later mesh/GCI disposition exist.

## Next Useful Actions

1. Monitor Slurm job `3310179` for exact-label medium/fine S13 rows.
2. If it succeeds, inspect the sampler `summary.json`, `sampling_error_log.csv`,
   and `medium_fine_exact_label_qoi_rows.csv`.
3. Only then open a separate post-sampler row to evaluate terminal-window
   equivalence and mesh/GCI disposition.
