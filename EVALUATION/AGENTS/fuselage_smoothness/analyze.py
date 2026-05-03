"""
Fuselage smoothness and curvature analyzer.

This is a fast geometry-quality tool. It reads the companion JSON emitted by the
OpenVSP generator, reconstructs a simplified longitudinal fuselage/boom radius
profile, and reports curvature, taper angles, and pressure-recovery risk.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
OUT_DIR = PROJECT_ROOT / "EVALUATION" / "fuselage_reports"


def load_model_meta(path_arg: str | None) -> tuple[Path, dict[str, Any]]:
    if path_arg:
        path = Path(path_arg).resolve()
        if path.suffix.lower() == ".vsp3":
            path = path.with_suffix(".json")
    else:
        candidates = sorted(AIRCRAFT_DIR.glob("MODEL_*.json"), key=lambda p: p.stat().st_mtime)
        if not candidates:
            raise FileNotFoundError("No MODEL_*.json companion files found in AIRCRAFT/")
        path = candidates[-1]

    if not path.exists():
        raise FileNotFoundError(f"Companion JSON not found: {path}")
    return path, json.loads(path.read_text())


def meta_float(meta: dict[str, Any], key: str, default: float, assumptions: list[str]) -> float:
    value = meta.get(key)
    if value is None:
        assumptions.append(f"{key} missing; assumed {default}")
        return default
    return float(value)


def eq_radius(width: float, height: float) -> float:
    """Area-equivalent radius for an elliptical section with width and height."""
    return 0.5 * math.sqrt(max(width, 0.0) * max(height, 0.0))


def make_station(label: str, x: float, width: float, height: float, z_center: float = 0.0) -> dict[str, float | str]:
    return {
        "label": label,
        "x_m": round(x, 4),
        "z_center_m": round(z_center, 4),
        "width_m": round(width, 4),
        "height_m": round(height, 4),
        "top_z_m": round(z_center + 0.5 * height, 4),
        "bottom_z_m": round(z_center - 0.5 * height, 4),
        "eq_radius_m": round(eq_radius(width, height), 4),
    }


def build_profile(meta: dict[str, Any]) -> tuple[list[dict[str, float | str]], list[str]]:
    assumptions: list[str] = []
    config = str(meta.get("configuration", "unknown"))

    explicit_stations = meta.get("fuselage_stations")
    if isinstance(explicit_stations, list) and explicit_stations:
        stations = []
        for idx, station in enumerate(explicit_stations):
            if not isinstance(station, dict):
                assumptions.append(f"fuselage_stations[{idx}] is not an object; skipped")
                continue
            label = str(station.get("label", f"station {idx}"))
            x = float(station["x_m"])
            width = float(station.get("width_m", 0.0))
            height = float(station.get("height_m", 0.0))
            z_center = float(station.get("z_center_m", 0.0))
            stations.append(make_station(label, x, width, height, z_center))
        return sorted(stations, key=lambda s: float(s["x_m"])), assumptions

    fuse_length = meta_float(meta, "fuse_length_m", 3.9, assumptions)

    if config == "pod_and_boom":
        max_width = meta_float(meta, "fuse_max_width_m", 1.10, assumptions)
        max_height = meta_float(meta, "fuse_max_height_m", 0.75, assumptions)
        taper_width = meta_float(meta, "fuse_taper_width_m", 0.20, assumptions)
        taper_height = meta_float(meta, "fuse_taper_height_m", 0.20, assumptions)
        boom_x = meta_float(meta, "boom_x_m", max(fuse_length - 0.30, 0.0), assumptions)
        boom_length = meta_float(meta, "boom_length_m", 1.90, assumptions)
        boom_diameter = meta_float(meta, "boom_diameter_m", 0.12, assumptions)

        if boom_x < fuse_length:
            assumptions.append("boom_x is inside the pod length; profile joins boom at pod tail")
            boom_join_x = fuse_length
        else:
            boom_join_x = boom_x

        stations = [
            make_station("nose point", 0.0, 0.0, 0.0),
            make_station("forward cabin", 0.25 * fuse_length, max_width, max_height),
            make_station("aft cabin", 0.65 * fuse_length, max_width, max_height),
            make_station("pod taper exit", fuse_length, taper_width, taper_height),
        ]
        if boom_join_x > fuse_length:
            stations.append(make_station("boom start", boom_join_x, boom_diameter, boom_diameter))
        stations.append(make_station("tail boom end", boom_x + boom_length, boom_diameter, boom_diameter))
        return sorted(stations, key=lambda s: float(s["x_m"])), assumptions

    max_width = meta_float(meta, "fuse_max_width_m", 0.84, assumptions)
    max_height = meta_float(meta, "fuse_max_height_m", 1.05, assumptions)
    stations = [
        make_station("nose point", 0.0, 0.0, 0.0),
        make_station("forward cabin", 0.25 * fuse_length, max_width, max_height),
        make_station("aft cabin", 0.70 * fuse_length, max_width, max_height),
        make_station("tail point", fuse_length, 0.0, 0.0),
    ]
    return stations, assumptions


def segment_metrics(stations: list[dict[str, float | str]]) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for start, end in zip(stations, stations[1:]):
        dx = float(end["x_m"]) - float(start["x_m"])
        dr = float(end["eq_radius_m"]) - float(start["eq_radius_m"])
        slope = dr / dx if dx else 0.0
        angle = math.degrees(math.atan(slope))
        segments.append(
            {
                "from": start["label"],
                "to": end["label"],
                "dx_m": round(dx, 4),
                "radius_change_m": round(dr, 4),
                "slope": round(slope, 4),
                "angle_deg": round(angle, 2),
            }
        )
    return segments


def point_curvature(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float]) -> float:
    a = math.dist(p0, p1)
    b = math.dist(p1, p2)
    c = math.dist(p0, p2)
    denom = a * b * c
    if denom == 0.0:
        return 0.0
    double_area = abs(
        (p1[0] - p0[0]) * (p2[1] - p0[1])
        - (p1[1] - p0[1]) * (p2[0] - p0[0])
    )
    return 2.0 * double_area / denom


def curvature_metrics(stations: list[dict[str, float | str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pts = [(float(s["x_m"]), float(s["eq_radius_m"]), str(s["label"])) for s in stations]
    for idx in range(1, len(pts) - 1):
        kappa = point_curvature(pts[idx - 1][:2], pts[idx][:2], pts[idx + 1][:2])
        rows.append(
            {
                "station": pts[idx][2],
                "curvature_1_per_m": round(kappa, 4),
                "radius_of_curvature_m": round(1.0 / kappa, 3) if kappa > 0 else None,
            }
        )
    return rows


def centerline_metrics(stations: list[dict[str, float | str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    segments: list[dict[str, Any]] = []
    for start, end in zip(stations, stations[1:]):
        dx = float(end["x_m"]) - float(start["x_m"])
        dz = float(end.get("z_center_m", 0.0)) - float(start.get("z_center_m", 0.0))
        slope = dz / dx if dx else 0.0
        angle = math.degrees(math.atan(slope))
        segments.append(
            {
                "from": start["label"],
                "to": end["label"],
                "dx_m": round(dx, 4),
                "z_change_m": round(dz, 4),
                "slope": round(slope, 4),
                "angle_deg": round(angle, 2),
            }
        )

    rows: list[dict[str, Any]] = []
    pts = [(float(s["x_m"]), float(s.get("z_center_m", 0.0)), str(s["label"])) for s in stations]
    for idx in range(1, len(pts) - 1):
        kappa = point_curvature(pts[idx - 1][:2], pts[idx][:2], pts[idx + 1][:2])
        rows.append(
            {
                "station": pts[idx][2],
                "curvature_1_per_m": round(kappa, 4),
                "radius_of_curvature_m": round(1.0 / kappa, 3) if kappa > 0 else None,
            }
        )
    return segments, rows


def longitudinal_line_metrics(
    stations: list[dict[str, float | str]],
    line_name: str,
    value_getter,
) -> dict[str, list[dict[str, Any]]]:
    """Return slope and curvature metrics for a top/bottom/side fuselage curve."""
    segments: list[dict[str, Any]] = []
    for start, end in zip(stations, stations[1:]):
        dx = float(end["x_m"]) - float(start["x_m"])
        dv = value_getter(end) - value_getter(start)
        slope = dv / dx if dx else 0.0
        angle = math.degrees(math.atan(slope))
        segments.append(
            {
                "line": line_name,
                "from": start["label"],
                "to": end["label"],
                "dx_m": round(dx, 4),
                "value_change_m": round(dv, 4),
                "slope": round(slope, 4),
                "angle_deg": round(angle, 2),
            }
        )

    rows: list[dict[str, Any]] = []
    pts = [(float(s["x_m"]), value_getter(s), str(s["label"])) for s in stations]
    for idx in range(1, len(pts) - 1):
        kappa = point_curvature(pts[idx - 1][:2], pts[idx][:2], pts[idx + 1][:2])
        rows.append(
            {
                "line": line_name,
                "station": pts[idx][2],
                "curvature_1_per_m": round(kappa, 4),
                "radius_of_curvature_m": round(1.0 / kappa, 3) if kappa > 0 else None,
            }
        )

    return {"segments": segments, "curvature": rows}


def classify_pressure_risk(segments: list[dict[str, Any]], curvatures: list[dict[str, Any]]) -> tuple[str, list[str]]:
    findings: list[str] = []
    max_nose_angle = 0.0
    max_aft_taper = 0.0
    passed_max_radius = False

    for segment in segments:
        angle = float(segment["angle_deg"])
        dr = float(segment["radius_change_m"])
        if dr > 0 and not passed_max_radius:
            max_nose_angle = max(max_nose_angle, abs(angle))
        if dr < 0:
            passed_max_radius = True
            max_aft_taper = max(max_aft_taper, abs(angle))

    max_curvature = max((float(row["curvature_1_per_m"]) for row in curvatures), default=0.0)

    if max_nose_angle > 25.0:
        findings.append(f"rapid nose/canopy expansion angle {max_nose_angle:.1f} deg")
    if max_aft_taper > 12.0:
        findings.append(f"steep aft pressure-recovery taper {max_aft_taper:.1f} deg")
    if max_curvature > 0.65:
        findings.append(f"localized radius-profile curvature {max_curvature:.2f} 1/m")

    if len(findings) >= 2:
        return "high", findings
    if findings:
        return "medium", findings
    return "low", ["no major profile-slope or curvature threshold exceeded"]


def analyze(meta_path: Path, meta: dict[str, Any]) -> dict[str, Any]:
    stations, assumptions = build_profile(meta)
    segments = segment_metrics(stations)
    curvatures = curvature_metrics(stations)
    centerline_segments, centerline_curvatures = centerline_metrics(stations)
    surface_lines = {
        "top": longitudinal_line_metrics(stations, "top", lambda s: float(s["top_z_m"])),
        "bottom": longitudinal_line_metrics(stations, "bottom", lambda s: float(s["bottom_z_m"])),
        "side_half_width": longitudinal_line_metrics(
            stations,
            "side_half_width",
            lambda s: 0.5 * float(s["width_m"]),
        ),
    }
    pressure_risk, findings = classify_pressure_risk(segments, curvatures)

    max_radius = max(float(s["eq_radius_m"]) for s in stations)
    total_length = max(float(s["x_m"]) for s in stations)
    max_diameter = 2.0 * max_radius
    fineness_ratio = total_length / max_diameter if max_diameter else 0.0
    max_curvature = max((float(row["curvature_1_per_m"]) for row in curvatures), default=0.0)
    max_slope_angle = max((abs(float(row["angle_deg"])) for row in segments), default=0.0)
    max_centerline_curvature = max((float(row["curvature_1_per_m"]) for row in centerline_curvatures), default=0.0)
    max_centerline_slope_angle = max((abs(float(row["angle_deg"])) for row in centerline_segments), default=0.0)
    max_surface_curvature = max(
        (
            float(row["curvature_1_per_m"])
            for line in surface_lines.values()
            for row in line["curvature"]
        ),
        default=0.0,
    )
    max_surface_slope_angle = max(
        (
            abs(float(row["angle_deg"]))
            for line in surface_lines.values()
            for row in line["segments"]
        ),
        default=0.0,
    )

    penalty = 0.0
    penalty += max(0.0, max_slope_angle - 12.0) * 1.8
    penalty += max(0.0, max_curvature - 0.35) * 25.0
    penalty += max(0.0, max_centerline_slope_angle - 10.0) * 0.8
    penalty += max(0.0, max_centerline_curvature - 0.25) * 18.0
    penalty += max(0.0, max_surface_curvature - 0.55) * 12.0
    if fineness_ratio < 4.0:
        penalty += (4.0 - fineness_ratio) * 8.0
    smoothness_score = max(0.0, min(100.0, 100.0 - penalty))

    recommendations = []
    if pressure_risk != "low":
        recommendations.append("Add intermediate fuselage sections or increase pod/boom transition length.")
        recommendations.append("Reduce aft taper angle toward 10-12 deg for pressure recovery.")
    if fineness_ratio < 4.0:
        recommendations.append("Increase fuselage/boom length or reduce maximum diameter to improve fineness ratio.")
    if not recommendations:
        recommendations.append("Profile is acceptable by current heuristic thresholds.")

    model_name = Path(str(meta.get("model_file", meta_path.name))).name
    return {
        "model": model_name,
        "source_json": str(meta_path),
        "configuration": meta.get("configuration", "unknown"),
        "summary": {
            "total_profile_length_m": round(total_length, 3),
            "max_equivalent_diameter_m": round(max_diameter, 3),
            "fineness_ratio": round(fineness_ratio, 2),
            "max_radius_profile_curvature_1_per_m": round(max_curvature, 4),
            "max_profile_slope_angle_deg": round(max_slope_angle, 2),
            "max_centerline_curvature_1_per_m": round(max_centerline_curvature, 4),
            "max_centerline_slope_angle_deg": round(max_centerline_slope_angle, 2),
            "max_surface_curve_curvature_1_per_m": round(max_surface_curvature, 4),
            "max_surface_curve_slope_angle_deg": round(max_surface_slope_angle, 2),
            "smoothness_score_0_100": round(smoothness_score, 1),
            "pressure_recovery_risk": pressure_risk,
        },
        "findings": findings,
        "recommendations": recommendations,
        "assumptions": assumptions,
        "stations": stations,
        "segments": segments,
        "curvature": curvatures,
        "centerline_segments": centerline_segments,
        "centerline_curvature": centerline_curvatures,
        "surface_curve_lines": surface_lines,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", nargs="?", help="Path to MODEL_*.json or MODEL_*.vsp3. Defaults to newest AIRCRAFT companion JSON.")
    parser.add_argument("--out", type=Path, default=None, help="Optional output JSON path.")
    args = parser.parse_args()

    try:
        meta_path, meta = load_model_meta(args.model)
        report = analyze(meta_path, meta)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = args.out or OUT_DIR / f"{Path(report['model']).stem}_fuselage_smoothness.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))
    print(f"REPORT_FILE:{out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
