# S0-S11 Gate Flow Diagram Source

Use this as a manuscript figure draft or as input for a later graphical
rendering task.

```text
S0 baseline control surface
  status: complete; diagnostic/infrastructure
  output: legal target and missing-prediction inventory
        |
S1 external-boundary dictionary
  status: complete contract; Fluid integration separate
  output: setup-facing runtime-input dictionary
        |
S2 split heat-loss evidence
  status: complete residual-owner evidence
  output: heat-path separation before fitting
        |
S3 pressure source envelope
  status: complete diagnostic non-admission
  output: pressure-basis/source-envelope guard
        |
S4 recirculation guard
  status: complete diagnostic guard
  output: ordinary upcomer Nu/f_D/K disabled
        |
S5 source/property split release
  status: complete blocked release gate
  output: 0 fit rows, 0 model-selection rows
        |
S6 frozen scorecard shell
  status: complete blocked shell
  output: 1 placeholder candidate, 16 split-role rows, 0 final scores
        |
S7 sensor-map contract
  status: complete score-target contract
  output: TP/TW score-only; 0 runtime temperature inputs
        |
S8 wall/test-section candidate review
  status: complete negative result
  output: 0 admitted candidates, 0 S11-ready candidates
        |
S9 upcomer onset/exchange UQ
  status: open
  output needed: exchange/onset evidence with same-window uncertainty
        |
S10 pressure/F6 UQ and anchor gate
  status: open
  output needed: same-QOI UQ and low-recirculation pressure anchor
        |
S11 candidate-specific release refresh
  status: trigger-gated
  output needed: named runtime-legal candidate for S6 thaw
```

Caption caveat: the flow is an admission sequence, not a claim that every gate
has produced an admitted predictive closure.
