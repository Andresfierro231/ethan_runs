---
provenance:
  task: AGENT-334/AGENT-340
  generated_by: tools/analyze/build_salt_cfd_training_evidence_inventory.py
tags: [cfd-pp, salt-cfd, admission, training-split, corrected-q, upcomer-onset]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/forward-predictive-model.md
---
# Salt CFD Training Evidence Inventory

## Observed Facts

- Salt-only candidate rows inventoried: `25`; water rows are excluded from this package.
- Current usable split remains Salt2 training, Salt3 validation, Salt4 holdout.
- Corrected Salt-Q rows admitted now: `0`.
- Live corrected-Q job `3293924` scheduler state at build time: `RUNNING` (`state inferred from prior live gate if sacct is unavailable`).
- Live selected continuation rows are `salt2_lo10q`, `salt2_hi10q`, `salt4_lo10q`, and `salt4_hi10q`; all remain pending terminal harvest.
- Salt2 mesh-family evidence exists, but current mesh/GCI gates admit `0` publication-ready closure-QOI rows and `0` fit-admissible thermal rows.
- Upcomer recirculation evidence currently available for admitted nominal diagnostics spans Re_upcomer `71.125` to `134.883`; all available rows remain recirculating.

## Inferred Interpretation

Slurm completion and solver advancement are runtime facts, not admission. A salt row can enter model training/validation/holdout only after terminal operating-point and steady-state evidence exists and the split policy allows that use. Corrected-Q perturbations are useful sensitivity candidates, but they are not independent training rows under the current split discipline.

`rcExternalTemperature` wall patches include emissivity/Tsur radiation, and `wallHeatFlux` already folds radiation into the total wall heat balance. Do not add a separate radiation residual when consuming CFD wallHeatFlux.

## Math And Assumptions

- Re_upcomer is consumed from the upstream onset package as the section Reynolds number, interpreted under the standard form `Re = rho U D / mu` for the upcomer section/window already defined there.
- Recirculation evidence is not inferred from runtime completion. It requires extracted flow metrics such as backflow fraction, reverse-flow area/mass fraction, Ri_median, and recirculation intensity on a matched retained window.
- The current non-recirculating/ordinary-pipe anchor criterion is the one stated in `next_evidence_requirements.csv`: backflow_fraction <= 0.02 and Ri_median < 0.30, or a bounded transition pair straddling backflow_fraction 0.02-0.10.
- Perturbed-Q rows may move thermal/buoyancy state, but their Re_upcomer/backflow/Ri are blank here until terminal postprocessing extracts them from the actual fields.

## Usable Now

- `salt2_jin_nominal_continuation`: training candidate.
- `salt3_jin_nominal_continuation`: validation candidate.
- `salt4_jin_nominal_continuation`: holdout candidate.

No corrected-Q row can expand training now.

## Running

- Job `3293924` (`saltq_sel_cont`) is tracked through `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.out`, `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/slurm-saltq_sel_cont-3293924.err`, and live solver logs listed in `corrected_q_perturbation_status.csv`.
- Rows in that job: `salt2_lo10q`, `salt2_hi10q`, `salt4_lo10q`, `salt4_hi10q`.

## Could Still Be Continued

- Partial/deferred corrected-Q rows outside job `3293924` can be continued only if they are re-gated after a sufficient perturbed operating-point window.
- Failed Salt3 high-Q rows need cause documentation before rebuild/rerun.
- Salt1 rows need an explicit Salt1 admission/split policy before any training use.

## Need Postprocessing Or Admission Review

- Live corrected-Q selected rows need terminal harvest, postprocessing, steady-state/admission gate, and BC role reduction.
- Salt2 mesh family needs closure-QOI GCI/sign/heat-balance gates before fit or publication use.
- Corrected-Q rows need a dated split policy before any admitted perturbation is used as training rather than sensitivity/correlation support.

## Can Existing CFD Bracket Upcomer Recirculation Onset?

Not yet. Existing mined Salt2/Salt3/Salt4 diagnostics are useful recirculating references, but the highest available admitted diagnostic is `salt4_jin_nominal_continuation` at Re_upcomer `134.883`, and it still has observed recirculation. There is no ordinary-pipe/non-recirculating anchor and no admitted transition pair straddling the backflow threshold.

The nearest existing candidates are Salt4 corrected-Q rows, especially `salt4_hi10q` from live job `3293924` and stopped `salt4_hi5q`, but they are availability candidates only until terminal harvest, postprocessing, and admission evidence exist. If those rows do not naturally land near/above Re_upcomer 150 with bounded recirculation metrics, the next step is new targeted Salt CFD at Re_upcomer 150, 200, and 250.

See `upcomer_onset_candidate_cases.csv` for availability, Re_upcomer, recirculation evidence, onset role, and next action per case.

## Recommended Next Actions

See `run_actions_needed.csv` for grouped blockers and concrete unlocks. The highest-value cfd-pp action remains terminal harvest of job `3293924` after it exits.
