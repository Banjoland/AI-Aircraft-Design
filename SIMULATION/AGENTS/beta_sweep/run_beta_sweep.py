"""
VSPAERO VLM beta (sideslip) sweep simulation — directional and lateral stability.

Loads the most recent MODEL_*.vsp3 from AIRCRAFT/ (or the path given as argv[1]),
runs a VLM beta sweep via the OpenVSP Python API at a fixed alpha of 4.0 deg
(representative cruise), and writes results to
SIMULATION/results/<model_stem>_beta_sweep.json.

Computes lateral-directional stability derivatives via linear regression:
  CY_beta  — side-force derivative (negative = stable side force)
  Cl_beta  — rolling-moment derivative / dihedral effect (negative = stable)
  Cn_beta  — yawing-moment derivative (positive = directionally stable)

Prints a JSON summary to stdout between BEGIN_JSON / END_JSON sentinels.

Run via openvsp-python:
    openvsp-python run_beta_sweep.py
    openvsp-python run_beta_sweep.py path/to/MODEL_xx.vsp3
"""

import json
import math
import os
import sys
from pathlib import Path

import openvsp as vsp

# ── Paths ──────────────────────────────────────────────────────────────────────
# run_beta_sweep.py lives at SIMULATION/AGENTS/beta_sweep/run_beta_sweep.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
SIM_DIR      = PROJECT_ROOT / "SIMULATION"
RESULTS_DIR  = SIM_DIR / "results"
RUNS_DIR     = SIM_DIR / "runs"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)

# ── Spec constants (SPECIFICATION.md) ─────────────────────────────────────────
MTOW_KG    = 218.0          # kg max gross weight
MTOW_N     = MTOW_KG * 9.81
RHO_SL     = 1.225          # kg/m³ sea-level ISA
P_ENGINE_W = 18.0 * 745.7   # W, 18 hp engine

# Wing reference geometry fallbacks — overwritten from companion JSON if available
WING_AREA = 6.86            # m²
WING_SPAN = 9.8             # m
WING_MAC  = 0.71            # m
X_CG      = 1.35            # m

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

# Read geometry metadata written by generate.py. This keeps reference geometry
# synchronized when batch designs vary wing area or chord.
companion_path = model_path.with_suffix(".json")
if companion_path.exists():
    geom_meta = json.loads(companion_path.read_text())
    WING_AREA = float(geom_meta.get("wing_area_m2", WING_AREA))
    WING_SPAN = float(geom_meta.get("wingspan_m", WING_SPAN))
    WING_MAC  = float(geom_meta.get("wing_mac_m", WING_MAC))
    X_CG      = float(geom_meta.get("x_cg_m", geom_meta.get("pilot_x_m", X_CG)))
else:
    print(
        f"WARN: no companion geometry JSON for {model_path.name}; "
        "using fallback reference geometry",
        file=sys.stderr,
    )

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

# ── Sweep parameters ───────────────────────────────────────────────────────────
ALPHA_FIXED = 4.0    # deg — near cruise, held constant for entire beta sweep
BETA_START  = -15.0  # deg
BETA_END    =  15.0  # deg
BETA_NPTS   = 11     # -15 -12 -9 -6 -3 0 3 6 9 12 15 (3° spacing)
MACH        =  0.15  # ≈ 51 m/s at sea level, representative cruise

try:
    # ── 1. Compute degenerate geometry (VLM panels) ──────────────────────────
    # Symmetry=0 is REQUIRED for a beta sweep.
    # With Symmetry=1 VSPAERO exploits the XZ mirror plane which zeroes out all
    # antisymmetric loads (CY, Cl, Cn) — making the sweep meaningless.
    # We must run the full asymmetric problem so sideslip-induced lateral loads
    # are computed correctly.
    vsp.SetAnalysisInputDefaults("VSPAEROComputeGeometry")
    vsp.SetIntAnalysisInput("VSPAEROComputeGeometry", "GeomSet",     [vsp.SET_NONE], 0)
    vsp.SetIntAnalysisInput("VSPAEROComputeGeometry", "ThinGeomSet", [vsp.SET_ALL],  0)
    vsp.SetIntAnalysisInput("VSPAEROComputeGeometry", "Symmetry",    [0],            0)  # asymmetric for beta
    vsp.ExecAnalysis("VSPAEROComputeGeometry")

    # ── 2. Beta sweep at fixed alpha ─────────────────────────────────────────
    vsp.SetAnalysisInputDefaults("VSPAEROSweep")
    vsp.SetIntAnalysisInput("VSPAEROSweep", "GeomSet",     [vsp.SET_NONE], 0)
    vsp.SetIntAnalysisInput("VSPAEROSweep", "ThinGeomSet", [vsp.SET_ALL],  0)
    vsp.SetIntAnalysisInput("VSPAEROSweep", "RefFlag",     [1],            0)  # auto ref from wing
    vsp.SetIntAnalysisInput("VSPAEROSweep", "Symmetry",    [0],            0)  # asymmetric — required for beta sweep
    vsp.SetIntAnalysisInput("VSPAEROSweep", "WakeNumIter", [3],            0)

    # Set CG so moments are computed about the actual CG, not the nose
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "X_cg", [X_CG], 0)
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "Y_cg", [0.0],  0)
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "Z_cg", [0.0],  0)

    if wing_ids:
        vsp.SetStringAnalysisInput("VSPAEROSweep", "WingID", wing_ids, 0)

    # Fixed alpha: AlphaStart = AlphaEnd, AlphaNpts = 1
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "AlphaStart", [ALPHA_FIXED], 0)
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "AlphaEnd",   [ALPHA_FIXED], 0)
    vsp.SetIntAnalysisInput(   "VSPAEROSweep", "AlphaNpts",  [1],           0)

    # Beta sweep
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "BetaStart", [BETA_START], 0)
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "BetaEnd",   [BETA_END],   0)
    vsp.SetIntAnalysisInput(   "VSPAEROSweep", "BetaNpts",  [BETA_NPTS],  0)

    # Fixed Mach
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "MachStart", [MACH], 0)
    vsp.SetDoubleAnalysisInput("VSPAEROSweep", "MachEnd",   [MACH], 0)
    vsp.SetIntAnalysisInput(   "VSPAEROSweep", "MachNpts",  [1],    0)

    rid = vsp.ExecAnalysis("VSPAEROSweep")

finally:
    os.chdir(_orig_dir)

# ── 3. Extract beta sweep results ──────────────────────────────────────────────
# ResultsVec structure for a beta sweep (verified against VSPAERO 7.2.2):
#   [0..N-1]  VSPAERO_History — one sub-result per beta, contains per-iteration
#             convergence history.  Rolling/yawing keys are CMxtot and CMztot.
#   [N]       VSPAERO_Polar   — one sub-result with all N betas in each array.
#             This is the most convenient source; we prefer it.
#   [N+1..]   VSPAERO_Load    — spanwise load distribution, one per beta.
#
# Key name mapping (confirmed by diagnostic run):
#   CL lift      : CLtot
#   Side force   : CYtot / CY  (returns 0.0 in VLM — VLM does not model side force)
#   Rolling moment: CMxtot     (NOT Cltot/Cmxtot)
#   Yawing moment : CMztot     (NOT Cntot/Cmztot)

rid_vec = vsp.GetStringResults(rid, "ResultsVec")

if not rid_vec:
    print("ERROR: VSPAEROSweep returned no results", file=sys.stderr)
    sys.exit(1)

# ── Strategy: prefer the VSPAERO_Polar sub-result which contains all betas in
# one array.  Fall back to per-history sub-results if polar is not found.

def _get_double_defensive(sub_rid, key_candidates, fallback=None):
    """Try each key in key_candidates; return the full vector of the first hit, else None."""
    for k in key_candidates:
        vec = vsp.GetDoubleResults(sub_rid, k)
        if vec:
            return list(vec)
    return fallback

# Key candidate lists (in priority order)
CY_KEYS  = ["CYtot", "CY"]
CLR_KEYS = ["CMxtot", "Cmxtot", "Cltot", "Cl"]    # rolling moment
CN_KEYS  = ["CMztot", "Cmztot", "Cntot", "Cn"]    # yawing moment

betas, CYs, Cls, Cns, CLs = [], [], [], [], []

# First pass: look for a VSPAERO_Polar sub-result (most reliable)
polar_found = False
for sub in rid_vec:
    try:
        rname = vsp.GetResultsName(sub)
    except Exception:
        rname = ""
    if "Polar" not in rname:
        continue

    beta_vec  = vsp.GetDoubleResults(sub, "Beta")
    cl_vec    = vsp.GetDoubleResults(sub, "CLtot")
    if not beta_vec or not cl_vec:
        continue

    cy_vec   = _get_double_defensive(sub, CY_KEYS,  fallback=[0.0] * len(beta_vec))
    clr_vec  = _get_double_defensive(sub, CLR_KEYS, fallback=[0.0] * len(beta_vec))
    cn_vec   = _get_double_defensive(sub, CN_KEYS,  fallback=[0.0] * len(beta_vec))

    # Pad shorter vectors to the length of beta_vec
    n = len(beta_vec)
    def _pad(v, n):
        return list(v) + [0.0] * (n - len(v)) if len(v) < n else list(v)[:n]
    cy_vec  = _pad(cy_vec,  n)
    clr_vec = _pad(clr_vec, n)
    cn_vec  = _pad(cn_vec,  n)
    cl_vec  = _pad(list(cl_vec), n)

    for j in range(n):
        betas.append(round(beta_vec[j], 3))
        CYs.append(round(cy_vec[j],    6))
        Cls.append(round(clr_vec[j],   6))
        Cns.append(round(cn_vec[j],    6))
        CLs.append(round(cl_vec[j],    6))

    polar_found = True
    print(f"INFO: extracted {n} beta points from VSPAERO_Polar sub-result", file=sys.stderr)
    break

# Second pass (fallback): use per-history sub-results one at a time
if not polar_found:
    print("INFO: VSPAERO_Polar not found; falling back to per-history sub-results", file=sys.stderr)
    n_pts = min(len(rid_vec), BETA_NPTS)
    for i in range(n_pts):
        sub = rid_vec[i]
        beta_vec = vsp.GetDoubleResults(sub, "Beta")
        cl_vec   = vsp.GetDoubleResults(sub, "CLtot")

        if not beta_vec or not cl_vec:
            continue  # skip load/polar sub-results without beta data

        # Take the last iteration value (converged solution)
        b_val   = beta_vec[-1]
        cl_val  = cl_vec[-1]

        cy_v    = _get_double_defensive(sub, CY_KEYS,  fallback=[0.0])
        clr_v   = _get_double_defensive(sub, CLR_KEYS, fallback=[0.0])
        cn_v    = _get_double_defensive(sub, CN_KEYS,  fallback=[0.0])

        cy_val  = cy_v[-1]   if cy_v  else 0.0
        clr_val = clr_v[-1]  if clr_v else 0.0
        cn_val  = cn_v[-1]   if cn_v  else 0.0

        # Skip truly empty padding entries (all zeros including lift)
        if cl_val == 0.0 and cy_val == 0.0 and clr_val == 0.0 and cn_val == 0.0:
            continue

        betas.append(round(b_val,   3))
        CYs.append(round(cy_val,    6))
        Cls.append(round(clr_val,   6))
        Cns.append(round(cn_val,    6))
        CLs.append(round(cl_val,    6))

# ── 4. Detect sweep failure ────────────────────────────────────────────────────
beta_sweep_failed = len(betas) < 2

if beta_sweep_failed:
    print(
        f"ERROR: beta sweep returned only {len(betas)} valid data point(s). "
        "Check that VSPAERO supports BetaStart/BetaEnd/BetaNpts inputs in this version. "
        "All derivatives set to 0.0.",
        file=sys.stderr,
    )

# ── 5. Stability derivatives (linear regression vs. beta in radians) ──────────
def _linfit(xs, ys):
    """Return (slope, intercept) of least-squares line through (xs, ys)."""
    n   = len(xs)
    xm  = sum(xs) / n
    ym  = sum(ys) / n
    Sxx = sum((x - xm) ** 2 for x in xs)
    Sxy = sum((xs[i] - xm) * (ys[i] - ym) for i in range(n))
    slope = Sxy / Sxx if Sxx != 0 else 0.0
    return slope, ym - slope * xm


if not beta_sweep_failed:
    betas_rad = [math.radians(b) for b in betas]
    CY_beta, _  = _linfit(betas_rad, CYs)
    Cl_beta, _  = _linfit(betas_rad, Cls)
    Cn_beta, _  = _linfit(betas_rad, Cns)
else:
    CY_beta = 0.0
    Cl_beta = 0.0
    Cn_beta = 0.0

# Stability assessments
directionally_stable = Cn_beta > 0    # positive Cn_beta → yaw restoring
dihedral_effect      = Cl_beta < 0    # negative Cl_beta → roll restoring (stable dihedral)

# ── 6. Build results table ─────────────────────────────────────────────────────
sweep_table = [
    {
        "beta_deg": betas[i],
        "CY":       CYs[i],
        "Cl":       Cls[i],
        "Cn":       Cns[i],
        "CL_lift":  CLs[i],
    }
    for i in range(len(betas))
]

# ── 7. Write results ───────────────────────────────────────────────────────────
results = {
    "model":               model_path.name,
    "analysis":            "VSPAEROSweep_VLM_beta",
    "alpha_fixed_deg":     ALPHA_FIXED,
    "mach":                MACH,
    "beta_range_deg":      [BETA_START, BETA_END],
    "beta_npts_requested": BETA_NPTS,
    "beta_npts_obtained":  len(betas),

    "reference": {
        "mtow_kg":       MTOW_KG,
        "wing_area_m2":  WING_AREA,
        "wing_span_m":   WING_SPAN,
        "wing_mac_m":    WING_MAC,
        "x_cg_m":        X_CG,
        "engine_power_w": P_ENGINE_W,
    },

    "sweep_table": sweep_table,

    # Stability derivatives (per radian)
    "CY_beta":    round(CY_beta, 5),
    "Cl_beta":    round(Cl_beta, 5),
    "Cn_beta":    round(Cn_beta, 5),

    # Stability assessments
    "directionally_stable": directionally_stable,
    "dihedral_effect":      dihedral_effect,
    "Cn_beta_sign":         "positive (stable)" if Cn_beta > 0 else "negative (UNSTABLE)",
    "Cl_beta_sign":         "negative (stable dihedral)" if Cl_beta < 0 else "positive (adverse/no dihedral)",

    # Flag sweep problems
    "beta_sweep_failed":    beta_sweep_failed,
}

out_file = RESULTS_DIR / f"{model_path.stem}_beta_sweep.json"
out_file.write_text(json.dumps(results, indent=2))

# ── 8. Emit sentinels ──────────────────────────────────────────────────────────
print(f"RESULTS_FILE:{out_file}")
print("BEGIN_JSON")
print(json.dumps(results, indent=2))
print("END_JSON")
