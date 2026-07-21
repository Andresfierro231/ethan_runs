---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/RUNNING.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/coarse_raw_face_metrics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/coarse_pair_diagnostics.csv
tags: [f6, coarse-vtk, raw-face, recirculation, static-pressure-blocker]
related:
  - .agent/status/2026-07-21_TODO-F6-COARSE-VTK-SAMPLER-SUBMIT.md
  - imports/2026-07-21_f6_coarse_vtk_sampler_submit.json
task: TODO-F6-COARSE-VTK-SAMPLER-SUBMIT
date: 2026-07-21
role: Scheduler / cfd-pp / Tester / Writer
type: journal
status: complete
---

# F6 Coarse VTK Sampler Submit

## Attempted

I implemented the Stage B coarse sampler package from the repaired coarse path
matrix. The builder reuses Stage A endpoint coordinates and normals, but uses
the repaired coarse reconstructed case paths and retained times. The generated
OpenFOAM sampler requests only `U`, `p_rgh`, `rho`, and `T`, because static `p`
is absent and must not be invented.

After local validation, I submitted the one scheduler-authorized job through
`login3`. The job completed quickly, so I reran the builder in harvest mode with
the recorded job ID.

## Observed

Job `3308382` completed with state `COMPLETED` and exit `0:0` after `00:01:04`
on `c318-016`. The sampler produced all 12 expected VTK surfaces for the three
coarse cases and four endpoint stations per case.

The harvested diagnostics show all 12 faces sampled. Static `p_mean_pa` is blank
by design. `p_rgh`, density, temperature, face area, signed mass flux,
reverse-area fraction, reverse-mass fraction, and secondary-velocity fraction
are populated.

All six coarse endpoint pairs remain diagnostic only. The maximum reverse-area
fractions are material, roughly `0.38-0.47` in the right leg and `0.62-0.63` in
the test-section span. Reverse-mass fractions are about `0.5`. These values
reinforce the recirculation diagnosis; they do not create ordinary-flow F6
evidence.

## Inferred

The coarse VTK-output blocker is resolved: we now have face-area and
recirculation diagnostics for all repaired coarse endpoint rows. The
static-pressure/UQ blocker is unchanged because the source fields still lack
`p`, and this task deliberately did not reconstruct `p` from `p_rgh`.

The current scientific state is therefore stronger diagnostically but unchanged
for coefficient admission: no F6 fit, component K, cluster K, or F3 comparison
should be admitted from these coarse rows.

## Contradictions Or Caveats

The in-job harvest initially wrote a summary without the submitted flag because
the run script calls the builder with `--harvest` only. I reran the builder with
`--harvest --submitted --record-job-id 3308382` after terminal completion so the
package metadata matches the scheduler evidence.

The diagnostic magnitudes should be reviewed in a separate QA row before they
are used in any synthesis table. This row's acceptance was submission plus
handoff, not final interpretation.

## Next Useful Actions

Claim a Stage B harvest-QA/admission-refresh row. It should compare these coarse
diagnostics against the existing Stage A medium/fine QA and update the F6
same-QOI gate while preserving the static-pressure blocker. If a later task
tries to recover static pressure from `p_rgh`, it must separately define and
validate the hydrostatic and reference-pressure convention.
