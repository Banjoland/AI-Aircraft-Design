"""
Test driver for the modification_registry agent.

The test runs the audit against the real DESIGN_GUIDELINES.md and validates the
schema, feature count, and important guideline entries without requiring OpenVSP.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
AGENT_DIR = HERE.parent
PROJECT_ROOT = HERE.parents[3]
SCRIPT = AGENT_DIR / "audit_guidelines.py"
OUT_DIR = HERE / "out"
OUT_JSON = OUT_DIR / "guideline_capability_audit_test.json"
OUT_MD = OUT_DIR / "guideline_capability_audit_test.md"


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--out-json",
        str(OUT_JSON),
        "--out-md",
        str(OUT_MD),
    ]
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, text=True, capture_output=True, timeout=60)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        return fail(f"audit script exited with {proc.returncode}")

    if not OUT_JSON.exists():
        return fail(f"missing JSON report: {OUT_JSON}")
    if not OUT_MD.exists():
        return fail(f"missing Markdown report: {OUT_MD}")

    audit = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    features = audit.get("features", [])
    summary = audit.get("summary", {})

    if summary.get("features_total", 0) < 60:
        return fail(f"expected at least 60 guideline features, got {summary.get('features_total')}")

    slugs = {record.get("slug") for record in features}
    required = {
        "fuselage_length",
        "airfoil_root",
        "winglet_height",
        "horizontal_tail_area",
        "propeller_diameter",
        "thrust_line_relative_to_cg",
    }
    missing = sorted(required - slugs)
    if missing:
        return fail(f"audit did not include required slugs: {missing}")

    status_counts = summary.get("status_counts", {})
    if not status_counts:
        return fail("summary.status_counts is empty")

    print(json.dumps(summary, indent=2))
    print(f"REPORT_JSON:{OUT_JSON}")
    print(f"REPORT_MD:{OUT_MD}")
    print("PASS: modification_registry audit produced a valid feature matrix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
