---
provenance:
  - operational_notes/07-26/21/2026-07-21_THESIS_CSEM_BOARD_DISPATCH.md
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
  - ../papers/UTexas_Research/3d_analysis/sections/02_dataset_and_case_selection.tex
  - ../papers/UTexas_Research/3d_analysis/sections/03_postprocessing_method_and_provenance.tex
  - ../papers/UTexas_Research/3d_analysis/sections/04_salt_family_results.tex
  - ../papers/UTexas_Research/3d_analysis/sections/05_salt2_mechanism_results.tex
  - ../papers/UTexas_Research/3d_analysis/figures/README.md
  - ../papers/UTexas_Research/3d_analysis/notes/asset_import_log.md
  - ../papers/UTexas_Research/3d_analysis/tables/table_artifact_provenance.tex
  - ../papers/UTexas_Research/3d_analysis/tables/table_salt_case_matrix.tex
  - ../papers/UTexas_Research/3d_analysis/tables/table_salt_family_quantitative_summary.tex
  - ../papers/UTexas_Research/3d_analysis/tables/table_salt2_matched_case_summary.tex
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_csem_enrichment_writing_pass/README.md
tags: [thesis-section, current-section, csem, cfd-evidence, salt-family, provenance]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
  - reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
task: TODO-THESIS-CH3-CSEM-CFD-EVIDENCE-DRAFT
date: 2026-07-21
role: Writer/Reviewer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# CFD Evidence Database

## Chapter Claim

The CFD evidence database is a provenance-controlled reference layer for
reduced-order modeling. It supports transport redistribution, model-form
selection, target definition, and diagnostic residual attribution. It does not
by itself admit every local closure coefficient, and it is not experimental
validation.

This chapter supports CL-01, CL-11, CL-19, and CL-21.

## Evidence Layers

The existing 3D Salt paper gives the mature CFD evidence layer for this thesis.
It uses two complementary views:

| Evidence layer | Source | Thesis use |
| --- | --- | --- |
| Salt-family trend layer | `../papers/UTexas_Research/3d_analysis/sections/04_salt_family_results.tex` | Shows loopwise heat-loss redistribution, grouped intended/parasitic accounting, and circumferential-mean wall transport for promoted Salt subsets. |
| Matched Salt 2 mechanism layer | `../papers/UTexas_Research/3d_analysis/sections/05_salt2_mechanism_results.tex` | Shows friction, wall-registered pressure-gradient, effective thermal transport, and safe-branch thermal resistance differences in a controlled matched family. |
| Provenance/method layer | `../papers/UTexas_Research/3d_analysis/sections/02_dataset_and_case_selection.tex` and `03_postprocessing_method_and_provenance.tex` | Defines retained windows, repaired loopwise coordinate, wall-boundary setup, and artifact hierarchy. |
| Trust boundary layer | `../papers/UTexas_Research/3d_analysis/tables/table_artifact_provenance.tex` and `table_trust_boundaries.tex` | States which assets are promoted, which are support-only, and which wordings are disallowed. |

Water remains future-work context in the current 3D paper. The thesis should
not convert the Salt-focused evidence into a Salt-versus-Water law.

## Case Selection And Retained Windows

The Salt-family paper uses nine Salt cases from the completed field-transport
campaign and narrows the main-text result layer to promoted Salt subsets. The
matched Salt 2 comparison is important because it compares validation, Jin, and
Kirst property branches on the same loop family.

The Salt 2 validation row has a specific continuation caveat: the paper uses
the corrected retained window `8598-8602 s` from the readable
continuation-era case. That retained-window provenance should stay attached
wherever the validation row appears.

Use `../papers/UTexas_Research/3d_analysis/tables/table_salt_case_matrix.tex`
for the thesis case-definition table and retained-window summary.

## Postprocessing Method

The 3D paper's promoted reductions are reproducible products, not ad hoc
plots. The workflow freezes a late-time retained window, repairs the loopwise
coordinate, reduces hydraulic and thermal fields on a shared span basis,
groups heat by thermal role, and promotes only scrutiny-cleared branch-local
thermal results.

Key reductions include:

- streamwise heat-loss comparisons;
- grouped intended-versus-parasitic heat accounting;
- circumferential-mean azimuthal wall transport;
- shear-based Darcy friction;
- wall-registered direct pressure-gradient diagnostics;
- effective `UA'` and effective thermal resistance;
- safe-branch branch-local thermal summaries.

These reductions are physically useful because they show where transport
burdens move around the loop. They are still diagnostics unless a later
closure-admission row permits coefficient fitting.

## Evidence Rights And Legal Uses

Each CFD artifact should enter the thesis with an evidence-rights label. This
keeps the chapter from overstating what a postprocessed quantity can prove.

| Artifact family | Legal thesis use | Not legal without later admission |
| --- | --- | --- |
| Retained-window CFD fields | High-fidelity reference targets and qualitative field evidence. | Experimental validation or final predictive inputs. |
| Patch and branch heat ledgers | Heat-path ownership, role grouping, residual diagnosis. | Runtime wall heat flux for a predictive model. |
| Friction and pressure-gradient reductions | Hydraulic redistribution evidence and pressure-basis diagnostics. | Admitted component `K`, F6, or global pressure multiplier. |
| TP/TW and branch temperatures | Score targets and sensor-map checks. | Runtime temperature inputs or tuning data for holdout/external rows. |
| Perturbation and external-test rows | Stress tests, holdout/external scoring when frozen, and blocker context. | Model selection or source choice. |
| Missing or blocked fields | Extraction queue and uncertainty limits. | Filled-in values from inference or convenience. |

This evidence-rights view is the bridge between the CFD database and the
admission chapter. The same row may be strong evidence for model-form selection
and weak evidence for coefficient admission.

## Wall-Boundary Setup

The readable Ethan cases are single-fluid CFD models with external hardware
represented through wall boundary conditions, not fully resolved conjugate heat
transfer models with heater solids, insulation volumes, and coolant-jacket
domains. The 3D paper states that the final `0/T` implementation is the
governing setup source when nominal metadata differ.

For thesis prose, this means:

- heater power is represented through powered wall boundary conditions;
- the cooling branch uses wall-surrogate sink behavior rather than a resolved
  coolant-side model;
- the Salt test section includes a powered wall patch;
- insulation and radiation enter through wall-boundary model structure;
- setup claims should avoid resolved-solid or resolved-coolant language.

This setup boundary is important for the `fluid+walls` model because the 1D
model should represent the same physical roles without double-counting realized
wall fluxes.

## Current CFD Results To Carry Forward

The Salt-family result is a transport-redistribution result. In promoted Salt 2
and Salt 4 subsets, the dominant intended-transfer burden sits in the
test-section span, while the dominant parasitic-loss burden sits in the left
lower leg. The exact quantitative summary belongs in
`table_salt_family_quantitative_summary.tex`.

The matched Salt 2 mechanism result shows redistributed hydraulic and thermal
behavior across validation, Jin, and Kirst:

- lower-leg and upper-leg mean shear-based Darcy friction increase across the
  validation to Jin to Kirst ordering in the cited paper section;
- upper-leg and left-upper-leg wall-registered direct pressure-gradient means
  rise across the same ordering;
- effective `UA'` decreases and effective thermal resistance increases on
  important left-side and test-section spans;
- safe-branch metrics keep the branch-local result on scrutiny-cleared
  regions.

The thesis should present these as CFD evidence for local ownership and
model-form selection. It should not present them as admitted local HTC,
friction, or component-K truth.

## Figures And Tables

Use these assets in this chapter:

| Asset | Placement | Caveat |
| --- | --- | --- |
| `fig_salt2_heat_loss.pdf` | Salt 2 heat redistribution. | Grouped channels depend on thermal-role metadata. |
| `fig_salt4_heat_loss.pdf` | Salt 4 heat redistribution. | Salt-only evidence. |
| `fig_salt2_azimuthal_means.pdf` | Circumferential-mean wall transport. | Trend-level, not local closure admission. |
| `fig_salt4_azimuthal_means.pdf` | Circumferential-mean wall transport. | Trend-level, not local closure admission. |
| `fig_salt2_friction_pressure_zoomed.pdf` | Matched Salt 2 hydraulic diagnostics. | Diagnostic pressure evidence, not admitted closure. |
| `fig_salt2_thermal_resistance.pdf` | Matched Salt 2 thermal diagnostics. | Effective, QC-masked quantities. |
| `table_artifact_provenance.tex` | Evidence hierarchy table. | Promotion surface and numeric source are distinct. |
| `table_salt_case_matrix.tex` | Case and retained-window table. | Keep `8598-8602 s` validation caveat. |
| `table_salt_family_quantitative_summary.tex` | Family quantitative summary. | Hotspots depend on role grouping. |
| `table_salt2_matched_case_summary.tex` | Matched Salt 2 quantitative summary. | Continuation caveat remains attached. |

## Chapter-Ready Wording

The CFD database provides the high-fidelity reference used throughout this
thesis. Its current strongest result is not a universal closure law; it is a
transport-redistribution result. The promoted Salt-family evidence shows that
the test-section span carries the dominant intended-transfer burden while the
left lower leg carries the dominant parasitic-loss burden. The matched Salt 2
evidence then shows that property-model choice changes loopwise friction,
wall-registered pressure-gradient diagnostics, effective thermal transport,
and thermal resistance on a shared loop family.

These results are exactly the kind of evidence needed before building a 1D
closure ledger. They show that pressure and heat residuals have structure and
location. They do not, by themselves, admit every local coefficient. In the
thesis, the CFD fields define reference targets, motivate model-form slots, and
diagnose residual ownership. Coefficients enter the predictive 1D model only
through the admission framework described in the following chapters.
