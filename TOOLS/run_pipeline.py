"""
Full simulation pipeline runner.

Finds the most recent MODEL_*.vsp3 in AIRCRAFT/ (or uses the path given as argv[1])
and runs all analysis steps in the correct order:

  Step 1  generate.py           OpenVSP-Python  geometry + companion JSON
  Step 2  alpha_sweep           OpenVSP-Python  CL, CD, Cm_alpha polar
  Step 3  beta_sweep            OpenVSP-Python  lateral derivatives
  Step 4  parasite_drag         OpenVSP-Python  CD breakdown by component
  Step 5  inertia_estimator     Python 3        mass distribution, Iyy/Ixx/Izz
  Step 6  dynamic_stability     Python 3        eigenvalues (phugoid, SP, dutch roll)
  Step 7  range_estimator       Python 3        range and fuel budget
  Step 8  static_margin         Python 3        SM, neutral point
  Step 9  cost_scorer           Python 3        total cost function

Steps 1–4 require the OpenVSP bundled Python launcher.
Steps 5–9 run with the system Python 3.

Usage:
    python run_pipeline.py                      # most recent MODEL_*.vsp3
    python run_pipeline.py AIRCRAFT/MODEL_xx.vsp3
    python run_pipeline.py --skip-openvsp       # run only plain-Python steps (5–9)

Output:  prints a one-page summary table to stdout
         writes SIMULATION/results/<model>_pipeline_summary.json
"""

import json
import subprocess
import sys
import time
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR  = PROJECT_ROOT / "SIMULATION" / "results"
SCORES_DIR   = PROJECT_ROOT / "EVALUATION" / "scores"

OPENVSP_LAUNCHER = Path(
    r"C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd"
)

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SCORES_DIR.mkdir(parents=True, exist_ok=True)

# ── Parse args ─────────────────────────────────────────────────────────────────
skip_openvsp = "--skip-openvsp" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]

if args:
    model_path = Path(args[0]).resolve()
else:
    candidates = sorted(AIRCRAFT_DIR.glob("MODEL_*.vsp3"),
                        key=lambda p: p.stat().st_mtime)
    if not candidates:
        print("ERROR: no MODEL_*.vsp3 found in AIRCRAFT/. "
              "Generate a model first with generate.py.", file=sys.stderr)
        sys.exit(1)
    model_path = candidates[-1]

model_stem = model_path.stem
print(f"\n{'='*60}")
print(f"  Pipeline: {model_path.name}")
print(f"{'='*60}")

# ── Step runners ───────────────────────────────────────────────────────────────

def _run_openvsp(label, script, extra_args=()):
    if skip_openvsp:
        print(f"  [SKIP] {label} (--skip-openvsp)")
        return None
    if not OPENVSP_LAUNCHER.exists():
        print(f"  [SKIP] {label} — OpenVSP launcher not found at {OPENVSP_LAUNCHER}")
        return None
    cmd = [str(OPENVSP_LAUNCHER), str(script)] + [str(a) for a in extra_args]
    t0 = time.monotonic()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    elapsed = time.monotonic() - t0
    ok = proc.returncode == 0
    status = "OK" if ok else f"FAIL (exit {proc.returncode})"
    print(f"  [{status:20s}] {label:40s} {elapsed:5.1f}s")
    if not ok:
        for line in proc.stderr.splitlines()[-5:]:
            print(f"             | {line}", file=sys.stderr)
    return proc


def _run_python(label, script, extra_args=()):
    cmd = [sys.executable, str(script)] + [str(a) for a in extra_args]
    t0 = time.monotonic()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    elapsed = time.monotonic() - t0
    ok = proc.returncode == 0
    status = "OK" if ok else f"FAIL (exit {proc.returncode})"
    print(f"  [{status:20s}] {label:40s} {elapsed:5.1f}s")
    if not ok:
        for line in proc.stderr.splitlines()[-5:]:
            print(f"             | {line}", file=sys.stderr)
    return proc


# ── Step definitions ───────────────────────────────────────────────────────────
AGENTS  = PROJECT_ROOT / "SIMULATION" / "AGENTS"
EVALAG  = PROJECT_ROOT / "EVALUATION" / "AGENTS"

alpha_json   = RESULTS_DIR / f"{model_stem}_alpha_sweep.json"
inertia_json = RESULTS_DIR / f"{model_stem}_inertia.json"

print()
# Step 2: Alpha sweep (needs vsp3, produces alpha_sweep.json)
_run_openvsp("Alpha sweep (VLM)",
             AGENTS / "alpha_sweep" / "run_sweep.py",
             [model_path])

# Step 3: Beta sweep
_run_openvsp("Beta sweep (VLM)",
             AGENTS / "beta_sweep" / "run_beta_sweep.py",
             [model_path])

# Step 4: Parasite drag
_run_openvsp("Parasite drag",
             AGENTS / "parasite_drag" / "analyze.py",
             [model_path])

# Step 5: Inertia estimator (needs companion JSON)
geom_json = model_path.with_suffix(".json")
_run_python("Inertia estimator",
            AGENTS / "inertia_estimator" / "estimate.py",
            [geom_json] if geom_json.exists() else [])

# Step 6: Dynamic stability
_run_python("Dynamic stability",
            AGENTS / "dynamic_stability" / "analyze.py",
            ([alpha_json, inertia_json]
             if alpha_json.exists() and inertia_json.exists()
             else [alpha_json] if alpha_json.exists() else []))

# Step 7: Range estimator
_run_python("Range estimator",
            AGENTS / "range_estimator" / "estimate.py",
            ([alpha_json, geom_json]
             if alpha_json.exists() and geom_json.exists()
             else [alpha_json] if alpha_json.exists() else []))

# Step 8: Static margin
_run_python("Static margin",
            AGENTS / "static_margin" / "compute.py",
            ([alpha_json, geom_json]
             if alpha_json.exists() and geom_json.exists()
             else [alpha_json] if alpha_json.exists() else []))

# Step 9: Cost scorer
_run_python("Cost scorer",
            EVALAG / "cost_scorer" / "score.py",
            [alpha_json] if alpha_json.exists() else [])

# ── Summary table ──────────────────────────────────────────────────────────────
print(f"\n{'─'*60}")
print(f"  SUMMARY: {model_stem}")
print(f"{'─'*60}")

def _load(path):
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}

alpha   = _load(alpha_json)
inertia = _load(inertia_json)
dynstab = _load(RESULTS_DIR / f"{model_stem}_dynamic_stability.json")
rng     = _load(RESULTS_DIR / f"{model_stem}_range.json")
sm      = _load(RESULTS_DIR / f"{model_stem}_static_margin.json")
score   = _load(SCORES_DIR  / f"{model_stem}_score.json")
geom    = _load(geom_json)

def _fmt(val, fmt=".2f", missing="—"):
    return format(val, fmt) if val is not None else missing

def _ok(flag, yes="PASS", no="FAIL"):
    return yes if flag else no

rows = [
    # Label, value, unit/note
    ("Empty mass",  _fmt(geom.get("empty_mass_est_kg")),        "kg  (spec ≤ 110)"),
    ("V_stall",     _fmt(alpha.get("vstall_est_ms")),            f"m/s  [{_ok(alpha.get('vstall_ok', False))}]"),
    ("V_cruise",    _fmt(alpha.get("vcruise_75pct_ms")),         "m/s  (spec 54.2)"),
    ("L/D cruise",  _fmt(alpha.get("LD_cruise")),                ""),
    ("Cm_alpha",    _fmt(alpha.get("Cm_alpha_per_deg"), ".5f"),  "/deg"),
    ("Static margin", _fmt(sm.get("static_margin", {}).get("SM_pct_mac"), ".1f"),
                    f"%MAC  [{sm.get('static_margin',{}).get('SM_status','—')}]"),
    ("Phugoid ζ",   _fmt(next((m["zeta"] for m in
                    dynstab.get("longitudinal",{}).get("modes",[])
                    if m.get("name") == "phugoid"), None), ".3f"),  ""),
    ("Short-period ζ", _fmt(next((m["zeta"] for m in
                    dynstab.get("longitudinal",{}).get("modes",[])
                    if m.get("name") == "short_period"), None), ".3f"),  ""),
    ("Lon stable",  _ok(dynstab.get("longitudinal",{}).get("all_stable")), ""),
    ("Lat stable",  _ok(dynstab.get("lateral",{}).get("all_stable")), ""),
    ("Range",       _fmt(rng.get("range",{}).get("range_actual_km"), ".0f"),
                    f"km  [{_ok(rng.get('compliance',{}).get('range_ok'))}]  (spec 1100)"),
    ("Fuel avail",  _fmt(rng.get("fuel",{}).get("fuel_avail_kg"), ".1f"),  "kg"),
    ("Rate of climb", _fmt(rng.get("climb",{}).get("best_RC_ms"), ".2f"),  "m/s"),
    ("Service ceiling", _fmt(rng.get("climb",{}).get("service_ceiling_m"), ".0f"),  "m"),
    ("Iyy",         _fmt(inertia.get("Iyy_kgm2"), ".1f"),       "kg·m²"),
    ("x_CG",        _fmt(inertia.get("cg_x_m"), ".3f"),         "m from nose"),
]

# Score
stall_c   = score.get("stall_cost")
stab_c    = score.get("stability_cost")
mass_c    = score.get("mass_cost")
cr_rew    = score.get("cruise_reward")
total_c   = score.get("total_cost")
stab_src  = score.get("stability_source", "—")

for label, val, note in rows:
    print(f"  {label:<22} {val:>10}  {note}")

print(f"\n  {'COST BREAKDOWN':─<50}")
print(f"  {'Stall cost':<22} {_fmt(stall_c):>10}")
print(f"  {'Stability cost':<22} {_fmt(stab_c):>10}  [{stab_src}]")
print(f"  {'Mass cost':<22} {_fmt(mass_c):>10}")
print(f"  {'Cruise reward':<22} {_fmt(cr_rew):>10}")
print(f"  {'TOTAL COST':<22} {_fmt(total_c):>10}")
print(f"{'='*60}\n")

# ── Write summary JSON ─────────────────────────────────────────────────────────
summary = {
    "model":     model_stem + ".vsp3",
    "alpha":     alpha,
    "inertia":   inertia,
    "dyn_stab":  dynstab,
    "range":     rng,
    "sm":        sm,
    "score":     score,
}
out = RESULTS_DIR / f"{model_stem}_pipeline_summary.json"
out.write_text(json.dumps(summary, indent=2))
print(f"  Summary written → {out.relative_to(PROJECT_ROOT)}")
