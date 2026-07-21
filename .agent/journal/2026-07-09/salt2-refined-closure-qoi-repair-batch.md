# Salt2 Refined Closure-QOI Repair Batch

Task: `AGENT-245`

## Context

AGENT-239 staged and ran Salt2 medium/fine extraction quickly, but review of the
outputs showed the run was not closure-QOI ready:

- `section_mean_pressure_*.json` had 30/30 station rows with `status=no_output`;
- `segment_friction.csv` had only a header;
- thermal rows were `no_cutplane_output` except the intentionally blocked
  downcomer row;
- the previous shared `foampostprocess_*.log` was overwritten by later thermal
  extraction, so the repair batch must gate each step explicitly instead of
  assuming file presence means successful extraction.

## Work Done

Built a new repair package:

`work_products/2026-07/2026-07-09/2026-07-09_salt2_refined_closure_qoi_repair_batch/`

The generated runner:

- stages fresh local mirrors under the package;
- copies `constant/`, `system/`, `0/`, and `case_config.yaml`;
- symlinks only processor directories from the source case;
- leaves source case trees read-only;
- clears staged `postProcessing` before section sampling;
- runs section sampling before adding a wallHeatFlux symlink for thermal parsing;
- hard-fails on missing section samples, empty friction/momentum rows, or thermal
  rows with no cut-plane data.

## Submitted Job

Submitted from `login3`:

```bash
sbatch work_products/2026-07/2026-07-09/2026-07-09_salt2_refined_closure_qoi_repair_batch/scripts/sbatch_repair_extraction_9pm.sh
```

Scheduler accepted:

```text
3287580|PENDING|2026-07-09T21:00:00|2026-07-09T17:46:57|0:00|1|(BeginTime)|agent245_salt2_qoi
```

## July 10 Result

Job `3287580` started at `2026-07-09T21:00:03`, ran on `c318-018`, and failed
after `00:03:05` with exit code `1:0`.

The repaired hard gates worked: they stopped the workflow before empty
friction/GCI products could be produced. The failure was in medium section
sampling:

- `reconstructPar` completed under OpenFOAM 13.
- `foamPostProcess` ran under OpenFOAM 13.
- `foamPostProcess` failed while reading reconstructed `recon/medium/518/T` with
  `wrong token type - expected Scalar ... punctuation token '-'`.
- Inspecting the reconstructed `T` around the fatal line showed garbage
  floating-point values and `-nan`; inspecting the decomposed source
  `processors64/518/T` at the same line range showed normal temperatures near
  `455-458 K`.

This means the medium/fine closure-QOI extraction is still not ready. Pressure
sampling may be salvageable by rerunning section sampling without
`--dump-temperature`, using only `U p_rgh rho`. Thermal bulk-temperature/HTC/UA
sampling remains blocked until the `T` reconstruction/read path is repaired or
replaced.

## Next

Do not use AGENT-239 or AGENT-245 section/friction outputs as closure evidence.
The next task should split pressure and thermal recovery:

1. pressure-only section sampling without `T`;
2. friction/momentum reductions from pressure-only outputs;
3. separate diagnosis of corrupted reconstructed `T` before thermal closure
   extraction.
