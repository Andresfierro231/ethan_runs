# M3+TS, val_salt2, and Matched-Plane sbatch Submission

Task: AGENT-439
Generated: 2026-07-15

This package prepares and validates three requested overnight jobs:

1. `M3+TS` setup-only study/scorecard scaffold.
2. `val_salt2` setup-only external-test scaffold.
3. PM5 matched-plane/onset extraction after local field-contract preflight.

## Guardrail

The M3+TS and val_salt2 scorecard jobs are setup/preflight rebuilds from
existing evidence and do not use realized CFD wallHeatFlux, CFD mdot, imposed
CFD cooler duty, or validation temperatures as runtime model inputs. The
matched-plane job runs OpenFOAM postprocessing only on a compute node.

## Local Preflight Result

- M3+TS rows: `3`
- val_salt2 rows: `1`
- matched-plane preflight rows: `4`
- matched-plane preflight failures: `0`

## sbatch Scripts

- `scripts/run_m3ts_setup_only_scorecard.sbatch`
- `scripts/run_val_salt2_external_test.sbatch`
- `scripts/run_matched_plane_onset_extraction.sbatch`

Submit with dependency on the current corrected-Q harvest unless a later
coordinator changes the scheduler chain:

```bash
sbatch --dependency=afterok:3295438 <script>
```
