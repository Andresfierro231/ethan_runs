---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_fluid_empirical_bias_models_publication_report/report.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/transfer_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_predictive_model_blocker_burndown/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
tags: [thesis-draft, rom, empirical-bias, predictive-model, digital-twin]
task: TODO-THESIS-TWO-TRACK-ROM-MODEL-WRITEUP-2026-07-23
date: 2026-07-23
role: Writer / Reviewer / Forward-pred
type: thesis-insert
status: complete
---
# Two-Track Final ROM Model Statement

The final thesis model story should be written as two model tracks, because the
digital-twin objective and the physical-admission objective are related but not
identical.

The first track is a **bias-corrected CFD-ROM track**. Its purpose is to give
the best current reduced-order representation of the CFD temperature outputs
for digital-twin use. In this track, an empirical bias or discrepancy layer is
allowed, provided it is named as empirical, trained only on designated
calibration rows, frozen before testing, and reported separately from physical
closure admission. This is not a weakness if stated directly. A digital twin
often needs a calibrated ROM; the defensibility comes from split discipline and
honest labeling, not from pretending the empirical term is a first-principles
coefficient.

The second track is a **strict predictive/admission track**. Its purpose is to
identify which parts of the one-dimensional `fluid+walls` model are physically
source-backed, runtime-legal, and eligible for thesis-style predictive claims.
This track forbids scored-row CFD mass flow, realized wall heat flux, pressure
losses from the scored row, validation temperatures, and hidden residual
absorption as runtime inputs. It is therefore more conservative and currently
less complete than the bias-corrected ROM track.

## Track A: Bias-Corrected CFD-ROM / Discrepancy Model

The strongest current bias-corrected ROM evidence comes from the reduced-DOF
empirical transfer screen. Six predeclared correction families were fitted on
Salt1/Salt2 train/support sensor rows and then applied unchanged to Salt3/Salt4
legacy transfer stress rows. The baseline transfer MAE was `106.121666 K`.

The best numerical transfer family is
`F5_thermal_family_offset_shared_multiplier`:

```text
T_corrected = a * T_1D + b_family
```

It uses a shared multiplier plus thermal-family offsets. It reduced transfer
MAE from `106.121666 K` to `13.324483 K`, an `87.444145%` MAE reduction. This
is the strongest current stress-row numerical result.

The best thesis-facing empirical ROM family is probably `F2_global_affine`:

```text
T_corrected = 0.3729829182408737 * T_1D + 246.55192842685844 K
```

It uses only two degrees of freedom and reduced transfer MAE from
`106.121666 K` to `13.873169 K`, an `86.927110%` MAE reduction. It is only
`0.548686 K` worse than the four-degree-of-freedom `F5` result on the same
transfer set. For the thesis, this parsimony matters: `F2` shows that the
dominant mismatch is coherent and low-dimensional, not an arbitrary
sensor-by-sensor repair.

This track should be reported as the **best-performing CFD-ROM track**:

- It is appropriate for a digital-twin ROM claim if the empirical layer is
  described as a calibrated discrepancy model.
- It should be evaluated by frozen-coefficient transfer performance, not by
  physical-coefficient admission.
- It should not be described as a first-principles heat-transfer closure.
- It does not by itself release source/property labels or final external-test
  validation.

Suggested thesis wording:

> To support the digital-twin objective, a separate empirical discrepancy
> track was retained. In this track the reduced-order model is allowed to carry
> a named bias-correction layer, but the layer is frozen before test-case
> evaluation and is not interpreted as a physical heat-transfer coefficient.
> The low-degree-of-freedom affine correction reduced Salt3/Salt4 transfer MAE
> from approximately 106 K to approximately 14 K, showing that much of the
> current 1D/CFD temperature mismatch is coherent and correctable by a compact
> ROM calibration.

## Track B: Strict Thesis-Defensible Predictive Model

The strict predictive track remains the source/admission track. It is the right
answer to the question: "What model can be claimed as physically predictive
from setup-known inputs only?"

The current best strict model form is the steady `fluid+walls` architecture
with source/property, pressure, thermal, recirculation, uncertainty, and split
labels carried on every term. The most promising current candidate lane is
`P1D-BULK-CV-H2` / `PASSIVE-H2-CAND001`, because it moves toward a
setup-driven outer-insulation/radiation operator rather than importing realized
CFD wall heat flux. However, the current gate state is still fail-closed for
final prediction:

- freeze-ready candidates: `0`;
- final score values: `0`;
- source/property release-ready rows: `0` in the blocker-burndown summary;
- strict final scoring remains blocked by row-specific source/property release,
  same-QOI UQ, and unresolved thermal/pressure model-form gates.

This track should be reported as the **best defensible predictive/admission
track**:

- It is physically cleaner than the empirical ROM track.
- It is not yet the best numerical predictor.
- It is the path that would support a final predictive claim after freeze.
- Until freeze, it should appear as a blocked scorecard / admission ledger, not
  as a final performance table.

Suggested thesis wording:

> In parallel with the empirical ROM track, the thesis maintains a stricter
> predictive-admission track. This track permits only setup-known runtime
> inputs and source-released coefficients. Under that stricter rule set, the
> present `fluid+walls`/PASSIVE-H2 pathway is the leading physical candidate,
> but it has not yet reached a frozen final score. The result is therefore a
> defensible blocked scorecard: the model architecture and admission gates are
> established, while protected final scores remain zero until a runtime-legal
> candidate passes source/property, same-QOI uncertainty, and split audits.

## How The Two Tracks Should Be Compared

The thesis should not force one track to do both jobs. The comparison should
say:

| Question | Track A answer | Track B answer |
| --- | --- | --- |
| Best present numerical ROM of CFD temperatures? | `F2` main / `F5` upper-bound empirical bias-corrected ROM. | Not yet; final score is blocked. |
| Best physics/admission story? | Useful discrepancy model; not a physical closure. | `fluid+walls` with P1D/PASSIVE-H2 path and strict gates. |
| Digital-twin usefulness today? | High, if calibrated and frozen before test cases. | Medium/low today; high once gates release. |
| Thesis defensibility? | Defensible as empirical ROM/discrepancy correction. | Defensible as physical predictive path and blocked-scorecard discipline. |
| Main caveat? | Coefficients are empirical and not source-released. | Numerically incomplete; no final protected score yet. |

This makes the final contribution stronger, not weaker. The thesis is not
claiming that the empirical bias is physics. It is claiming that:

1. a low-dimensional empirical ROM can reproduce much of the CFD temperature
   response and is useful for a digital twin;
2. the physical model-form/admission track identifies what must be true before
   the same ROM can be called a strict predictive closure;
3. the difference between those two tracks is itself a research result, because
   it quantifies the gap between useful calibrated ROM behavior and
   source-admitted predictive physics.

## Recommended Final Model Labels

Use these labels consistently:

- **Bias-corrected ROM, main:** `F2_global_affine`.
- **Bias-corrected ROM, upper-bound:** `F5_thermal_family_offset_shared_multiplier`.
- **Best diagnostic model-form signal:** `D4_M3_segment_offsets_min2_train`,
  with transfer RMSE `7.940403 K`, but not admitted.
- **Strict predictive architecture:** steady `fluid+walls` network.
- **Strict predictive candidate lane:** `P1D-BULK-CV-H2` /
  `PASSIVE-H2-CAND001`.
- **Final physical predictive endpoint:** `M6`, currently blocked with `0`
  final score values.

## What Not To Say

Do not say the empirical bias model is an admitted physical closure. Do not say
Salt3/Salt4 transfer stress rows are a final external-test validation. Do not
say PASSIVE-H2 has final predictive scores. Do not hide the remaining heat
residual in internal Nusselt number or a global multiplier.

The clean final thesis claim is:

> The digital-twin ROM is presently strongest as a frozen empirical
> bias-corrected ROM, while the physically strict predictive model remains a
> gated `fluid+walls` admission problem. Reporting both tracks preserves
> numerical usefulness and scientific defensibility.
