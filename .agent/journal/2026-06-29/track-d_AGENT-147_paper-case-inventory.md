# AGENT-147 Raw Notes

## 2026-06-29

- Claimed the first June 29 additive paper-evidence lane for a dated Salt
  paper-case inventory.
- Primary intended sources:
  - `reports/2026-06/2026-06-26/2026-06-26_ethan_progressive_story_synthesis/open_analysis_queue.md`
  - `journals/2026-06/2026-06-29_ethan_runs.md`
  - `reports/2026-06/2026-06-23/2026-06-23_ethan_cfd_freeze_checkpoint/freeze_case_windows.csv`
  - `reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_1d_validation/**`
  - `reports/2026-06/2026-06-23/2026-06-23_ethan_1d_closure_bakeoff/**`
  - per-case `work_products/*/case_inventory.csv`
  - per-case `work_products/*/cross_model_case_contract_joined.csv`
  - per-case `work_products/*/qoi_summary.csv`
- Initial working assumption:
  - freeze the current paper subset around the representative Salt Jin latest
    window family and the current readable Salt 1D shadow surfaces, while
    keeping older Salt-side mechanism assets explicit as supporting evidence
    rather than silently mixing them into one undifferentiated subset.
- Implemented `tools/analyze/build_ethan_paper_case_inventory.py` to merge:
  - per-case `work_products/*/{case_inventory,qoi_summary,cross_model_case_contract_joined}.csv`
  - June 23 checkpoint maturity from `freeze_case_windows.csv`
  - current readable 1D shadow metrics from
    `2026-06-23_ethan_frozen_state_1d_validation/case_metric_summary.csv`
  - current bundle contract from
    `2026-06-23_ethan_1d_closure_bakeoff/{surface_summary,scenario_bundle_alignment}.csv`
  - June 17/18 paper-asset gates and the June 23 presentation figure manifest
- Generated outputs:
  - `work_products/2026-06-29_ethan_paper_case_inventory/paper_case_inventory.csv`
  - `work_products/2026-06-29_ethan_paper_case_inventory/paper_case_claim_map.csv`
  - `reports/2026-06/2026-06-29/2026-06-29_ethan_paper_case_inventory/README.md`
- Current frozen classification encoded by the script:
  - `paper-grade`: Salt 1 Jin, Salt 2 Jin, Salt 3 Jin, Salt 4 Jin
  - `exploratory`: Salt 2 Kirst
  - `blocked`: Salt 1 Kirst, Salt 2 Val
  - `exclude`: Salt 3 Kirst, Salt 4 Kirst
