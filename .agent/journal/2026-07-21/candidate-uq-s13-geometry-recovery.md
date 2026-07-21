---
provenance:
  - .agent/status/2026-07-21_TODO-CANDIDATE-UQ-S13-GEOMETRY-RECOVERY-2026-07-21.md
  - work_products/2026-07/2026-07-21/2026-07-21_candidate_uq_s13_geometry_recovery/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_candidate_uq_s13_geometry_recovery/qoi_prerequisite_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_candidate_uq_s13_geometry_recovery/s13_sampler_manifest_requirements.csv
tags: [journal, same-qoi-uq, s12, s13, s14, upcomer, pressure]
related:
  - imports/2026-07-21_candidate_uq_s13_geometry_recovery.json
  - work_products/2026-07/2026-07-21/2026-07-21_candidate_uq_s13_geometry_recovery/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/README.md
task: TODO-CANDIDATE-UQ-S13-GEOMETRY-RECOVERY-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: journal
status: complete
---
# Candidate UQ and S13 Geometry Recovery

I claimed a narrow row because the requested S13 geometry contract itself had
already been completed and failed closed. The useful next step was therefore a
cross-candidate repair package: identify what evidence is still missing for
S12-HIAX1, S13 exchange/onset, and S14 pressure/F6 leading anchors, while
preserving no-admission guardrails.

Observed facts: S13 has validated whole-mesh `cell_vtk` and cell-volume CSVs
for Salt2, Salt3, and Salt4, but the S13 geometry contract released zero
exchange-interface rows, zero wall/core rows, and zero `Q_wall_W` rows. The
S13 sampler manifest preflight reports `0/3` sampler-ready rows. Same-QOI
Phase C has zero accepted UQ rows. S14 identifies right-leg and
test-section-span as future ordinary F6 lanes, plus low-recirculation terminal
anchors, but keeps current rows diagnostic/future because ordinary-flow,
terminal/source, and same-QOI UQ gates do not pass.

Inference: same-QOI UQ repair cannot be admitted by better wording alone. The
leading candidates first need finite QOI rows on the same basis. For S12-HIAX1
that means S13 exchange-state QOIs; for S13 it means trusted geometry/source
inputs before harvest; for S14 it means terminal/source endpoint fields with
RAF/RMF ordinary-flow checks before F3-vs-F6 review.

Contradiction resolved: the user's immediate technical task named "claim/execute
the S13 geometry contract row", but repo evidence shows that row is already
complete and fail-closed. This package treats that result as source evidence
and emits the follow-on geometry recovery classification instead of rerunning
the completed contract.

Caveat: I did not inspect scheduler terminal state for new high-heat or
corrected-Q completion beyond the cited read-only S14/S13 packages, because
this task row forbids scheduler action and its acceptance is the repair ledger,
not terminal harvest.

Next useful actions:

1. Complete S13 exchange-interface and recirculation-mask definition.
2. Define S13 wall/core band and `Q_wall_W` on top of that released mask.
3. Rerun S13 sampler manifest preflight; require `3/3` sampler-ready rows.
4. Harvest S13 exchange QOIs and same-QOI UQ, then reassess S12-HIAX1.
5. Refresh S14 terminal/source readiness only after watched cases land, then
   run endpoint/UQ repair before any F6 comparison.
