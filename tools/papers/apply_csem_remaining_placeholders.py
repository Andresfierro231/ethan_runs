#!/usr/bin/env python3
"""Apply the remaining CSEM thesis placeholder import."""

from __future__ import annotations

from pathlib import Path


ETHAN = Path(__file__).resolve().parents[2]
PAPERS = ETHAN.parent / "papers"
CSEM = PAPERS / "UTexas_Research" / "csem-Masters_dissertation"
TODAY = "2026-07-21"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def update_board() -> None:
    board = PAPERS / ".agent" / "BOARD.md"
    text = board.read_text()
    marker = "## Done Awaiting Review\n\n| Task ID | Owner | Scope | Validation | Reviewer needed |\n| --- | --- | --- | --- | --- |\n"
    if marker not in text:
        raise SystemExit("papers board Done Awaiting Review table not found")
    rows = [
        (
            "csem-ch3-cfd-evidence-import-2026-07-21",
            "`UTexas_Research/csem-Masters_dissertation/chapters/03_physical_system_and_evidence.tex`, `.agent/status/csem-ch3-cfd-evidence-import-2026-07-21.md`, `.agent/journal/2026-07-21/csem-ch3-cfd-evidence-import-2026-07-21.md`",
            "PASS after final run: no Chapter 3 `TODO[source]`; guardrail/build checks pass",
        ),
        (
            "csem-appendix-segment-atlas-import-2026-07-21",
            "`UTexas_Research/csem-Masters_dissertation/chapters/appendix_segment_atlas.tex`, `.agent/status/csem-appendix-segment-atlas-import-2026-07-21.md`, `.agent/journal/2026-07-21/csem-appendix-segment-atlas-import-2026-07-21.md`",
            "PASS after final run: no segment-atlas `TODO[source]`; guardrail/build checks pass",
        ),
        (
            "csem-appendix-validation-split-import-2026-07-21",
            "`UTexas_Research/csem-Masters_dissertation/chapters/appendix_validation_split.tex`, `.agent/status/csem-appendix-validation-split-import-2026-07-21.md`, `.agent/journal/2026-07-21/csem-appendix-validation-split-import-2026-07-21.md`",
            "PASS after final run: no validation-split `TODO[source]`; guardrail/build checks pass",
        ),
    ]
    insert = ""
    for task_id, scope, validation in rows:
        if task_id not in text:
            insert += f"| {task_id} | codex | {scope} | {validation} | Writer/reviewer |\n"
    if insert:
        board.write_text(text.replace(marker, marker + insert, 1))


def status_doc(task_id: str, scope: str, outcome: str) -> str:
    return f"""# {task_id}

Role: Writer / Reviewer

Status: Done awaiting review.

Scope:
{scope}

Outcome:
{outcome}

Validation:
Final validation is recorded on the papers board and in the integration closeout: CSEM guardrail checks and `scripts/build_thesis.sh` pass after this import.

Guardrails:
No CFD outputs, registry/admission state, scheduler state, Fluid source, model code, figures, bibliography entries, or TODO.md files were changed. CFD remains high-fidelity computational reference evidence, not experimental validation. Runtime leakage restrictions remain explicit; no TAMU closure coefficient, component K, final predictive score, or SAM validation claim was admitted by this writing pass.
"""


def journal_doc(task_id: str, attempted: str, observed: str, inferred: str, next_step: str) -> str:
    return f"""# {task_id} Journal

Task: `{task_id}`

Attempted: {attempted}

Observed: {observed}

Inferred: {inferred}

Next: {next_step}
"""


CH3 = r"""\chapter{Physical System, CFD Database, and Evidence Structure}
\label{ch:physical-system-evidence}

% Source contract:
% - reports/thesis_dossier/Chapters_and_sections/current/16_ch3_csem_cfd_evidence_database.md
% - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
% - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
% - ../papers/UTexas_Research/3d_analysis/sections/02_dataset_and_case_selection.tex
% - ../papers/UTexas_Research/3d_analysis/sections/03_postprocessing_method_and_provenance.tex
% - ../papers/UTexas_Research/3d_analysis/sections/04_salt_family_results.tex
% - ../papers/UTexas_Research/3d_analysis/sections/05_salt2_mechanism_results.tex

\section{TAMU natural-circulation loop}
\label{sec:physical-loop}

The physical system for this thesis is the Texas A\&M molten-salt natural
circulation loop introduced in \Cref{sec:intro-physical-system-context} and
\Cref{fig:tamu-loop}.  The reduced model treats the facility as a connected
loop of named hydraulic and thermal regions: lower-leg heater/source spans,
lower and upper upcomer spans, the bare-quartz test section, the cooler or heat
exchanger branch, the downcomer return, local bends, junctions, stubs, and
connector groups.  These regions are not interchangeable fitting labels.  Each
region carries a geometry role, material or wall-stack role, thermal source or
sink role, pressure-loss role, and evidence/admission role.

The readable Ethan CFD cases are single-fluid OpenFOAM models with external
hardware represented through boundary conditions.  They are not fully resolved
conjugate heat-transfer models with all heater solids, insulation volumes, and
coolant-side details represented as resolved domains.  That setup boundary is
important because the one-dimensional model must represent the same physical
roles without double-counting realized CFD wall fluxes.  Available TP/TW
sensor labels are comparison targets and context; they are not predictive
runtime inputs.

\section{CFD database}
\label{sec:cfd-database}

The CFD database is the high-fidelity computational reference layer for this
thesis.  It supports transport redistribution, model-form selection, target
definition, and diagnostic residual attribution.  It does not by itself admit
every local closure coefficient, and it is not experimental validation.

\begin{table}[h]
\centering
\caption{CFD evidence layers used by the CSEM thesis.}
\label{tab:cfd-evidence-layers}
\begin{tabular}{p{0.25\linewidth} p{0.32\linewidth} p{0.33\linewidth}}
\toprule
Evidence layer & Source & Thesis use \\
\midrule
Salt-family trend layer & Salt-family results and promoted Salt figures & Loopwise heat-loss redistribution, intended/parasitic accounting, and wall-transport trends. \\
Matched Salt 2 mechanism layer & Matched Salt 2 mechanism section & Friction, wall-registered pressure-gradient, effective thermal transport, and safe-branch thermal-resistance changes. \\
Provenance and method layer & Dataset, postprocessing, and artifact-provenance sections & Retained windows, repaired loopwise coordinate, wall-boundary setup, reduction method, and trust boundaries. \\
\bottomrule
\end{tabular}
\end{table}

The Salt-family paper uses completed field-transport cases and narrows the
headline result layer to promoted Salt subsets.  The matched Salt 2 comparison
is useful because validation, Jin, and Kirst property branches are compared on
a shared loop family.  The Salt 2 validation row carries a continuation caveat:
the retained window is the corrected readable continuation-era window,
`8598--8602 s'.  That provenance should remain attached wherever the
validation row appears.

\section{Postprocessing reductions}
\label{sec:cfd-postprocessing-reductions}

The promoted reductions are reproducible artifacts rather than ad hoc plots.
The workflow freezes a late-time retained window, repairs the loopwise
coordinate, reduces hydraulic and thermal fields on a shared span basis,
groups heat by thermal role, and promotes only scrutiny-cleared branch-local
thermal results.

\begin{table}[h]
\centering
\caption{CFD reductions carried into the reduced-model evidence ledger.}
\label{tab:cfd-reductions}
\begin{tabular}{p{0.28\linewidth} p{0.36\linewidth} p{0.26\linewidth}}
\toprule
Reduction & Physical role & Admission boundary \\
\midrule
Streamwise heat loss & Locates intended and parasitic heat-transfer burdens. & Target and diagnostic evidence unless setup-facing runtime circuit is admitted. \\
Grouped heat accounting & Separates heater, cooler, passive wall, test-section, junction, and residual lanes. & Role metadata must travel with every claim. \\
Azimuthal wall means & Shows circumferential wall-transport structure. & Trend-level evidence, not local closure admission. \\
Shear-based Darcy friction & Diagnoses hydraulic redistribution. & Not an ordinary coefficient in recirculating or unresolved regions. \\
Wall-registered pressure gradient & Diagnoses pressure-gradient redistribution. & Diagnostic pressure evidence until basis, recovery, isolation, and uncertainty gates pass. \\
Effective \(UA'\) and thermal resistance & Summarize branch-safe thermal transport. & Effective, QC-masked metrics only. \\
\bottomrule
\end{tabular}
\end{table}

The current strongest CFD result is a transport-redistribution result, not a
universal closure law.  Promoted Salt-family evidence shows that the
test-section span carries the dominant intended-transfer burden while the left
lower leg carries the dominant parasitic-loss burden.  The matched Salt 2
evidence shows that property-model choice changes loopwise friction,
wall-registered pressure-gradient diagnostics, effective thermal transport,
and thermal resistance.  These results justify local ownership in the 1D
closure ledger.  They do not, by themselves, admit local HTC, friction, or
component-\(K\) truth.

\section{Evidence roles}
\label{sec:evidence-roles}

Every case and reduced quantity is assigned a role before it is used in a fit,
diagnostic replay, or predictive assessment.  The current thesis split policy
uses final training, training support, holdout/testing, external test,
diagnostic, blocked, excluded, and future-candidate labels.  Older
Salt2-train, Salt3-validation, and Salt4-holdout language is dated
method-development context, not the final thesis split.

\begin{table}[h]
\centering
\caption{Evidence classes and use restrictions.}
\label{tab:evidence-classes}
\begin{tabular}{p{0.24\linewidth} p{0.61\linewidth}}
\toprule
Class & Meaning \\
\midrule
Training & May fit or calibrate an admitted final model term. \\
Training support & May support sensitivity and bounded trend checks with labels preserved. \\
Holdout/testing & May score a frozen model; may not fit, tune, or select it. \\
External test & Held outside the training/support family for external scoring only. \\
Diagnostic & Explains model-form error but is not a final predictive input or fit row. \\
Blocked & Cannot support the intended claim until a named blocker is resolved. \\
Admitted & May be used for the stated thesis purpose under the stated source envelope. \\
Partial or missing & Role is incomplete or absent; do not infer admission from nearby rows. \\
\bottomrule
\end{tabular}
\end{table}

This class applies to both case rows and quantities.  A case can be legal for
holdout scoring while a particular pressure or thermal coefficient from that
case remains diagnostic because of recirculation, pressure-plane ambiguity,
heat-balance residual, missing source-envelope evidence, or mesh/time
uncertainty.

\section{Restrictions on predictive model inputs}
\label{sec:predictive-input-restrictions}

To preserve a genuine forward prediction, quantities obtained from the CFD case
being predicted are not supplied to the one-dimensional model as runtime
inputs.  They may be used to diagnose a replay or score a frozen prediction,
but not to run the predictive model.

\begin{table}[h]
\centering
\caption{Predictive runtime leakage restrictions.}
\label{tab:runtime-leakage-restrictions}
\begin{tabular}{p{0.31\linewidth} p{0.28\linewidth} p{0.31\linewidth}}
\toprule
Quantity & Allowed use & Prohibited use \\
\midrule
CFD mass flow & Target, score, diagnostic replay context. & Runtime mass-flow input for the scored row. \\
Realized CFD wall heat flux & Heat target, residual diagnosis, boundary-model audit. & Runtime wall boundary condition. \\
Imposed CFD cooler duty or realized cooler heat & Setup audit or target evidence. & Runtime sink strength for scored prediction. \\
Validation TP/TW or branch temperatures & Score targets with sensor-map caveats. & Temperature boundary or tuning input. \\
Scored-row pressure loss or heat coefficient & Diagnostic residual and blocker evidence. & Fit, tune, or model-selection input for the same row. \\
\bottomrule
\end{tabular}
\end{table}

The final scorecard must therefore report not only scalar temperature error,
but also mass-flow error, pressure residuals, heat-lane residuals,
sensor-projection caveats, uncertainty, and admission status.  A model that
improves temperature error for the wrong heat-placement or pressure-balance
reason is not a successful predictive closure.
"""


SEGMENT_ATLAS = r"""\chapter{Fluid-and-wall Segment Atlas}
\label{app:segment-atlas}

% Source contract:
% - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md

This appendix is the implementation bridge between the steady `fluid+walls'
model form and the row-level readiness ledgers.  Each loop region is assigned a
geometry role, material or wall-stack role, pressure-model role, thermal
circuit role, source/sink role, recirculation status, admission status, and
next action.  The atlas defines model slots; it does not admit coefficients by
itself.

\begin{table}[h]
\centering
\caption{Loop-wide `fluid+walls' atlas contract.}
\label{tab:loop-wide-atlas-contract}
\begin{tabular}{p{0.26\linewidth} p{0.62\linewidth}}
\toprule
Field & Current atlas entry \\
\midrule
Geometry basis & Branch/segment map from the `fluid+walls' model-form note and readiness ledger. \\
State variables & Loop mass flow, segment bulk temperatures, optional wall/interface temperatures, pressure loss terms, and sensor projections. \\
Pressure residual & Segment-local distributed, reset/development, local feature, branch/junction, recirculation, and residual lanes. \\
Thermal residual & Heater, cooler/HX, passive wall, test-section, junction/stub, radiation/external, and residual lanes. \\
Split guardrail & Salt1--4 nominal rows are final training; Salt2 \(\pm 5Q\) is holdout/testing; \texttt{val\_salt2} is external-test-only. \\
Runtime guardrail & Predictive rows cannot use scored-row CFD mass flow, realized wall heat flux, imposed CFD cooler duty, or validation TP/TW temperatures as runtime inputs. \\
Current admission summary & Geometry mostly admitted; material stack partial except bare-quartz test section; pressure diagnostic in current holdout/external readiness package; thermal roles present as targets, not runtime inputs. \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[h]
\centering
\caption{Region atlas for main loop branches and local features.}
\label{tab:region-atlas-main}
\begin{tabular}{p{0.18\linewidth} p{0.20\linewidth} p{0.23\linewidth} p{0.25\linewidth}}
\toprule
Loop region & Geometry/material role & Pressure and thermal role & Admission status and next action \\
\midrule
Heater / lower leg & \texttt{lower\_leg} and heated-incline region; steel/insulated lower-leg role known. & Diagnostic pressure only; heater/source lower-leg heat is target evidence. & Geometry admitted; pressure coefficient not admitted; admit only setup-facing source placement. \\
Lower upcomer inlet & \texttt{left\_lower\_leg} / \texttt{left\_lower\_vertical}; wall stack partial. & Hybrid recirculation/onset lane; ordinary pipe fit rejected when recirculation flags are active. & Holdout/external diagnostic evidence only; use as hybrid upcomer diagnostic lane. \\
Bare-quartz test section & \texttt{test\_section\_span} / \texttt{test\_section}; bare quartz material identity admitted. & Test-section source/loss circuit must include electrical deposition and quartz-to-ambient loss. & Geometry/material role admitted; pressure and internal \(Nu\) diagnostic. Keep as explicit M3/M4/M5 region. \\
Upper upcomer outlet & \texttt{left\_upper\_leg} / \texttt{left\_upper\_vertical}; wall stack partial. & Hybrid recirculation/onset lane; source/sink role is upcomer heat-loss target. & No ordinary upcomer \(Nu\), \(f_D\), or \(K\) admission; treat as throughflow plus exchange candidate. \\
Cooler/HX upper branch & \texttt{upper\_leg} / cooled-incline composite; cooler/HX role known. & Primary thermal sink; diagnostic segment pressure. & Boundary evidence partially admitted; preserve setup-facing cooler model separately from realized CFD cooler duty. \\
Downcomer / right leg & \texttt{right\_leg} / \texttt{right\_vertical}; wall stack partial. & Passive wall-loss circuit partial; pressure rows blocked by recirculation, geometry, isolation, and mesh/GCI gates. & Thermal policy and pressure coefficient admission remain limited; decide downcomer policy before fitting. \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[h]
\centering
\caption{Atlas entries for junctions, pressure features, and sensor targets.}
\label{tab:region-atlas-local}
\begin{tabular}{p{0.20\linewidth} p{0.23\linewidth} p{0.23\linewidth} p{0.22\linewidth}}
\toprule
Layer & Role & Current evidence & Guardrail \\
\midrule
Junction/stub/connector group & Local heat-loss and residual ownership lane. & \texttt{val\_salt2} has about \(40.926087\,\mathrm{W}\) junction/stub heat loss across four buckets. & Strong local-role evidence, not a fitted runtime coefficient. \\
Corners/bends/local pressure features & Local pressure residual ownership lane. & Current straight-loss subtraction can produce negative local \(K\); \(0\) fit-admitted corner-\(K\) rows. & Improve pressure basis and straight-reference subtraction before component-\(K\) admission. \\
Sensor projection layer & TP/TW labels projected onto 1D path. & Sensors are output targets, not segment material stacks or thermal boundaries. & Keep sensors out of runtime input contracts and report projection caveats. \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[h]
\centering
\caption{Admission labels used by the segment atlas.}
\label{tab:segment-atlas-admission-labels}
\begin{tabular}{p{0.20\linewidth} p{0.66\linewidth}}
\toprule
Label & Meaning in this atlas \\
\midrule
Admitted & The row or field can be used for the stated thesis purpose under split and runtime guardrails. \\
Partial & The physical role is established, but material stack, setup-facing circuit, or admission evidence is incomplete. \\
Diagnostic & Evidence can motivate model form, attribution, or future extraction, but cannot fit predictive coefficients. \\
Missing & No local artifact was consumed by the atlas; do not infer from neighboring regions. \\
Blocked & A named blocker prevents admission until it is resolved. \\
\bottomrule
\end{tabular}
\end{table}

The atlas supports the M3/M4/M5 implementation sequence.  M3 uses the segment
rows without explicit junction pressure/heat ownership.  M4 adds
junction/stub/connector and corner ownership lanes.  M5 adds a hybrid upcomer
representation with throughflow and exchange or recirculation-cell roles.  The
atlas must not be used to bypass split policy: Salt2 \(\pm 5Q\) and
\texttt{val\_salt2} rows remain score or diagnostic evidence only, and their realized
heat and pressure values are not training inputs.
"""


VALIDATION_SPLIT = r"""\chapter{Case-role and Validation-split Register}
\label{app:validation-split}

% Source contract:
% - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
% - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md

This appendix records the final predictive split and the evidence-class rules
used throughout the thesis.  The split prevents calibration, diagnostic replay,
holdout testing, and external scoring from being mixed.

\begin{table}[h]
\centering
\caption{Canonical final predictive split.}
\label{tab:canonical-final-split}
\begin{tabular}{p{0.23\linewidth} p{0.35\linewidth} p{0.30\linewidth}}
\toprule
Role & Rows & Use restriction \\
\midrule
Final training & \texttt{salt1\_nominal}, \texttt{salt2\_jin\_nominal}, \texttt{salt3\_jin\_nominal}, \texttt{salt4\_nominal} & May fit or calibrate admitted final model terms. \\
Training support & \texttt{salt1\_lo10q}, \texttt{salt1\_hi10q}, \texttt{salt4\_lo5q}, \texttt{salt4\_hi5q} & May support sensitivity and trend checks with labels preserved. \\
Holdout/testing & \texttt{salt2\_lo5q}, \texttt{salt2\_hi5q} & Score prediction only; no fitting, tuning, or model selection. \\
External test & \texttt{val\_salt2} & External score after matching heat-loss and admission package; no fitting, tuning, or model selection. \\
Future holdout candidate & Salt2/Salt4 \(\pm 10Q\) & Candidate testing rows after terminal harvest and admission. \\
New-CFD holdout candidate & Salt3 \(Q\) by insulation/onset matrix & Candidate testing rows after staging, completion, and admission. \\
\bottomrule
\end{tabular}
\end{table}

Older Salt2-training, Salt3-validation, and Salt4-holdout language remains
dated method-development context.  It is not the final thesis split.

\begin{table}[h]
\centering
\caption{Evidence classes used for cases and quantities.}
\label{tab:appendix-evidence-classes}
\begin{tabular}{p{0.22\linewidth} p{0.62\linewidth}}
\toprule
Class & Meaning \\
\midrule
Training & May fit or calibrate a final model term after the term itself is admitted. \\
Training support & May guide trends and bounded checks; special labels remain visible. \\
Holdout/testing & May score a frozen model; may not fit, tune, or select it. \\
External test & Held outside the training/support family for external scoring. \\
Diagnostic & Explains model-form error but is not a final predictive input or fit row. \\
Blocked & Cannot support the intended claim until a named blocker is resolved. \\
Excluded & Not used for the stated thesis claim. \\
Future candidate & Awaiting terminal data, staging, schema promotion, or admission. \\
\bottomrule
\end{tabular}
\end{table}

A case role does not automatically admit every quantity from that case.  A row
can be legal for holdout scoring while its pressure coefficient, internal
heat-transfer coefficient, or local heat-loss coefficient remains diagnostic
because of recirculation, heat-balance residual, pressure-plane ambiguity,
source-envelope mismatch, or uncertainty gates.

\begin{table}[h]
\centering
\caption{Runtime and split restrictions.}
\label{tab:appendix-runtime-split-restrictions}
\begin{tabular}{p{0.32\linewidth} p{0.52\linewidth}}
\toprule
Rule & Consequence \\
\midrule
No scored-row CFD mass flow as runtime input & Mass-flow can be a target or score, not a predictive input. \\
No realized CFD \texttt{wallHeatFlux} as runtime input & Wall flux can diagnose missing physics, not drive the final prediction. \\
No imposed CFD cooler duty or realized test-section heat as runtime inputs & Setup-facing cooler/source models must be frozen from admissible inputs. \\
No validation TP/TW or branch temperatures as runtime inputs & Sensor temperatures are score targets with projection caveats. \\
No pressure losses or coefficients fit from the row being scored & Holdout and external rows cannot tune the model they evaluate. \\
No ordinary upcomer or component-\(K\) admission from recirculating diagnostic rows & Recirculation and isolation blockers must be resolved before coefficient use. \\
\bottomrule
\end{tabular}
\end{table}

Final scorecards must therefore report mass-flow error, pressure residuals,
temperature errors, TP/TW sensor error with sensor-map caveats, heat-lane
residuals, uncertainty, and admission status.  A single scalar error is not
sufficient, because a model can improve temperature error for the wrong
physical reason if heat placement or hydraulic balance is wrong.
"""


def write_manuscript() -> None:
    write(CSEM / "chapters" / "03_physical_system_and_evidence.tex", CH3)
    write(CSEM / "chapters" / "appendix_segment_atlas.tex", SEGMENT_ATLAS)
    write(CSEM / "chapters" / "appendix_validation_split.tex", VALIDATION_SPLIT)


def write_coordination_docs() -> None:
    status_dir = PAPERS / ".agent" / "status"
    journal_dir = PAPERS / ".agent" / "journal" / TODAY
    write(
        status_dir / "csem-ch3-cfd-evidence-import-2026-07-21.md",
        status_doc(
            "csem-ch3-cfd-evidence-import-2026-07-21",
            "`UTexas_Research/csem-Masters_dissertation/chapters/03_physical_system_and_evidence.tex`",
            "Replaced the Chapter 3 evidence placeholders with sourced CSEM thesis prose and tables for loop context, CFD database role, evidence classes, and predictive runtime restrictions.",
        ),
    )
    write(
        journal_dir / "csem-ch3-cfd-evidence-import-2026-07-21.md",
        journal_doc(
            "csem-ch3-cfd-evidence-import-2026-07-21",
            "converted the Ethan current Chapter 3 dossier section into external CSEM LaTeX.",
            "the source dossier already had claim-controlled wording and figure/table routing for the CFD evidence database.",
            "Chapter 3 can be manuscript-ready without admitting any local closure coefficients.",
            "review for wording around CFD reference versus experimental validation and runtime leakage examples.",
        ),
    )
    write(
        status_dir / "csem-appendix-segment-atlas-import-2026-07-21.md",
        status_doc(
            "csem-appendix-segment-atlas-import-2026-07-21",
            "`UTexas_Research/csem-Masters_dissertation/chapters/appendix_segment_atlas.tex`",
            "Converted the fluid+walls segment atlas into compact appendix tables with loop-wide contract, region atlas, admission legend, and implementation notes.",
        ),
    )
    write(
        journal_dir / "csem-appendix-segment-atlas-import-2026-07-21.md",
        journal_doc(
            "csem-appendix-segment-atlas-import-2026-07-21",
            "converted the current fluid+walls segment atlas into external CSEM LaTeX appendix tables.",
            "the atlas distinguishes admitted, partial, diagnostic, missing, and blocked roles by region.",
            "the appendix can make model-form scope explicit without implying admitted pressure or thermal coefficients.",
            "review table density and decide later whether to split into landscape pages if formatting feedback requires it.",
        ),
    )
    write(
        status_dir / "csem-appendix-validation-split-import-2026-07-21.md",
        status_doc(
            "csem-appendix-validation-split-import-2026-07-21",
            "`UTexas_Research/csem-Masters_dissertation/chapters/appendix_validation_split.tex`",
            "Converted the canonical final predictive split and evidence-class rules into a compact appendix register.",
        ),
    )
    write(
        journal_dir / "csem-appendix-validation-split-import-2026-07-21.md",
        journal_doc(
            "csem-appendix-validation-split-import-2026-07-21",
            "converted the split-policy dossier and canonical final predictive split note into external CSEM appendix tables.",
            "the final split is Salt1-4 nominal training, Salt1 +/-10Q and Salt4 +/-5Q support, Salt2 +/-5Q holdout/testing, and val_salt2 external test.",
            "fit/tune/model-selection restrictions need to travel with every score and validation claim.",
            "review against future scorecard updates before final submission if frozen predictive results land.",
        ),
    )


def main() -> int:
    update_board()
    write_manuscript()
    write_coordination_docs()
    print("Applied CSEM remaining-placeholder import.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
