# Salt Mesh Coarse Reconciliation

Generated: `2026-07-09T10:41:28-05:00`

This read-only package compares Ethan external coarse mesh endpoint cases
against the repo's current mainline Jin continuations from the July 8
scenario contract. It does not stage data, mutate solver outputs, or
update the registry.

## Observed Facts

- `salt_test_2_jin`: `superseded_by_mainline`; time relation `mainline_extends_external`; coarse use `do_not_use_external_coarse_for_publication_gci`.
- `salt_test_4_jin`: `superseded_by_mainline`; time relation `mainline_extends_external`; coarse use `do_not_use_external_coarse_for_publication_gci`.

## Interpretation

A `superseded_by_mainline` verdict means the external coarse root is useful
for provenance and screening, but should not be treated as the current
publication-grade coarse level without an explicit later decision to align
the mainline continuation and mesh-family endpoint values.
