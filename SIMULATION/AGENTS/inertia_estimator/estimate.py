"""
Component-based mass distribution and inertia estimator.

Reads the companion geometry JSON produced by generate.py and constructs
a component breakdown of mass, center of gravity, and moments of inertia.
The outputs feed the dynamic stability analyzer.

No OpenVSP API is required — run with plain Python 3.

Run:
    python estimate.py
    python estimate.py path/to/MODEL_xx.json

Output: SIMULATION/results/<model_stem>_inertia.json
"""

import json
import math
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR  = PROJECT_ROOT / "SIMULATION" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Spec constants (SPECIFICATION.md) ─────────────────────────────────────────
MTOW_KG        = 218.0
ENGINE_MASS_KG = 40.0
SYSTEMS_MASS_KG = 8.0
USEFUL_LOAD_KG = 117.0   # pilot + baggage
SKIN_DENSITY   = 6.0     # kg/m²

# ── Find companion geometry JSON ───────────────────────────────────────────────
if len(sys.argv) > 1:
    geom_path = Path(sys.argv[1]).resolve()
    if geom_path.suffix == ".vsp3":
        geom_path = geom_path.with_suffix(".json")
else:
    candidates = sorted(AIRCRAFT_DIR.glob("MODEL_*.json"),
                        key=lambda p: p.stat().st_mtime)
    if not candidates:
        print("ERROR: no MODEL_*.json in AIRCRAFT/", file=sys.stderr)
        sys.exit(1)
    geom_path = candidates[-1]

if not geom_path.exists():
    print(f"ERROR: geometry JSON not found: {geom_path}", file=sys.stderr)
    sys.exit(1)

geom = json.loads(geom_path.read_text())
model_stem = geom_path.stem
print(f"Geometry: {geom_path.name}", file=sys.stderr)

# ── Extract geometry fields ────────────────────────────────────────────────────
L           = float(geom.get("total_length_m",    5.0))
wing_area   = float(geom.get("wing_area_m2",      4.2))
wing_span   = float(geom.get("wing_span_m",       geom.get("wingspan_m", 9.8)))
wing_mac    = float(geom.get("wing_mac_m",        wing_area / wing_span))
wing_x      = float(geom.get("wing_x_m",          1.8))

htail_area  = float(geom.get("htail_area_m2",     0.43))
htail_mac   = float(geom.get("htail_mac_m",       0.27))
htail_x     = float(geom.get("htail_x_m",         4.5))

vtail_area  = float(geom.get("vtail_area_m2",     0.21))
vtail_x     = float(geom.get("vtail_x_m",         4.3))
vtail_root_c = float(geom.get("vtail_root_chord_m", 0.40))

fuse_wetted  = float(geom.get("fuse_wetted_m2",   10.0))
wing_wetted  = float(geom.get("wing_wetted_m2",   8.7))
htail_wetted = 2.0 * htail_area * 1.02
vtail_wetted = 2.0 * vtail_area * 1.02

x_engine    = float(geom.get("x_engine_m",        0.70))
cockpit_x   = float(geom.get("cockpit_x_m",       wing_x))
empty_mass  = float(geom.get("empty_mass_est_kg", 170.0))

# ── Component mass table ───────────────────────────────────────────────────────
# Each entry: (label, mass_kg, x_m, y_m, z_m)
# y = 0 for symmetric components; wing half-span contributions handled via
# Ixx formula instead of individual y offsets.
PILOT_Z = -0.30   # pilot CG below fuselage centerline (seated)

fuel_kg = max(0.0, MTOW_KG - empty_mass - USEFUL_LOAD_KG)
x_fuel  = min(x_engine + 0.25, wing_x - 0.10)

components = [
    # label,              mass,                    x,                                y,    z
    ("fuselage_skin",     fuse_wetted * SKIN_DENSITY,  L / 2.0,                     0.0,  0.0),
    ("wing_skin",         wing_wetted * SKIN_DENSITY,  wing_x + wing_mac * 0.25,    0.0,  0.0),
    ("htail_skin",        htail_wetted * SKIN_DENSITY, htail_x + htail_mac * 0.25,  0.0,  0.0),
    ("vtail_skin",        vtail_wetted * SKIN_DENSITY, vtail_x + vtail_root_c * 0.25, 0.0, 0.15),
    ("engine",            ENGINE_MASS_KG,              x_engine,                    0.0,  0.0),
    ("systems",           SYSTEMS_MASS_KG,             L * 0.30,                    0.0,  0.0),
    ("fuel",              fuel_kg,                     x_fuel,                      0.0,  0.0),
    ("pilot_and_payload", USEFUL_LOAD_KG,              cockpit_x,                   0.0,  PILOT_Z),
]

total_mass = sum(c[1] for c in components)

# ── Center of gravity ─────────────────────────────────────────────────────────
cg_x = sum(c[1] * c[2] for c in components) / total_mass
cg_y = 0.0   # symmetric aircraft
cg_z = sum(c[1] * c[4] for c in components) / total_mass

# ── Moments of inertia ─────────────────────────────────────────────────────────
# Iyy (pitch): dominated by mass distribution along x-axis
Iyy = sum(c[1] * (c[2] - cg_x)**2 for c in components)

# Ixx (roll): dominated by wing span distribution
# Wing skin treated as uniform spanwise plate: Ixx_wing = m_wing * b² / 12
m_wing = wing_wetted * SKIN_DENSITY
Ixx_wing = m_wing * wing_span**2 / 12.0
Ixx_other = sum(c[1] * ((c[4] - cg_z)**2) for c in components
                if c[0] != "wing_skin")
Ixx = Ixx_wing + Ixx_other

# Izz (yaw): combination of span and length contributions
# Perpendicular axis theorem (approximate for near-flat distribution):
#   Izz ≈ Ixx + Iyy
# This overestimates for very flat aircraft but is appropriate here.
Izz = Ixx + Iyy

# Ixz (cross product, pitch-roll coupling)
# For symmetric aircraft with wing at mid-height, approximately zero.
Ixz = 0.0

# ── Fuel load range (for range check) ─────────────────────────────────────────
# Spec: 30.3 L/hr burn rate, cruise speed TBD → fuel capacity based on range
# This gives a max fuel mass if the aircraft were lighter:
FUEL_DENSITY_KG_L = 0.72   # avgas density
FUEL_BURN_L_HR    = 30.3
RANGE_KM          = 1100.0

# ── Report ────────────────────────────────────────────────────────────────────
report = {
    "model":             model_stem + ".vsp3",
    "geom_source":       geom_path.name,
    "total_mass_kg":     round(total_mass, 2),
    "empty_mass_kg":     round(empty_mass, 1),
    "fuel_kg":           round(fuel_kg, 1),
    "useful_load_kg":    USEFUL_LOAD_KG,
    "cg_x_m":           round(cg_x, 4),
    "cg_y_m":           round(cg_y, 4),
    "cg_z_m":           round(cg_z, 4),
    "Iyy_kgm2":         round(Iyy, 2),
    "Ixx_kgm2":         round(Ixx, 2),
    "Izz_kgm2":         round(Izz, 2),
    "Ixz_kgm2":         round(Ixz, 2),
    "components": [
        {
            "label":   c[0],
            "mass_kg": round(c[1], 2),
            "x_m":     round(c[2], 3),
            "z_m":     round(c[4], 3),
        }
        for c in components
    ],
    "notes": [
        "Wing Ixx treated as uniform spanwise plate: m_wing * b^2 / 12",
        "Izz approximated as Ixx + Iyy (perpendicular axis theorem)",
        "Fuel mass = max(0, MTOW - empty_mass - useful_load); placed at x_fuel",
        "CG at MTOW including pilot and full fuel load",
    ],
}

out_file = RESULTS_DIR / f"{model_stem}_inertia.json"
out_file.write_text(json.dumps(report, indent=2))

print(f"RESULTS_FILE:{out_file}")
print("BEGIN_JSON")
print(json.dumps(report, indent=2))
print("END_JSON")
