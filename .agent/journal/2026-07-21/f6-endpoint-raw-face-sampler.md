---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_face_uq_execution/launch_preflight.csv
  - work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_face_uq_execution/endpoint_face_sampling_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/summary.json
tags: [pressure-ledger, f6, endpoint-sampler, raw-face, no-admission]
related:
  - .agent/status/2026-07-21_TODO-F6-ENDPOINT-RAW-FACE-SAMPLER.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/README.md
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-F6-ENDPOINT-RAW-FACE-SAMPLER
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer
type: journal
status: complete
---

# F6 Endpoint Raw Face Sampler

## Attempted

I converted the F6 endpoint face/UQ execution package from a preflight-only
state into a scheduler-ready raw-face sampler handoff. The implementation reads
the existing endpoint-face matrix and launch preflight, separates passable Salt2
medium/fine rows from blocked coarse rows, writes OpenFOAM controlDicts for the
two passable cases, and emits a staged-copy runner plus sbatch wrapper.

The runner stages source cases into this workspace, links processor directories,
disables existing functions in the staged copy, reconstructs `U`, `p`, `p_rgh`,
`rho`, and `T`, samples endpoint planes, and then reruns the builder in harvest
mode. It is intentionally a future compute-node action, not something this row
launched.

## Observed

Salt2 medium and fine source paths are usable for Stage A because their retained
times exist and contain required fields. That yields eight endpoint-face rows:
two mesh levels, two branches, and upstream/downstream faces for each selected
endpoint pair. The rows are in `raw_f6_endpoint_face_metrics.csv` with
`sample_status=pending_sampler_launch`.

The coarse rows are still not launch-ready. Salt2/Salt3/Salt4 coarse paths in
the inherited preflight resolve to missing retained-time evidence and missing
required field confirmation, so twelve endpoint-face rows are preserved in
`blocked_coarse_endpoint_face_matrix.csv`.

## What Worked

The useful unblock is the separation of the problem into a small Stage A job and
a clear coarse-path repair queue. This avoids waiting on every mesh family
before testing the raw-face extraction mechanics. The generated package also
keeps the pressure-basis and admission ledgers clean: it records raw metric
placeholders and ordinary-flow gates without inventing sampled values.

The test suite catches the main scientific guardrails: no sampled rows before
launch, no F6/component-K admission, no clipped K or hidden multiplier, and the
expected Stage A/coarse row counts.

## What Did Not Work

This task did not recover raw RAF/RMF or pressure metrics, because the board row
did not authorize scheduler launch or solver/postprocessing execution. That is a
deliberate stop, not a failed harvest.

The coarse mesh family did not become ready. The inherited source paths still
need a separate repair/provenance step before those rows can participate in
same-QOI mesh uncertainty.

## Inferred

The immediate blocker has changed shape. The F6 sampler is no longer missing as
a specification or script; it is missing executed raw output. The efficient next
step is a scheduler-authorized Stage A launch, followed by harvest and parser
validation against the eight expected VTK surfaces.

Any later F6 statement must still wait for finite raw face metrics, ordinary-flow
RAF/RMF gates, same-QOI time and mesh uncertainty, and an admission-review row
that compares explicitly against the frozen F3 baseline without a global
multiplier.

## Contradictions Or Caveats

The package is marked complete because the row's acceptance was an unblock and
handoff. It should not be cited as sampled evidence. The strongest current claim
is: eight Salt2 medium/fine endpoint-face rows are ready for staged-copy
sampling; zero raw sampled rows and zero F6/component-K admissions exist.

## Next Useful Actions

Claim a scheduler-authorized Stage A sampler row. Submit
`scripts/submit_stage_a_f6_endpoint_sampler.sbatch` from the package, monitor
for the expected eight VTK surfaces, rerun the builder with
`--harvest --record-job-id <jobid>`, and then open a narrow parser/UQ review row.
