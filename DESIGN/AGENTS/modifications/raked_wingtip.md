# Skill: Raked Wingtip

## What It Modifies
Extends the wingtip with a highly swept "rake" section, smoothly stretching the effective span in a low-mass form.

## Parameter in generate.py
Not implemented — requires a multi-section WING geom with a separate, highly swept tip section (sweep > 35 deg) added outboard.

## Physical Effect
A raked wingtip (as on Boeing 777) is an alternative to winglets for reducing induced drag. The high sweep stretches the tip vortex core over a longer path, reducing its concentrated downwash effect. Raked tips have less bending moment penalty than vertical winglets at the same span extension. They provide a 1–3% induced drag reduction compared to a squared-off tip.

## How to Apply
Add a second XSec section to the WING geom at 90% semi-span, with increased sweep (35–45 deg) and a reduced chord. This requires changing the main wing from a single-section to a two-section wing in generate.py using `vsp.InsertXSec`. Introduce `P["tip_rake_sweep_deg"] = 40.0` and `P["tip_rake_span"] = 0.5` as new parameters.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
