#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.analyze.check_corrected_salt_preflight as checker  # noqa: E402


def _args(**over) -> argparse.Namespace:
    ns = argparse.Namespace(
        expected_processors=2,
        atol=1e-7,
        rtol=1e-9,
        allow_missing_processors=False,
        check_runtime_controls=False,
        min_time_precision=12,
        max_time_precision=None,
        required_time_format="fixed",
        restart_times={},
    )
    for key, value in over.items():
        setattr(ns, key, value)
    return ns


def _manifest_row(case_dir: Path) -> dict[str, str]:
    return {
        "case_key": "salt2_jin_hi5q_corrected",
        "q_ratio": "1.05",
        "target_heater_power_W": "278.985",
        "target_cooler_q04_W": "-16.9455321449",
        "target_cooler_q05_W": "-109.277212611",
        "target_cooler_q06_W": "-16.9455321449",
        "case_dir": str(case_dir),
    }


def _field_text(heater_patch_q: float, cooler_q: tuple[float, float, float]) -> str:
    values = {
        "pipeleg_lower_04_straight": heater_patch_q,
        "pipeleg_lower_05_straight": heater_patch_q,
        "pipeleg_lower_06_straight": heater_patch_q,
        "pipeleg_upper_04_reducer": cooler_q[0],
        "pipeleg_upper_05_cooler": cooler_q[1],
        "pipeleg_upper_06_reducer": cooler_q[2],
    }
    lines = []
    for patch, value in values.items():
        lines.extend(
            [
                f'"{patch}"',
                "{",
                "    type            externalWallHeatFluxTemperature;",
                f"    Q               constant {value:.12g};",
                "}",
            ]
        )
    return "\n".join(lines) + "\n"


def _decomposed_field(blocks: list[str]) -> bytes:
    out = bytearray(b"FoamFile\n{\n    class       decomposedBlockData;\n}\n")
    for idx, block in enumerate(blocks):
        raw = block.encode("latin-1")
        out += f"// Processor{idx}\n\n{len(raw)}\n(".encode("ascii")
        out += raw
        out += b")\n"
    return bytes(out)


def _write_case(case_dir: Path, heater_patch_q: float, cooler_q: tuple[float, float, float]) -> None:
    case_dir.mkdir(parents=True)
    (case_dir / "0").mkdir()
    (case_dir / "case_config.yaml").write_text(
        "\n".join(
            [
                "operating_point:",
                "  heater_power_W: 278.985",
                "bc_params:",
                "  heater:",
                "    Q: 278.985",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    text = _field_text(heater_patch_q, cooler_q)
    (case_dir / "0/T").write_text(text, encoding="utf-8")
    latest = case_dir / "processors64" / "7915"
    latest.mkdir(parents=True)
    (latest / "T").write_bytes(_decomposed_field([text, text]))


def _write_control_dict(
    case_dir: Path,
    *,
    start_from: str,
    start_time: str,
    time_format: str = "fixed",
    time_precision: int,
) -> None:
    system = case_dir / "system"
    system.mkdir(exist_ok=True)
    (system / "controlDict").write_text(
        "\n".join(
            [
                "application     foamRun;",
                f"startFrom       {start_from};",
                f"startTime       {start_time};",
                "stopAt          endTime;",
                "endTime         30000;",
                "deltaT          0.01;",
                "adjustTimeStep  yes;",
                "writeControl    adjustableRunTime;",
                f"timeFormat      {time_format};",
                f"timePrecision   {time_precision};",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_audit_case_accepts_matching_root_and_collated_restart(tmp_path):
    case_dir = tmp_path / "case"
    _write_case(case_dir, 278.985 / 3.0, (-16.9455321449, -109.277212611, -16.9455321449))

    result = checker.audit_case(_manifest_row(case_dir), _args())

    assert result["config_ok"] is True
    assert result["root_field_ok"] is True
    assert result["processor_field_ok"] is True
    assert result["overall_ok"] is True
    assert result["processor_summary"]["processor_blocks"] == 2


def test_audit_case_rejects_processor_value_mismatch(tmp_path):
    case_dir = tmp_path / "case"
    _write_case(case_dir, 278.985 / 3.0, (-16.9455321449, -109.277212611, -16.9455321449))
    bad_text = _field_text(99.0, (-16.9455321449, -109.277212611, -16.9455321449))
    (case_dir / "processors64" / "7915" / "T").write_bytes(_decomposed_field([bad_text, bad_text]))

    result = checker.audit_case(_manifest_row(case_dir), _args())

    assert result["root_field_ok"] is True
    assert result["processor_field_ok"] is False
    assert result["overall_ok"] is False
    assert "pipeleg_lower_04_straight" in "; ".join(result["processor_summary"]["mismatches"])


def test_audit_case_rejects_bad_collated_frame(tmp_path):
    case_dir = tmp_path / "case"
    _write_case(case_dir, 278.985 / 3.0, (-16.9455321449, -109.277212611, -16.9455321449))
    text = _field_text(278.985 / 3.0, (-16.9455321449, -109.277212611, -16.9455321449))
    raw = bytearray(b"FoamFile\n{\n    class       decomposedBlockData;\n}\n")
    raw += f"// Processor0\n\n{len(text) + 10}\n(".encode("ascii")
    raw += text.encode("latin-1") + b")\n"
    (case_dir / "processors64" / "7915" / "T").write_bytes(bytes(raw))

    result = checker.audit_case(_manifest_row(case_dir), _args())

    assert result["processor_field_ok"] is False
    assert result["overall_ok"] is False
    assert result["processor_summary"]["frame_error_count"] == 1


def test_audit_case_accepts_explicit_integer_restart_with_general_low_precision(tmp_path):
    case_dir = tmp_path / "case"
    _write_case(case_dir, 278.985 / 3.0, (-16.9455321449, -109.277212611, -16.9455321449))
    _write_control_dict(
        case_dir,
        start_from="startTime",
        start_time="7915",
        time_format="general",
        time_precision=6,
    )

    result = checker.audit_case(
        _manifest_row(case_dir),
        _args(
            check_runtime_controls=True,
            restart_times={"salt2_jin_hi5q_corrected": "7915"},
            min_time_precision=6,
            max_time_precision=6,
            required_time_format="general",
        ),
    )

    assert result["runtime_controls_ok"] is True
    assert result["overall_ok"] is True


def test_audit_case_rejects_latest_time_when_explicit_restart_is_required(tmp_path):
    case_dir = tmp_path / "case"
    _write_case(case_dir, 278.985 / 3.0, (-16.9455321449, -109.277212611, -16.9455321449))
    _write_control_dict(
        case_dir,
        start_from="latestTime",
        start_time="0",
        time_format="general",
        time_precision=6,
    )

    result = checker.audit_case(
        _manifest_row(case_dir),
        _args(
            check_runtime_controls=True,
            restart_times={"salt2_jin_hi5q_corrected": "7915"},
            min_time_precision=6,
            max_time_precision=6,
            required_time_format="general",
        ),
    )

    assert result["runtime_controls_ok"] is False
    assert result["restart_time_s"] == "7915"
    assert result["overall_ok"] is False
    assert "startFrom latestTime != startTime" in "; ".join(result["runtime_summary"]["mismatches"])


def test_audit_case_rejects_high_general_precision_for_integer_restart_repair(tmp_path):
    case_dir = tmp_path / "case"
    _write_case(case_dir, 278.985 / 3.0, (-16.9455321449, -109.277212611, -16.9455321449))
    _write_control_dict(
        case_dir,
        start_from="startTime",
        start_time="7915",
        time_format="general",
        time_precision=17,
    )

    result = checker.audit_case(
        _manifest_row(case_dir),
        _args(
            check_runtime_controls=True,
            restart_times={"salt2_jin_hi5q_corrected": "7915"},
            min_time_precision=6,
            max_time_precision=6,
            required_time_format="general",
        ),
    )

    assert result["runtime_controls_ok"] is False
    assert result["overall_ok"] is False
    assert "timePrecision 17 > 6" in "; ".join(result["runtime_summary"]["mismatches"])


def test_audit_case_rejects_fixed_time_format_for_integer_restart_repair(tmp_path):
    case_dir = tmp_path / "case"
    _write_case(case_dir, 278.985 / 3.0, (-16.9455321449, -109.277212611, -16.9455321449))
    _write_control_dict(
        case_dir,
        start_from="startTime",
        start_time="7915",
        time_format="fixed",
        time_precision=6,
    )

    result = checker.audit_case(
        _manifest_row(case_dir),
        _args(
            check_runtime_controls=True,
            restart_times={"salt2_jin_hi5q_corrected": "7915"},
            min_time_precision=6,
            max_time_precision=6,
            required_time_format="general",
        ),
    )

    assert result["runtime_controls_ok"] is False
    assert result["overall_ok"] is False
    assert "timeFormat fixed != general" in "; ".join(result["runtime_summary"]["mismatches"])
