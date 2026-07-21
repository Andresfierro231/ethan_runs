# AGENT-148 Raw Notes

## 2026-06-29

- Claimed the reduction-contract audit immediately after the paper-case
  inventory freeze landed.
- Primary intended sources:
  - `work_products/2026-06-29_ethan_paper_case_inventory/paper_case_inventory.csv`
  - `work_products/2026-06-29_ethan_paper_case_inventory/paper_case_claim_map.csv`
  - `tmp/2026-06-23_ethan_latest_window_case_analysis_refresh/salt1_jin/**`
  - existing June 23 validation and bakeoff branch-policy / bundle-alignment
    tables
  - per-case `work_products/*/{case_inventory,qoi_summary,cross_model_case_contract_joined}.csv`
- Initial working assumption:
  - keep this package additive and provenance-first: reuse existing reduction
    outputs, write down the current station and branch contract explicitly, and
    avoid reopening shared June 10-26 package builders.
- Implemented `tools/analyze/build_ethan_reduction_contract_audit.py` and
  `tools/analyze/test_ethan_reduction_contract_audit.py`.
- Generated the first additive audit package:
  - `reports/2026-06/2026-06-29/2026-06-29_ethan_reduction_contract_audit/README.md`
  - `reports/2026-06/2026-06-29/2026-06-29_ethan_reduction_contract_audit/summary.json`
  - `work_products/2026-06-29_ethan_reduction_contract_audit/{station_map,branch_map,source_contract_map,reduction_choice_audit,paper_reduced_branch_summary,paper_reduced_major_loss_summary,paper_reduced_streamwise_heat_loss_summary}.csv`
- Main observed output from the generated package:
  - station contract matched across all `4` paper-grade Salt Jin cases
  - branch geometry contract matched across all `4` paper-grade Salt Jin cases
  - reduction-choice audit published `79` explicit choice rows
  - reduced bundle published `28` branch rows, `24` major-loss rows, and
    `904` streamwise heat-loss rows plus headers
- Important boundary preserved explicitly in the report/package:
  - `Salt 1 Jin` currently points at the latest readable June 23 refresh root
    while `AGENT-121` is still rebuilding that path
  - `Salt 2-4 Jin` still use the older June 15 reduced package roots, so the
    audit is intentionally mixed-provenance rather than falsely “all latest”
- Validation run:
  - `python3.11 -m unittest tools.analyze.test_ethan_reduction_contract_audit`
  - `python3.11 -m unittest tools.analyze.test_ethan_reduction_contract_audit tools.analyze.test_ethan_paper_case_inventory tools.analyze.test_ethan_latest_window_frozen_state_stack`
  - `python3.11 tools/analyze/build_ethan_reduction_contract_audit.py`
