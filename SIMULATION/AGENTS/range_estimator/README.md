# Agent: range_estimator

## Role
Compute the aircraft's achievable range, fuel budget, rate of climb, and service ceiling. Verifies the 1100 km range specification from SPECIFICATION.md.

## When to use
After running the alpha sweep. Call before or after the dynamic stability analyzer.

## Steps
```
python SIMULATION\AGENTS\range_estimator\estimate.py
# or for a specific model:
python SIMULATION\AGENTS\range_estimator\estimate.py \
    SIMULATION\results\MODEL_xx_alpha_sweep.json \
    AIRCRAFT\MODEL_xx.json
```

## Method

### Fuel budget
```
fuel_available = MTOW (218 kg) − empty_mass − useful_load (117 kg)
```
If empty_mass > 101 kg, fuel = 0 → range = 0 (aircraft is over gross weight).

### Range (direct)
```
endurance_hr = fuel_volume_L / fuel_burn_L_hr          (30.3 L/hr from spec)
range_km     = V_cruise_km_hr × endurance_hr
```

### Range (Breguet, reference)
```
R = (V / SFC) × (L/D) × ln(W_initial / W_final)
```

### Rate of climb
```
RC = (P_engine − P_drag_at_V) / MTOW_N
```
Best RC speed (V_y) is found by scanning over speed range.

### Service ceiling
Altitude where RC drops to 0.5 m/s (100 ft/min). Engine power modelled as proportional to air density.

## Key output fields
```json
{
  "fuel": { "fuel_avail_kg": 0.0, "fuel_required_kg": 88.4, "fuel_shortfall_kg": 88.4 },
  "range": { "range_actual_km": 0.0, "range_ok": false },
  "climb": { "best_RC_ms": 2.3, "service_ceiling_m": 1850 },
  "compliance": { "range_ok": false, "range_gap_km": 1100, "notes": [...] }
}
```

## Limitations
- Range calculation uses constant cruise speed and does not model climb/descent fuel burn.
- Engine power loss with altitude uses a simplified density ratio model.
- Breguet range assumes ideal propulsive efficiency; treat as an upper bound.

## Test
```
python SIMULATION\AGENTS\range_estimator\TEST\run_test.py
```
