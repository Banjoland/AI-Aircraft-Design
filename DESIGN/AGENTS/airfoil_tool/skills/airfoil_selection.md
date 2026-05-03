# Skill: Airfoil Selection

## What It Modifies
The airfoil section profile of the MainWing in OpenVSP.
Controlled by the NACA 4-digit designation passed to `airfoil_modifier.py`.

## How to Apply

### Apply a NACA airfoil to the current best model
```bat
cd "C:\Users\asgin\OneDrive\Documents\PROJECTS\AI AIRPLANE DESIGN\AIRCRAFT DESIGN 2\DESIGN\AGENTS\airfoil_tool"
"C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd" airfoil_modifier.py NACA2412
```

### Check 2-D aerodynamic performance first
```bat
python xflr5_batch.py NACA2412
```

### Generate a .dat file for manual xflr5 analysis
```bat
python naca_dat_generator.py NACA2412
```

## Parameters Modified in OpenVSP

For each XSec of the MainWing XSec surface:
| Parameter | Group | Description |
|-----------|-------|-------------|
| `Camber` | `XSecCurve` | Max camber as fraction of chord (e.g. 0.02 for NACA 2xxx) |
| `CamberLoc` | `XSecCurve` | Chordwise location of max camber (e.g. 0.4 for NACAxxx) |
| `ThickChord` | `XSecCurve` | Thickness ratio (e.g. 0.12 for NACAxxx12) |

## NACA 4-digit Parsing Reference

`NACA[m][p][tt]` where:
- `m` = max camber × 100  (first digit)
- `p` = camber location × 10  (second digit)
- `tt` = thickness × 100  (last two digits)

Examples:
- NACA 0012: m=0, p=0.4(default), t=0.12 — symmetric, low drag
- NACA 2412: m=0.02, p=0.4, t=0.12 — classic general-purpose
- NACA 4412: m=0.04, p=0.4, t=0.12 — high lift
- NACA 4415: m=0.04, p=0.4, t=0.15 — high lift, thicker

## Performance Impact Log

| Iteration | Airfoil | CL_max | CD_cruise | L/D_cruise | Stall Cost | Total Cost | Notes |
|-----------|---------|--------|-----------|------------|------------|------------|-------|
