---
provenance:
  - AGENTS.md
  - imports/2026-07-22_1d_train_only_setup_uq_smoke_terminal_harvest_and_validator.json
  - reference/geometry_reference.md
  - registry/case_registry.csv
tags: [repo-user-guide, provenance, data-policy]
related:
  - docs/repo_user_guide/repo_organization.md
  - docs/repo_user_guide/glossary.md
task: TODO-REPO-USER-GUIDE-README-TOOLING
date: 2026-07-22
role: Writer/Implementer/Tester
type: report
status: complete
---
# Data and Provenance

Scientific claims in this repo should be recoverable from files. A good package
answers: what source data were read, what files changed, what commands ran, what
was not changed, and which rows remain diagnostic or blocked.

## Native Solver Outputs

Native CFD/OpenFOAM outputs are read-only by default. Do not edit files in
imported source directories. If postprocessing must run, the board row must say
whether it is reading native outputs, writing task-scoped generated files, or
working on a staged copy.

Never cite `linked_cases/` as provenance. Cite the real source path recorded in
the manifest, package README, or registry row.

## Import Manifests

Every significant task writes a dated JSON manifest under `imports/`.

Expected fields include:

- `task` or `task_id`;
- `date`;
- `summary`;
- `changed_files`;
- `read_only_context`;
- mutation flags such as `native_solver_outputs_mutated`,
  `registry_mutated`, `scheduler_action`, `external_fluid_edit`;
- score/admission flags when relevant, such as `source_property_release`,
  `qwall_release`, `coefficient_admission`, `candidate_freeze`, and
  `final_score_claim`.

Inspect a representative manifest:

```bash
python3.11 -m json.tool imports/2026-07-22_1d_train_only_setup_uq_smoke_terminal_harvest_and_validator.json | sed -n '1,160p'
```

## Registry

`registry/case_registry.csv` is shared state. It connects `source_id` values to
case paths and workflow metadata. Update it only under an assigned intake or
registry row.

Read-only discovery:

```bash
head -20 registry/case_registry.csv
```

## Work Products

`work_products/` is the normal home for generated evidence packages. A good
package usually contains:

- `README.md`;
- machine-readable CSV/JSON tables;
- scripts or command provenance;
- validation output;
- explicit guardrails.

Find recent packages:

```bash
find work_products/2026-07/2026-07-22 -maxdepth 2 -name README.md
```

## Reports and Thesis Dossier

`reports/` stores durable reports and thesis-facing packets. Do not edit thesis
body, LaTeX, or current chapter files unless the board row explicitly claims
those paths. Evidence packets can be read to support documentation and planning.

## Geometry and Naming Truth

Use `reference/geometry_reference.md` before making spatial claims. Important
current conventions:

- `lower_leg` is the heater span;
- `right_leg` is the downcomer;
- `upper_leg` is the cooler;
- `left_lower_leg`, `test_section_span`, and `left_upper_leg` compose the
  upcomer/test-section side;
- probe CSV schematic names are swapped relative to mesh/span names.

## Runtime-Input Discipline

Predictive models may not use protected CFD outputs as runtime inputs unless a
later explicit release row changes policy. Forbidden predictive runtime inputs
include CFD `mdot`, realized `wallHeatFlux`, imposed CFD cooler duty,
validation/holdout/external-test temperatures, realized test-section heat, and
hidden global multipliers.
