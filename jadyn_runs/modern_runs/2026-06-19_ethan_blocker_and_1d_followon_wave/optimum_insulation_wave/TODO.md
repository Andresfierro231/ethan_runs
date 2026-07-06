# TODO

- [x] Stage the four Jin Salt optimum-insulation continuation copies.
- [x] Validate each staged tree has `0/`, `constant/`, `system/`, and `processors64/`.
- [x] Submit the packed 256-rank node.
- [x] If login-node staging remains slow, submit via the compute-node
  self-staging launcher instead of waiting on a partial local copy.
- [x] Record the packed job ID in `campaign_manifest.csv`.
- [x] Recheck queue state after submission.
- [x] Preserve the failed self-staging artifacts instead of deleting them.
- [x] Remove the compute-node `rg` dependency from the staging checks.
- [x] Relaunch the packed wave from the already staged local case roots.
- [x] Raise all staged optimum cases to `purgeWrite 21`.
- [x] Resubmit the packed optimum node after the capped-window stop and continuation repack.
- [x] Cancel the repacked optimum node once the stricter `< 2 W`
  heat-balance gate ruled out an insulation-only relaunch under the current
  fixed-`Q` 3D contract.
- [ ] If this wave is revived later, add a defensible 3D ambient-loss or
  residual-solve contract before any new `sbatch` submission.
