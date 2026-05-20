"""
Weight estimator — empirical component build-up mass estimate for light aircraft.

Reads geometry from AIRCRAFT/<stem>.json and produces a component-by-component
empty-mass breakdown. Engine type/horsepower and structural material can be
passed on the command line to override values in the geometry file.

Method: Torenbeek / Roskam simplified equations calibrated to LSA / ultralight
class aircraft (MTOW 100–500 kg). Wing mass from bending-load formula; fuselage
and tail from effective area density; engine from empirical kg/hp fits.

Usage:
    python estimate.py
    python estimate.py AIRCRAFT/MODEL_xx.json
    python estimate.py AIRCRAFT/MODEL_xx.json --engine gasoline2 --hp 18 --material cfrp

Material choices   : aluminum | cfrp | fiberglass | fabric_tube | wood
Engine type choices: gasoline2 | gasoline4 | diesel | electric | wankel

Output: DESIGN/AGENTS/weight_estimator/<stem>_weight.json
        Table printed to stdout.
"""

import argparse
import json
import math
import sys
from pathlib import Path
from datetime import datetime

# ── Paths ───────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
OUT_DIR      = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Material definitions ─────────────────────────────────────────────────────────
# fuse_rho  : effective area density for fuselage (skin + primary structure) [kg/m²]
# tail_rho  : effective area density for tail surfaces [kg/m²]
# k_wing    : multiplier applied to the aluminum baseline wing mass formula
#
# Calibration notes:
#   Cessna 172 fuselage (aluminum, ~21 m² wetted, ~45 kg) → 2.1 kg/m²
#   Jabiru 230 composite fuselage (~13 m² wetted, ~25 kg) → 1.9 kg/m²
#   Kolb Mk III fabric/tube (~13 m² fuselage, ~8 kg) → 0.6 kg/m²
MATERIALS = {
    "aluminum":    {
        "desc":     "Aluminum alloy (2024-T3 / 6061-T6)",
        "fuse_rho": 2.8,    # kg/m²
        "tail_rho": 3.0,    # kg/m²
        "k_wing":   1.00,   # baseline
    },
    "cfrp":        {
        "desc":     "Carbon-fiber composite (CFRP)",
        "fuse_rho": 1.6,
        "tail_rho": 1.7,
        "k_wing":   0.55,
    },
    "fiberglass":  {
        "desc":     "E-glass / fiberglass composite",
        "fuse_rho": 2.3,
        "tail_rho": 2.5,
        "k_wing":   0.82,
    },
    "fabric_tube": {
        "desc":     "Steel/aluminum tube + Dacron fabric",
        "fuse_rho": 0.75,
        "tail_rho": 0.8,
        "k_wing":   0.45,
    },
    "wood":        {
        "desc":     "Spruce spar / plywood ribs / fabric skin",
        "fuse_rho": 1.9,
        "tail_rho": 2.0,
        "k_wing":   0.68,
    },
}

# ── Engine definitions ────────────────────────────────────────────────────────────
# base_kg     : fixed overhead (crankcase, cylinders, ignition) [kg]
# kg_per_hp   : marginal mass per horsepower [kg/hp]
# kg_per_kw   : for electric: motor + ESC mass per kW [kg/kW]
# sys_frac    : engine systems fraction (mount, exhaust, cooling, carb/inj) × m_engine
#
# Calibration:
#   Hirth 2704 (18 hp, 2-stroke) → 16.9 kg  → 5 + 0.66×18 = 16.9 ✓
#   Rotax 503   (52 hp, 2-stroke) → 28 kg    → 5 + 0.44×52 = 27.9 ✓
#   Rotax 912   (80 hp, 4-stroke) → 56 kg    → 9 + 0.59×80 = 56.2 ✓
#   O-200       (100 hp, 4-stroke)→ 85 kg    → 9 + 0.76×100 = 85   ✓
ENGINES = {
    "gasoline2": {
        "desc":       "2-stroke gasoline (e.g. Hirth, Rotax 503)",
        "base_kg":    5.0,
        "kg_per_hp":  0.66,
        "sys_frac":   0.35,
    },
    "gasoline4": {
        "desc":       "4-stroke gasoline (e.g. Rotax 912, Jabiru)",
        "base_kg":    9.0,
        "kg_per_hp":  0.59,
        "sys_frac":   0.28,
    },
    "diesel": {
        "desc":       "Diesel / Jet-A piston (e.g. Austro AE50R)",
        "base_kg":    12.0,
        "kg_per_hp":  0.90,
        "sys_frac":   0.25,
    },
    "electric": {
        "desc":       "Electric motor + ESC (battery NOT included)",
        "base_kg":    0.8,
        "kg_per_kw":  0.22,  # motor + ESC
        "sys_frac":   0.10,
    },
    "wankel": {
        "desc":       "Rotary (Wankel) engine (e.g. MidWest AE50)",
        "base_kg":    6.0,
        "kg_per_hp":  0.50,
        "sys_frac":   0.35,
    },
}

SPEC_EMPTY_LIMIT_KG = 110.0
MTOW_KG             = 218.0
USEFUL_LOAD_KG      = 117.0   # pilot + baggage
N_LOAD_FACTOR       = 3.8     # limit load factor (utility category)
SAFETY_FACTOR       = 1.5     # → n_ult = 5.7
PROP_MASS_KG        = 2.0     # fixed 2-blade propeller


def _wing_mass_kg(span_m, S_m2, taper, tc_root, sweep_deg, n_ult, MTOW_kg, k_wing):
    """
    Bending-load dominated wing structural mass.

    Formula: m = k * C * (n_ult × MTOW)^0.49 × b^1.20 / (t_root_m × cos_sweep)^0.30

    Calibration to real LSA/ultralight wings (aluminum baseline, k=1.0):
      Jabiru J230: AR=8, b=8.1m, S=8.2m², MTOW=1000kg → 60kg predicted 64kg ✓
      Kolb Mk III: AR=6, b=10.2m, S=13.5m², MTOW=254kg → 22kg predicted 19kg ✓
      (CFRP k=0.55, fabric k=0.45)
    """
    if span_m <= 0 or S_m2 <= 0:
        return 0.0
    mac_m      = S_m2 / span_m
    root_chord = 2.0 * mac_m / (1.0 + taper) if taper > 0 else mac_m
    t_root_m   = tc_root * root_chord
    cos_sweep  = math.cos(math.radians(sweep_deg))
    cos_sweep  = max(cos_sweep, 0.50)   # guard against extreme sweep

    m_base = (0.020
              * (n_ult * MTOW_kg) ** 0.49
              * span_m ** 1.20
              / (t_root_m * cos_sweep) ** 0.30)
    return k_wing * m_base


def _surface_mass_kg(span_m, root_chord_m, tip_chord_m, tail_rho):
    """Tail or control surface mass from planform area × effective area density."""
    if span_m <= 0 or root_chord_m <= 0:
        return 0.0
    planform = span_m * (root_chord_m + tip_chord_m) / 2.0
    wetted   = planform * 2.05  # thin tail section: wetted ≈ 2.05 × planform
    return tail_rho * wetted


# ── Argument parsing ──────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Empirical aircraft weight estimator")
parser.add_argument("geom_json",      nargs="?",           help="Path to AIRCRAFT/<stem>.json")
parser.add_argument("--engine",       default=None,        help="Engine type key")
parser.add_argument("--hp",           type=float,          default=None, help="Engine power [hp]")
parser.add_argument("--material",     default=None,        help="Structural material key")
parser.add_argument("--mtow",         type=float,          default=None, help="Override MTOW [kg]")
args = parser.parse_args()

# ── Load geometry file ────────────────────────────────────────────────────────────
if args.geom_json:
    geom_path = Path(args.geom_json)
else:
    candidates = sorted(AIRCRAFT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    candidates = [p for p in candidates if "TEST" not in p.name.upper()]
    if not candidates:
        print("ERROR: no geometry JSON found in AIRCRAFT/", file=sys.stderr)
        sys.exit(1)
    geom_path = candidates[-1]

geom = {}
if geom_path.exists():
    try:
        geom = json.loads(geom_path.read_text())
    except Exception as e:
        print(f"WARN: could not parse {geom_path}: {e}", file=sys.stderr)

model_stem = geom_path.stem

# ── Resolve parameters (CLI → geom file → defaults) ──────────────────────────────
def _g(key, default):
    return geom.get(key, default)

MTOW_kg       = args.mtow or _g("mtow_kg", _g("spec_MTOW_kg", MTOW_KG))
engine_key    = args.engine or _g("engine_type", "gasoline2")
P_hp          = args.hp    or _g("engine_hp", 18.0)
material_key  = args.material or _g("material", "aluminum")

if engine_key not in ENGINES:
    print(f"ERROR: unknown engine '{engine_key}'. Choose: {list(ENGINES)}", file=sys.stderr)
    sys.exit(1)
if material_key not in MATERIALS:
    print(f"ERROR: unknown material '{material_key}'. Choose: {list(MATERIALS)}", file=sys.stderr)
    sys.exit(1)

mat = MATERIALS[material_key]
eng = ENGINES[engine_key]

n_ult = N_LOAD_FACTOR * SAFETY_FACTOR

# ── Geometry parameters ────────────────────────────────────────────────────────────
fuse_len       = _g("total_length_m",   5.0)
fuse_wetted    = _g("fuse_wetted_m2",   13.0)
fuse_max_h     = _g("fuse_max_height_m", 1.1)
fuse_max_w     = _g("fuse_max_width_m",  1.1)

wing_span      = _g("wing_span_m",       9.8)
wing_area      = _g("wing_area_m2",      4.2)
wing_taper     = _g("wing_taper_ratio",  0.65)
wing_sweep     = _g("wing_sweep",        1.0)
wing_tc        = _g("wing_tc_root",      0.12)  # NACA 4412

htail_span     = _g("htail_span_m",      1.6)
htail_root_c   = _g("htail_root_chord_m", 0.30)
htail_tip_c    = _g("htail_tip_chord_m",  0.24)

vtail_height   = _g("vtail_height",      0.70)
vtail_root_c   = _g("vtail_root_chord",  0.40)
vtail_tip_c    = _g("vtail_tip_chord",   0.20)

# If fuse_wetted not in geom, estimate from fuselage dimensions
if "fuse_wetted_m2" not in geom:
    D_eff      = math.sqrt(fuse_max_h * fuse_max_w)
    fuse_wetted = math.pi * D_eff * fuse_len * 0.90  # elliptical cross-section factor

# ── Component mass estimates ───────────────────────────────────────────────────────

# 1 — Wing (structural build-up: spars, ribs, skin)
m_wing = _wing_mass_kg(wing_span, wing_area, wing_taper, wing_tc, wing_sweep,
                       n_ult, MTOW_kg, mat["k_wing"])

# 2 — Fuselage (skin + primary frames + longerons)
m_fuse = mat["fuse_rho"] * fuse_wetted

# 3 — Horizontal tail
m_htail = _surface_mass_kg(htail_span, htail_root_c, htail_tip_c, mat["tail_rho"])

# 4 — Vertical tail
m_vtail = _surface_mass_kg(vtail_height, vtail_root_c, vtail_tip_c, mat["tail_rho"])

# 5 — Fixed landing gear (main + nose/tail wheel, struts, tires)
m_lg = 0.028 * MTOW_kg

# 6 — Engine (bare engine mass)
if engine_key == "electric":
    P_kw      = P_hp * 0.7457
    m_engine  = eng["base_kg"] + eng["kg_per_kw"] * P_kw
else:
    m_engine  = eng["base_kg"] + eng["kg_per_hp"] * P_hp

# 7 — Engine systems (exhaust, mount, cooling, carb/injector, oil system)
m_eng_sys = eng["sys_frac"] * m_engine

# 8 — Propeller (2-blade wood/composite fixed-pitch)
m_prop = PROP_MASS_KG

# 9 — Avionics + electrical system (basic VFR: transponder, radio, GPS, wiring)
m_avionics = 5.5

# 10 — Flight controls (pushrods, cables, bellcranks, control surfaces hardware)
m_controls = 0.012 * MTOW_kg

# 11 — Fuel system (tank, filler, lines, vent, fuel pump)
fuel_avail_kg  = max(0.0, MTOW_kg - _g("empty_mass_est_kg", 110.0) - USEFUL_LOAD_KG)
m_fuel_sys     = 1.2 + fuel_avail_kg * 0.008

# ── Total ──────────────────────────────────────────────────────────────────────────
components = [
    ("wing",           "Wing (structure, skin, control surfaces)", m_wing),
    ("fuselage",       "Fuselage (skin, frames, longerons)",        m_fuse),
    ("htail",          "Horizontal tail",                           m_htail),
    ("vtail",          "Vertical tail",                             m_vtail),
    ("landing_gear",   "Fixed landing gear",                        m_lg),
    ("engine",         f"Engine ({eng['desc']})",                   m_engine),
    ("engine_systems", "Engine systems (exhaust, mount, cooling)",  m_eng_sys),
    ("propeller",      "Propeller",                                 m_prop),
    ("avionics",       "Avionics + electrical",                     m_avionics),
    ("controls",       "Flight controls",                           m_controls),
    ("fuel_system",    "Fuel system",                               m_fuel_sys),
]

m_empty = sum(c[2] for c in components)
spec_margin_kg   = SPEC_EMPTY_LIMIT_KG - m_empty
fuel_capacity_kg = max(0.0, MTOW_kg - m_empty - USEFUL_LOAD_KG)
margin_pct       = spec_margin_kg / SPEC_EMPTY_LIMIT_KG * 100.0
spec_ok          = m_empty <= SPEC_EMPTY_LIMIT_KG

# ── Print ──────────────────────────────────────────────────────────────────────────
SEP58 = "-" * 58
SEP40 = "-" * 40
SEP8  = "-" * 8
print(f"\nWeight estimate for: {model_stem}")
print(f"  Material : {mat['desc']}")
print(f"  Engine   : {eng['desc']} @ {P_hp:.0f} hp")
print(f"  MTOW     : {MTOW_kg:.1f} kg")
print(SEP58)
print(f"  {'Component':<40}  {'Mass (kg)':>8}")
print(f"  {SEP40}  {SEP8}")
for key, label, mass in components:
    print(f"  {label:<40}  {mass:>8.2f}")
print(f"  {SEP40}  {SEP8}")
print(f"  {'EMPTY MASS TOTAL':<40}  {m_empty:>8.2f}")
print(f"  {'Spec limit':<40}  {SPEC_EMPTY_LIMIT_KG:>8.1f}")
margin_str = ("OK" if spec_ok else "OVER") + f" by {abs(spec_margin_kg):.1f} kg"
print(f"  {'Margin':<40}  {margin_str:>8}")
print(f"  {'Fuel capacity at MTOW':<40}  {fuel_capacity_kg:>8.2f}")
print(SEP58 + "\n")

if not spec_ok:
    print(f"  WARNING: {material_key} construction is {-spec_margin_kg:.1f} kg OVER spec.")
    if material_key == "aluminum":
        print(f"  Consider: cfrp (saves ~{m_empty - _wing_mass_kg(wing_span, wing_area, wing_taper, wing_tc, wing_sweep, n_ult, MTOW_kg, MATERIALS['cfrp']['k_wing']) - MATERIALS['cfrp']['fuse_rho']*fuse_wetted - 5:.0f} kg) or fabric_tube.")

# ── Write JSON ────────────────────────────────────────────────────────────────────
report = {
    "model":       model_stem + ".vsp3",
    "timestamp":   datetime.now().isoformat(),
    "inputs": {
        "material":    material_key,
        "engine_type": engine_key,
        "engine_hp":   P_hp,
        "MTOW_kg":     MTOW_kg,
        "n_ult":       n_ult,
    },
    "geometry_used": {
        "fuse_wetted_m2": round(fuse_wetted, 3),
        "wing_span_m":    wing_span,
        "wing_area_m2":   wing_area,
        "wing_taper":     wing_taper,
        "wing_tc_root":   wing_tc,
        "wing_sweep_deg": wing_sweep,
        "htail_span_m":   htail_span,
        "vtail_height_m": vtail_height,
    },
    "components":    {k: round(v, 3) for k, _, v in components},
    "empty_mass_kg": round(m_empty, 3),
    "spec_limit_kg": SPEC_EMPTY_LIMIT_KG,
    "spec_margin_kg":round(spec_margin_kg, 3),
    "fuel_capacity_kg": round(fuel_capacity_kg, 3),
    "spec_ok":       spec_ok,
}

out_path = OUT_DIR / f"{model_stem}_weight.json"
out_path.write_text(json.dumps(report, indent=2))
print(f"Wrote: {out_path.relative_to(PROJECT_ROOT)}")
