---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
tags: [thesis-section, current-section, sam, interpretation, closure-ledger, reduced-order-model]
related:
  - TODO-THESIS-ENRICHMENT-RESEARCH-AVENUES
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
task: AGENT-516
date: 2026-07-17
role: Writer/Reviewer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# SAM-Facing Interpretation

## Claim Boundary

This thesis can inform SAM-facing model construction, but it does not validate
SAM. The current evidence is a CFD-to-1D closure and admission workflow for the
TAMU molten-salt natural-circulation loop. A SAM validation claim would require
an actual SAM model, frozen SAM inputs, score tables, and preferably independent
experimental comparison. Those are outside the current evidence base.

The paper-safe claim is:

> The closure ledger developed here is transferable to SAM-facing reduced-order
> modeling because it identifies which hydraulic losses, thermal paths,
> recirculation flags, and coefficient admissions should be preserved when a
> CFD-informed loop is represented by 1D components.

## What Transfers To SAM-Facing Work

| Thesis artifact | SAM-facing interpretation | What not to claim |
| --- | --- | --- |
| Branchwise pressure ledger | Use branch/component-specific loss ownership rather than one global hydraulic multiplier. | Do not claim a SAM minor-loss coefficient is validated unless it is fitted and scored in a SAM model. |
| Junction/stub heat ledger | Preserve junction, connector, and stub heat-loss ownership as explicit local roles where geometry supports it. | Do not feed realized CFD junction heat directly as a predictive runtime input. |
| Corner pressure diagnostics | Treat corner/bend losses as visible structured features that need better extraction before coefficient admission. | Do not admit current negative local K diagnostics as physical component K values. |
| `fluid+walls` thermal circuit | Carry internal convection, wall conduction, insulation/contact, external convection, radiation, heater transfer, cooler removal, and residual lanes separately. | Do not collapse all thermal mismatch into a single heat-loss multiplier. |
| Upcomer recirculation flags | Mark states where a single throughflow pipe closure may be invalid and an exchange/mixing or regime flag is needed. | Do not apply ordinary pipe `Nu`, `f_D`, or `K` labels to recirculating rows. |
| Admission/uncertainty status | Attach fit-safe, diagnostic, blocked, support, holdout, and external labels to every coefficient or comparison. | Do not use holdout/external evidence for tuning because the score looks favorable. |
| Model-form ladder M0-M6 | Compare how much each added physical role buys before committing to a final systems-code representation. | Do not present diagnostic replay forms as predictive models. |

## Branchwise Pressure Losses

The hydraulic lesson is not simply that the 1D model needs "more K." The thesis
evidence shows that pressure residuals depend on where losses are assigned:
straight segments, reset/development regions, bends, junctions, branch clusters,
and recirculating upcomer spans do not have the same evidentiary status.

For SAM-facing work, this suggests a pressure-input workflow:

1. Build the component network with physical branch labels.
2. Assign literature or setup-known losses where geometry supports them.
3. Keep CFD-derived apparent losses in diagnostic lanes until component
   isolation, pressure basis, straight-reference subtraction, recirculation, and
   mesh/GCI gates pass.
4. Score branchwise pressure and mdot residuals after coefficients are frozen.

This is a discipline for constructing a SAM model, not a claim that the current
corner-K diagnostics are SAM-ready.

## Heat Ledgers And Wall Ownership

The thermal lesson is that total heat loss is not enough. The final 1D model and
any SAM-facing model should keep at least these roles distinct:

- heater electrical/setup source;
- cooler/HX heat removal;
- ordinary passive pipe wall loss;
- bare-quartz test-section source/loss balance;
- junction/stub/connector heat loss;
- external convection and radiation;
- residual or blocked lane.

The `val_salt2` junction/stub evidence is useful here: about `40.926087 W` of
junction/stub heat loss appears across four buckets. That magnitude is large
enough to motivate local ownership in a SAM-facing model, but it remains
external-test evidence and not a training input.

## Recirculation Flags

The upcomer evidence warns against applying ordinary 1D pipe closures wherever
the CFD field contains material reverse flow or strong recirculation. In a
SAM-facing model, those rows should carry a regime or validity flag. Possible
representations include:

- a throughflow path with an exchange/mixing lane;
- a recirculation penalty or onset flag;
- a component split that isolates the test-section span from the ordinary
  upcomer legs;
- exclusion of recirculating rows from ordinary `Nu`, `f_D`, and `K` fitting.

The exact SAM implementation is future work. The thesis contribution is the
evidence trail that says a single ordinary-pipe closure would be unsafe.

## Admission Status As A Systems-Code Input

SAM-facing inputs should inherit admission metadata:

| Metadata | Why it matters |
| --- | --- |
| Split role | Prevents tuning on holdout/external rows. |
| Runtime legality | Separates setup-facing coefficients from realized CFD replay. |
| Mesh/GCI status | Prevents diagnostic mesh-sensitive coefficients from becoming final inputs. |
| Recirculation flag | Prevents ordinary single-stream closures from being used outside their flow state. |
| Sensor caveat | Prevents overinterpretation of TP/TW comparisons. |
| Blocker | Makes open physics visible instead of hiding it in a multiplier. |

This metadata is as important as the coefficient value. A coefficient without
its admission status is not thesis-safe and should not become a SAM-facing input
without review.

## Suggested Thesis Text

The reduced-order workflow developed here is directly relevant to SAM-facing
model construction, but it should be interpreted as closure discipline rather
than SAM validation. The branchwise pressure ledger identifies where losses are
ordinary distributed terms, reset/development features, local fitting or corner
features, junction/connector effects, or recirculation-dominated residuals. The
thermal ledger separates heater input, cooler removal, passive wall loss,
bare-quartz test-section balance, radiation/external-boundary effects, and
junction/stub losses. These distinctions are exactly the distinctions that must
be preserved when a CFD-informed loop is reduced to systems-code components.

The same workflow also defines what not to transfer. Current corner-K evidence
is diagnostic because straight-loss subtraction can produce negative local K and
zero rows are fit-admitted. Upcomer internal coefficients are not ordinary pipe
coefficients where recirculation is material. Realized CFD wall heat fluxes and
sensor temperatures are scoring targets, not predictive runtime inputs. Thus,
the SAM-facing outcome of this thesis is a vetted ledger of roles, caveats, and
candidate inputs, not a validated SAM model.
