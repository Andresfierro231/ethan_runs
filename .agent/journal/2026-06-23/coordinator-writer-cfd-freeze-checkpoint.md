# AGENT-108 Raw Journal

## 2026-06-23T10:34:58-05:00

### Observed output

- Built the bounded checkpoint report package at
  `reports/2026-06-23_ethan_cfd_freeze_checkpoint/`.
- Confirmed from the report tables that Salt 2-4 each have at least `20`
  representative retained saved times in the continuation, high-Q, and low-Q
  lanes.
- Confirmed that Salt 1 remains below the new retained-window target with only
  `18` saved times.
- Verified that the Water `4 x 64` pilot advanced all four lanes without an
  obvious overload, OOM, or node-failure signature before the mistaken cancel.
- Verified the mistaken cancellations:
  - `3250777` `ethan_salt_contpack`
  - `3251884` `ethan_salt_loqbal3`
  - `3253879` `ethan_water_cont_nq`
  - `3253880` `ethan_salt_hiqb3_nq`
- Requeued the continuation jobs immediately:
  - `3254178` `ethan_salt_contpack`
  - `3254179` `ethan_salt_loqbal3`
  - `3254180` `ethan_water_cont_nq`
  - `3254181` `ethan_salt_hiqb3_nq`
- Immediate queue check after recovery:
  - `3254178` pending on `Resources`
  - `3254179` pending on `Priority`
  - `3254180` pending on `Priority`
  - `3254181` pending on `Priority`

### Interpretation

- The June 23 checkpoint is a valid bounded analysis snapshot, not the final
  CFD endpoint.
- The corrected campaign state is "checkpointed and resumed," not "frozen and
  stopped."
- Water `4 x 64` on a dedicated `256`-CPU node remains acceptable as an
  operational packing pilot, but the current evidence still does not justify a
  claim that all four Water cases were at steady state.

### Follow-up

- Let the temporary Salt checkpoint copy finish under
  `tmp/2026-06-23_salt_last20_checkpoint/`.
- Once that background copy completes, write or confirm the local manifest for
  the temporary analysis bundle.
