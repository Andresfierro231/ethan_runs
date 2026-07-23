---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_strict_source_envelope_and_release_uq_conversion/summary.json
tags: [PASSIVE-H2, strict-source-envelope, same-qoi-uq, blocker-plan, pressure-corner, f6, start-here, coordinator]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_strict_source_envelope_and_release_uq_conversion/README.md
  - .agent/BLOCKERS.md
  - operational_notes/maps/forward-predictive-model.md
task: TODO-PASSIVE-H2-STRICT-SOURCE-ENVELOPE-AND-RELEASE-UQ-CONVERSION-2026-07-22
date: 2026-07-22
role: Coordinator / Writer
owner: claude
type: operational_note
status: current
---

# Start-here: PASSIVE-H2 strict conversion + pressure-corner / F6 blocker plans (2026-07-22)

## Why this exists
Codex ran out of credits; every "active" board row was already codex-`COMPLETE`
and just left on the live board. This session (a) cleaned the board, (b) converted
the diagnostic PASSIVE-H2 R4 evidence into a strict source-envelope + a
fail-closed release-UQ determination, and (c) staged concrete attack plans for
the two remaining scientific frontiers (pressure-corner, F6). The frontier is
physics gates, not coordination or Codex availability.

## Board state after this session
- Live Active table = 5 genuinely trigger-gated rows (S15, S11, three CSEM
  narrative refreshes) + this task. Planned/Unclaimed = empty. 17 complete rows
  archived to `.agent/BOARD_ARCHIVE.md`; `board_archive --check` = OK.
- The trigger-gated rows CANNOT advance until an upstream candidate is released;
  do not "claim" them as work — drive the blockers instead.

## Open these first
1. `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_strict_source_envelope_and_release_uq_conversion/README.md`
2. `.agent/STATE.md` (authoritative: active tasks + open blockers) and `.agent/BLOCKERS.md`
3. This session's tool: `tools/analyze/build_passive_h2_strict_source_envelope_and_release_uq_conversion.py`

## PASSIVE-H2 result and the single remaining freeze blocker
Strict source-envelope now PASSES for 8 train rows (Salt1+Salt2 x 4 retained R4
families) using wallHeatFlux-free mesh/setup-backed provenance. The freeze
blocker set collapsed to ONE item: a same-QOI **3-mesh GCI triplet**
(coarse/medium/fine) of the **Salt2 nominal physical window** with identical QOI
extraction (`mdot`, `qambient`, `passive_h2_outer_total`), fed through
`tools/analyze/compute_gci.py`. S13 confirmed 0 exact native medium/fine targets
exist, so this needs a scheduled reconstruction (likely an NCC medium/fine mesh
from Ethan). Until it lands, release/freeze stay closed. Do NOT self-admit a
freeze; with Codex gone there is no independent S11/S15 reviewer.

---

## Pressure-corner blocker plan (`corner_lower_right`, 3 of 6 open blockers)
The densest knot. Three linked blockers, all the same root cause: the
`corner_lower_right` endpoints materially recirculate, which forbids ordinary
component-K, which forbids the same-QOI UQ.

Trusted precedent packages (read first):
- `work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/endpoint_recirculation_metrics.csv`
  (RAF ~= 0.76, RMF ~= 0.50, SVF ~= 0.80 for salt_2/3/4 — far above the
  `RAF/RMF < 0.01` ordinary-K threshold)
- `work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_isolation_decision/component_isolation_audit.csv`
  (`fail_no_admissible_straight_reference_for_ordinary_K`)
- `work_products/2026-07/2026-07-18/2026-07-18_two_tap_same_qoi_uq_status/same_qoi_uncertainty_audit.csv`
  (`missing_no_GCI_diagnostic_only`)

The single acceptance signal that clears ALL THREE: **a non-recirculating anchor
endpoint pair (RAF/RMF < 0.01) with same-label multi-mesh + multi-time windows
enabling a real GCI.** Recommended sequence:
1. Sweep candidate tap pairs / sections to find an endpoint pair whose reverse-
   area and reverse-mass fractions are below 0.01 (a genuinely non-recirculating
   anchor). If none exists on current geometry, formally record that ordinary
   component-K is not admissible and keep the **section-effective** diagnostic
   treatment (this is a legitimate scientific outcome, not a failure).
2. For an admissible anchor, repeat the exact endpoint contract across a
   coarse/medium/fine mesh family + neighboring time windows; compute GCI with
   `tools/analyze/compute_gci.py`. Guardrail: do not borrow unrelated GCI, do not
   fabricate monotonicity, no clipping, no hidden multiplier, no F6 fit.
3. Only if 1-2 pass: admit the same-QOI UQ and let
   `TODO-THESIS-CSEM-PRESSURE-ADMISSION-REFRESH` write the narrative.

## F6 friction blocker plan (self-contained, second target)
Blocker: `f6-friction-re-correction` — buoyancy/Re friction correction is not yet
a validated closure (memory: `friction-ri-fit-failure` — phi=1+c*Ri failed;
try phi vs Re). Trusted anchor plan:
`work_products/2026-07/2026-07-18/2026-07-18_f6_legwise_pressure_anchor_plan/README.md`.
Recommended sequence:
1. Build leg-wise pressure anchors on the isothermal upcomer (the only leg with
   trustworthy f ~ 2-2.7; see memory `friction-buoyancy-source-finding`) — avoid
   single-leg p_rgh gradients on heated/cooled legs (they give unphysical
   negative f).
2. Fit phi(Re) (not phi(Ri)) with an explicit DOF count and same-QOI UQ before
   claiming a closure; keep it diagnostic until GCI + source-gate pass.
3. Feed a validated phi(Re) to the pressure narrative refresh.

## Output contract (unchanged repo convention)
Every follow-up ends with: work_product package (README + summary.json), status
file, dated journal, import manifest, and tests for any new tool. Fail-closed by
default; keep release/freeze/score at False until gates pass.

## Do-not-do
No solver/sampler launch from an analysis row, no native/registry/scheduler/
Fluid/thesis mutation, no source/property release, no candidate freeze, no
protected/final scoring, no fitting/model selection, no hidden multiplier, no
runtime wallHeatFlux use, no S11/S15/S6 trigger firing, no commit/push without an
explicit request.
