# Slide 6 Thermal Replay Interpretation

Generated: `2026-07-09T15:46:04+00:00`
Task: `AGENT-219` presentation package follow-up

## What Baseline / Current 1D Means

The slide-6 baseline is `P0_fixed_mdot_current_1d_contract`. It is not the fully predictive 1D solve and it is not a CFD-prescribed heat-ledger replay. It is a fixed-mdot thermal replay that holds the 1D mass flow equal to the admitted Salt CFD mass flow and then solves only the 1D thermal periodicity problem. The pressure residual is still reported, but it is diagnostic and is not used to change mdot.

Within that fixed-mdot replay, `current 1D` means the existing Fluid salt thermal contract:

- geometry and refined Fluid loop segmentation are unchanged;
- mdot is imposed from CFD for Salt 2/3/4;
- the heater/source side uses the current Fluid salt source contract: imposed heater duty plus the legacy `37 W` test-section input;
- the cooler/HX side remains the predictive air-side HX model rather than a CFD-prescribed cooler heat rate;
- internal ambient/passive-loss and radiation settings remain those used by the current Fluid salt scenario;
- no CFD patchwise heat-loss map is injected;
- no hydraulic pressure-root search is performed.

So the baseline answers a narrow question: if the hydraulic state is forced to match CFD mdot, how wrong is the current 1D thermal boundary model by itself?

## Focused Comparison

| Replay path | What changes relative to baseline | Mean `|Tmean error|` | Mean `|loop delta-T error|` | Interpretation |
| --- | --- | ---: | ---: | --- |
| Baseline current 1D (`P0`) | Nothing; current Fluid thermal contract at CFD mdot | 63.75 K | 1.08 K | 1D loop mean is much too hot. |
| CFD cooler duty only (`P1`) | Replace predictive air-side HX duty with CFD cooler `wallHeatFlux` magnitude; keep current 1D sources | 4.46 K | 0.14 K | Best three-case mean thermal-state replay. |
| CFD cooler + heater flux (`P4`) | Prescribe CFD cooler duty and CFD heater interface wall flux; omit legacy `37 W` test-section source | 39.75 K | 0.58 K | Loop becomes too cold by roughly 39-41 K in each case. |

## Why The Agreement Behaves This Way

The baseline error is dominated by the absolute heat-removal level, not by the loop delta-T shape. In `P0`, the current 1D model removes only about `46-53 W` through the HX while also removing `256-318 W` through ambient/passive paths. The replay still closes thermal periodicity, but it lands at a loop-mean temperature about `62-65 K` above CFD. This is consistent with an external-boundary mismatch: the modeled temperature-dependent sink network finds a different absolute equilibrium temperature than the CFD case.

Prescribing only the CFD cooler duty fixes the dominant absolute-temperature anchor. In `P1`, `qhx_total_W` becomes the CFD cooler magnitude, about `136 W`, `151 W`, and `169 W` for Salt 2/3/4. The current 1D sources are left alone, and the remaining ambient/passive loss falls to `166-205 W` because the loop equilibrates near a cooler mean temperature. That combination brings the loop mean to within `2.7-6.2 K` of CFD and keeps loop delta-T error below `0.2 K` on average. This is why the slide claim should be phrased as: the cooler/HX heat-removal model is the largest current thermal-state lever.

Adding CFD heater wall flux in `P4` makes the result worse because it changes the source side at the same time as the cooler side. The CFD heater-interface wall flux used by this replay is lower than the current 1D source contract: the source total drops from `302.7/334.5/374.6 W` in `P0/P1` to `243.5/273.2/310.5 W` in `P4`. With the stronger CFD cooler duty still imposed, that lower source contract over-cools the 1D loop. The sign of the error flips: the model mean temperature is about `38.6-40.9 K` below CFD.

Scientifically, this says the one-at-a-time cooler intervention is more diagnostic than the combined cooler+heater intervention. The cooler-only replay shows that the current predictive HX/cooler boundary is the main reason the current 1D thermal state sits too hot at CFD mdot. The combined replay shows that simply replacing multiple thermal terms with patchwise CFD values is not automatically more physical inside the current 1D semantics, because the source, passive-loss, and imposed-HX contracts are coupled through the periodic mean-temperature solve.

## Per-Case Values

### Baseline current 1D (`P0`)

- `salt_2`: `Tmean_error_K = 62.23`, `loop_delta_T_error_K = -0.90`, `qhx_total_W = 46.29`, `qambient_total_W = 256.41`, `source_total_W = 302.70`
- `salt_3`: `Tmean_error_K = 63.99`, `loop_delta_T_error_K = -1.14`, `qhx_total_W = 49.66`, `qambient_total_W = 284.84`, `source_total_W = 334.50`
- `salt_4`: `Tmean_error_K = 65.03`, `loop_delta_T_error_K = -1.18`, `qhx_total_W = 53.47`, `qambient_total_W = 317.81`, `source_total_W = 374.60`

### CFD cooler duty only (`P1`)

- `salt_2`: `Tmean_error_K = 6.22`, `loop_delta_T_error_K = 0.14`, `qhx_total_W = 136.35`, `qambient_total_W = 166.35`, `source_total_W = 302.70`
- `salt_3`: `Tmean_error_K = 4.45`, `loop_delta_T_error_K = -0.11`, `qhx_total_W = 150.77`, `qambient_total_W = 183.73`, `source_total_W = 334.50`
- `salt_4`: `Tmean_error_K = 2.70`, `loop_delta_T_error_K = -0.17`, `qhx_total_W = 169.23`, `qambient_total_W = 205.37`, `source_total_W = 374.60`

### CFD cooler + heater flux (`P4`)

- `salt_2`: `Tmean_error_K = -38.62`, `loop_delta_T_error_K = -0.37`, `qhx_total_W = 136.35`, `qambient_total_W = 107.17`, `source_total_W = 243.52`
- `salt_3`: `Tmean_error_K = -39.75`, `loop_delta_T_error_K = -0.64`, `qhx_total_W = 150.77`, `qambient_total_W = 122.39`, `source_total_W = 273.16`
- `salt_4`: `Tmean_error_K = -40.88`, `loop_delta_T_error_K = -0.73`, `qhx_total_W = 169.23`, `qambient_total_W = 141.26`, `source_total_W = 310.49`

## Presentation Wording

Use this wording on the slide: `At fixed CFD mdot, the current 1D thermal contract is about 64 K too hot in loop mean temperature. Replacing only the predictive cooler/HX duty with the CFD cooler wallHeatFlux magnitude reduces the mean error to about 4.5 K. Replacing both cooler duty and heater wall flux over-corrects because the source contract changes at the same time, so this is a diagnostic replay, not a final predictive model.`

## Claim Boundary

This slide does not prove that prescribing CFD cooler duty is a predictive model. It proves that the cooler/HX boundary condition is the dominant lever in the fixed-mdot thermal-state mismatch. The next 1D model should predict that cooler removal from geometry, coolant conditions, and heat-transfer closure rather than importing it from CFD.
