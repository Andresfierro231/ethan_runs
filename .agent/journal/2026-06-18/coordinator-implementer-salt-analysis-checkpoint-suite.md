# AGENT-081 Raw Journal — Salt Analysis Checkpoint Suite

## 2026-06-18

- Re-read the repo startup instructions, board, file-ownership map, role map,
  and `tools/` local override before opening a new task.
- Opened `AGENT-081` as a new additive coordination/reporting task because the
  user asked for a plan that turns the remaining Salt analysis into documented
  phases with checkpoints, explanations, and handoff-friendly artifacts.
- Kept the implementation strictly additive:
  - no edits to the active shared June 15/17 extraction stack
  - no edits to the June 18 Salt closure/correlation package builder
  - one new builder plus one new report package rooted on top of those inputs
- Decided the deliverable should be a single checkpoint suite rather than five
  separate builders, so the user can navigate one package while still getting
  a durable subdirectory per phase.
- Chose the package shape:
  - `tools/analyze/build_ethan_salt_analysis_checkpoint_suite.py`
  - `reports/2026-06-18_ethan_salt_analysis_checkpoint_suite/`
  - `phase1_hydraulic_hardening`
  - `phase2_heatloss_enthalpy_closure`
  - `phase3_branch_trust_gate`
  - `phase4_boundary_layer_context`
  - `phase5_fit_ready_handoff`
- Grounded the suite in existing additive artifacts instead of new extraction:
  - June 18 Salt closure/correlation package
  - June 17 pressure / HTC / boundary-layer package
- Confirmed the reusable input schemas before coding:
  - straight-section closure tables
  - feature `K_eff` tables
  - heat-loss partition tables
  - leg enthalpy tables
  - branch trust tables
  - boundary-layer summary/profile tables
  - bulk-vs-centerline correction tables
  - fit-exclusion log
- Implemented the new builder to:
  - read only the additive Salt-family artifacts needed for the checkpoint
    story
  - optionally filter to a bounded source-ID subset for smoke validation
  - materialize one documented subpackage per phase
  - emit machine-readable CSV checkpoint tables and summary JSON files
  - emit PNG/SVG/PDF figures per phase
  - write phase-level READMEs and a root README that explains the sequence,
    intended interpretation, and remaining analysis gap after each checkpoint
- Phase implementation choices:
  - phase 1 emphasizes hydraulic screening status, straight-section fit
    candidates, feature `K_eff` status, and buoyancy-aided spans
  - phase 2 emphasizes heat partition fractions, leg enthalpy residuals, and
    case-level closure ranking
  - phase 3 turns branch usability into a durable promotion gate with reason
    summaries and candidate subsets
  - phase 4 separates all-case boundary-layer context from the preserved
    representative Salt profile context and adds bulk-vs-centerline
    temperature correction tables
  - phase 5 assembles the current fit-ready subset and an exclusion audit so
    later regression work can only consume rows already screened upstream
- Ran static validation:
  - `python -m py_compile tools/analyze/build_ethan_salt_analysis_checkpoint_suite.py`
- Ran a bounded 2-case smoke build:
  - `val_salt_test_2_coarse_mesh_laminar`
  - `viscosity_screening_salt_test_4_jin_coarse_mesh`
- Smoke build completed and produced all five phase subpackages, figures, and
  phase summaries without schema or plotting failures.
- Promoted the same builder to the durable 9-case Salt suite.
- Final durable suite summary counts:
  - phase 1: `54` hydraulic rows, `12` candidate straight-section rows,
    `45` feature rows, `19` candidate feature rows, `18` buoyancy-aided
    straight sections
  - phase 2: `54` leg rows, `1` candidate leg row, `1` screening leg row,
    `52` blocked leg rows, worst residual fraction
    `7.787809779468553`
  - phase 3: `63` branch rows, `36` candidate rows, `14` screening rows,
    `13` blocked rows; candidate branch names are `left_lower_leg`,
    `left_upper_leg`, `test_section_span`, and `upcomer`
  - phase 4: `54` boundary summary rows, `7015` representative profile rows,
    `1073` Salt bulk-vs-centerline rows
  - phase 5: `12` fit-ready hydraulic rows, `19` fit-ready feature rows,
    `36` fit-ready thermal rows, `148` exclusion-audit rows
- Final durable package size:
  - `5.1M`
- Important observed outcomes preserved for the next real implementation step:
  - phase 1 confirms that the hydraulic story is still limited by inherited
    feature-path closure and by buoyancy-aided/net-gain straight sections
  - phase 2 confirms that enthalpy closure is still the dominant unresolved
    thermal blocker; the suite now documents that failure mode cleanly rather
    than burying it inside later fitting
  - phase 3 makes the current Salt thermal promotion gate explicit, which
    keeps `right_leg` out of later regression work by default
  - phase 4 provides a usable dissertation-context checkpoint for boundary
    thickness and bulk-vs-centerline interpretation without overstating the
    current representative-profile coverage
  - phase 5 makes the currently admissible hydraulic, feature, and thermal
    subsets durable and auditable
- Important limitations preserved explicitly:
  - no new upstream hydro-integral extractor was created here
  - no resolved heat-loss decomposition was created here
  - no new all-case boundary-layer field reconstruction was created here
