# TODO

- Monitor active continuation `3202708` for the first successful timestep progression and first clean write after restart.
- If `3202708` completes a meaningful continuation window, re-run QoI extraction and compare against the prior salt2 row plus the canonical reference row.
- If the continuation later fails numerically, distinguish runtime failure from solver-physics divergence before deciding whether to keep pushing restarts.
- If coworker-provided runtime access arrives, compare it against the fallback `/work/.../OpenFOAM-13` alias before changing the canonical runtime path.
- Keep the persistent runtime root in `/work`; do not move this fallback tree onto scratch.

- Use `reports/2026-06-02_ethan_case_metadata_index/` and `reports/2026-06-02_ethan_closure_and_visualization_scaffold/` as the current durable handoff layer for assumptions, geometry, closure-term planning, and steady-state visualization readiness.
