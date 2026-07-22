# Tomorrow Presentation Package

Generated: `2026-07-09T15:46:04+00:00`
Task: `AGENT-219`

## Scope

This package expands the July 8 postprocessor story into a slide-ready outline
with bullet points, figure calls, and speaker notes. It also creates four
support figures from existing evidence using a reusable script. It performs no
new OpenFOAM extraction and creates no new closure fit.

## Main Outputs

- `slide_outline_with_speaker_notes.md`
- `slide6_thermal_replay_analysis.md`
- `missing_and_nice_to_have_figures.md`
- `figure_manifest.csv`
- `source_inventory.csv`
- `summary.json`
- `figures/minor_loss_k_apparent_vs_local.svg`
- `figures/minor_loss_separation_phi.svg`
- `figures/fixed_mdot_thermal_replay_error.svg`
- `figures/t13_re_sweep_plan.svg`

## Interpretation Boundary

Tomorrow's defensible claim is that pressure, heat, and regime terms are now
being decomposed into traceable ledgers with admission boundaries. The current
package should not be used to claim final publication-grade closure coefficients
because mesh/GCI, time-window uncertainty, corrected Salt gate admission, and
some raw two-tap feature extraction remain incomplete.

## Reproduce

```bash
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
python tools/analyze/build_tomorrow_presentation_package.py
python -m pytest tools/analyze/test_tomorrow_presentation_package.py -q
```
