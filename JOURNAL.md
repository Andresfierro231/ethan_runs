# JOURNAL

Curated consolidated journal for `ethan_runs/`.

## 2026-06-09

- Established a repo-level agent coordination system in `.agent/` so agents can
  start from the repo root or a subdirectory and still share board state, file
  ownership, journal rules, and cleanup safety rules.
- Preserved the existing detailed research record in `journals/` and
  `operational_notes/`; no historical scientific content was rewritten in this
  setup pass.

## 2026-06-09 Curated Research Summary

### Established results

- `Salt 2` remains the strongest validation-style salt anchor, but it should be
  described as usable with caveats rather than fully converged. The June 4
  practical-steadiness audit judged it usable based on flat late-window
  behavior and low final heat-balance residual even though the coded
  convergence flag stayed false. Sources:
  `journals/2026-06/2026-06-04_ethan_runs.md`,
  `reports/2026-06-04_ethan_essential_steadiness_audit/README.md`.
- The current best-supported mechanism story is coupled wall-loss plus
  hydraulic-resistance mismatch, not a wall-loss-only explanation. That theme
  is consistent across the June 4 section-transport package, the June 5
  wall-loss/resistance report, and the June 8 sponsor deck scaffold. Sources:
  `journals/2026-06/2026-06-04_ethan_runs.md`,
  `journals/2026-06/2026-06-05_ethan_runs.md`,
  `reports/2026-06-08_sponsor_salt_status_deck/README.md`.
- The reconstruction-first ParaView path is now the operationally trusted local
  figure route. By June 7 it was validated for at least the Salt 1 Kirst and
  validation Salt 2 smoke cases with typed `png/svg/pdf` outputs and aggregate
  status tracking. Sources:
  `journals/2026-06/2026-06-05_ethan_runs.md`,
  `journals/2026-06/2026-06-07_ethan_runs.md`,
  `figures/last_timestep_temperature_slice_status.json`.

### Partial results and unresolved investigations

- `Salt 4 Jin` was scientifically worth continuing and the runtime-bootstrap
  failure was narrowed substantially between June 4 and June 5, but by June 8
  the live-running status was stale and the current state had become `TIMEOUT`.
  That means the repaired environment path is useful evidence, but Salt 4 Jin
  still should not be written up as a completed sensitivity result. Sources:
  `reports/2026-06-05_ethan_continuation_diagnosis/README.md`,
  `journals/2026-06/2026-06-08_ethan_presentation_package_and_parameterization.md`,
  `journals/2026-06/2026-06-08_ethan_runs.md`.
- `Salt 1` no longer looks blocked by the broad MPI/bootstrap problem, yet it
  is still not a clean steady-state result. Salt 1 Jin accumulated successful
  repaired retries, while Salt 1 Kirst still carried a follow-on staged-restart
  defect caused by a missing root-level `T`. Sources:
  `reports/2026-06-05_ethan_continuation_diagnosis/README.md`,
  `journals/2026-06/2026-06-07_ethan_runs.md`,
  `reports/2026-06-08_sponsor_salt_status_deck/README.md`.
- The transient axial package became strong enough for scientific use, but the
  full-field path is still incomplete because reconstructed `T` remains
  unreadable for some staged rows. The usable fallback is q-profile and
  wall-heat-history reporting rather than forcing all rows through the same
  latest-time scalar-field extraction. Sources:
  `journals/2026-06/2026-06-04_ethan_runs.md`,
  `journals/2026-06/2026-06-05_ethan_runs.md`,
  `reports/2026-06-04_ethan_transient_axial_package/README.md`.

### Open questions and recommended next steps

- Decide whether another `Salt 2` extension is worth the allocation now that
  the latest continuation outcome is `TIMEOUT` rather than environment failure.
  Sources: `reports/2026-06-05_ethan_continuation_diagnosis/README.md`,
  `journals/2026-06/2026-06-07_ethan_runs.md`.
- Repair the `Salt 1 Kirst` staged restart tree before any new retry, because
  the remaining blocker is a restart-field layout defect rather than runtime
  bootstrap. Sources:
  `reports/2026-06-05_ethan_continuation_diagnosis/README.md`,
  `reports/2026-06-08_sponsor_salt_status_deck/README.md`.
- Build true transient `Delta p_rgh(t)` extraction if the next paper or sponsor
  deck pass needs pressure evolution instead of latest-time branch ranking.
  Sources:
  `journals/2026-06/2026-06-07_ethan_runs.md`,
  `journals/2026-06/2026-06-08_ethan_presentation_package_and_parameterization.md`.
