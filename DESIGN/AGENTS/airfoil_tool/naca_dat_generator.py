"""
NACA 4-digit .dat file generator.

Computes airfoil coordinates using the NACA 4-digit formula and writes a
Selig-format .dat file suitable for import into xflr5 or XFOIL.

Usage:
    python naca_dat_generator.py NACA2412
    python naca_dat_generator.py 2412       # bare digits also accepted

Output:
    DESIGN/AGENTS/airfoil_tool/dat/<NACAXXXX>.dat

The Selig format is:
    <AirfoilName>
    x1_upper  y1_upper
    x2_upper  y2_upper
    ...
    x1_lower  y1_lower
    ...
    (upper surface from LE to TE, lower surface from LE to TE)
"""

import math
import re
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
DAT_DIR = _HERE / "dat"
DAT_DIR.mkdir(exist_ok=True)

N_POINTS = 60  # number of points on each surface (upper / lower)


# ── Argument parsing ───────────────────────────────────────────────────────────
def usage():
    print("Usage: python naca_dat_generator.py NACAXXXX", file=sys.stderr)
    print("  e.g. python naca_dat_generator.py NACA2412", file=sys.stderr)
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

digits = m_match.group(1)
d1  = int(digits[0])
d2  = int(digits[1])
d34 = int(digits[2:])

max_camber     = d1  / 100.0   # fraction of chord
camber_loc     = d2  / 10.0    # fraction of chord
thickness_ratio = d34 / 100.0  # fraction of chord

print(f"[naca_dat] {naca_arg}: m={max_camber}, p={camber_loc}, t={thickness_ratio}", file=sys.stderr)


# ── NACA 4-digit formulas ──────────────────────────────────────────────────────
def thickness_distribution(x, t):
    """Half-thickness as a fraction of chord at chordwise position x."""
    return (5.0 * t * (
        0.2969 * math.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x ** 2
        + 0.2843 * x ** 3
        - 0.1015 * x ** 4
    ))


def camber_line(x, m, p):
    """
    Mean camber line ordinate at x.
    Returns (yc, dyc_dx).
    """
    if m == 0 or p == 0:
        return 0.0, 0.0
    if x <= p:
        yc      = (m / p ** 2) * (2.0 * p * x - x ** 2)
        dyc_dx  = (m / p ** 2) * (2.0 * p - 2.0 * x) if p != 0 else 0.0
    else:
        yc      = (m / (1.0 - p) ** 2) * (1.0 - 2.0 * p + 2.0 * p * x - x ** 2)
        dyc_dx  = (m / (1.0 - p) ** 2) * (2.0 * p - 2.0 * x)
    return yc, dyc_dx


def naca_coordinates(m, p, t, n=N_POINTS):
    """
    Compute upper and lower surface (x, y) coordinates.

    Uses cosine spacing for better resolution near the leading edge.

    Returns:
        upper: list of (x, y) from LE to TE
        lower: list of (x, y) from LE to TE
    """
    # Cosine spacing: beta from 0 to pi → x from 0 to 1
    betas = [math.pi * i / (n - 1) for i in range(n)]
    xs    = [(1.0 - math.cos(b)) / 2.0 for b in betas]

    upper = []
    lower = []
    for x in xs:
        yt         = thickness_distribution(x, t)
        yc, dyc_dx = camber_line(x, m, p)
        if m == 0:
            # Symmetric: no camber, no twist angle
            xu = x
            yu =  yt
            xl = x
            yl = -yt
        else:
            theta = math.atan(dyc_dx)
            xu = x  - yt * math.sin(theta)
            yu = yc + yt * math.cos(theta)
            xl = x  + yt * math.sin(theta)
            yl = yc - yt * math.cos(theta)
        upper.append((xu, yu))
        lower.append((xl, yl))

    return upper, lower


# ── Generate coordinates ───────────────────────────────────────────────────────
upper, lower = naca_coordinates(max_camber, camber_loc, thickness_ratio)

print(f"[naca_dat] Generated {len(upper)} upper + {len(lower)} lower points", file=sys.stderr)

# ── Write .dat file (Selig format) ────────────────────────────────────────────
out_path = DAT_DIR / f"{naca_arg}.dat"

with open(out_path, "w") as f:
    f.write(f"{naca_arg}\n")
    # Upper surface: LE (x=0) to TE (x=1)
    for x, y in upper:
        f.write(f"{x:.6f}  {y:.6f}\n")
    # Lower surface: LE (x=0) to TE (x=1)
    for x, y in lower:
        f.write(f"{x:.6f}  {y:.6f}\n")

print(f"[naca_dat] Wrote {out_path}  ({len(upper) + len(lower)} points total)", file=sys.stderr)
print(str(out_path))   # plain stdout for callers to capture the path
