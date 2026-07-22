---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_s13_mesh_gci_upcomer_exchange_evidence_packet/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/outputs
tags: [journal, s13, mesh-gci, upcomer-exchange, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-THESIS-S13-MESH-GCI-UPCOMER-EXCHANGE-EVIDENCE-PACKET-2026-07-22.md
  - imports/2026-07-22_thesis_s13_mesh_gci_upcomer_exchange_evidence_packet.json
task: TODO-THESIS-S13-MESH-GCI-UPCOMER-EXCHANGE-EVIDENCE-PACKET-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Uncertainty / Writer / Reviewer / Tester
type: journal
status: complete
---
# S13 Mesh/GCI Upcomer-Exchange Evidence Packet

## Attempted

I checked Slurm accounting for split rerun `3311146`. All six Salt2/Salt3/Salt4
medium/fine elements completed with exit code `0:0`, so I claimed the
downstream thesis evidence packet.

The first preflight exposed a board-shape problem: the row lived in a priority
table, so the parser treated the owner column as scope and found no writable
paths. I normalized that row to the parser's expected role/owner/scope/goal
shape. A second preflight exposed a real conflict with an open S11 row that
owns broad `tools/analyze/`, so I removed the optional shared checker path and
kept all executable generation inside the task-owned work product package.

## Observed

The completed split outputs contain `72` exact-label QOI rows: three Salt
cases, two mesh levels, three terminal neighbor windows, and four QOI labels.
Each of the six case-mesh outputs reports `12` exact-label QOI rows and `0`
sampling errors. The source preflight rows are compute-ready, but all six have
`strict_contract_windows_available=false`; the terminal candidate windows do
not match the strict coarse contract windows.

Medium/fine terminal comparisons show that `Q_wall_W` is relatively stable:
`0.0247%` for Salt2, `0.503%` for Salt3, and `0.344%` for Salt4 relative to
fine. The exchange mass proxy, recirculation residence-time proxy, and
wall/core contrast are much more mesh-sensitive, with relative medium/fine
differences of roughly `19.7%` to `95.5%` depending on QOI and case.

The same-QOI temporal uncertainty package remains useful context, but the
medium/fine deltas exceed the temporal uncertainty for every case/QOI row in
this packet. That comparison is diagnostic only; it is not a GCI estimate.

## Inferred

The face-area-vector repair unblocked exact-label medium/fine evidence, but it
did not unblock production admission. S13 can now support a thesis statement
that the exchange-cell observables are measurable and mesh sensitive on the
repaired masks. It cannot support a released exchange coefficient, source
property release, candidate-specific review, freeze, or validation score until
the same-label coarse member/time-equivalence gap is resolved or a documented
two-level non-GCI uncertainty policy is explicitly admitted by a later row.

Ordinary upcomer `Nu/f_D/K` remains disabled for this evidence path because the
rows quantify recirculating exchange-cell behavior, not an ordinary single
throughflow pipe segment.

## Caveats

The packet uses terminal candidate windows from medium/fine native outputs and
does not substitute probes, endpoint fields, postProcessing profiles, or
source-side heat-flow rows for direct QOI labels. It deliberately keeps
`Q_wall_W` and source/property release closed even where the medium/fine Qwall
relative deltas are small.

## Next Useful Actions

The next useful unlock is a same-time same-label coarse/medium/fine bridge or a
formal two-level uncertainty policy for S13. Without that, S13 should remain
diagnostic thesis evidence. In parallel, the source/property release unblock
study and thermal residual-owner figure packet can proceed because they do not
require new S13 scheduler work.
