---
provenance:
  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/fluid_walls_readiness_ledger.csv
  - work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/thermal_source_sink_ledger.csv
  - work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/pressure_readiness_ledger.csv
  - work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/pm5_recirc_readiness_ledger.csv
tags: [thesis-section, current-section, fluid-walls, segment-atlas, model-implementation, admission-ledger]
related:
  - TODO-THESIS-ENRICHMENT-RESEARCH-AVENUES
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
task: AGENT-516
date: 2026-07-17
role: Writer/Reviewer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# Fluid+Walls Segment Atlas

## Purpose

This atlas is the one-page implementation bridge between the thesis model form
and the row-level readiness ledgers. Each loop region is described by geometry,
material stack, pressure model, thermal circuit, source/sink role,
boundary-layer state, recirculation flag, uncertainty/admission status, and
next action.

The atlas should be used in two places:

- in the methodology chapter, to define the reduced-order control volumes;
- in the forward-model chapter, to show what is admitted, diagnostic, or blocked
  before final scoring.

## Loop-Wide Contract

| Field | Current atlas entry |
| --- | --- |
| Geometry basis | Branch/segment map from the `fluid+walls` model-form note and readiness ledger. |
| State variables | Loop mass flow, segment bulk temperatures, optional wall/interface temperatures, pressure loss terms, and sensor projections. |
| Pressure residual | Segment-local distributed, reset/development, local feature, branch/junction, recirculation, and residual lanes. |
| Thermal residual | Heater, cooler/HX, passive wall, test-section, junction/stub, radiation/external, and residual lanes. |
| Split guardrail | Salt1-4 nominal rows are final training; Salt2 +/-5Q is holdout/testing; `val_salt2` is external-test-only. |
| Runtime guardrail | Predictive rows cannot use scored-row CFD `mdot`, realized `wallHeatFlux`, imposed CFD cooler duty, or validation TP/TW temperatures as runtime inputs. |
| Current admission summary | Geometry mostly admitted; material stack partial except bare-quartz test section; pressure diagnostic in current holdout/external readiness package; thermal roles present as targets, not runtime inputs. |

## Region Atlas

| Loop region | Geometry | Material stack | Pressure model | Thermal circuit | Source/sink role | Boundary-layer state | Recirculation flag | Uncertainty/admission status | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Heater / lower leg | Mapped as `lower_leg` / `heated_incline` in the readiness ledger. | Steel/insulated lower-leg role known; final runtime wall-stack contract still partial. | Diagnostic only; blocked by recirculation mask, pressure-definition conflicts, component isolation, geometry normalization, and mesh/GCI. | Partial wall/material circuit; realized section heat is a scoring target. | Heater/source lower leg; `val_salt2` target heat is about `244.631 W`; Salt2 +/-5Q examples are about `230.674 W` in the readiness ledger. | Development/reset state planned but not fitted. | Pressure recirculation flags present in readiness evidence. | Geometry admitted; pressure coefficient not admitted; thermal source role diagnostic/target-only. | Coordinate with heater source redistribution screens; admit only setup-facing source placement. |
| Lower upcomer inlet | Mapped as `left_lower_leg` / `left_lower_vertical`. | Upcomer wall stack partially known, not finalized in this atlas. | Diagnostic only; ordinary pipe fit rejected when recirculation flags are active. | Partial circuit; PM5 fields exist for Salt2 +/-5Q but are not fit-admitted. | Lower upcomer before test section; heat target is a loss lane in readiness rows. | Hybrid recirculation/onset lane, not ordinary single-stream entry flow. | Salt2 +/-5Q PM5 rows show material reverse-flow/reverse-area flags; `val_salt2` lacks matching PM5 plane metrics in the consumed source set. | Holdout/external evidence only; no pressure/HTC coefficient fitting. | Use as hybrid upcomer diagnostics; queue `val_salt2` PM5 extraction only if final external scoring needs it. |
| Bare-quartz test section | Mapped as `test_section_span` / `test_section`. | Bare quartz is explicitly admitted as the material identity. | Diagnostic only; single-stream `f_D`/`K` rejected under recirculation and isolation blockers. | Test-section source/loss circuit must include electrical deposition and quartz-to-ambient loss. | Physical middle-upcomer span; it is not removable cleanup heat loss. | Hybrid/upcomer lane; internal HTC/Nu remains gated. | PM5 Salt2 +/-5Q diagnostics exist; `val_salt2` has pressure recirculation flags but no matching PM5 plane metrics in this package. | Geometry/material role admitted; pressure and internal Nu diagnostic. | Keep test-section as explicit source/loss region in M3/M4/M5; do not hide it in passive hA. |
| Upper upcomer outlet | Mapped as `left_upper_leg` / `left_upper_vertical`. | Upcomer wall stack partial. | Diagnostic; ordinary pipe coefficients blocked by recirculation and missing/partial mesh evidence. | Partial wall circuit; source/sink role is an upcomer heat-loss target. | Upper upcomer after test section. | Hybrid recirculation/onset lane. | Salt2 +/-5Q outlet PM5 diagnostics show strong reverse-flow indicators; `val_salt2` has pressure recirculation flags only in current source set. | No ordinary upcomer `Nu`, `f_D`, or `K` admission. | Treat as throughflow plus exchange/mixing candidate region. |
| Cooler/HX upper branch | Mapped as `upper_leg` / `cooled_incline_composite`. | Cooler/HX role known; segment-local wall/HX material stack still partial. | Diagnostic in readiness rows. | Cooler/HX removal is a primary thermal sink; setup-facing cooler model evidence is more mature than passive wall loss. | Cooling branch sink; `val_salt2` target heat is about `-136.351 W` in readiness evidence. | Development/reset state planned but not fitted. | Pressure recirculation flags present in readiness rows. | Boundary evidence partially admitted; segment pressure coefficient not admitted. | Preserve admitted cooler setup-facing model separately from realized CFD cooler duty. |
| Downcomer / right leg | Mapped as `right_leg` / `right_vertical`. | Downcomer wall stack partial. | Diagnostic; pressure rows blocked by recirculation mask, geometry normalization, component isolation, and mesh/GCI. | Passive wall-loss circuit partial; realized heat is target-only. | Right-leg downcomer/passive wall loss. | Development/reset state planned. | Pressure recirculation flags present. | Thermal downcomer policy and pressure coefficient admission remain limited. | Decide downcomer thermal policy before fitting thermal closure rows. |
| Junction/stub/connector group | Mapped as `junctions` / `junction_stub_connector_group` in the readiness ledger. | Local geometry/material ownership incomplete. | Missing or diagnostic for local pressure in the readiness package; corner K diagnostic elsewhere. | Partial local heat-loss circuit; `val_salt2` junction/stub split is about `40.926087 W` across four buckets. | Junction, stub, step, connector heat-loss and residual ownership lane. | Reset/local development state not parameterized. | Recirculation evidence missing or indirect in current atlas source. | Strong thesis evidence for local heat ownership; not a fitted runtime coefficient. | Build setup-facing junction/stub thermal circuit only after geometry/material ownership is finalized. |
| Corners/bends/local pressure features | Distributed across branch transitions rather than a single ordinary segment. | Local fitting/connector material detail incomplete. | Diagnostic; current straight-loss subtraction can produce negative local K. | Not a primary heat circuit unless paired with junction/stub surfaces. | Local pressure residual ownership lane. | Reset/development feature by definition. | Recirculation and plane-placement flags can invalidate component isolation. | `0` fit-admitted corner-K rows in current evidence. | Improve pressure basis/straight-reference subtraction before admitting component K. |
| Sensor projection layer | TP/TW labels projected onto 1D path. | Sensor material is not a segment material stack. | No pressure model. | Sensors are outputs/targets, not thermal boundary inputs. | Validation target only. | Not a boundary-layer model. | Not applicable, though sensor location may sit near recirculating regions. | TP/TW coordinates provisional; TP2/TW10 require special policy handling. | Keep sensors out of runtime input contracts; report projection caveats with score tables. |

## Admission Legend

| Label | Meaning in this atlas |
| --- | --- |
| Admitted | The row/field can be used for the stated thesis purpose under split and runtime guardrails. |
| Partial | The physical role is established, but material stack, setup-facing circuit, or admission evidence is incomplete. |
| Diagnostic | The evidence can motivate model form, attribution, or future extraction, but cannot fit predictive coefficients. |
| Missing | No local artifact was consumed by the atlas; do not infer from neighboring regions. |
| Blocked | A known blocker prevents admission until resolved. |

## Implementation Notes

The atlas supports M3/M4/M5 implementation:

- M3 uses the segment rows without explicit junction pressure/heat ownership.
- M4 adds junction/stub/connector and corner ownership lanes.
- M5 adds a hybrid upcomer representation, with throughflow and exchange or
  recirculation-cell roles.

The atlas should not be used to bypass split policy. Salt2 +/-5Q and
`val_salt2` rows in the readiness ledger are score/diagnostic evidence only.
Their realized heat and pressure rows are not training inputs.
