# TODO

- Stage a writable copy of the source case into `case_stage/`.
- Confirm whether continuation should preserve the processor decomposition or reconstruct first.
- Decide the new stopping target and walltime for the continuation run.
- Regenerate QoI summaries after continuation and compare against the same 100-sample convergence rule.
- Update the journal and operational notes with the continuation outcome.
- Provide a readable OpenFOAM 13 bashrc path and readable `libRCWallBC.so` path, then submit `run_continuation_openfoam13_template.sbatch`.
- The validated `andres_2d` launch path uses the container `/corral-secure/utexas/ASC23046/Images/openfoam-default_latest.sif`, but that runtime still needs a bound readable `libRCWallBC.so` directory.
