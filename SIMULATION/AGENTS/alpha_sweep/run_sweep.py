"""
VSPAERO VLM alpha sweep simulation.

Loads the most recent MODEL_*.vsp3 from AIRCRAFT/ (or the path given as argv[1]),
runs a VLM alpha sweep via the OpenVSP Python API, and writes results to
SIMULATION/results/<model_stem>_alpha_sweep.json.

Prints a JSON summary to stdout.

Run via openvsp-python:
    openvsp-python run_sweep.py
    openvsp-python run_sweep.py path/to/MODEL_xx.vsp3
"""

import json
import math
import os
import sys
from pathlib import Path

import openvsp as vsp

# ── Paths ──────────────────────────────────────────────────────────────────────
# run_sweep.py lives at SIMULATION/AGENTS/alpha_sweep/run_sweep.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
SIM_DIR      = PROJECT_ROOT / "SIMULATION"
RESULTS_DIR  = SIM_DIR / "results"
RUNS_DIR     = SIM_DIR / "runs"       # VSPAERO writes temp files here
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)

# ── Spec constants (SPECIFICATION.md) ─────────────────────────────────────────
MTOW_KG      = 218.0          # kg max gross weight
MTOW_N       = MTOW_KG * 9.81
RHO_SL       = 1.225          # kg/m³ sea-level ISA
P_ENGINE_W   = 18.0 * 745.7   # W, 18 hp engine
WING_AREA    = 6.86           # m² fallback; overwritten from companion JSON when available
WING_SPAN    = 9.8            # m fallback
WING_MAC     = 0.71           # m fallback
X_CG         = 1.35           # m fallback; overwritten from companion JSON when available
VSTALL_LIMIT = 21.0           # m/s (SPECIFICATION.md)

# ── Find model ─────────────────────────────────────────────────────────────────
if len(sys.argv) > 1:
    model_path = Path(sys.argv[1]).resolve()
else:
    candidates = sorted(AIRCRAFT_DIR.glob("MODEL_*.vsp3"),
                        key=lambda p: p.stat().st_mtime)
    if not candidates:
        print("ERROR: no MODEL_*.vsp3 found in AIRCRAFT/", file=sys.stderr)
        sys.exit(1)
    model_path = candidates[-1]

print(f"Model: {model_path.name}", file=sys.stderr)

# Read geometry metadata written by generate.py. This keeps stall/cruise
# calculations synchronized when batch designs vary wing area or chord.
companion_path = model_path.with_suffix(".json")
if companion_path.exists():
    geom_meta = json.loads(companion_path.read_text())
    WING_AREA    = float(geom_meta.get("wing_area_m2", WING_AREA))
    WING_SPAN    = float(geom_meta.get("wingspan_m", WING_SPAN))
    WING_MAC     = float(geom_meta.get("wing_mac_m", WING_MAC))
    X_CG         = float(geom_meta.get("x_cg_m", geom_meta.get("pilot_x_m", X_CG)))
    # Read spec constants if embedded by generate.py
    if "spec_MTOW_kg" in geom_meta:
        MTOW_KG      = float(geom_meta["spec_MTOW_kg"])
        MTOW_N       = MTOW_KG * 9.81
    if "spec_vstall_lim_ms" in geom_meta:
        VSTALL_LIMIT = float(geom_meta["spec_vstall_lim_ms"])
    if "spec_P_engine_kw" in geom_meta and geom_meta["spec_P_engine_kw"] > 0:
        P_ENGINE_W   = float(geom_meta["spec_P_engine_kw"]) * 1000.0
else:
    print(f"WARN: no companion geometry JSON for {model_path.name}; using fallback reference geometry", file=sys.stderr)

# ── Load model ─────────────────────────────────────────────────────────────────
vsp.ClearVSPModel()
vsp.ReadVSPFile(str(model_path))
vsp.Update()

wing_ids = vsp.FindGeomsWithName("MainWing")
if not wing_ids:
    print("WARN: 'MainWing' not found; RefFlag will use defaults", file=sys.stderr)

# ── Change to runs dir so VSPAERO temp files stay tidy ─────────────────────────
_orig_dir = os.getcwd()
os.chdir(str(RUNS_DIR))

try:
    # ── 1. Compute degenerate geometry (VLM panels) ──────────────────────────
    vsp.SetAnalysisInputDefaults("VSPAEROComputeGeometry")
    vsp.SetIntAnalysisInput("VSPAEROComputeGeometry", "GeomSet",     [vsp.SET_NONE], 0)
    vsp.SetIntAnalysisInput("VSPAEROComputeGeometry", "ThinGeomSet", [vsp.SET_ALL],  0)
    vsp.SetIntAnalysisInput("VSPAEROComputeGeometry", "Symmetry",    [1],            0)
    vsp.ExecAnalysis("VSPAEROComputeGeometry")

    # ── 2. Alpha sweep ───────────────────────────────────────────────────────
    ALPHA_START = -4.0
    ALPHA_END   = 16.0
    ALPHA_NPTS  = 11     # 2° increments: -4 -2 0 2 4 6 8 10 12 14 16
    MACH        = 0.15   # ≈ 51 m/s at sea level, representative cruise

    vsp.SetAnalysisInputDefaults("VSPAEROSweep")
    vsp.SetIntAnalysisInput("VSPAEROSweep", "GeomSet",     [vsp.SET_NONE], 0)
    vsp.SetIntAnalysisInput("VSPAEROSweep", "ThinGeomSet", [vsp.SET_ALL],  0)
    vsp.SetIntAnalysisInput("VSPAEROSweep", "RefFlag",     [1],            0)  # auto ref from wing
    vsp.SetIntAnalysisInput("VSPAEROSweep", "Symmetry",    [1],            0)
    vsp.SetIntAnalysisInput("VSPAEROSweep", "WakeNumIter", [3],            0)

    # Set CG location so moments are computed about the actual CG, not the nose
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "X_cg", [X_CG], 0)
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "Y_cg", [0.0],  0)
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "Z_cg", [0.0],  0)

    if wing_ids:
        vsp.SetStringAnalysisInput("VSPAEROSweep", "WingID", wing_ids, 0)

    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "AlphaStart", [ALPHA_START], 0)
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "AlphaEnd",   [ALPHA_END],   0)
    vsp.SetIntAnalysisInput(   "VSPAEROSweep", "AlphaNpts",  [ALPHA_NPTS],  0)
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "MachStart",  [MACH],        0)
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "MachEnd",    [MACH],        0)
    vsp.SetIntAnalysisInput(   "VSPAEROSweep", "MachNpts",   [1],           0)

    rid = vsp.ExecAnalysis("VSPAEROSweep")

finally:
    os.chdir(_orig_dir)

# ── 3. Extract polar ───────────────────────────────────────────────────────────
# rid_vec contains per-alpha history sub-results (one per alpha point) followed
# by load-distribution sub-results for the final iteration.  Only process the
# first ALPHA_NPTS entries, which are the alpha-sweep history results.
rid_vec = vsp.GetStringResults(rid, "ResultsVec")

if not rid_vec:
    print("ERROR: VSPAEROSweep returned no results", file=sys.stderr)
    sys.exit(1)

n_pts = min(len(rid_vec), ALPHA_NPTS)

# Correct key confirmed by diagnostic: "CMytot" (not "CMy")
CM_KEYS = ["CMytot", "CMy", "Cmy", "CMtot"]

alphas, CLs, CDs, CMs = [], [], [], []
for i in range(n_pts):
    a_vec  = vsp.GetDoubleResults(rid_vec[i], "Alpha")
    cl_vec = vsp.GetDoubleResults(rid_vec[i], "CLtot")
    cd_vec = vsp.GetDoubleResults(rid_vec[i], "CDtot")

    if not a_vec or not cl_vec:
        continue  # skip empty sub-results

    cd_val = cd_vec[-1] if cd_vec else 0.0
    if cd_val == 0.0 and cl_vec[-1] == 0.0:
        continue  # skip zero-result entries (padding from load sub-results)

    # Try multiple possible CM key names
    cm_val = 0.0
    for ck in CM_KEYS:
        cm_res = vsp.GetDoubleResults(rid_vec[i], ck)
        if cm_res:
            cm_val = cm_res[-1]
            break

    alphas.append(round(a_vec[-1],  3))
    CLs.append(   round(cl_vec[-1], 6))
    CDs.append(   round(cd_val,     6))
    CMs.append(   round(cm_val,     6))

if len(alphas) < 2:
    print(
        f"ERROR: VSPAEROSweep returned only {len(alphas)} valid polar point(s); "
        "cannot compute stability or performance derivatives",
        file=sys.stderr,
    )
    sys.exit(1)

# ── 4. Stability and performance derivatives ───────────────────────────────────
def _linfit(xs, ys):
    """Return (slope, intercept) of least-squares line through (xs, ys)."""
    n   = len(xs)
    xm  = sum(xs) / n
    ym  = sum(ys) / n
    Sxx = sum((x - xm)**2 for x in xs)
    Sxy = sum((xs[i] - xm)*(ys[i] - ym) for i in range(n))
    slope = Sxy / Sxx if Sxx != 0 else 0.0
    return slope, ym - slope * xm

CL_alpha_per_deg, CL_0  = _linfit(alphas, CLs)
Cm_alpha_per_deg, Cm_0  = _linfit(alphas, CMs)

# Stall speed from peak VLM CL (VLM is linear but max alpha gives upper-bound CL)
CL_max = max(CLs)
vstall_est = math.sqrt(2.0 * MTOW_N / (RHO_SL * WING_AREA * CL_max))

# Cruise speed estimate: numerically find V where P_available = D*V
# P_avail at 75% power
P_avail = 0.75 * P_ENGINE_W
# D = 0.5*rho*V²*S*CD, L = W → CL = 2W/(rho*V²*S)
# P_req = D*V = 0.5*rho*V³*S*CD(CL)
# Interpolate CD from polar at each candidate V
# Find V where P_req = P_avail using the alpha=2° point as cruise estimate

def _interp_at_cl(cl_target, xs, ys):
    """Linear interpolate ys at cl_target (xs = CLs, ys = CDs or alphas)."""
    for i in range(len(xs)-1):
        if (xs[i] <= cl_target <= xs[i+1]) or (xs[i] >= cl_target >= xs[i+1]):
            t = (cl_target - xs[i]) / (xs[i+1] - xs[i])
            return ys[i] + t * (ys[i+1] - ys[i])
    return None

# Iterate V until P_req == P_avail (bisection)
v_lo, v_hi = 20.0, 120.0
vcruise = None
for _ in range(60):
    v_mid = 0.5 * (v_lo + v_hi)
    cl_mid = 2.0 * MTOW_N / (RHO_SL * v_mid**2 * WING_AREA)
    cd_mid = _interp_at_cl(cl_mid, CLs, CDs)
    if cd_mid is None:
        cd_mid = CDs[-1] if cl_mid < CLs[-1] else CDs[0]
    p_req = 0.5 * RHO_SL * v_mid**3 * WING_AREA * cd_mid
    if p_req < P_avail:
        v_lo = v_mid
    else:
        v_hi = v_mid
    if v_hi - v_lo < 0.01:
        vcruise = v_mid
        break

if vcruise is None:
    vcruise = 0.5 * (v_lo + v_hi)

# L/D at cruise
cl_cruise = 2.0 * MTOW_N / (RHO_SL * vcruise**2 * WING_AREA)
cd_cruise = _interp_at_cl(cl_cruise, CLs, CDs) or CDs[len(CDs)//2]
ld_cruise = cl_cruise / cd_cruise if cd_cruise > 0 else 0.0

# ── 5. Write results ───────────────────────────────────────────────────────────
polar = [{"alpha_deg": alphas[i], "CL": CLs[i], "CD": CDs[i], "CM": CMs[i],
          "LD": round(CLs[i]/CDs[i], 2) if CDs[i] > 0 else 0}
         for i in range(len(alphas))]

results = {
    "model":              model_path.name,
    "analysis":           "VSPAEROSweep_VLM",
    "mach":               MACH,
    "alpha_range_deg":    [ALPHA_START, ALPHA_END],
    "reference": {
        "mtow_kg": MTOW_KG,
        "wing_area_m2": WING_AREA,
        "wing_span_m": WING_SPAN,
        "wing_mac_m": WING_MAC,
        "x_cg_m": X_CG,
        "engine_power_w": P_ENGINE_W,
    },

    "polar":              polar,

    "CL_alpha_per_deg":   round(CL_alpha_per_deg, 5),
    "CL_0":               round(CL_0, 5),
    "Cm_alpha_per_deg":   round(Cm_alpha_per_deg, 5),
    "Cm_0":               round(Cm_0, 5),

    "CL_max_vlm":         round(CL_max, 4),
    "vstall_est_ms":      round(vstall_est, 2),
    "vstall_limit_ms":    VSTALL_LIMIT,
    "vstall_ok":          vstall_est < VSTALL_LIMIT,

    "vcruise_75pct_ms":   round(vcruise, 2),
    "CL_cruise":          round(cl_cruise, 4),
    "CD_cruise":          round(cd_cruise, 6),
    "LD_cruise":          round(ld_cruise, 2),

    "longitudinal_stable": Cm_alpha_per_deg < 0,
    "Cm_alpha_sign":       "negative (stable)" if Cm_alpha_per_deg < 0 else "positive (UNSTABLE)",
}

out_file = RESULTS_DIR / f"{model_path.stem}_alpha_sweep.json"
out_file.write_text(json.dumps(results, indent=2))

# vspaero.exe writes progress to our stdout, so we can't use plain print for JSON.
# Instead: emit a sentinel line that callers can find, then the path to the results file.
print(f"RESULTS_FILE:{out_file}")
# Also emit the JSON after the sentinel — callers can extract it if needed.
print("BEGIN_JSON")
print(json.dumps(results, indent=2))
print("END_JSON")
