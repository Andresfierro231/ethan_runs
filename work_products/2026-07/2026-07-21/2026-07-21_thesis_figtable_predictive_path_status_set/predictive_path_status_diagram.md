# Predictive Path Status Diagram

```mermaid
flowchart LR
  A[Train-only full solve] --> B[Attribution]
  B --> C[Freeze one candidate]
  C --> D[Validation/support scoring]
  D --> E[Holdout scoring]
  E --> F[External-test scoring]
  A -. current .-> X[S12 candidate contract named; no train solve yet]
  C -. blocked .-> Y[S6/S15 blocked; 0 final score values]
```

Caption: the rigorous sequence is train-only full solve, attribution, freeze,
validation, holdout, and external-test. Current evidence stops before the
train-only solve for the named S12 contract, so the final scorecard remains a
blocked shell with `0` final score values.
