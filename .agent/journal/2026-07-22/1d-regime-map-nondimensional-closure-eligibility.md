---
provenance:
  - tools/analyze/build_1d_regime_map_nondimensional_closure_eligibility.py
  - work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility/formula_validity_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility/closure_eligibility_decisions.csv
task: TODO-1D-REGIME-MAP-NONDIMENSIONAL-CLOSURE-ELIGIBILITY-2026-07-22
date: 2026-07-22
role: Forward-pred / Hydraulics / Thermal-modeling / LitRev / Writer / Reviewer
type: journal
status: complete
tags: [journal, predictive-1d, regime-map, nondimensional, closure-eligibility]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility
  - .agent/status/2026-07-22_TODO-1D-REGIME-MAP-NONDIMENSIONAL-CLOSURE-ELIGIBILITY-2026-07-22.md
---
# 1D Regime Map Nondimensional Closure Eligibility

## Attempted

Claimed the nondimensional regime-map row and built a reproducible synthesis from
the LitRev model-form extraction, source inventory, CFD postprocessing contract,
gated single-stream developing branch table, throughflow/recirculation
exchange-cell design, MF07 entrance/development package, and S13 diagnostic
evidence. Added formula/provenance, case/span regime, source-overlap,
closure-decision, source-manifest, guardrail, summary, and SVG map outputs.

## Observed

The existing gated single-stream table has the required nondimensional fields
across Salt2-Salt4 and six spans, with property-mode variants. The rows already
carry the important blocker structure: recirculation invalidates ordinary
single-stream use in many spans, same-QOI UQ is missing, and source-envelope
status is precheck or blocked rather than fit-admitted.

The LitRev source inventory supports formulas and source-overlap reasoning, but
not direct transfer of coefficients. Shah/London and Muzychka/Yovanovich provide
developing-flow coordinates; Everts/Meyer/Mahdavi provide mixed-convection
screening discipline; Patino-Jaramillo and related recirculation sources support
diagnostics and model-form escalation, not TAMU thresholds.

## Inferred

The regime map is now useful as a model-form selector. It says which closures
are impossible to justify today and which physical architecture should be
studied next. It does not justify fitting. The next source of progress is new
admissible evidence: exact-label S13 mesh/GCI, source/property release, or
low-recirculation pressure anchors.

## Contradictions or Caveats

Some spans are not directly recirculation-blocked and appear as
`single_stream_precheck_only_not_admitted`. That is not a contradiction with the
fail-closed decision: precheck-only still lacks same-QOI UQ and source/property
release. The package deliberately distinguishes "possibly eligible later" from
"admitted now."

The formulas are standard regime coordinates, but the package relies on local
LitRev extraction/provenance rather than re-opening external literature. If a
future publication table needs exact source page/figure citations, claim a
separate LitRev citation-polish row.

## Next Useful Actions

1. Feed the regime map into source/property release atlas and thesis evidence
   packet rows as a fail-closed eligibility table.
2. After exact-label S13 sampler/GCI terminal evidence lands, rerun the S13
   post-sampler production harvest gate against this regime map.
3. Do not reopen ordinary `Nu`, `f_D`, component `K`, or F6 coefficient fitting
   from this package alone.
