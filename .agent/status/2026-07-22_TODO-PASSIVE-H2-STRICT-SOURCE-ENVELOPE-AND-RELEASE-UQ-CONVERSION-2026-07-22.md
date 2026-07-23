# TODO-PASSIVE-H2-STRICT-SOURCE-ENVELOPE-AND-RELEASE-UQ-CONVERSION-2026-07-22 Status

Date: `2026-07-22`
Role: Implementer / Tester / Writer / Reviewer
Owner: claude

## Scope
Convert diagnostic-complete PASSIVE-H2 R4 (junction-excluded, four-family)
evidence into (A) a strict, wallHeatFlux/postProcessing-free source-envelope and
(B) a release-grade same-QOI UQ readiness determination, without releasing,
freezing, or scoring anything. Also: board hygiene (Codex out of credits) and
blocker-attack plans for the pressure-corner and F6 friction frontier.

## Completed
- Board hygiene: archived 17 codex-`COMPLETE` rows out of the live Active and
  Planned tables via `tools/agent/board_archive.py --archive-task ... --apply`;
  removed 5 stale already-archived duplicate Planned rows. Live Active table now
  holds only the 5 genuinely trigger-gated rows; `board_archive --check` = OK.
- Built `tools/analyze/build_passive_h2_strict_source_envelope_and_release_uq_conversion.py`
  (reads committed inputs; emits 8 artifacts) and its test
  (`test_..._conversion.py`, 8 tests, all pass).
- Result: **strict source-envelope = 8/16 PASS** (Salt1+Salt2 train x 4 retained
  R4 families) — the first non-zero strict count. Salt3/Salt4 correctly
  fail-closed on `c3` (protected, per-row props unverified). Junction recorded as
  a known bounded R4 omission (`hA ~= 0.418 W/K`, Salt2).
- Same-QOI release UQ = **fail-closed** (0 ready labels). `source_gate` now
  passes for train, isolating the sole freeze blocker to a same-QOI 3-mesh GCI
  triplet (medium/fine CFD at the Salt2 physical window; S13 found 0 such rows).
- Kept `source_property_release=False`, `candidate_freeze=False`,
  `final_score=0`; all 15 no-mutation guardrails `False`.
- Wrote package README, import manifest, operational_notes handoff (with the
  pressure-corner and F6 blocker plans).

## Current State
Strict source-envelope conversion is complete and tested. The PASSIVE-H2 R4
freeze blocker set has collapsed from three items to one concrete data need.
Nothing was released, frozen, or scored. Codex is out of credits, so no
independent reviewer is currently available to admit a release.

## Follow-up
1. Highest-value: request/schedule a coarse/medium/fine reconstruction of the
   Salt2 nominal physical window with identical QOI extraction, run through
   `tools/analyze/compute_gci.py`, to build the same-QOI GCI triplet. This is the
   sole remaining PASSIVE-H2 R4 freeze blocker.
2. Only after (1): S11/S15 review of the 8 strict train rows for a freeze
   decision (do not self-admit without an independent reviewer).
3. Optional: recover setup-only junction wall-layer metadata to lift R4 to a
   five-family candidate; and independently verify Salt3/Salt4 per-row operator
   props if they are ever needed beyond protected scoring.
4. Pressure-corner + F6 frontier plans are staged in the operational_notes
   handoff for a future session.
