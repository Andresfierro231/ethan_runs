# Paper Methods Note: Non-Upcomer F6 Branch Modeling

The ordinary F6 branch-modeling lane should avoid the upcomer, corners, and
junction/control-volume rows that currently carry material reverse flow or
component/cluster ambiguity. The fit-screened branch candidates are the
Salt2/Salt3/Salt4 `right_leg` and `test_section_span` rows, which are classified
as ordinary straight candidates in the legwise F6 inventory.

The proposed F6 quantity is a named branch pressure residual relative to
`F3_shah_apparent`, not a hidden global multiplier. The residual subtracts
hydrostatic/`p_rgh` basis, kinetic correction, F3 straight-pipe loss, and
development/reset terms from the measured branch pressure drop. The rows are
not fit-ready today because same-window raw endpoint pressure/velocity pairs
and same-QOI mesh/time uncertainty are missing.
