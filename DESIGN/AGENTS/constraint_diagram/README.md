# Agent: constraint_diagram

## Role
Generate a thrust-to-weight vs wing-loading constraint diagram. Shows whether the engine and wing sizing simultaneously satisfy stall, cruise, and climb requirements. The primary tool for identifying engine power shortfalls.

## When to use
- When starting a new design, to find the feasible T/W and W/S range.
- When the iteration_suggester flags low cruise speed, to understand if more power is needed.
- To compare different engine/AR/CL_max combinations.

## Usage

```
python DESIGN\AGENTS\constraint_diagram\plot.py
python DESIGN\AGENTS\constraint_diagram\plot.py path/to/spec_override.json
```

## Key output

```
Stall constraint  W/S <= 486 N/m²
At stall-limit W/S:
  T/W required (cruise) = 0.0471  (needs 20.1 hp at eta=0.75)
  T/W required (climb)  = 0.0718  (needs 14.6 hp at eta=0.65)
  T/W available         = 0.0437  (cruise)   0.0506  (climb)

CRUISE: Engine is 2.1 hp SHORT for cruise at stall-limited W/S.
```

The diagram reveals the **18 hp engine is 2.1 hp short** for cruise at the stall-limited wing loading with the default spec. The aircraft needs either more engine power, lower MTOW, or a higher-drag configuration to allow a smaller, lighter wing.

## Theory

| Constraint | Formula |
|---|---|
| Stall      | W/S ≤ ½ρV²_stall × CL_max |
| Cruise     | T/W = q×CD0/(W/S) + (W/S)/(q×π×e×AR) |
| Climb      | T/W = RC/V + q×CD0/(W/S) + (W/S)/(q×π×e×AR) |

Available T/W from a fixed-pitch prop engine at constant power:
`T/W = η_prop × P / (V × MTOW × g)`

## Output files
- `constraint_diagram.json` — full sweep data + deficit analysis
- `constraint_diagram.png` — plot (if matplotlib is available)

## Test

```
python DESIGN\AGENTS\constraint_diagram\TEST\run_test.py
```
