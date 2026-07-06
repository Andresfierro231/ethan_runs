# Scientific Analysis

## Observed result

The Salt-family mean effective optimum is `1.907` in, with a rounded
uniform target of `1.90` in. The Water-family mean effective
optimum is `0.393` in, with a rounded uniform target of
`0.40` in.

## Comparison to known 3D cases

The known Salt screening CFD runs currently cluster at `1.400` in,
while the lone Salt validation CFD row sits at `1.650` in. The Water CFD rows
cluster at `0.400` in.

Relative to the matched experimental optima, the Salt screening rows differ by a mean of `-0.507` in
and the Water rows differ by a mean of `0.007` in.

## Important exception

`Salt 1` does not actually close to zero within the scanned thickness band. Its best scanned fit is
`2.400` in with residual `Q_unaccounted = -24.22` W, and that residual still sits outside the
propagated uncertainty band. This means the family-level Salt target should be read as a useful
effective trend, not as proof that thickness alone explains every Salt thermal-loss mismatch.

## Interpretation

The effective-thickness fit is closing a measured-state energy balance, so it should be read as a lumped thermal
surrogate. If the fitted thickness differs from the physical 3D wall setup, the discrepancy can stand in for multiple
unmodeled effects at once: installation compression, contact resistances, fixture leakage, ambient/radiative closure
error, or simplifications in the fin-loss treatment. It is therefore strong evidence about the thermal-loss budget,
but weaker evidence about literal wrap thickness alone.

## Scope limits

- This package does not infer a predictive cooler HTC.
- This package does not overwrite the current 3D case setups or claim that a new 3D optimum is proven without reruns.
- The most defensible near-term use is to rank whether the current 3D thickness assumptions are likely low, high, or roughly aligned relative to the wall-loss closure fit.
