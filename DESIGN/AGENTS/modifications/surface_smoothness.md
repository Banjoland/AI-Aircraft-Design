# Skill: Surface Smoothness / Roughness Factor

## What It Modifies
Adjusts the effective surface roughness of the aircraft skin, governing the transition from laminar to turbulent boundary layer.

## Parameter in generate.py
Not modelled in VLM (VSPAERO panel method) — affects profile drag via viscous boundary-layer physics, which VLM does not capture. Would need a separate drag build-up tool.

Geometric fuselage smoothness is now audited by
`EVALUATION/AGENTS/fuselage_smoothness/analyze.py`, using explicit
`fuselage_stations` metadata when present.

## Physical Effect
A smooth surface (equivalent sand roughness k_s < 1 µm) can maintain laminar flow over 30–50% of the chord, reducing skin-friction drag by 30–40% compared to fully turbulent flow. Surface imperfections (rivet heads, paint steps, waviness) trip the boundary layer early. For composite construction the laminar-flow benefit is achievable; for fabric covering it is not.

## How to Apply
This parameter is not adjustable in the current VLM simulation. To account for it in a drag budget: add a `P["cf_factor"]` (1.0 = fully turbulent, 0.6 = 40% laminar) to the profile-drag term in the scoring/evaluation script. In the physical design, specify polished composite skins forward of maximum thickness to maximise laminar run.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
| 66 / MODEL_05_02_2026_07 | Smoothed single full-length fuselage with 15 explicit stations | 18.87 | 46.48 | 2186.7406 | Smoothness score 61.8/100, low pressure-recovery risk, max centerline slope 20.56 deg; large wetted-area mass penalty remains |
| 67 / MODEL_05_02_2026_11 | Rebuilt fuselage stations from cubic top/bottom/side curves with C2 OpenVSP skinning and rounded end caps | 18.90 | 40.17 | 1873.5660 | Visual skinning should be smoother; analyzer score 57.6/100 with high risk remaining from short nose/engine and aft closeout transitions |
