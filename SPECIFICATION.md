## Aircraft Specification

Number of engines: 1
Engine type: gasoline (4-stroke or equivalent)
Engine power: 31 kW  (41.6 hp)
Engine mass: 42 kg
Engine compartment: engine requires a volume no smaller than 0.8 m × 0.6 m × 0.6 m (length × width × height)

Aircraft empty mass: target ≤ 125 kg
Aircraft number of passengers: 1
Aircraft useful load (passenger + baggage): 110 kg  (passenger ≤ 100 kg, baggage ≤ 10 kg)
Aircraft max gross weight (MTOW): 295 kg
Aircraft range: 1667 km  (900 nautical miles)
Aircraft fuel capacity: assume BSFC = 0.30 kg/kWhr at 75% power.  Determine fuel from range and cruise speed.
Stall speed: less than 17.9 m/s  (40 mph)
Cruise speed: approximately 50 m/s  (180 km/hr, 97 knots) at 75% power
Stability: aircraft will have positive longitudinal stability (Cm_alpha < 0).  Righting moments should minimize induced cross response in other axes.
Size: aircraft is small and built for only one person

Wing: high-wing configuration (wing mounts on top of fuselage)
Wing airfoil: NACA 4412 (4% camber, 12% thickness)
Wing twist: the wings should have a washout twist (tip pitched down ~1.5°) so that a stall progresses from the inboard root outward
Planform: conventional tractor configuration.  Single fuselage from nose to tail.  No pod-and-boom (permanently retired per CLAUDE.md).
Model: the model should model a propeller as a thrust disk
Model: the following are model features that can be changed to optimize performance: airfoil, wing chord, wing length, wing location, wing sweep, fuselage cross section and cross-section location relative to centerline, tail size, tail position.
Optimization targets: reduced weight, maximum cruise speed, minimum stall speed, positive stability, reduced parasite drag


## Constraints

- Wingspan shall not exceed 15 m
- Cockpit size: cockpit area must accommodate a pilot who is 2.0 m (6'7") tall.  Minimum internal cockpit height: 1.25 m.  It should allow for 0.30 m of clearance on each side of a large adult's shoulders (minimum internal width: 1.10 m).
- Geometry connectivity: all wings, horizontal tails, vertical tails, and other flying surfaces must be physically connected to the fuselage.  No floating surfaces.
- Fuselage will have no sharp curves — elegant sweeping spline profiles.
- Engine compartment: fuselage must enclose a volume of 0.8 m × 0.6 m × 0.6 m for the engine ahead of the cockpit.
- All units are SI.  Do not use imperial units in any design file.
