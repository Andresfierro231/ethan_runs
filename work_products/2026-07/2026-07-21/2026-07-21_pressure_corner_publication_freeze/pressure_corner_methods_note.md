# Pressure-Corner Methods Note

## Sign Convention

The frozen result uses downstream-minus-upstream static pressure across
`lower_leg__s04->right_leg__s00`. A positive gross static value is a static
pressure rise along this endpoint pair, not an irreversible loss.

## Decomposition

The publication freeze preserves the available same-endpoint identity:

```text
dp_static(down-up) = dp_hydrostatic + dp_kinetic + dp_available_residual
```

The straight/developing term is intentionally blank because the current evidence
does not provide a same-basis straight/developing reference for this endpoint
pair, retained time, pressure basis, and velocity basis.

## Scientific Interpretation

The gross static rise is hydrostatic dominated. The signed available residual
after hydrostatic and kinetic correction is negative, small compared with the
gross static rise, and remains a pressure-recovery / recirculating-section
diagnostic. It is not clipped, not multiplied into global friction, and not
admitted as a component loss coefficient.

## Publication Wording

Use: "gross static pressure rise", "hydrostatic dominated",
"signed available residual", "section-effective pressure diagnostic", and
"pressure-recovery diagnostic".

Avoid: "negative loss", "negative component K", "corner produces pressure",
"F6 correction", and "admitted component coefficient".
