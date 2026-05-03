"""
Test driver for airfoil_tool agent.

Tests:
  1. naca_dat_generator.py NACA2412 — confirms .dat file created with >= 50 points
  2. airfoil_modifier.py NACA2412 <model> via openvsp-python — confirms new model file created
  3. Confirms companion JSON created alongside new model
  4. Confirms companion JSON contains airfoil_designation == "NACA2412"

Run from any working directory:
    python TEST/run_test.py
"""

import json
import subprocess
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
# run_test.py lives at DESIGN/AGENTS/airfoil_tool/TEST/run_test.py
# _HERE         = …/TEST
# _HERE.parent  = …/airfoil_tool  (AGENT_DIR)
# _HERE.parents[0] = …/airfoil_tool
# _HERE.parents[1] = …/AGENTS
# _HERE.parents[2] = …/DESIGN
# _HERE.parents[3] = …/AIRCRAFT DESIGN 2  (PROJECT_ROOT)
_HERE        = Path(__file__).resolve().parent          # …/TEST
AGENT_DIR    = _HERE.parent                             # …/airfoil_tool
PROJECT_ROOT = _HERE.parents[3]                         # …/AIRCRAFT DESIGN 2
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"

OPENVSP_PY  = Path(
    r"C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd"
)
DAT_SCRIPT   = AGENT_DIR / "naca_dat_generator.py"
MOD_SCRIPT   = AGENT_DIR / "airfoil_modifier.py"
TEST_AIRFOIL = "NACA2412"

# Source model to use
SOURCE_MODEL = AIRCRAFT_DIR / "MODEL_05_01_2026_62.vsp3"
if not SOURCE_MODEL.exists():
    # Fall back to the most recently modified .vsp3
    candidates = sorted(AIRCRAFT_DIR.glob("*.vsp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    SOURCE_MODEL = candidates[0] if candidates else None


# ── Helpers ────────────────────────────────────────────────────────────────────
PASS_COUNT = 0
FAIL_COUNT = 0

def report(label: str, passed: bool, detail: str = ""):
    global PASS_COUNT, FAIL_COUNT
    status = "PASS" if passed else "FAIL"
    mark   = "[PASS]" if passed else "[FAIL]"
    print(f"  {mark}  {label}")
    if detail:
        indent = "         "
        for line in detail.splitlines():
            print(f"{indent}{line}")
    if passed:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1


def run(cmd, timeout=120):
    """Run a command list; return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as exc:
        return -2, "", str(exc)


# ── Test 1: naca_dat_generator ─────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  Test 1: naca_dat_generator.py {TEST_AIRFOIL}")
print(f"{'='*60}")

rc, out, err = run([sys.executable, str(DAT_SCRIPT), TEST_AIRFOIL])

dat_path_str = out.strip().splitlines()[-1] if out.strip() else ""
dat_path     = Path(dat_path_str) if dat_path_str else (AGENT_DIR / "dat" / f"{TEST_AIRFOIL}.dat")

if rc != 0:
    report("naca_dat_generator runs without error", False,
           f"Return code: {rc}\nstderr: {err[:300]}")
else:
    report("naca_dat_generator runs without error", True)

if dat_path.exists():
    lines = [l for l in dat_path.read_text().splitlines() if l.strip()]
    # First line is name; rest are x y coordinate pairs
    coord_lines = [l for l in lines[1:] if len(l.split()) == 2]
    point_count = len(coord_lines)
    passed = point_count >= 50
    report(
        f".dat file created with >= 50 points",
        passed,
        f"Path: {dat_path}\nTotal coordinate points: {point_count}"
    )
else:
    report(".dat file exists", False, f"Expected at: {dat_path}")

# ── Test 2: airfoil_modifier via openvsp-python ────────────────────────────────
print(f"\n{'='*60}")
print(f"  Test 2: airfoil_modifier.py {TEST_AIRFOIL} via openvsp-python")
print(f"{'='*60}")

if SOURCE_MODEL is None:
    report("Source model exists", False, f"No .vsp3 files found in {AIRCRAFT_DIR}")
    new_model_path = None
else:
    print(f"  Source model: {SOURCE_MODEL}")
    report("Source model exists", SOURCE_MODEL.exists(),
           f"Path: {SOURCE_MODEL}")

    # Snapshot of existing models before running modifier
    existing_before = set(AIRCRAFT_DIR.glob("*.vsp3"))

    rc, out, err = run(
        [str(OPENVSP_PY), str(MOD_SCRIPT), TEST_AIRFOIL, str(SOURCE_MODEL)],
        timeout=120
    )

    print(f"\n  --- stdout ---")
    for line in out.splitlines():
        print(f"  {line}")
    if err.strip():
        print(f"\n  --- stderr (first 30 lines) ---")
        for line in err.splitlines()[:30]:
            print(f"  {line}")

    if rc != 0:
        report("airfoil_modifier runs without error", False,
               f"Return code: {rc}\nstderr: {err[:300]}")
        new_model_path = None
    else:
        report("airfoil_modifier runs without error", True)

        # Find the new .vsp3 file
        existing_after = set(AIRCRAFT_DIR.glob("*.vsp3"))
        new_files = existing_after - existing_before
        if new_files:
            new_model_path = sorted(new_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        else:
            new_model_path = None


# ── Test 3: new model file created ────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  Test 3: new model file created")
print(f"{'='*60}")

if new_model_path is not None and new_model_path.exists():
    report("New .vsp3 model file created", True, f"Path: {new_model_path}")
else:
    report("New .vsp3 model file created", False,
           "No new .vsp3 file detected in AIRCRAFT/ after running airfoil_modifier")
    new_model_path = None


# ── Test 4: companion JSON contains airfoil_designation ───────────────────────
print(f"\n{'='*60}")
print(f"  Test 4: companion JSON contains airfoil_designation == '{TEST_AIRFOIL}'")
print(f"{'='*60}")

if new_model_path is not None:
    json_path = new_model_path.with_suffix(".json")
    if json_path.exists():
        try:
            meta = json.loads(json_path.read_text())
            has_field = meta.get("airfoil_designation") == TEST_AIRFOIL
            report(
                f"JSON airfoil_designation == '{TEST_AIRFOIL}'",
                has_field,
                f"JSON path: {json_path}\n"
                f"airfoil_designation = {meta.get('airfoil_designation', '<missing>')}"
            )
            # Also check that existing source fields are preserved
            has_source = "model_file" in meta or "source_model" in meta
            report("JSON carries forward source model fields", has_source,
                   f"Keys present: {list(meta.keys())[:8]} ...")
        except Exception as exc:
            report("JSON is valid and parseable", False, str(exc))
    else:
        report("Companion JSON exists", False, f"Expected at: {json_path}")
else:
    report("Companion JSON (skipped — no model produced)", False)


# ── Summary ────────────────────────────────────────────────────────────────────
total = PASS_COUNT + FAIL_COUNT
print(f"\n{'='*60}")
print(f"  RESULTS: {PASS_COUNT}/{total} passed")
if FAIL_COUNT == 0:
    print("  ALL TESTS PASSED")
else:
    print(f"  {FAIL_COUNT} TEST(S) FAILED")
print(f"{'='*60}\n")

sys.exit(0 if FAIL_COUNT == 0 else 1)
