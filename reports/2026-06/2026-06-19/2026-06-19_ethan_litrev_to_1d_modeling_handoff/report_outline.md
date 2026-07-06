# Report Outline

## 1. Purpose And Scope Boundary

- State that this package is a repo-local handoff, not a replacement for the
  literature review manuscript.
- State that the target reader is the future 1D model builder for Ethan CFD
  follow-on work.
- State that the package maps literature closures onto the current repo artifact
  stack and current admitted boundaries.

## 2. Correction To The Fully Developed Assumption

- Explain that long sections are not automatically pressure-drop-developed or
  thermally developed.
- Point to the literature-review friction chapter and June 19 hybrid-model
  handoff as the basis for this correction.
- Distinguish:
  - baseline limit
  - developing-flow correction
  - local-loss term
  - unresolved residual bucket

## 3. Property Model Contract

- Explain why an explicit Jin/Kirst/validation salt branch is required.
- Cross-reference the June 2 discrepancy report.
- Define the minimum state variables needed by the future 1D solver.

## 4. Hydraulic Closure Taxonomy

- Fully developed straight friction baseline
- Apparent friction and redevelopment
- Local-loss terms
- Feature `K_eff` blocker and residual strategy

## 5. Thermal Closure Taxonomy

- Fully developed Nu limits as comparison only
- Direct left-lower-leg `Nu(Re)` admission boundary
- `UA'(x)` primary surface
- `HTC(x)` secondary surface
- Graetz and mixed-convection diagnostics

## 6. Boundary-Condition And External-Loss Contract

- Readable heater `Q`
- Readable fixed cooler `Q`
- Ambient and insulation
- Why live cooler-side `h` is not admitted from the readable artifacts

## 7. Segment Policy Table

- Walk through the rows in `segment_closure_policy.csv`
- Highlight the admitted Salt subset
- Highlight the blocked right-leg and Water-family lanes

## 8. Nondimensional Strategy

- Explain the priority of `Re`, `Pr`, `Gz`, `Gr`, `Ra`, `Ri`
- Explain why `Nu` is branch-specific and support-gated
- Explain why boundary-layer ratios remain diagnostic-only

## 9. Required Future CFD Observables

- Use `required_future_cfd_observables.csv`
- Keep blocked closures tied to exact missing observables
- Separate:
  - needs more runtime
  - needs a new extractor
  - needs a better boundary-model provenance link

## 10. Recommended Next Steps

- Preserve this package as the planning surface
- Open a new implementation task when work moves into actual 1D code
- Revisit this package after the current continuation and bracket waves mature
