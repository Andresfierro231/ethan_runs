# Source/Property Release Atlas Writer Brief

Decision: `source_property_release_atlas_ready_no_release_no_freeze`.

Use this packet to explain why the thesis has diagnostic CFD evidence but no
source/property release for a frozen predictive candidate.

Safe claims:

- All four nominal train rows have source/property labels, but zero rows are
  release-ready.
- Protected validation/holdout/external rows remain unreleased.
- S12/S13/wall/source/empirical paths are useful as evidence, not as frozen
  candidates.

Forbidden claims:

- Do not claim a source/property release.
- Do not claim a final score, candidate freeze, validation score, holdout score,
  or external-test score.
- Do not absorb thermal residuals into internal Nu.
- Do not use realized CFD mdot, wall heat flux, cooler duty, protected
  temperatures, or protected residuals as runtime inputs.
