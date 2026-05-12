"""
Parasite drag analysis using OpenVSP's built-in ParasiteDrag analysis.

Loads a .vsp3 model, runs the parasite drag analysis at cruise conditions,
and writes a per-component drag breakdown report to:
    SIMULATION/results/<model_stem>_parasite_drag.json

Prints a JSON summary to stdout.

Run via openvsp-python:
    openvsp-python analyze.py
    openvsp-python analyze.py path/to/MODEL_xx.vsp3
"""

import json
import math
import sys
from pathlib import Path

import openvsp as vsp

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR  = PROJECT_ROOT / "SIMULATION" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Spec constants ─────────────────────────────────────────────────────────────
CRUISE_MS   = 52.2     # m/s cruise speed (from recent best models)
ALT_FT      = 0.0     # sea level (ft — ParasiteDrag uses feet for altitude)
MTOW_KG     = 218.0
SREF_DEFAULT = 4.21   # m² fallback wing reference area

# ── Find model ─────────────────────────────────────────────────────────────────
if len(sys.argv) > 1:
    model_path = Path(sys.argv[1]).resolve()
else:
    candidates = sorted(AIRCRAFT_DIR.glob("MODEL_*.vsp3"),
                        key=lambda p: p.stat().st_mtime)
    if not candidates:
        print("ERROR: no MODEL_*.vsp3 in AIRCRAFT/", file=sys.stderr)
        sys.exit(1)
    model_path = candidates[-1]

print(f"Model: {model_path.name}", file=sys.stderr)

# Read companion JSON for geometry metadata
companion = model_path.with_suffix(".json")
sref = SREF_DEFAULT
cruise_ms = CRUISE_MS
if companion.exists():
    geom = json.loads(companion.read_text())
    sref = geom.get("wing_area_m2", SREF_DEFAULT)

print(f"Sref={sref:.3f} m², Vinf={cruise_ms:.1f} m/s, Alt=0 m (SL)", file=sys.stderr)

# ── Load model ─────────────────────────────────────────────────────────────────
vsp.ClearVSPModel()
vsp.ReadVSPFile(str(model_path))
vsp.Update()

# ── Configure and run ParasiteDrag analysis ────────────────────────────────────
vsp.SetAnalysisInputDefaults("ParasiteDrag")

# Reference area
vsp.SetIntAnalysisInput("ParasiteDrag", "RefFlag", [0])   # 0 = manual Sref
vsp.SetDoubleAnalysisInput("ParasiteDrag", "Sref", [float(sref)])

# Flight condition: sea-level cruise
vsp.SetIntAnalysisInput("ParasiteDrag", "VelocityUnit", [vsp.V_UNIT_M_S])
vsp.SetDoubleAnalysisInput("ParasiteDrag", "Vinf", [float(cruise_ms)])
vsp.SetDoubleAnalysisInput("ParasiteDrag", "Altitude", [ALT_FT])   # 0 ft = sea level

# Turbulent boundary layer (conservative)
vsp.SetIntAnalysisInput("ParasiteDrag", "RecomputeGeom", [1])

# Suppress CSV file output (write to null)
vsp.SetStringAnalysisInput("ParasiteDrag", "FileName", ["NUL"])

res_id = vsp.ExecAnalysis("ParasiteDrag")

# ── Extract results ────────────────────────────────────────────────────────────
def _doubles(name):
    return list(vsp.GetDoubleResults(res_id, name, 0))

def _strings(name):
    try:
        return list(vsp.GetStringResults(res_id, name, 0))
    except Exception:
        return []

def _ints(name):
    try:
        return list(vsp.GetIntResults(res_id, name, 0))
    except Exception:
        return []

# Per-component fields
labels    = _strings("Comp_Label")
swet      = _doubles("Comp_Swet")
cd_comp   = _doubles("Comp_CD")
cf_comp   = _doubles("Comp_Cf")
ff_out    = _doubles("Comp_FFOut")
fine_rat  = _doubles("Comp_FineRat")
pct_total = _doubles("Comp_PercTotalCD")
q_int     = _doubles("Comp_Q")

# Total
total_cd_list = _doubles("Total_CD_Total")
total_cd = total_cd_list[0] if total_cd_list else float("nan")

# ── Build component report ─────────────────────────────────────────────────────
n_comp = len(labels)
components = []
for i in range(n_comp):
    components.append({
        "name":        labels[i]   if i < len(labels)    else f"comp_{i}",
        "Swet_m2":     round(swet[i],    4) if i < len(swet)     else None,
        "CD":          round(cd_comp[i], 6) if i < len(cd_comp)  else None,
        "Cf":          round(cf_comp[i], 6) if i < len(cf_comp)  else None,
        "FF":          round(ff_out[i],  4) if i < len(ff_out)   else None,
        "fineness":    round(fine_rat[i],2) if i < len(fine_rat) else None,
        "pct_total":   round(pct_total[i] * 100.0, 1) if i < len(pct_total) else None,
        "Q_interf":    round(q_int[i],   3) if i < len(q_int)    else None,
    })

# Sort by CD contribution descending
components.sort(key=lambda c: c.get("CD") or 0.0, reverse=True)

# ── Streamlining recommendations ──────────────────────────────────────────────
recommendations = []
for c in components:
    ff = c.get("FF") or 0.0
    fr = c.get("fineness") or 0.0
    name = c["name"]
    pct  = c.get("pct_total") or 0.0

    if ff > 1.8 and fr < 5:
        recommendations.append(
            f"{name}: form factor {ff:.2f} is high (fineness {fr:.1f}). "
            f"Elongate or streamline to reach fineness 5-8."
        )
    elif ff > 1.3:
        recommendations.append(
            f"{name}: form factor {ff:.2f} suggests blunt shape. "
            f"Improve aft taper to reduce base drag."
        )
    if pct > 30.0:
        recommendations.append(
            f"{name} contributes {pct:.0f}% of parasite drag — "
            f"highest-priority drag reduction target."
        )

# Minimum drag target (Sears-Haack reference)
# For an axisymmetric body: CD_min = 9*pi^2 / (2 * (L/D)^2) based on volume
# For our fuselage: rough Sears-Haack comparison
fuse_comp = next((c for c in components if "pod" in c["name"].lower()
                  or "fuse" in c["name"].lower() or "boom" in c["name"].lower()), None)
if fuse_comp and fuse_comp.get("fineness"):
    fr_actual = fuse_comp["fineness"]
    ff_ideal_fr = 1.0 + 60.0 / max(fr_actual ** 3, 1.0) + fr_actual / 400.0
    if fuse_comp.get("FF") and fuse_comp["FF"] > ff_ideal_fr * 1.1:
        recommendations.append(
            f"Fuselage form factor {fuse_comp['FF']:.2f} exceeds fineness-based optimum "
            f"{ff_ideal_fr:.2f} at FR={fr_actual:.1f} — nose/tail shaping needed."
        )

# ── Assemble report ────────────────────────────────────────────────────────────
report = {
    "model":          model_path.name,
    "cruise_ms":      cruise_ms,
    "sref_m2":        sref,
    "altitude_m":     0.0,
    "total_CD_parasite": round(total_cd, 6),
    "total_drag_N":   round(0.5 * 1.225 * cruise_ms**2 * sref * total_cd, 2),
    "components":     components,
    "recommendations": recommendations,
}

out_path = RESULTS_DIR / f"{model_path.stem}_parasite_drag.json"
out_path.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
print(f"\nWrote: {out_path}", file=sys.stderr)
