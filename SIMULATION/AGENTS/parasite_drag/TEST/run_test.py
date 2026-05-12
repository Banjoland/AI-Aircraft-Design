"""
Smoke-test for the parasite drag analyzer.

Runs analyze.py on the most recent MODEL_*.vsp3 and verifies:
  1. The analysis completes without error.
  2. The result JSON contains expected top-level keys.
  3. At least one component is returned.
  4. total_CD_parasite is a positive finite number.
  5. The dominant component accounts for > 0% of total drag.
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
AIRCRAFT_DIR = PROJECT_ROOT / "AIRCRAFT"
RESULTS_DIR  = PROJECT_ROOT / "SIMULATION" / "results"
LAUNCHER     = Path(r"C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd")
SCRIPT       = Path(__file__).resolve().parents[1] / "analyze.py"

# Pick most recent model
candidates = sorted(AIRCRAFT_DIR.glob("MODEL_*.vsp3"), key=lambda p: p.stat().st_mtime)
if not candidates:
    print("SKIP: no MODEL_*.vsp3 found")
    sys.exit(0)
model = candidates[-1]

print(f"Running parasite drag analysis on: {model.name}")
result = subprocess.run(
    [str(LAUNCHER), str(SCRIPT), str(model)],
    capture_output=True, text=True, timeout=180
)

if result.returncode != 0:
    print("FAIL: analyze.py returned non-zero exit code")
    print(result.stderr[-2000:])
    sys.exit(1)

# Parse stdout as JSON
try:
    report = json.loads(result.stdout)
except json.JSONDecodeError as e:
    print(f"FAIL: stdout is not valid JSON: {e}")
    print(result.stdout[:500])
    sys.exit(1)

# Checks
errors = []
for key in ("model", "total_CD_parasite", "components", "recommendations"):
    if key not in report:
        errors.append(f"missing key: {key}")

cd = report.get("total_CD_parasite", 0)
if not (0 < cd < 1.0):
    errors.append(f"total_CD_parasite={cd} out of expected range (0, 1)")

comps = report.get("components", [])
if not comps:
    errors.append("components list is empty")
else:
    top = comps[0]
    for ckey in ("name", "CD", "FF", "Swet_m2", "pct_total"):
        if top.get(ckey) is None:
            errors.append(f"component[0] missing: {ckey}")

    pct_sum = sum(c.get("pct_total") or 0 for c in comps)
    if not (80 <= pct_sum <= 120):
        errors.append(f"pct_total sum {pct_sum:.1f}% not near 100%")

# Check result file exists
stem = model.stem
json_out = RESULTS_DIR / f"{stem}_parasite_drag.json"
if not json_out.exists():
    errors.append(f"result file not written: {json_out.name}")

if errors:
    print("FAIL:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)

print("PASS")
print(f"  total_CD_parasite = {cd:.5f}")
print(f"  components: {len(comps)}")
print(f"  top drag contributor: {comps[0]['name']} ({comps[0].get('pct_total')}%)")
