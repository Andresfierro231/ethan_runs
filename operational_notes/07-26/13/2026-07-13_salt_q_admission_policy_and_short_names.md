# Salt-Q Admission Policy And Short Names

Date: `2026-07-13`
Task: `AGENT-269`

## Policy

Converged or stationary Salt-Q perturbation rows are closure-fit admissible. The
older `too_short` post-restart-advance label is retained only as context for an
otherwise converged row.

Rows that still lack a usable terminal window, have short failed/cancelled launch
evidence, or have unresolved patch/launcher faults remain repair-first.

## Names

Use these short names in current coordination:

- `salt2_lo10q`
- `salt2_hi10q`
- `salt4_lo10q`

The old `*_corrected` source keys remain in manifests and registry rows for
provenance and patcher lookup.

## Repack

The selected continuation launcher is now set up for:

- `salt2_lo10q`
- `salt2_hi10q`
- `salt4_lo10q`

No job was launched by this documentation/implementation pass.

## Code Consistency

Current status-table, F4-gate helper, upcomer-onset summary, and presentation
builders no longer treat Salt-Q rows as categorically excluded. Failed/cancelled
or special-scrutiny rows remain blocked.

## Quarantined Cleanup

The older June 19 and June 25 invalid Salt perturbation staged roots were
deleted after path-specific destructive approval. Targeted `find` verification
found no matching old invalid Salt perturbation names remaining in those two run
roots, and confirmed the July 4 repaired Salt-Q roots remain present.
