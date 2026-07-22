# Parallel Agent Prompts

## Agent A: Cooler/HX Duty Audit

Prompt:
You are AGENT-HX. In ethan_runs, claim a new board task scoped to a cooler/HX audit. Read AGENTS.md, .agent/BOARD.md, the AGENT-209 package, and the Fluid solver HX implementation. Compare CFD cooler wallHeatFlux for Salt 2/3/4 against Fluid predictive qhx_total_W and the P1 replay. Audit air-flow units, shell hydraulic diameter, annulus area, active HX length, counterflow/parallel assumptions, and whether reducer patches should contribute to the cooling-jacket duty. Write a dated operational note with exact source lines, equations, and a recommended Fluid patch or no-patch decision.

## Agent B: Source/Test-Section Contract Audit

Prompt:
You are AGENT-SOURCE. In ethan_runs, claim a new board task scoped to source and test-section thermal contract. Read the AGENT-209 package, patchwise heat ledger, and Fluid cases.yaml/solver source distribution. Verify whether Salt 2/3/4 should use heater imposed duty, heater interface wallHeatFlux, or a split solid/fluid heater contract. Audit the 37 W quartz test-section source against CFD net test-section wallHeatFlux, including radiation/emissivity implications. Produce a table of proposed Fluid source/loss inputs and tests.

## Agent C: Radiation/qr Reconstruction

Prompt:
You are AGENT-QR. In ethan_runs, claim a new board task scoped to radiation semantics. Read the scenario contract, patchwise heat ledger, and OpenFOAM boundary files for Salt 2/3/4. Determine exactly why `qr` is absent despite emissivity metadata, whether `rcExternalTemperature` is computing radiative exchange implicitly or only using metadata, and what post-processing or solver changes would be required to export a patchwise radiation term. Document how to separate convection, conduction, and radiation without double counting.

## Agent D: Fixed-mdot Fluid Solver Design

Prompt:
You are AGENT-FROZEN. In the Fluid repo, claim a task scoped to fixed-mdot/frozen-hydraulics thermal replay. Read AGENT-208 and AGENT-209 outputs plus solver.py. Design and implement, or produce a precise patch plan for, a fixed_mdot_kg_s mode that solves thermal periodicity at prescribed mdot without pressure root search while still reporting pressure residual separately. Include tests proving solve_case fixed-mdot equals solve_temperature_periodicity at the target mdot and that model-form bakeoff cannot mix fixed-mdot thermal replay scores with predictive mdot scores.
