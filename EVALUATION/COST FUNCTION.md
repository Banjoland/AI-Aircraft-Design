# Cost Functions

Aircraft are scored using the sum of the cost functions below. **Lower total cost = better design.**

| Performance Spec | Formula | Notes |
|-----------------|---------|-------|
| Stall Speed | Stall speeds at or below the spec limit score **0**. Stall speeds above the limit score **(V_stall - V_spec)^2** | V_spec = 21.0 m/s |
| Stability | Stable aircraft score **1 / distance_from_origin** on the s-plane plot of aircraft longitudinal response. Unstable aircraft (or aircraft where stability cannot be confirmed) score **100** | Smaller distance from origin = larger cost; prefer eigenvalues far into the stable half-plane |
| Cruise Speed | **exp(3 * (V_cruise - V_ref) / V_ref)**, capped at a maximum of **100** | V_ref = 54.2 m/s. This term is **subtracted** from the total cost; faster cruise reduces the total cost score. |
| Mass | Mass will be scored as exp(10 * (mass - mass_spec)/mass_spec) - 1 |

## Total Cost

```
total_cost = stall_cost + stability_cost + mass_cost - cruise_reward
```

where `cruise_reward = min(exp(3 * (V_cruise - 54.2) / 54.2), 100)`

## Reference Values

| Quantity | Value | Source |
|----------|-------|--------|
| Stall speed limit | 21.0 m/s | SPECIFICATION.md |
| Reference cruise speed | 54.2 m/s | SPECIFICATION.md |
| Stability threshold | Cm_alpha < 0 | Longitudinal static stability |
| Empty mass spec | 110 kg | SPECIFICATION.md |
