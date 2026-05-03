# Skill: Airfoil Selection (Root)

## What It Modifies
Sets the airfoil section at the wing root, controlling root lift, drag, and stall characteristics at the highest chord Reynolds number.

## Parameter in generate.py
Use `DESIGN/AGENTS/airfoil_tool/airfoil_modifier.py` — default is the OpenVSP built-in default (no specific NACA applied in baseline generate.py).

## Physical Effect
The root airfoil operates at the highest Reynolds number (largest chord) and carries the highest spanwise load. Selecting a high-CL, low-Cd airfoil here maximises wing efficiency at cruise. A moderately cambered (2–4%) thick (14–18%) low-speed section (Eppler, Selig, or NACA 4-series) is appropriate. The root section also determines the wing root bending resistance through its depth.

## How to Apply
Run `airfoil_modifier.py` with the target model file and specify the root XSec index (typically XSec_1 at the root). Supply a NACA 4-digit designation (e.g., `--airfoil NACA2415`) or a .dat file path. Verify the airfoil is applied by inspecting the VSPAERO polar output for improved L/D at cruise CL.

## Performance Impact Log

| Iteration | Change Made | V_stall (m/s) | V_cruise (m/s) | total_cost | Notes |
|-----------|-------------|---------------|----------------|------------|-------|
| — | Baseline | — | — | — | No data yet |
