# AGENT-091 Raw Journal — Ethan Insulation Optimizer

## 2026-06-19

- Re-read the repo startup instructions, board, file ownership map, role map,
  and local override files before opening the new additive scope.
- Claimed `AGENT-091` because the user asked for:
  - a local insulation optimizer
  - a compute-node run
  - a durable report inside `ethan_runs`
- Kept the work additive and local:
  - no edits to the sibling TAMU model repo
  - no edits to any AGENT-072/087/089 shared extractor or report roots

### Reconnaissance and model boundary

- Confirmed that the relevant read-only source is:
  - `../cfd-modeling-tools/tamu_first_order_model/Ethan_wall_and_heat_losses/first_order_model_tamu_loop.py`
- Reconfirmed the modeling boundary before implementation:
  - the Ethan wall-loss model prescribes measured temperatures
  - cooler heat removal comes from an air-side enthalpy balance
  - the result is an effective thermal-loss fit, not a predictive cooler HTC
- Reused the same truncation pattern already present in the sibling Fluid model:
  - load the Ethan script only through the code before `# Main output`
  - avoid executing the report-printing footer at import time

### Builder implementation

- Added `tools/analyze/build_ethan_insulation_optimizer_package.py`.
- Core builder behavior:
  - load the Ethan namespace read-only
  - evaluate `Q_unaccounted = Q_expected_loss - Q_total_loss`
  - build coarse family-specific thickness traces
  - search for a zero crossing with bounded bisection when the trace brackets a root
  - fall back to the minimum-absolute-residual trace point when no zero crossing exists
  - propagate the original Ethan uncertainty components at the fitted thickness
  - compare the fitted optima against known 3D case thicknesses from:
    - `reports/2026-06-17_ethan_nondimensional_dashboard_package/salt_dashboard.csv`
    - `reports/2026-06-17_ethan_nondimensional_dashboard_package/water_dashboard.csv`
- Added report outputs:
  - case optima CSV
  - thickness trace CSV
  - family summary CSV
  - all-known-case thickness comparison CSV
  - Salt-screening-only thickness quantification CSV
  - markdown interpretation files
  - figure bundle for Salt traces, Water traces, and 3D-vs-effective comparison

### Early runtime fixes

- First bounded smoke attempt exposed a small wrapper bug:
  - the Ethan script does not export `meters_to_inches`
  - fixed by adding a local conversion helper in the builder
- The first long smoke run also made the operational issue obvious:
  - the solve is numerically heavy enough that no intermediate output is easy to distinguish without explicit progress logging
  - added per-case progress prints with `flush=True`
- Detached `nohup` and `tmux` attempts were blocked by the sandbox/runtime boundary, so the final durable run stayed alive in the active Codex compute-node exec session instead

### Durable compute-node run

- Durable validation/build command:
  - `env PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib_ethan_runs python -m tools.analyze.build_ethan_insulation_optimizer_package --output-dir /scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-19_ethan_insulation_optimizer_package`
- The full run completed on the current compute-node allocation.
- Progress observations from the live run:
  - Salt cases were materially slower than Water cases
  - `Salt 1` was the hardest case and never reached a zero-closure fit within the scanned band
  - `Salt 2-4` and `Water 1-4` all converged to tight effective optima

### Results captured

- Family-level results:
  - Salt mean effective optimum: `1.9066 in`
  - Salt rounded uniform target: `1.9 in`
  - Water mean effective optimum: `0.3932 in`
  - Water rounded uniform target: `0.4 in`
- Salt-vs-3D comparison:
  - known Salt CFD cases average `1.4278 in`
  - the 8 Salt screening runs at `1.4 in` all sit below the matched experimental effective optima
  - the Salt validation row at `1.65 in` is close to the matched Salt 2 optimum
- Water-vs-3D comparison:
  - known Water CFD cases are all `0.4 in`
  - fitted Water optima cluster tightly around that same value
- Important scientific caution preserved:
  - `Salt 1` still carries a large negative residual at its best scanned fit (`-24.22 W` at `2.4 in`)
  - this indicates thickness alone cannot absorb the full Salt 1 closure mismatch in the present simplified wall-loss model

### Final interpretation boundary

- The new package is useful for:
  - effective insulation inference
  - ranking whether the existing 3D thickness assumptions are low/high/aligned
  - showing that Water is already close to the current 3D choice while Salt is not
- The new package is not sufficient for:
  - a predictive cooler-HTC recommendation
  - a literal physical-wrap redesign claim without new CFD/1D follow-up
  - proving that every Salt mismatch is only an insulation-thickness issue
