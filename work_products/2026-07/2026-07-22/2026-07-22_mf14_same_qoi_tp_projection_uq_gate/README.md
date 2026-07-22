# MF14 Same-QOI TP Projection UQ Gate

This package is the second queued MF13/MF12 follow-on study. It asks whether TP projection evidence is ready for predictive runtime use.

## Decision

`same_qoi_tp_projection_uq_fail_closed_no_runtime_temperature_release`

Same-QOI TP labels and projection operators exist diagnostically, but quantitative projection UQ and runtime temperature release do not.

## Outputs

- `tp_same_qoi_projection_uq.csv`: TP1-TP6 projection/UQ/runtime status.
- `projection_release_gate.csv`: fail-closed release matrix.
- `d2_reuse_boundary.csv`: how D2 evidence may be cited without new scoring or admission.
- `split_claim_matrix.csv`: train/protected/external-test claim boundaries.
- `thesis_tp_projection_uq_insert.md`: thesis-ready interpretation.
- `next_study_queue.csv`: continuation sequence.

## Claim Boundary

No protected scoring, model selection, runtime-temperature release, bulk-to-TP correction release, source/property release, or coefficient admission is made here.
