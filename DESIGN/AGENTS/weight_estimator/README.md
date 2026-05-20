# Agent: weight_estimator

## Role
Empirical component build-up empty-mass estimate. Given aircraft geometry, engine type/power, and structural material, produces a component-by-component mass breakdown and checks it against the 110 kg empty-mass specification.

## When to use
- Before or after generating a new model, to predict whether the material/engine choice will meet the mass spec.
- When the iteration suggester flags `mass_cost > 0`, to understand which component group dominates.
- To compare material options (aluminum vs CFRP vs fabric/tube) for a given geometry.

## Usage

```
python DESIGN\AGENTS\weight_estimator\estimate.py
python DESIGN\AGENTS\weight_estimator\estimate.py AIRCRAFT\MODEL_xx.json
python DESIGN\AGENTS\weight_estimator\estimate.py AIRCRAFT\MODEL_xx.json --engine gasoline2 --hp 18 --material cfrp
```

### Material options

| Key          | Description                         | Relative wing mass |
|---|---|---|
| `aluminum`   | Aluminum alloy (2024-T3 / 6061-T6)  | 1.00× (baseline) |
| `cfrp`       | Carbon-fiber composite (CFRP)       | 0.55× |
| `fiberglass` | E-glass / fiberglass composite      | 0.82× |
| `fabric_tube`| Steel/aluminum tube + Dacron fabric | 0.45× |
| `wood`       | Spruce spar / plywood ribs / fabric | 0.68× |

### Engine options

| Key          | Description                  |
|---|---|
| `gasoline2`  | 2-stroke gasoline (Hirth, Rotax 503) |
| `gasoline4`  | 4-stroke gasoline (Rotax 912, Jabiru) |
| `diesel`     | Diesel / Jet-A piston |
| `electric`   | Electric motor + ESC (battery mass NOT included) |
| `wankel`     | Rotary (Wankel) engine |

## Method

### Wing mass
Bending-load dominated formula (Torenbeek simplified, calibrated to LSA data):

```
m_wing = k_mat × C × (n_ult × MTOW)^0.49 × b^1.20 / (t_root_m × cos_sweep)^0.30
```

Where `k_mat` is the material efficiency factor, `n_ult = 3.8 × 1.5 = 5.7`, and `C = 0.020`.

### Fuselage and tail mass
Effective area density × wetted area:
```
m_fuse = fuse_rho[material] × fuse_wetted_m2
m_tail = tail_rho[material] × tail_wetted_m2
```

Typical fuselage area densities (skin + primary structure):

| Material     | fuse_rho (kg/m²) |
|---|---|
| Aluminum     | 2.8 |
| CFRP         | 1.6 |
| Fabric/tube  | 0.75 |

*Note: The spline_aircraft generator uses 6 kg/m² for a rough MTOW estimate — this is intentionally conservative. The weight_estimator uses refined component-level densities.*

### Engine mass
```
m_engine = base_kg + kg_per_hp × P_hp
m_engine_sys = sys_frac × m_engine   # exhaust, mount, cooling
```

Calibrated to: Hirth 2704 (18 hp → 16.9 kg), Rotax 503 (52 hp → 28 kg), Rotax 912 (80 hp → 56 kg).

## Key output fields

```json
{
  "empty_mass_kg": 76.4,
  "spec_limit_kg": 110.0,
  "spec_margin_kg": 33.6,
  "fuel_capacity_kg": 24.6,
  "spec_ok": true,
  "components": {
    "wing":           18.5,
    "fuselage":       21.1,
    "htail":           2.1,
    "vtail":           1.2,
    "landing_gear":    6.1,
    "engine":         14.9,
    "engine_systems":  5.2,
    "propeller":       2.0,
    "avionics":        5.5,
    "controls":        2.6,
    "fuel_system":     1.3
  }
}
```

## Design guidance from test results

At the default spec geometry (5 m fuselage, 9.8 m span, 18 hp):

| Material     | Empty mass | Fuel at MTOW | Spec OK |
|---|---|---|---|
| Aluminum     | 104.5 kg   | 0.0 kg       | Yes (barely) |
| CFRP         | 76.4 kg    | 24.6 kg      | Yes |
| Fiberglass   | ~88 kg     | ~13 kg       | Yes |
| Fabric/tube  | 61.7 kg    | 39.3 kg      | Yes |
| Wood         | ~82 kg     | ~18 kg       | Yes |

**Conclusion:** Aluminum at 18 hp is feasible but leaves no fuel margin. CFRP or fabric/tube construction is needed for meaningful range.

## Test

```
python DESIGN\AGENTS\weight_estimator\TEST\run_test.py
```
