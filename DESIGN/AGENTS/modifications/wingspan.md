# Skill: Wingspan

## What It Modifies
Sets the total tip-to-tip span of the main wing.

## Parameter in generate.py
`P["wing_span"]` — current default value: 9.8 m

## Physical Effect
Increasing span raises aspect ratio, reducing induced drag (proportional to 1/AR). Span is the single most powerful lever for improving cruise efficiency. However, longer spans increase bending loads, structural mass, and wetted area. The specification limits wingspan to 15 m maximum.

## How to Apply
Change `P["wing_span"]` in the P dict. Increasing span reduces induced drag but increases wetted area and structural mass. Keep `P["wing_span"] <= 15.0` per specification. After changing, recompute `wing_area_m2` and `aspect_ratio` from the summary JSON and re-run VSPAERO to assess drag polar shift.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
