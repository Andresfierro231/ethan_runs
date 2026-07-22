---
task: TODO-LITREV-MODEL-FORM-EXTRACTION-2026-07-21
date: 2026-07-21
role: Coordinator / Writer / Reviewer
type: work_product
status: complete
provenance:
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/README.md
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/chapters/06_minor_losses_quartz_transition.tex
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/chapters/14_final_integration_cfd_postprocessing.tex
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/appendices/N_cfd_postprocessing_equations.tex
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/appendices/S_equation_threshold_admission_registry.tex
  - ../papers/UTexas_Research/LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL/appendices/V_final_model_form_candidates.tex
tags: [litrev-synthesis, model-forms, pressure-corner, cfd-postprocessing, one-d-model]
related:
  - operational_notes/maps/literature-synthesis-and-gates.md
  - operational_notes/maps/pressure-and-momentum-budget.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
---
# LitRev Model-Form Extraction

## Why this package exists
The new LitRev is now a source-audited model-construction document, not just a citation list. This package extracts the parts that matter for the Ethan 1D modeling mission and CFD postprocessing, especially the open question of pressure increasing around corners.

The controlling interpretation is conservative: static pressure recovery or source-defined negative coefficients can occur around area changes, bends, tees, and junction paths, but they are not automatic evidence for a negative component loss. The next agents must preserve pressure basis, velocity basis, hydrostatic and kinetic corrections, straight-loss subtraction, recovery-plane status, recirculation diagnostics, and source-use category before admitting any coefficient.

## Files to open first
- `model_form_candidates.csv` -- assignable reduced-model forms and their gates.
- `pressure_corner_extraction_findings.csv` -- pressure/corner rules and non-admission implications.
- `cfd_postprocessing_contract.csv` -- minimum CFD reductions and diagnostics required by the LitRev.
- `litrev_source_inventory.csv` -- source provenance by author/title/path.
- `next_agent_task_matrix.csv` -- concrete next rows for the modeling wave.

## Trusted LitRev source paths
- `chapters/06_minor_losses_quartz_transition.tex`: fitting, tee, junction, pressure recovery, negative source-defined K, and minor-loss schema.
- `chapters/14_final_integration_cfd_postprocessing.tex`: final CFD-to-1D protocol, pressure/heat reduction equations, calibration hierarchy, and switching calibration.
- `appendices/N_cfd_postprocessing_equations.tex`: compact CFD pressure, heat-transfer, and recirculation equations.
- `appendices/S_equation_threshold_admission_registry.tex`: candidate equations, diagnostic definitions, and no-silent-threshold rule.
- `appendices/V_final_model_form_candidates.tex`: six candidate model forms and switching logic.
- `data/schemas/*.csv`: machine-readable pressure, minor-loss, development, mixed-convection, and heat-loss ledger columns.

## Output contract
This package is an extraction and coordination artifact only. It does not:
- change native CFD/OpenFOAM outputs;
- mutate registry/admission state;
- launch solver or postprocessing jobs;
- edit external Fluid code;
- fit F6, component K, or thermal closures;
- admit any new pressure, heat-transfer, or recirculation model.

## Key implications for the next modeling wave
- Fully developed `64/Re` and fully developed `Nu` remain reference limits unless a branch-specific development check supports active use.
- Corner and junction pressure rises must be decomposed into static pressure change, hydrostatic head, kinetic pressure change, straight/developing loss, pressure recovery, and residual.
- Component `K` requires isolation and recovery; otherwise use `section_K`, `cluster_K`, or residual assignment.
- Negative coefficients are allowed only when the source definition supports them and the energy ledger stays consistent.
- Recirculation diagnostics distinguish local reverse area/mass from negative net branch flow; no universal switching threshold is admitted.
- Throughflow-plus-recirculation/exchange-cell modeling is the preferred escalation for persistent local exchange where one bulk state fails.

## Do-not-do guardrails
- Do not hide pressure residuals inside a global friction multiplier.
- Do not hide external heat loss inside internal `Nu`.
- Do not use planar tee coefficients as circular-pipe universal K values.
- Do not use source thresholds for `F_A`, `F_m`, `Ri`, `Gz`, or recovery without TAMU envelope and calibration.
- Do not classify current F6/two-tap/corner rows as fit-admitted from this literature extraction alone.
