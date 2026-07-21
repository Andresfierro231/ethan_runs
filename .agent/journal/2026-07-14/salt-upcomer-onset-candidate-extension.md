---
provenance:
  task: AGENT-340
  generated_by: codex
tags: [journal, cfd-pp, salt-cfd, upcomer-onset, corrected-q]
related:
  - .agent/status/2026-07-14_AGENT-340.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/blocked_missing_metrics.csv
---
# Salt Upcomer Onset Candidate Extension

## Why This Work Happened

The coordinator needed a concrete answer to three questions: why Salt1 is still diagnostic-only, why corrected-Q perturbations have not been harvested, and whether existing Salt CFD can bracket upcomer recirculation onset around Re_upcomer 150, 200, and 250.

## Evidence Read

- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/blocked_missing_metrics.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/upcomer_recirculation_onset_conditions.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/next_evidence_requirements.csv`
- `registry/case_registry.csv`
- `registry/_all_postprocessing_runs.csv`
- `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/**`

## Math And Assumptions

Re_upcomer is treated as the section Reynolds number from the upstream onset evidence package, using the standard `Re = rho U D / mu` definition already implied by that package's section/window contract. This extension does not recompute Re from native CFD fields.

Recirculation evidence is admitted only when extracted metrics exist: backflow fraction, reverse-flow area/mass fraction where available, Ri_median, and recirculation intensity. Runtime completion alone is not recirculation evidence.

The ordinary-pipe/non-recirculating anchor criterion is imported from `next_evidence_requirements.csv`: backflow_fraction <= 0.02 and Ri_median < 0.30, or a transition pair straddling backflow_fraction 0.02-0.10. The current Salt2-4 rows have backflow fractions 0.277778, 0.21875, and 0.171875, so all remain recirculating.

Perturbed-Q rows are not assigned estimated Re_upcomer. Their Re/backflow/Ri fields stay blank until terminal field extraction exists.

## Results

- Salt1 remains diagnostic-only because the existing terminal evidence is context-only pending a Salt1 admission/split policy, and no matched onset metrics are available for it.
- Job 3293924 is still running by direct `squeue -j 3293924` check: state `R`, elapsed `19:37:53`, node `c318-016`.
- Existing CFD cannot bracket onset today. The highest mined admitted diagnostic is Salt4 nominal at Re_upcomer 134.883, and it is still recirculating.
- Salt4 high-Q corrected rows are the closest existing transition candidates, but `salt4_hi10q` is running in job 3293924 and `salt4_hi5q` is stopped/under-advanced. Neither can be admitted without terminal harvest/postprocessing/gate evidence.
- New targeted Re_upcomer 150, 200, and 250 rows were added as explicit would-require-new-run candidates. Re 250 is the ordinary-pipe anchor target.

## Artifacts

- `work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/upcomer_onset_candidate_cases.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/run_actions_needed.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/README.md`
- `imports/2026-07-14_salt_upcomer_onset_candidate_extension.json`

## Next Action

Do not launch an immediate harvest while job 3293924 is still running. After terminal scheduler state, harvest stdout/stderr and solver logs, run corrected-Q postprocessing and steady/admission gates, then extract matched onset metrics. If Salt4 high-Q does not provide a transition/non-recirculating anchor, create a separate targeted-CFD board row for Re_upcomer 150, 200, and 250.

