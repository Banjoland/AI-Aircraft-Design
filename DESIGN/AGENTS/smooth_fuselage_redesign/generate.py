"""
Smooth full-fuselage redesign generator.

Creates a new aircraft from a source model, replacing the pod-and-boom layout
with one continuous full-length fuselage. The fuselage has a low engine bay,
high cockpit/CG station, high attached wing saddle, and aft tail support shaped
as one smoothly swooping body. Stations are sampled from low-order smooth
curves for the top, bottom, and symmetric side profile.

Run via OpenVSP Python:
    openvsp-python generate.py AIRCRAFT/MODEL_05_02_2026_05.vsp3
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import openvsp as vsp


PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
AIRCRAFT_DIR.mkdir(exist_ok=True)

MTOW_KG = 218.0
MTOW_N = MTOW_KG * 9.81
RHO_SL = 1.225
VSTALL_LIM = 21.0
CL_MAX_ANALYTIC = 1.7
SKIN_DENSITY = 6.0
ENGINE_MASS_KG = 40.0
SYSTEMS_MASS_KG = 8.0
EMPTY_MASS_SPEC = 110.0


def _set(geom_id: str, parm: str, group: str, value: float) -> bool:
    parm_id = vsp.FindParm(geom_id, parm, group)
    if parm_id == "":
        print(f"[warn] parm not found: {group}/{parm} on {vsp.GetGeomName(geom_id)}", file=sys.stderr)
        return False
    vsp.SetParmVal(parm_id, value)
    return True


def _xsec_set(xs: str, parm: str, value: float) -> bool:
    for parm_id in vsp.GetXSecParmIDs(xs):
        if vsp.GetParmName(parm_id) == parm:
            vsp.SetParmVal(parm_id, value)
            return True
    return False


def _apply_c2_skinning(xs: str) -> None:
    """Apply actual OpenVSP C2 skinning controls to all section edges."""
    vsp.ResetXSecSkinParms(xs)
    vsp.SetXSecContinuity(xs, 2)
    for continuity_name in ("ContinuityTop", "ContinuityRight", "ContinuityBottom", "ContinuityLeft"):
        _xsec_set(xs, continuity_name, 2.0)


def _geom_value(geom_id: str, parm: str, group: str, default: float) -> float:
    parm_id = vsp.FindParm(geom_id, parm, group)
    if parm_id == "":
        return default
    return float(vsp.GetParmVal(parm_id))


def _find_geom(name: str) -> str | None:
    geoms = vsp.FindGeomsWithName(name)
    return geoms[0] if geoms else None


def _extract_source_geometry(source_model: Path) -> dict[str, Any]:
    """Read major wing/tail/prop parameters from the requested source model."""
    meta_path = source_model.with_suffix(".json")
    source_meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    vsp.ClearVSPModel()
    vsp.ReadVSPFile(str(source_model))
    vsp.Update()

    values: dict[str, Any] = {
        "source_model": str(source_model),
        "source_meta": source_meta,
        "wing_span": 9.8,
        "wing_root_chord": 0.60,
        "wing_tip_chord": 0.37,
        "wing_sweep": 1.0,
        "wing_dihedral": 3.0,
        "wing_twist": 0.0,
        "wing_airfoil": source_meta.get("wing_airfoil", "NACA4412"),
        "htail_span": 1.6,
        "htail_root_chord": 0.30,
        "htail_tip_chord": 0.24,
        "htail_sweep": 8.0,
        "vtail_height": 0.70,
        "vtail_root_chord": 0.40,
        "vtail_tip_chord": 0.20,
        "vtail_sweep": 20.0,
        "prop_diameter": float(source_meta.get("prop_diameter_m", 1.10)),
    }

    wing_id = _find_geom("MainWing")
    if wing_id:
        values.update(
            {
                "wing_span": _geom_value(wing_id, "TotalSpan", "WingGeom", values["wing_span"]),
                "wing_root_chord": _geom_value(wing_id, "Root_Chord", "XSec_1", values["wing_root_chord"]),
                "wing_tip_chord": _geom_value(wing_id, "Tip_Chord", "XSec_1", values["wing_tip_chord"]),
                "wing_sweep": _geom_value(wing_id, "Sweep", "XSec_1", values["wing_sweep"]),
                "wing_dihedral": _geom_value(wing_id, "Dihedral", "XSec_1", values["wing_dihedral"]),
                "wing_twist": _geom_value(wing_id, "Twist", "XSec_1", values["wing_twist"]),
            }
        )

    htail_id = _find_geom("HorizTail")
    if htail_id:
        values.update(
            {
                "htail_span": _geom_value(htail_id, "TotalSpan", "WingGeom", values["htail_span"]),
                "htail_root_chord": _geom_value(htail_id, "Root_Chord", "XSec_1", values["htail_root_chord"]),
                "htail_tip_chord": _geom_value(htail_id, "Tip_Chord", "XSec_1", values["htail_tip_chord"]),
                "htail_sweep": _geom_value(htail_id, "Sweep", "XSec_1", values["htail_sweep"]),
            }
        )

    vtail_id = _find_geom("VertTail")
    if vtail_id:
        values.update(
            {
                "vtail_height": _geom_value(vtail_id, "TotalSpan", "WingGeom", values["vtail_height"]),
                "vtail_root_chord": _geom_value(vtail_id, "Root_Chord", "XSec_1", values["vtail_root_chord"]),
                "vtail_tip_chord": _geom_value(vtail_id, "Tip_Chord", "XSec_1", values["vtail_tip_chord"]),
                "vtail_sweep": _geom_value(vtail_id, "Sweep", "XSec_1", values["vtail_sweep"]),
            }
        )

    prop_id = _find_geom("PropDisk")
    if prop_id:
        values["prop_diameter"] = _geom_value(prop_id, "Diameter", "Design", values["prop_diameter"])

    return values


def _apply_naca_four_series(wing_id: str, designation: str) -> None:
    airfoil = designation.upper()
    if not airfoil.startswith("NACA") or len(airfoil) < 8:
        return
    digits = airfoil.replace("NACA", "")
    if len(digits) != 4 or not digits.isdigit():
        return

    camber = int(digits[0]) / 100.0
    camber_loc = int(digits[1]) / 10.0 if digits[1] != "0" else 0.4
    thickness = int(digits[2:]) / 100.0

    surf = vsp.GetXSecSurf(wing_id, 0)
    for idx in range(vsp.GetNumXSec(surf)):
        vsp.ChangeXSecShape(surf, idx, vsp.XS_FOUR_SERIES)
        vsp.Update()
        xs = vsp.GetXSec(surf, idx)
        for parm_id in vsp.GetXSecParmIDs(xs):
            name = vsp.GetParmName(parm_id)
            if name == "Camber":
                vsp.SetParmVal(parm_id, camber)
            elif name == "CamberLoc":
                vsp.SetParmVal(parm_id, camber_loc)
            elif name == "ThickChord":
                vsp.SetParmVal(parm_id, thickness)
    vsp.Update()


def _ellipse_perimeter(width: float, height: float) -> float:
    a = max(width, 0.0) / 2.0
    b = max(height, 0.0) / 2.0
    if a == 0.0 and b == 0.0:
        return 0.0
    return math.pi * (3.0 * (a + b) - math.sqrt((3.0 * a + b) * (a + 3.0 * b)))


def _fuselage_wetted_area(stations: list[dict[str, float]]) -> float:
    total = 0.0
    for start, end in zip(stations, stations[1:]):
        dx = end["x_m"] - start["x_m"]
        avg_perim = 0.5 * (
            _ellipse_perimeter(start["width_m"], start["height_m"])
            + _ellipse_perimeter(end["width_m"], end["height_m"])
        )
        total += max(dx, 0.0) * avg_perim
    return total


def _set_fuselage_station(fuse_id: str, index: int, station: dict[str, float], fuse_length: float) -> None:
    surf = vsp.GetXSecSurf(fuse_id, 0)
    xs = vsp.GetXSec(surf, index)
    use_point = float(station["width_m"]) < 0.03 or float(station["height_m"]) < 0.03
    if not use_point:
        vsp.ChangeXSecShape(surf, index, vsp.XS_ELLIPSE)
        vsp.Update()
        xs = vsp.GetXSec(surf, index)
        vsp.SetXSecWidthHeight(xs, station["width_m"], station["height_m"])
    else:
        vsp.ChangeXSecShape(surf, index, vsp.XS_POINT)
        vsp.Update()
        xs = vsp.GetXSec(surf, index)

    _xsec_set(xs, "XLocPercent", station["x_m"] / fuse_length)
    _xsec_set(xs, "YLocPercent", 0.0)
    _xsec_set(xs, "ZLocPercent", station["z_center_m"] / fuse_length)
    _apply_c2_skinning(xs)


def _ensure_xsec_count(fuse_id: str, desired_count: int) -> None:
    """Insert fuselage sections by bisecting the largest current interval."""
    while True:
        surf = vsp.GetXSecSurf(fuse_id, 0)
        count = vsp.GetNumXSec(surf)
        if count >= desired_count:
            return

        xlocs = []
        for idx in range(count):
            xs = vsp.GetXSec(surf, idx)
            xloc = 0.0
            for parm_id in vsp.GetXSecParmIDs(xs):
                if vsp.GetParmName(parm_id) == "XLocPercent":
                    xloc = float(vsp.GetParmVal(parm_id))
                    break
            xlocs.append(xloc)

        largest_idx = 0
        largest_gap = -1.0
        for idx in range(count - 1):
            gap = xlocs[idx + 1] - xlocs[idx]
            if gap > largest_gap:
                largest_gap = gap
                largest_idx = idx
        vsp.InsertXSec(fuse_id, largest_idx, vsp.XS_ELLIPSE)
        vsp.Update()


def _curve_slopes(points: list[tuple[float, float]]) -> list[float]:
    """Return conservative cubic Hermite slopes with local extrema flattened."""
    if len(points) < 2:
        return [0.0 for _ in points]

    secants = []
    for idx in range(len(points) - 1):
        dx = points[idx + 1][0] - points[idx][0]
        secants.append((points[idx + 1][1] - points[idx][1]) / dx if dx else 0.0)

    slopes: list[float] = []
    for idx in range(len(points)):
        if idx == 0:
            slopes.append(secants[0])
        elif idx == len(points) - 1:
            slopes.append(secants[-1])
        elif secants[idx - 1] * secants[idx] <= 0.0:
            slopes.append(0.0)
        else:
            slopes.append(0.5 * (secants[idx - 1] + secants[idx]))
    return slopes


def _cubic_hermite_eval(points: list[tuple[float, float]], x_value: float) -> float:
    """Evaluate a piecewise cubic curve through the supplied control points."""
    if x_value <= points[0][0]:
        return points[0][1]
    if x_value >= points[-1][0]:
        return points[-1][1]

    slopes = _curve_slopes(points)
    seg_idx = 0
    for idx in range(len(points) - 1):
        if points[idx][0] <= x_value <= points[idx + 1][0]:
            seg_idx = idx
            break

    x0, y0 = points[seg_idx]
    x1, y1 = points[seg_idx + 1]
    h = x1 - x0
    if h == 0.0:
        return y0

    t = (x_value - x0) / h
    h00 = 2.0 * t**3 - 3.0 * t**2 + 1.0
    h10 = t**3 - 2.0 * t**2 + t
    h01 = -2.0 * t**3 + 3.0 * t**2
    h11 = t**3 - t**2
    return h00 * y0 + h10 * h * slopes[seg_idx] + h01 * y1 + h11 * h * slopes[seg_idx + 1]


def _sample_curve_station(
    label: str,
    x_value: float,
    top_curve: list[tuple[float, float]],
    bottom_curve: list[tuple[float, float]],
    half_width_curve: list[tuple[float, float]],
) -> dict[str, float | str]:
    top = _cubic_hermite_eval(top_curve, x_value)
    bottom = _cubic_hermite_eval(bottom_curve, x_value)
    half_width = max(0.0, _cubic_hermite_eval(half_width_curve, x_value))
    height = max(0.0, top - bottom)
    return {
        "label": label,
        "x_m": round(x_value, 4),
        "width_m": round(2.0 * half_width, 4),
        "height_m": round(height, 4),
        "z_center_m": round(0.5 * (top + bottom), 4),
        "top_z_m": round(top, 4),
        "bottom_z_m": round(bottom, 4),
        "half_width_m": round(half_width, 4),
    }


def _build_smooth_curve_fuselage() -> tuple[
    float,
    list[dict[str, float | str]],
    dict[str, list[dict[str, float]]],
]:
    """Build stations from one top, one bottom, and one symmetric side curve."""
    fuse_length = 5.65
    top_curve = [
        (0.00, 0.22),
        (0.85, 0.38),
        (1.35, 0.42),
        (1.85, 0.48),
        (2.85, 1.02),
        (3.25, 1.11),
        (4.30, 1.02),
        (5.05, 0.91),
        (5.65, 0.78),
    ]
    bottom_curve = [
        (0.00, -0.38),
        (0.85, -0.50),
        (1.35, -0.47),
        (1.85, -0.40),
        (2.85, -0.48),
        (3.25, -0.31),
        (4.30, 0.02),
        (5.05, 0.25),
        (5.65, 0.46),
    ]
    half_width_curve = [
        (0.00, 0.30),
        (0.85, 0.49),
        (1.35, 0.49),
        (1.85, 0.49),
        (2.85, 0.55),
        (3.25, 0.525),
        (4.30, 0.375),
        (5.05, 0.25),
        (5.65, 0.15),
    ]
    station_labels = [
        (0.00, "faired engine nose"),
        (0.85, "engine bay start"),
        (1.35, "engine bay center clearance"),
        (1.85, "engine bay end"),
        (2.85, "cg cockpit"),
        (3.25, "high wing saddle"),
        (4.30, "tail wake fairing"),
        (5.05, "stabilizer pedestal"),
        (5.65, "tail close"),
    ]
    stations = [
        _sample_curve_station(label, x_value, top_curve, bottom_curve, half_width_curve)
        for x_value, label in station_labels
    ]
    controls = {
        "top_curve": [{"x_m": x, "z_m": z} for x, z in top_curve],
        "bottom_curve": [{"x_m": x, "z_m": z} for x, z in bottom_curve],
        "side_half_width_curve": [{"x_m": x, "half_width_m": w} for x, w in half_width_curve],
    }
    return fuse_length, stations, controls


def _next_model_path(out_dir: Path, tag: str | None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    if tag:
        return out_dir / f"{tag}.vsp3"
    date_str = datetime.now().strftime("%m_%d_%Y")
    existing = list(out_dir.glob(f"MODEL_{date_str}_*.vsp3"))
    return out_dir / f"MODEL_{date_str}_{len(existing) + 1:02d}.vsp3"


def generate(source_model: Path, out_dir: Path, tag: str | None) -> tuple[Path, dict[str, Any]]:
    source = _extract_source_geometry(source_model)

    fuse_length, stations, curve_controls = _build_smooth_curve_fuselage()
    x_cg = 2.85
    cockpit_vertical_space = 1.50
    engine_x = 1.35
    engine_z = -0.12
    cockpit_station = next(station for station in stations if station["label"] == "cg cockpit")
    cockpit_center_z = float(cockpit_station["z_center_m"])
    wing_x = x_cg
    wing_z = 1.11
    htail_x = 5.25
    htail_z = 0.86
    vtail_x = 5.20
    vtail_z = 0.46
    prop_x = -0.06
    prop_z = engine_z

    vsp.ClearVSPModel()

    fuse_id = vsp.AddGeom("FUSELAGE")
    vsp.SetGeomName(fuse_id, "SingleSwoopFuselage")
    _set(fuse_id, "Length", "Design", fuse_length)
    _set(fuse_id, "Tess_U", "Shape", 32.0)
    _set(fuse_id, "Tess_W", "Shape", 33.0)

    # Create enough sections for the explicit smooth station profile.
    _ensure_xsec_count(fuse_id, len(stations))
    vsp.Update()

    for idx, station in enumerate(stations):
        _set_fuselage_station(fuse_id, idx, station, fuse_length)
    vsp.Update()

    wing_id = vsp.AddGeom("WING", fuse_id)
    vsp.SetGeomName(wing_id, "MainWing")
    _set(wing_id, "TotalSpan", "WingGeom", source["wing_span"])
    _set(wing_id, "Root_Chord", "XSec_1", source["wing_root_chord"])
    _set(wing_id, "Tip_Chord", "XSec_1", source["wing_tip_chord"])
    _set(wing_id, "Sweep", "XSec_1", source["wing_sweep"])
    _set(wing_id, "Dihedral", "XSec_1", source["wing_dihedral"])
    _set(wing_id, "Twist", "XSec_1", source["wing_twist"])
    _set(wing_id, "X_Rel_Location", "XForm", wing_x)
    _set(wing_id, "Z_Rel_Location", "XForm", wing_z)
    _apply_naca_four_series(wing_id, source["wing_airfoil"])
    vsp.Update()

    htail_id = vsp.AddGeom("WING", fuse_id)
    vsp.SetGeomName(htail_id, "HorizTail")
    _set(htail_id, "TotalSpan", "WingGeom", source["htail_span"])
    _set(htail_id, "Root_Chord", "XSec_1", source["htail_root_chord"])
    _set(htail_id, "Tip_Chord", "XSec_1", source["htail_tip_chord"])
    _set(htail_id, "Sweep", "XSec_1", source["htail_sweep"])
    _set(htail_id, "X_Rel_Location", "XForm", htail_x)
    _set(htail_id, "Z_Rel_Location", "XForm", htail_z)
    vsp.Update()

    vtail_id = vsp.AddGeom("WING", fuse_id)
    vsp.SetGeomName(vtail_id, "VertTail")
    sym_parm = vsp.FindParm(vtail_id, "Sym_Planar_Flag", "Sym")
    if sym_parm != "":
        vsp.SetParmVal(sym_parm, 0)
    _set(vtail_id, "TotalSpan", "WingGeom", source["vtail_height"])
    _set(vtail_id, "Root_Chord", "XSec_1", source["vtail_root_chord"])
    _set(vtail_id, "Tip_Chord", "XSec_1", source["vtail_tip_chord"])
    _set(vtail_id, "Sweep", "XSec_1", source["vtail_sweep"])
    _set(vtail_id, "X_Rel_Rotation", "XForm", 90.0)
    _set(vtail_id, "X_Rel_Location", "XForm", vtail_x)
    _set(vtail_id, "Z_Rel_Location", "XForm", vtail_z)
    vsp.Update()

    try:
        prop_id = vsp.AddGeom("PROP", fuse_id)
        vsp.SetGeomName(prop_id, "PropDisk")
        if not _set(prop_id, "Diameter", "Design", source["prop_diameter"]):
            _set(prop_id, "Diameter", "PropGeom", source["prop_diameter"])
        _set(prop_id, "X_Rel_Location", "XForm", prop_x)
        _set(prop_id, "Z_Rel_Location", "XForm", prop_z)
    except Exception as exc:
        print(f"[warn] PROP geom failed ({exc}); using thin wing disk", file=sys.stderr)
        prop_id = vsp.AddGeom("WING", fuse_id)
        vsp.SetGeomName(prop_id, "PropDisk")
        _set(prop_id, "TotalSpan", "WingGeom", source["prop_diameter"])
        _set(prop_id, "Root_Chord", "XSec_1", 0.05)
        _set(prop_id, "Tip_Chord", "XSec_1", 0.05)
        _set(prop_id, "X_Rel_Location", "XForm", prop_x)
        _set(prop_id, "Z_Rel_Location", "XForm", prop_z)
    vsp.Update()

    out_path = _next_model_path(out_dir, tag)
    vsp.WriteVSPFile(str(out_path), 0)

    wing_area = source["wing_span"] * 0.5 * (source["wing_root_chord"] + source["wing_tip_chord"])
    aspect_ratio = source["wing_span"] ** 2 / wing_area
    wing_mac = (2.0 / 3.0) * (
        (
            source["wing_root_chord"] ** 2
            + source["wing_root_chord"] * source["wing_tip_chord"]
            + source["wing_tip_chord"] ** 2
        )
        / (source["wing_root_chord"] + source["wing_tip_chord"])
    )
    htail_area = source["htail_span"] * 0.5 * (source["htail_root_chord"] + source["htail_tip_chord"])
    vtail_area = source["vtail_height"] * 0.5 * (source["vtail_root_chord"] + source["vtail_tip_chord"])
    vstall_est = math.sqrt(2.0 * MTOW_N / (RHO_SL * wing_area * CL_MAX_ANALYTIC))

    wing_wetted = 2.0 * wing_area * 1.04
    htail_wetted = 2.0 * htail_area * 1.02
    vtail_wetted = 2.0 * vtail_area * 1.02
    fuselage_wetted = _fuselage_wetted_area(stations)
    total_wetted = wing_wetted + htail_wetted + vtail_wetted + fuselage_wetted
    empty_mass = total_wetted * SKIN_DENSITY + ENGINE_MASS_KG + SYSTEMS_MASS_KG

    cockpit_top = float(cockpit_station.get("top_z_m", cockpit_center_z + 0.5 * cockpit_vertical_space))
    engine_start_x = 0.85
    engine_end_x = 1.85
    engine_stations = [
        station
        for station in stations
        if engine_start_x <= float(station["x_m"]) <= engine_end_x
    ]
    engine_compartment = {
        "required_length_m": 0.8,
        "required_width_m": 0.6,
        "required_height_m": 0.6,
        "x_start_m": engine_start_x,
        "x_end_m": engine_end_x,
        "length_m": round(engine_end_x - engine_start_x, 3),
        "min_width_m": round(min(float(station["width_m"]) for station in engine_stations), 3),
        "min_height_m": round(min(float(station["height_m"]) for station in engine_stations), 3),
    }
    engine_compartment["meets_spec"] = (
        engine_compartment["length_m"] >= engine_compartment["required_length_m"]
        and engine_compartment["min_width_m"] >= engine_compartment["required_width_m"]
        and engine_compartment["min_height_m"] >= engine_compartment["required_height_m"]
    )

    htail_aft_te = max(
        htail_x + source["htail_root_chord"],
        htail_x
        + math.tan(math.radians(source["htail_sweep"])) * (0.5 * source["htail_span"])
        + source["htail_tip_chord"],
    )
    vtail_aft_te = max(
        vtail_x + source["vtail_root_chord"],
        vtail_x
        + math.tan(math.radians(source["vtail_sweep"])) * source["vtail_height"]
        + source["vtail_tip_chord"],
    )
    stabilizer_aftmost_te = max(htail_aft_te, vtail_aft_te)
    tail_extension = fuse_length - stabilizer_aftmost_te
    summary = {
        "model_file": str(out_path),
        "source_model": str(source_model),
        "configuration": "single_smooth_full_fuselage",
        "replaces_configuration": "pod_and_boom",
        "single_fuselage_structure": True,
        "removed_separate_tail_boom": True,
        "wing_area_m2": round(wing_area, 2),
        "aspect_ratio": round(aspect_ratio, 2),
        "wing_mac_m": round(wing_mac, 3),
        "htail_area_m2": round(htail_area, 2),
        "vtail_area_m2": round(vtail_area, 2),
        "prop_diameter_m": round(source["prop_diameter"], 3),
        "fuse_length_m": fuse_length,
        "fuse_max_width_m": max(s["width_m"] for s in stations),
        "fuse_max_height_m": max(s["height_m"] for s in stations),
        "fuselage_stations": stations,
        "fuselage_curve_method": "piecewise_cubic_hermite",
        "fuselage_curve_degree": 3,
        "fuselage_curve_controls": curve_controls,
        "openvsp_skinning_continuity": "C2",
        "openvsp_skinning_method": "ResetXSecSkinParms plus SetXSecContinuity(xs, 2) plus explicit C2 continuity on top/right/bottom/left",
        "x_cg_m": x_cg,
        "pilot_x_m": x_cg,
        "cockpit_vertical_space_m": cockpit_vertical_space,
        "cockpit_top_z_m": round(cockpit_top, 3),
        "engine_x_m": engine_x,
        "engine_z_m": engine_z,
        "engine_compartment": engine_compartment,
        "wing_x_m": wing_x,
        "wing_z_m": wing_z,
        "wing_above_cockpit_top_m": round(wing_z - cockpit_top, 3),
        "wing_high_attached_to_fuselage": wing_z >= cockpit_top,
        "htail_x_m": htail_x,
        "htail_z_m": htail_z,
        "horizontal_tail_aft_te_m": round(htail_aft_te, 3),
        "tail_buffet_design": "horizontal tail placed aft and slightly below high wing root line to sample separated root wake at stall onset",
        "vtail_x_m": vtail_x,
        "vtail_z_m": vtail_z,
        "vertical_tail_aft_te_m": round(vtail_aft_te, 3),
        "stabilizer_aftmost_te_m": round(stabilizer_aftmost_te, 3),
        "fuselage_extension_past_stabilizer_te_m": round(tail_extension, 3),
        "mtow_kg": MTOW_KG,
        "vstall_est_ms": round(vstall_est, 2),
        "vstall_limit_ms": VSTALL_LIM,
        "vstall_margin_ok": vstall_est < VSTALL_LIM,
        "wingspan_m": source["wing_span"],
        "wingspan_limit_m": 15.0,
        "wingspan_ok": source["wing_span"] <= 15.0,
        "total_wetted_area_m2": round(total_wetted, 2),
        "fuselage_wetted_area_m2": round(fuselage_wetted, 2),
        "empty_mass_est_kg": round(empty_mass, 1),
        "empty_mass_spec_kg": EMPTY_MASS_SPEC,
        "empty_mass_ok": empty_mass < EMPTY_MASS_SPEC,
        "wing_airfoil": source["wing_airfoil"],
        "notes": [
            "Single fuselage body replaces CockpitPod plus TailBoom.",
            "Cockpit station is centered on x_cg_m and provides 1.5 m vertical interior envelope by geometry.",
            "Fuselage top, bottom, and side stations are sampled from cubic Hermite curves with OpenVSP skin parameters reset and C2 enforced on all four section edges.",
            "Engine compartment is deliberately larger than the 0.8 m by 0.6 m by 0.6 m specification envelope to leave visible installation room inside the elliptical shell.",
            "Engine/prop line is below cockpit centerline.",
            "Wing is mounted at the fuselage crown, above cockpit top, while still intersecting the upper fuselage.",
            "Fuselage tail closeout ends at or slightly ahead of the aft stabilizer trailing edge instead of projecting past it.",
        ],
    }
    out_path.with_suffix(".json").write_text(json.dumps(summary, indent=2))
    return out_path, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source_model",
        nargs="?",
        default=str(AIRCRAFT_DIR / "MODEL_05_02_2026_05.vsp3"),
        help="Source .vsp3 model to redesign. Defaults to MODEL_05_02_2026_05.vsp3.",
    )
    parser.add_argument("--out-dir", type=Path, default=AIRCRAFT_DIR)
    parser.add_argument("--tag", default=None, help="Optional fixed output stem for tests.")
    args = parser.parse_args()

    source_model = Path(args.source_model).resolve()
    if not source_model.exists():
        print(f"ERROR: source model not found: {source_model}", file=sys.stderr)
        return 1

    try:
        out_path, summary = generate(source_model, args.out_dir.resolve(), args.tag)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("BEGIN_JSON")
    print(json.dumps(summary, indent=2))
    print("END_JSON")
    print(f"MODEL_FILE:{out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
