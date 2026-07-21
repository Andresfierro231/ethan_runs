# TODO-THESIS-PREDICTIVE-STUDIES-ROADMAP-2026-07-21

## Objective

Create a thesis-facing roadmap of studies to perform and document while
approaching the final predictive model that outputs `mdot` and temperatures
from setup inputs with pressure and thermal residual attribution.

## Outcome

Built `reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md`.
The section defines a staged study sequence: baseline current model, external
BC dictionary, heat-loss network, pressure source-envelope, recirculation guard,
source/property and split release, and frozen final scorecard. It explicitly
separates train/calibration, development validation/support, holdout/testing,
and external-test claims.

## Changes Made

- Added the current thesis section:
  `reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md`.
- Added index entries in:
  `reports/thesis_dossier/Chapters_and_sections/current/README.md`,
  `reports/thesis_dossier/Chapters_and_sections/README.md`, and
  `reports/thesis_dossier/README.md`.
- Claimed and updated the active board row for
  `TODO-THESIS-PREDICTIVE-STUDIES-ROADMAP-2026-07-21`.
- Added journal and import manifest closeout artifacts.
- Regenerated generated documentation indexes after validation.

## Validation

Passed:

- `python3.11 -c "...roadmap existence/content check..."` -> `roadmap_content_ok`.
- `python3 tools/docs/build_repo_index.py` -> indexed `2029` docs, `30` board rows, and `15` blockers.
- `python3 tools/docs/build_repo_index.py --check` -> blocker register OK with `15` entries.
- `python3 tools/docs/build_repo_index.py` after board completion -> indexed `2030` docs, `30` board rows, and `15` blockers.
- `python3.11 tools/agent/finish_task.py --task-id TODO-THESIS-PREDICTIVE-STUDIES-ROADMAP-2026-07-21` -> `finish_task: OK`.

## Unresolved Blockers

- The roadmap preserves the current final-predictive-model blocker state:
  `FINAL_FREEZE_TBD` is absent, no final candidate is admitted, and no final
  predictive accuracy claim is made.
- Active scientific blockers remain delegated to their owning packages and
  `.agent/BLOCKERS.md`.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: none.
- Solver/postprocessing launched: no.
- External Fluid source edited: no.
- External thesis/paper workspace edited: no.
- Fitting, tuning, model selection, or closure admission changed: no.
- Blocker register changed: no.
