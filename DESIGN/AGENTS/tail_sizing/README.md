# Agent: tail_sizing

## Role
Compute required horizontal and vertical tail areas for a target static margin and directional stability. Reads geometry JSON and tells you whether the current tail is too large, too small, or just right.

## When to use
- When generating a new design from scratch (to size the tail before running OpenVSP).
- After an alpha sweep, to verify that the aerodynamic static margin matches what the geometry predicts.
- When the iteration_suggester recommends changing CG or tail size.

## Usage

```
python DESIGN\AGENTS\tail_sizing\size.py
python DESIGN\AGENTS\tail_sizing\size.py AIRCRAFT\MODEL_xx.json
python DESIGN\AGENTS\tail_sizing\size.py AIRCRAFT\MODEL_xx.json --SM_target 0.15 --SM_min 0.05 --SM_max 0.25
```

## Theory

**Horizontal tail — static margin:**
```
SM = x_NP_frac - x_CG_frac
x_NP_frac = 0.25 + V_H × a_t × η_tail × (1 - dε/dα) / a_w
V_H = S_h × l_h / (S_w × c̄)
```

Inverted to find required V_H for a target SM:
```
V_H_req = (SM_target + x_CG_frac - 0.25) × a_w / (a_t × η_tail × (1 - dε/dα))
S_h_req = V_H_req × S_w × c̄ / l_h
```

**Vertical tail — directional stability:**
```
Cn_β = V_V × a_v × η_v × (1 - σ_β) + Cn_β_fuse
```
where Cn_β_fuse is the destabilizing fuselage contribution (negative).
Target: Cn_β ≥ 0.05 /rad for positive directional stability.

## Key output fields

```json
{
  "htail": {
    "SM_current_pct": 14.2,
    "S_h_current_m2": 0.432,
    "S_h_req_target_m2": 0.390,
    "S_h_req_min_m2": 0.280,
    "S_h_req_max_m2": 0.510,
    "htail_ok": true,
    "delta_S_h_m2": -0.042
  },
  "vtail": {
    "Cn_beta_current": 0.081,
    "S_v_required_m2": 0.210,
    "vtail_ok": true
  }
}
```

## Typical stability targets

| SM (%MAC) | Assessment |
|---|---|
| < 5% | Marginal — risk of departure |
| 5–25% | Good — recommended design range |
| 15% | Ideal target for this design |
| > 25% | Over-stable — excess trim drag at cruise |

## Test

```
python DESIGN\AGENTS\tail_sizing\TEST\run_test.py
```
