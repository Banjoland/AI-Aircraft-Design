# Agent: airfoil_tool

## Role

This agent provides two capabilities for airfoil-related design work:

1. **Apply a NACA 4-digit airfoil** to the MainWing of an existing OpenVSP model
2. **Analyze an airfoil's 2-D performance** using xflr5 (with graceful fallback to manual workflow)

---

## Files

| File | Purpose |
|------|---------|
| `airfoil_modifier.py` | Modifies the MainWing XSec shapes to a specified NACA airfoil (OpenVSP Python required) |
| `naca_dat_generator.py` | Generates a NACA 4-digit `.dat` coordinate file for xflr5/XFOIL |
| `xflr5_batch.py` | Runs xflr5 batch analysis on a NACA airfoil, reports Cl_max, Cl/Cd, zero-lift alpha |
| `dat/` | Generated `.dat` airfoil coordinate files |
| `xflr5_scripts/` | Generated xflr5 XML batch scripts |
| `xflr5_output/` | xflr5 polar output text files (populated when xflr5 runs successfully) |
| `skills/airfoil_selection.md` | Iteration log tracking airfoil performance vs. cost function |
| `TEST/run_test.py` | Automated test driver |

---

## How to Apply a NACA Airfoil to a Model

Run via the OpenVSP Python launcher (required for `import openvsp`):

```bat
"C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd" ^
    airfoil_modifier.py NACA2412
```

Or with an explicit model path:

```bat
"C:\Users\asgin\OneDrive\Documents\ENGINEERING\AERO\OpenVSP-3.49.0-win64\openvsp-python.cmd" ^
    airfoil_modifier.py NACA2412 "C:\...\AIRCRAFT\MODEL_05_01_2026_62.vsp3"
```

The script will:
- Parse the NACA designation (camber, camber location, thickness)
- Load the source model
- Find the `MainWing` geom
- Change each XSec shape to `XS_FOUR_SERIES`
- Set `Camber`, `CamberLoc`, and `ThickChord` parameters
- Save a new model file `AIRCRAFT/MODEL_MM_DD_YYYY_XX.vsp3`
- Write a companion `.json` with all source metadata plus airfoil fields
- Print a JSON summary wrapped in `BEGIN_JSON` / `END_JSON` sentinels to stdout

### NACA 4-digit parsing

For `NACA2412`:
- Digit 1 (`2`): max camber = 2/100 = 0.02 (2% chord)
- Digit 2 (`4`): camber location = 4/10 = 0.4 (40% chord)
- Digits 3-4 (`12`): thickness ratio = 12/100 = 0.12 (12% chord)

For symmetric airfoils (`NACA0012`): camber=0, camber_loc=0.4 (default), thickness=0.12

---

## How to Generate a .dat File

Standard Python (no OpenVSP needed):

```bat
python naca_dat_generator.py NACA2412
```

Output: `dat/NACA2412.dat` in Selig format (name on line 1, upper surface LE→TE, lower surface LE→TE).

Uses cosine spacing for better resolution near the leading edge (60 points per surface, 120 total).

---

## How to Run xflr5 Batch Analysis

```bat
python xflr5_batch.py NACA2412
```

This will:
1. Generate the `.dat` file (calls `naca_dat_generator.py`)
2. Write an xflr5 XML batch script to `xflr5_scripts/NACA2412_script.xml`
3. Attempt to run xflr5 with `-script` flag (60-second timeout)
4. If successful: parse `xflr5_output/NACA2412_polar.txt` and report:
   - Cl_max and stall angle
   - Cl/Cd at alpha = 4 deg (cruise proxy)
   - Zero-lift angle of attack
5. If xflr5 fails (no display, Qt error, headless system): print manual workflow instructions

Analysis conditions:
- Re = 500,000 (ultralight at cruise)
- Mach = 0.15
- NCrit = 9.0 (free-stream turbulence)
- Alpha range: -4 to +20 deg, step 0.5 deg

---

## Manual xflr5 Workflow (if batch mode fails)

xflr5 is a GUI application and may not run in headless batch mode. If `xflr5_batch.py` reports that xflr5 did not produce output:

1. Open xflr5 manually: `C:\...\xflr5_6.61_win64\xflr5.exe`

2. Import the airfoil:
   `File → Import → Foil from .dat File`
   Select the generated `.dat` file from `dat/NACA2412.dat`

3. Run polar analysis:
   `Analysis → Batch analysis` (F6)
   - Analysis type: Type 1 (fixed Reynolds)
   - Reynolds: 500000
   - Mach: 0.15
   - NCrit: 9.0
   - Alpha: -4 to 20, step 0.5 deg

4. Export polar:
   Right-click polar → Export → to text file
   Save to `xflr5_output/NACA2412_polar.txt`

5. Re-run `python xflr5_batch.py NACA2412` — it will detect and parse the saved output.

---

## Airfoil Selection Guidance for Low-Speed Ultralights

### Design conditions
- Cruise: ~28 m/s, Re ≈ 500,000–800,000
- Stall: < 21 m/s (per spec)
- MTOW: 218 kg
- Wing area: ~4.75 m²

### NACA 4-digit recommendations

| Airfoil | Camber | Thick | Character | Best use |
|---------|--------|-------|-----------|----------|
| NACA 0012 | 0% | 12% | Symmetric, low drag | Tail surfaces |
| NACA 2412 | 2% | 12% | Low-speed general purpose, moderate lift | Cruise-optimized main wing |
| NACA 4412 | 4% | 12% | High lift, moderate drag | High-lift main wing, lower stall speed |
| NACA 4415 | 4% | 15% | High lift + thicker (more internal volume) | When structural depth matters |
| NACA 2415 | 2% | 15% | Good L/D with structural thickness | Balanced compromise |

### Rules of thumb
- More camber (d1) → higher Cl_max, lower zero-lift alpha (better stall speed)
- More camber location (d2 = 4) → best L/D at moderate alpha
- Thicker section (d34) → better structural depth, more leading-edge drag
- For the current design's AR ≈ 20, reducing profile drag matters more than maximizing Cl_max;
  NACA 2412 or 2415 are good starting candidates.

---

## Test

```bat
python TEST/run_test.py
```

Expected output: PASS for each of 4 test steps.
