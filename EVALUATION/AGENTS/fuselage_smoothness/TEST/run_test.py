from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
AGENT_DIR = TEST_DIR.parent
FIXTURE = TEST_DIR / "fixtures" / "smooth_pod.json"
OUT = TEST_DIR / "out" / "smooth_pod_report.json"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(AGENT_DIR / "analyze.py"), str(FIXTURE), "--out", str(OUT)],
        capture_output=True,
        text=True,
    )
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    if proc.returncode != 0:
        print(f"FAIL: analyze.py exited {proc.returncode}")
        return 1
    if not OUT.exists():
        print(f"FAIL: missing report {OUT}")
        return 1

    report = json.loads(OUT.read_text())
    summary = report["summary"]
    failures = []
    if summary["fineness_ratio"] <= 4.0:
        failures.append("expected fixture fineness ratio > 4.0")
    if summary["max_radius_profile_curvature_1_per_m"] <= 0.0:
        failures.append("expected positive curvature")
    if summary["pressure_recovery_risk"] not in {"low", "medium", "high"}:
        failures.append("invalid pressure risk classification")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS: fuselage_smoothness analyzer produced valid report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
