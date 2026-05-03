Number of engines: 1
Engine type: gasoline
Engine power: 18 hp
Engine mass: 40 kg
Aircraft empty mass: less than 110 kg
Aircraft number of passengers: 1
Aircraft useful load, including passenger and baggage: 117 kg
Aircraft max gross weight: 218 kg
Aircraft range: 1100 km
Aircraft fuel capacity: assume 30.3 L/hour fuel burn. Determine capacity based on range requirement and computed cruise speed.
Stall speed: less than 21 m/s
Cruise speed: 54.2 m/s
Stability: aircraft will have positive stability. Righting moments should minimize induced cross response in other axes.
Size: aircraft is small and built for only one person
Skin density: 6 kg/m^2
Planform: any that meets the specification is fine.  A canard or tandem wing increases stall safety and should be considered alongside traditional planform designs
Wing twist:  the wings should have a twist so that a stall progresses from the inboard root of the wing outward
Canard: if a front canard or tandem wing configuraiton is used, the canard should have a lower stall speed than the main wing so that the aircraft pitches downward at onset of stall.  The front wing should stall at least 5 km/hr sooner than the main wing
Model: the model should model a propeller as a thrust disk
Model: the following are model features that can be changed in an attempt to optimize performance: airfoil, wing chord, wing length, wing location, wing sweep, new wing seciton, pod on wing , fuselage cross section and cross sectino location relative to centerline, new fuselage sections.
Optimization:  the following should be optimization targets: reduced weight, increased cruise speed, decreased stall speed, increased stability, decreased coupling of instability modes, reduced curvature of fuselage (i.e. less sharp transitions in section crosssections)
Model: each new model should have a unique filename so that changes can be tracked.  The filename should include mm_dd_yyyy_xx where xx is a version
Cockpit:  The cockpit area should be located such that the center of gravity of the aircraft is located in the cockpit.  The cockpit should have an unobstructed view for the pilot. There should be no wings or structure impeeding that view.  You should move the sections that comprise the cockpit up or down if necessary to allow for an unobstructed view.


## Constraints

- Wingspan shall not exceed 15m
- Cockpit size: cockpit area should accomodate a pilot who is 2 meters tall.  It should allow for .3 m of clearance on each side of a large adults shoulders
- Geometry connectivity: all wings, canards, horizontal tails, vertical tails, and other flying surfaces must be physically connected to the fuselage or a structural fairing. OpenVSP designs must not contain floating flying surfaces.
- Engine Compartment: the engine is assumed to require a volume no smaller than .8 m by .6m by .6m.
- Fuselage will have no sharp curves but instead will be elegant and sweeping