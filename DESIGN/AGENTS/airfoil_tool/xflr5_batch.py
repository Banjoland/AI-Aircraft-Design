"""
xflr5 Batch Analyzer — runs a 2-D airfoil polar analysis via xflr5.

Usage:
    python xflr5_batch.py NACA2412

Steps:
    1. Generates a .dat file using naca_dat_generator.py
    2. Writes an xflr5 XML batch script
    3. Attempts to run xflr5 in batch/script mode
    4. If successful, parses the polar output and reports key metrics
    5. If xflr5 fails (e.g. no display), falls back gracefully

Output files (all under DESIGN/AGENTS/airfoil_tool/):
    dat/<NACAXXXX>.dat        — airfoil coordinate file
    xflr5_scripts/<NACAXXXX>_script.xml  — batch XML
    xflr5_output/<NACAXXXX>_polar.txt    — raw polar output (if analysis ran)

Key metrics reported (stdout):
    Cl_max, Cl/Cd at alpha=4 deg, zero-lift alpha
"""

import math
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[3]

XFLR5_EXE   = Path(r"C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\xflr5_6.61_win64\xflr5.exe")
DAT_DIR      = _HERE / "dat"
SCRIPT_DIR   = _HERE / "xflr5_scripts"
OUTPUT_DIR   = _HERE / "xflr5_output"

for d in (DAT_DIR, SCRIPT_DIR, OUTPUT_DIR):
    d.mkdir(exist_ok=True)

# Analysis parameters
RE          = 500_000
MACH        = 0.15
N_CRIT      = 9.0
ALPHA_START = -4.0
ALPHA_END   = 20.0
ALPHA_DELTA = 0.5
TIMEOUT_SEC = 60


# ── Argument parsing ───────────────────────────────────────────────────────────
def usage():
    print("Usage: python xflr5_batch.py NACA2412", file=sys.stderr)
    sys.exit(1)


if len(sys.argv) < 2:
    usage()

naca_arg = sys.argv[1].strip().upper()
if not naca_arg.startswith("NACA"):
    naca_arg = "NACA" + naca_arg

m_match = re.fullmatch(r"NACA(\d{4})", naca_arg)
if m_match is None:
    print(f"[error] '{naca_arg}' is not a valid NACA 4-digit designation.", file=sys.stderr)
    sys.exit(1)


# ── Step 1: Generate .dat file ────────────────────────────────────────────────
print(f"\n[xflr5_batch] Step 1: generating .dat file for {naca_arg} ...")
dat_script = _HERE / "naca_dat_generator.py"
try:
    result = subprocess.run(
        [sys.executable, str(dat_script), naca_arg],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"[error] naca_dat_generator failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    dat_path = Path(result.stdout.strip())
    if not dat_path.exists():
        # Fall back: look in dat dir
        dat_path = DAT_DIR / f"{naca_arg}.dat"
    print(f"[xflr5_batch] .dat file: {dat_path}")
except Exception as e:
    print(f"[error] Could not run naca_dat_generator.py: {e}", file=sys.stderr)
    sys.exit(1)


# ── Step 2: Write xflr5 XML batch script ─────────────────────────────────────
print(f"\n[xflr5_batch] Step 2: writing xflr5 batch XML ...")

polar_name   = f"T1_Re{RE/1e6:.3f}_M{MACH:.2f}_N{N_CRIT:.1f}"
script_path  = SCRIPT_DIR / f"{naca_arg}_script.xml"
output_path  = OUTPUT_DIR / f"{naca_arg}_polar.txt"

# Notes on xflr5 batch XML format:
# - xflr5 6.x supports a -script flag that loads an XML command file
# - The XML structure below follows the documented format for xflr5 >= 6.47
# - PolarType 1 = fixed Reynolds number (Type 1 polar)
# - The Export element tells xflr5 to write the polar table to a text file
# - If xflr5 is run headless (no display) it may fail with a Qt error;
#   that failure is caught below and a fallback message is printed.
#
# Known xflr5 batch XML quirks:
# - The DOCTYPE declaration is required in some versions
# - FoilName must match exactly (case-sensitive)
# - ExportFile path must use forward slashes or escaped backslashes
# - Some builds of xflr5 do not support -script in batch mode at all;
#   in that case the tool reports failure and suggests the manual workflow.

xml_content = textwrap.dedent(f"""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xflr5 SYSTEM "xflr5.dtd">
<xflr5 version="6.61">
  <Foil>
    <FoilName>{naca_arg}</FoilName>
    <FileName>{dat_path.as_posix()}</FileName>
  </Foil>
  <Polar>
    <FoilName>{naca_arg}</FoilName>
    <PolarName>{polar_name}</PolarName>
    <PolarType>1</PolarType>
    <Reynolds>{RE}</Reynolds>
    <Mach>{MACH}</Mach>
    <NCrit>{N_CRIT}</NCrit>
    <ASpec>0</ASpec>
  </Polar>
  <Sequence>
    <FoilName>{naca_arg}</FoilName>
    <PolarName>{polar_name}</PolarName>
    <AlphaStart>{ALPHA_START}</AlphaStart>
    <AlphaEnd>{ALPHA_END}</AlphaEnd>
    <AlphaDelta>{ALPHA_DELTA}</AlphaDelta>
    <Sequence>true</Sequence>
    <InitBL>true</InitBL>
    <StoreOpp>false</StoreOpp>
    <Export>true</Export>
    <ExportFile>{output_path.as_posix()}</ExportFile>
  </Sequence>
</xflr5>
""")

script_path.write_text(xml_content, encoding="utf-8")
print(f"[xflr5_batch] Script written: {script_path}")


# ── Step 3: Run xflr5 in batch mode ──────────────────────────────────────────
print(f"\n[xflr5_batch] Step 3: launching xflr5 ...")
print(f"  Executable : {XFLR5_EXE}")
print(f"  Script     : {script_path}")
print(f"  Timeout    : {TIMEOUT_SEC}s")

xflr5_ok = False
if not XFLR5_EXE.exists():
    print(f"[warn] xflr5 executable not found at {XFLR5_EXE}", file=sys.stderr)
else:
    try:
        env = dict(os.environ)
        # Suppress Qt display errors on headless systems
        env.setdefault("QT_QPA_PLATFORM", "offscreen")

        proc = subprocess.run(
            [str(XFLR5_EXE), "-script", str(script_path)],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SEC,
            env=env,
        )
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        if stdout:
            print(f"[xflr5 stdout]\n{stdout}")
        if stderr:
            print(f"[xflr5 stderr]\n{stderr}", file=sys.stderr)

        if proc.returncode == 0 and output_path.exists():
            xflr5_ok = True
            print(f"[xflr5_batch] xflr5 completed successfully. Output: {output_path}")
        else:
            print(f"[warn] xflr5 returned code {proc.returncode}; "
                  f"output file {'found' if output_path.exists() else 'NOT found'}.",
                  file=sys.stderr)
            if output_path.exists():
                # Partial output — still try to parse
                xflr5_ok = True

    except subprocess.TimeoutExpired:
        print(f"[warn] xflr5 timed out after {TIMEOUT_SEC}s.", file=sys.stderr)
    except FileNotFoundError:
        print(f"[warn] Could not launch xflr5 at {XFLR5_EXE}.", file=sys.stderr)
    except Exception as exc:
        print(f"[warn] xflr5 run failed: {exc}", file=sys.stderr)


# ── Step 4: Parse output and report key metrics ────────────────────────────────
if xflr5_ok and output_path.exists():
    print(f"\n[xflr5_batch] Step 4: parsing polar output ...")

    # xflr5 polar export format (space-separated columns):
    # alpha  CL  CD  CDp  Cm  Top_Xtr  Bot_Xtr  (header lines start with spaces or letters)
    alphas, cls, cds = [], [], []

    raw = output_path.read_text(encoding="utf-8", errors="replace")
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("alpha") or line.startswith("-"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            a  = float(parts[0])
            cl = float(parts[1])
            cd = float(parts[2])
            alphas.append(a)
            cls.append(cl)
            cds.append(cd)
        except ValueError:
            continue

    if not alphas:
        print("[warn] Could not parse any data rows from polar output.", file=sys.stderr)
    else:
        # Cl_max
        cl_max = max(cls)
        a_clmax = alphas[cls.index(cl_max)]

        # Zero-lift alpha (interpolate where CL crosses zero)
        alpha_zero_lift = None
        for i in range(len(alphas) - 1):
            if cls[i] * cls[i + 1] <= 0.0:
                # Linear interpolation
                da = alphas[i + 1] - alphas[i]
                dc = cls[i + 1] - cls[i]
                alpha_zero_lift = alphas[i] - cls[i] * da / dc if dc != 0 else alphas[i]
                break

        # Cl/Cd at alpha = 4 deg (nearest point)
        target_alpha = 4.0
        cl_cd_at4 = None
        best_dist = float("inf")
        for i, a in enumerate(alphas):
            dist = abs(a - target_alpha)
            if dist < best_dist and cds[i] > 0:
                best_dist = dist
                cl_cd_at4 = cls[i] / cds[i]

        print("\n" + "=" * 50)
        print(f"  Airfoil : {naca_arg}")
        print(f"  Re      : {RE:,}   Mach: {MACH}")
        print(f"  Cl_max  : {cl_max:.3f}  at alpha = {a_clmax:.1f} deg")
        if alpha_zero_lift is not None:
            print(f"  Alpha_ZL: {alpha_zero_lift:.2f} deg  (zero-lift angle)")
        if cl_cd_at4 is not None:
            print(f"  Cl/Cd   : {cl_cd_at4:.1f}  at alpha = {target_alpha} deg")
        print("=" * 50 + "\n")

else:
    # ── Fallback: no xflr5 output ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  xflr5 batch analysis did not produce output.")
    print("=" * 60)
    lines = [
        "",
        "MANUAL XFLR5 WORKFLOW",
        "---------------------",
        "xflr5 requires a graphical display and does not reliably support",
        "headless batch operation on all platforms.  To analyze the airfoil",
        "manually:",
        "",
        "1. Open xflr5 (double-click xflr5.exe)",
        "",
        "2. Import the airfoil:",
        "   File -> Import -> Foil from .dat File",
        f"   Select: {dat_path}",
        "",
        "3. Define a polar:",
        "   Analysis -> Batch analysis  (or press F6 for single polar)",
        f"   - Foil name: {naca_arg}",
        "   - Analysis type: Type 1 (fixed speed)",
        f"   - Reynolds number: {RE}",
        f"   - Mach: {MACH}",
        f"   - NCrit: {N_CRIT}",
        f"   - Alpha range: {ALPHA_START} to {ALPHA_END} step {ALPHA_DELTA}",
        "",
        "4. Export the polar:",
        "   Right-click the polar -> Export to text file",
        f"   Save to: {output_path}",
        "",
        "5. Re-run this script to parse the saved output.",
        "",
    ]
    print("\n".join(lines))
    print("The .dat file and XML batch script are available for manual use:")
    print(f"  .dat file   : {dat_path}")
    print(f"  XML script  : {script_path}")
