# Parasite Drag Analyzer

Computes a per-component parasite drag breakdown for an OpenVSP aircraft model
using OpenVSP's built-in `ParasiteDrag` analysis.

## What it does

1. Loads the target `.vsp3` model.
2. Runs OpenVSP's `ParasiteDrag` analysis at sea-level cruise conditions.
3. Extracts per-component drag contributions: CD, skin-friction coefficient,
   form factor, fineness ratio, wetted area, and percentage of total drag.
4. Identifies the highest-drag components and generates streamlining recommendations
   based on form-factor theory (Hoerner, Shevell).
5. Writes a JSON report to `SIMULATION/results/<model>_parasite_drag.json`.

## Form factor interpretation

| Form factor | Shape description |
|-------------|------------------|
| 1.0         | Perfect flat plate (no thickness) |
| 1.1–1.2     | Well-streamlined airfoil or slender fuselage (FR > 8) |
| 1.3–1.5     | Moderately bluff body (FR ~ 5–6) |
| 1.8–2.5     | Blunt body (FR < 4) |
| > 2.5       | Poor streamlining — high pressure drag |

For fuselages, optimal fineness ratio is 5–8. Below 4, form drag grows steeply.
For wings, form factor is a function of t/c and sweep.

## Usage

```powershell
# Most recent model (default)
openvsp-python SIMULATION\AGENTS\parasite_drag\analyze.py

# Specific model
openvsp-python SIMULATION\AGENTS\parasite_drag\analyze.py AIRCRAFT\MODEL_xx.vsp3
```

## Test

```powershell
python SIMULATION\AGENTS\parasite_drag\TEST\run_test.py
```

## Output fields

```json
{
  "model": "MODEL_05_11_2026_03.vsp3",
  "cruise_ms": 52.2,
  "sref_m2": 4.21,
  "total_CD_parasite": 0.0248,
  "total_drag_N": 172.5,
  "components": [
    {
      "name": "MainWing",
      "Swet_m2": 8.77,
      "CD": 0.0118,
      "Cf": 0.0032,
      "FF": 1.12,
      "fineness": 8.6,
      "pct_total": 47.6,
      "Q_interf": 1.0
    }
  ],
  "recommendations": [
    "CockpitPod: form factor 2.14 is high (fineness 3.8). Elongate or streamline..."
  ]
}
```

## Drag reduction workflow

1. Run the analyzer to identify the dominant drag component.
2. Check form factor: if FF > 1.4 on a fuselage, elongate it (increase fineness ratio).
3. Check wetted area: if a component contributes > 35% of total drag, reduce its size.
4. Use the two-spline fuselage generator to reshape the fuselage with controlled
   slope and curvature to reduce form drag.
5. Re-run the analyzer to verify the drag reduction.
