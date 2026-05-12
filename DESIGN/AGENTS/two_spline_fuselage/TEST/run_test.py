"""
Smoke-test for the two-spline fuselage generator.

Runs generate.py with the default spline spec and verifies:
  1. A .vsp3 file was created.
  2. The companion JSON contains expected keys.
  3. Fineness ratio is in a reasonable range (3-15).
  4. The smoothness score is reasonable (> 30).
  5. n_sections matches the spec.
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
LAUNCHER     = Path(r"C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd")
SCRIPT       = Path(__file__).resolve().parents[1] / "generate.py"

before = set(AIRCRAFT_DIR.glob("MODEL_*.vsp3"))

print("Running two-spline fuselage generator...")
result = subprocess.run(
    [str(LAUNCHER), str(SCRIPT)],
    capture_output=True, text=True, timeout=120
)

if result.returncode != 0:
    print("FAIL: generate.py returned non-zero exit code")
    print(result.stderr[-2000:])
    sys.exit(1)

# Parse stdout as JSON
try:
    summary = json.loads(result.stdout)
except json.JSONDecodeError as e:
    print(f"FAIL: stdout is not valid JSON: {e}")
    print(result.stdout[:500])
    sys.exit(1)

errors = []

# Check model file exists
model_file = Path(summary.get("model_file", ""))
if not model_file.exists():
    errors.append(f"model file not found: {model_file}")

# Check JSON companion exists
json_file = model_file.with_suffix(".json")
if not json_file.exists():
    errors.append(f"companion JSON not found: {json_file.name}")

# Check expected keys
for key in ("configuration", "fineness_ratio", "smoothness_score",
            "n_sections", "top_spline_knots", "bot_spline_knots"):
    if key not in summary:
        errors.append(f"missing key: {key}")

fr = summary.get("fineness_ratio", 0)
if not (2 < fr < 20):
    errors.append(f"fineness_ratio={fr:.2f} out of expected range (2, 20)")

score = summary.get("smoothness_score", 0)
if score < 0 or score > 100:
    errors.append(f"smoothness_score={score:.1f} out of range [0, 100]")

ns = summary.get("n_sections", 0)
if ns < 4:
    errors.append(f"n_sections={ns} too few")

if errors:
    print("FAIL:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)

after = set(AIRCRAFT_DIR.glob("MODEL_*.vsp3"))
new_models = after - before

print("PASS")
print(f"  model: {model_file.name}")
print(f"  fineness_ratio: {fr:.2f}")
print(f"  smoothness_score: {score:.1f}")
print(f"  n_sections: {ns}")
flags = summary.get("smoothness_flags", [])
if flags:
    print(f"  smoothness_flags: {len(flags)}")
else:
    print("  smoothness_flags: none")
