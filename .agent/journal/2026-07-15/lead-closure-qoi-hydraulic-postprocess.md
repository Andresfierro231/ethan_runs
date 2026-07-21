---
provenance:
  task: AGENT-409
  generated_by: codex
tags: [journal, hydraulics, cfd-pp, mesh-gci]
related:
  - .agent/status/2026-07-15_AGENT-409.md
  - work_products/2026-07/2026-07-15/2026-07-15_lead_closure_qoi_hydraulic_postprocess/README.md
---
# Lead Closure-QOI Hydraulic Postprocess Journal

2026-07-15T08:41:19-05:00 - Used the existing AGENT-409 board claim and kept AGENT-406 PM5 scope read-only.

2026-07-15T08:48:33-05:00 - Built the first AGENT-409 package: closure-QOI failed-gate matrix, raw two-tap diagnostic table, internal-Nu reopen status, hydraulic refresh, and scratch-only runner.

2026-07-15T08:54:41-05:00 - Launched `scripts/run_staged_raw_two_tap.sh all` on node `c318-008`. The runner staged minimal case copies under `tmp/2026-07-15_lead_closure_qoi_hydraulic_postprocess/raw_two_tap`, symlinked read-only native `processors64`, reconstructed `U p p_rgh rho`, and ran `foamPostProcess` with two cutting planes.

2026-07-15T09:01:36-05:00 - The staged OpenFOAM chain completed for Salt2/Salt3/Salt4. Six raw plane files landed under `postProcessing/agent409RawTwoTapSurfaces`: lower `left_lower_leg__s00` and upper `left_upper_leg__s04` for all three cases.

2026-07-15T09:02:40-05:00 - Rebuilt AGENT-409 artifacts to prefer the staged OpenFOAM outputs. Final raw two-tap rows are `diagnostic_agent409_staged_copy_openfoam_parsed_not_fit_admitted`, not fit-admitted. Closure-QOI mesh/GCI remains open with 6 missing-triplet, 16 non-monotone/oscillatory, and 3 sign/semantics rows. Internal Nu remains 0 fit-admissible rows. Final forward-v1 remains blocked.

Validation passed:

- `python3.11 tools/analyze/build_lead_closure_qoi_hydraulic_postprocess.py`
- `work_products/2026-07/2026-07-15/2026-07-15_lead_closure_qoi_hydraulic_postprocess/scripts/run_staged_raw_two_tap.sh all`
- `python3.11 -m unittest tools.analyze.test_lead_closure_qoi_hydraulic_postprocess`
- `python3.11 -m py_compile tools/analyze/build_lead_closure_qoi_hydraulic_postprocess.py tools/analyze/test_lead_closure_qoi_hydraulic_postprocess.py`
- `git diff --check -- tools/analyze/build_lead_closure_qoi_hydraulic_postprocess.py tools/analyze/test_lead_closure_qoi_hydraulic_postprocess.py work_products/2026-07/2026-07-15/2026-07-15_lead_closure_qoi_hydraulic_postprocess`

No native CFD solver output, registry/admission state, scheduler state, external Fluid code, or completed upstream package was mutated.
