#!/usr/bin/env python3
"""Lock and validate the CFD<->1D segment-name map (action item #7).

WHY THIS EXISTS
---------------
The inspection found the closure artifacts use INCONSISTENT segment names:
  * friction fit `admitted_parent_segments` = ['heated_incline', 'test_section']
  * Nu fit `admitted_parent_segments`       = ['left_lower_vertical']
  * closure map `target_region`             = 'lower_leg|test_section_span',
                                              'left_lower_leg', 'upcomer', ...
  * CFD profile spans (authoritative)       = lower_leg, right_leg,
        left_lower_leg, test_section_span, left_upper_leg, upper_leg
and, worst, the token 'lower_leg' denotes the heated right-vertical CFD span in
the friction context but is used loosely elsewhere. A wrong CFD<->1D mapping
would apply a closure to the wrong physical segment.

This module defines ONE canonical map (CANONICAL_CFD_SPANS + NAME_ALIASES) with
an explicit confidence per alias, then scans the closure artifacts and reports
every segment token as: resolved (confident), resolved (PROVISIONAL - confirm),
or UNRESOLVED. It is the single source of truth other tools should import.

SCIENTIFIC HONESTY: aliases that require domain confirmation (heated_incline,
upcomer) are marked PROVISIONAL with the reasoning, NOT silently resolved. Run
this before trusting any segment-keyed closure wiring.

USAGE
  python tools/analyze/validate_segment_map.py
  python tools/analyze/validate_segment_map.py --closure-dir <ethan_cfd_informed_salt_v2 dir>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    ensure_dir,
    iso_timestamp,
    json_dump,
    relative_to_workspace,
)

# Authoritative CFD spans come from tools/case_analysis_profiles.py (the loop
# geometry contract). Listed here in loop order with a geometric description so
# the map is self-documenting even without importing the profile.
# Roles per the loop owner (Ethan, 2026-06-30) are AUTHORITATIVE. The probe
# coordinate frame in tp_tw_probe_locations.csv does NOT match the physical
# orientation, so geometric descriptions are given by role, not raw xyz.
CANONICAL_CFD_SPANS: dict[str, str] = {
    "lower_leg": "HEATED leg (bottom leg of the physical loop); carries the heater BC. This is 'heated_incline'. Do NOT confuse with left_lower_leg.",
    "right_leg": "DOWNCOMER (the descending return leg).",
    "left_lower_leg": "Upcomer section 1 of 3 (lower part of the riser); spans TP3->TP4.",
    "test_section_span": "Upcomer section 2 of 3 (the test section); spans TP4->TP5.",
    "left_upper_leg": "Upcomer section 3 of 3 (upper part of the riser); spans TP5->TP6.",
    "upper_leg": "Top leg; carries the cooler (pipeleg_upper_05_cooler).",
}

# Composite loop groupings (owner-defined). 'upcomer' is the riser = three
# sections, analyzed both per-section and all-together.
COMPOSITE_GROUPS: dict[str, list[str]] = {
    "upcomer": ["left_lower_leg", "test_section_span", "left_upper_leg"],
    "downcomer": ["right_leg"],
}

# alias -> (canonical_span | None, confidence, reasoning)
NAME_ALIASES: dict[str, dict[str, Any]] = {
    # confident
    "test_section": {"maps_to": "test_section_span", "confidence": "confident",
                     "why": "Both name the TP4->TP5 test-section leg."},
    "test_section_span": {"maps_to": "test_section_span", "confidence": "confident", "why": "Canonical."},
    "left_lower_vertical": {"maps_to": "left_lower_leg", "confidence": "confident",
                            "why": "Nu-fit branch name for the TP3->TP4 left lower vertical leg."},
    "left_lower_leg": {"maps_to": "left_lower_leg", "confidence": "confident", "why": "Canonical."},
    "left_upper_leg": {"maps_to": "left_upper_leg", "confidence": "confident", "why": "Canonical."},
    "lower_leg": {"maps_to": "lower_leg", "confidence": "confident",
                  "why": "Canonical right-vertical heated leg; beware the misleading 'lower' token."},
    "right_leg": {"maps_to": "right_leg", "confidence": "confident", "why": "Canonical."},
    "upper_leg": {"maps_to": "upper_leg", "confidence": "confident", "why": "Canonical."},
    # CONFIRMED by loop owner (Ethan, 2026-06-30)
    "heated_incline": {"maps_to": "lower_leg", "confidence": "confident",
                       "why": "Owner-confirmed: heated_incline IS lower_leg (the heated bottom leg). WARNING: do NOT confuse with left_lower_leg, which is part of the upcomer."},
    "upcomer": {"maps_to": ["left_lower_leg", "test_section_span", "left_upper_leg"], "confidence": "confident",
                "why": "Owner-confirmed: the upcomer (riser) is the composite of left_lower_leg + test_section_span + left_upper_leg, analyzed both per-section and all-together."},
    "downcomer": {"maps_to": "right_leg", "confidence": "confident",
                  "why": "Owner-confirmed: the downcomer is the right_leg."},
    # buckets / non-span targets (documented, not mapped to a single span)
    "all_segments": {"maps_to": "*", "confidence": "bucket", "why": "Applies to every span (material branch)."},
    "all_features": {"maps_to": "features", "confidence": "bucket", "why": "Feature set, not a span."},
    "lower_leg_heater": {"maps_to": "lower_leg", "confidence": "confident", "why": "Heater BC on lower_leg."},
    "cooler_sink_bucket": {"maps_to": "upper_leg", "confidence": "confident", "why": "Cooler on upper_leg."},
    # residual-bucket components (legitimately not single spans; lumped remainders)
    "features": {"maps_to": "residual_bucket", "confidence": "bucket", "why": "Lumped feature set (bends/fittings)."},
    "cooler_return": {"maps_to": "residual_bucket", "confidence": "bucket", "why": "Cooler-return remainder."},
    "reducers": {"maps_to": "residual_bucket", "confidence": "bucket", "why": "Reducer/expansion remainder."},
    "corners": {"maps_to": "residual_bucket", "confidence": "bucket", "why": "Corner remainder."},
    "unsupported_walls": {"maps_to": "residual_bucket", "confidence": "bucket", "why": "Thermally unsupported walls."},
    "cooler_vicinity": {"maps_to": "residual_bucket", "confidence": "bucket", "why": "Cooler-vicinity thermal remainder."},
}

DEFAULT_CLOSURE_DIR = (
    WORKSPACE_ROOT.parent
    / "cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/ethan_cfd_informed_salt_v2"
)
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "work_products" / "2026-06-30_claude_segment_map"


def split_region(token: str) -> list[str]:
    return [t.strip() for t in token.replace("|", " ").split() if t.strip()]


def resolve(token: str) -> dict[str, Any]:
    alias = NAME_ALIASES.get(token)
    if alias is None:
        return {"token": token, "status": "UNRESOLVED", "maps_to": None,
                "why": "No alias entry; not a canonical span."}
    status = {
        "confident": "resolved",
        "provisional": "resolved_PROVISIONAL_confirm",
        "provisional_unresolved": "UNRESOLVED_PROVISIONAL_confirm",
        "bucket": "resolved_bucket",
    }.get(alias["confidence"], "resolved")
    return {"token": token, "status": status, "maps_to": alias["maps_to"], "why": alias["why"]}


def scan_closure_artifacts(closure_dir: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    # JSON fits
    for fname in ("straight_friction_fit.json", "direct_nu_fit.json"):
        path = closure_dir / fname
        if path.exists():
            data = json.loads(path.read_text())
            for seg in data.get("admitted_parent_segments", []):
                findings.append({"artifact": fname, "field": "admitted_parent_segments", **resolve(seg)})
    # closure map CSV target_region
    cmap = closure_dir / "one_d_closure_map.csv"
    if cmap.exists():
        import csv

        with cmap.open() as handle:
            for row in csv.DictReader(handle):
                for tok in split_region(row.get("target_region", "")):
                    findings.append({"artifact": "one_d_closure_map.csv", "field": f"target_region[{row.get('closure_name','')}]", **resolve(tok)})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--closure-dir", default=str(DEFAULT_CLOSURE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)

    findings = scan_closure_artifacts(Path(args.closure_dir))
    unresolved = [f for f in findings if f["status"].startswith("UNRESOLVED")]
    provisional = [f for f in findings if "PROVISIONAL" in f["status"] and not f["status"].startswith("UNRESOLVED")]

    payload = {
        "generated_at": iso_timestamp(),
        "canonical_cfd_spans": CANONICAL_CFD_SPANS,
        "name_aliases": NAME_ALIASES,
        "closure_dir": str(args.closure_dir),
        "findings": findings,
        "summary": {
            "total_tokens": len(findings),
            "unresolved": len(unresolved),
            "provisional_confirm": len(provisional),
        },
        "composite_groups": COMPOSITE_GROUPS,
        "open_questions_for_domain_expert": [],
        "owner_confirmations_2026_06_30": [
            "heated_incline = lower_leg (heated bottom leg); NOT left_lower_leg.",
            "upcomer = left_lower_leg + test_section_span + left_upper_leg (riser; per-section and aggregate).",
            "downcomer = right_leg.",
        ],
    }
    json_dump(output_dir / "segment_map_validation.json", payload)

    print(f"# CFD<->1D segment-map validation  ({iso_timestamp()})")
    print(f"# tokens={len(findings)}  unresolved={len(unresolved)}  provisional={len(provisional)}")
    for f in findings:
        flag = "" if f["status"] == "resolved" else f"   <== {f['status']}"
        print(f"   {f['artifact']:26s} {f['token']:20s} -> {str(f['maps_to']):18s} [{f['status']}]{flag}")
    if provisional or unresolved:
        print("\nOPEN QUESTIONS FOR DOMAIN EXPERT:")
        for q in payload["open_questions_for_domain_expert"]:
            print(f"   - {q}")
    print(f"\nWrote {relative_to_workspace(output_dir / 'segment_map_validation.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
