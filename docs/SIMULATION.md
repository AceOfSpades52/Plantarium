# Simulation strategy

Simulation is a first-class product capability, not disposable mock code.

## Why
Until physical hardware is available, simulation lets us develop and test:

- longitudinal plant records,
- plant-state inference,
- diagnosis,
- prescriptions,
- safety behavior,
- sensor failure handling,
- experiments,
- genetics/phenotype analysis,
- multi-plant resource coordination.

The same provider contract is used by simulation and future physical sensors.

## Current simulation
`SimulatedPlantEnvironment` currently models a simple substrate plant with:

- dry system mass,
- root-zone water mass,
- field-capacity water,
- water use over time,
- pot mass,
- substrate moisture,
- air temperature/RH,
- root temperature,
- root EC.

Irrigation updates the same simulated water reservoir, so later observations can verify the treatment response.

This is intentionally simple. Passing simulation tests does not mean the biological model is realistic.

## Recorded-data replay
The replay provider is the bridge between simulation-only development and real evidence.

As soon as any real dataset becomes available—from a borrowed sensor, public research dataset, spreadsheet export, greenhouse logger, etc.—we can map it into normalized CSV and run the existing care/research stack over it without hardware.

This should be used before writing a dedicated live adapter whenever practical.

## Planned virtual grow lab
Next simulation work should add parameterized scenarios rather than hard-code one plant:

- soil
- coco/peat/substrate
- DWC/hydro reservoir
- different plant sizes and water-demand curves
- shared room/tent climate
- light/DLI
- root EC/pH
- reservoir depletion/refill
- sensor noise, drift, dropout and bad calibration
- actuator failures
- heat/drought/salinity challenge profiles
- multiple related plants for phenotype/genetics experiments

Each scenario should expose the same canonical sensor channels that real equipment would expose.

## Rule
Never label a result as a biological discovery merely because it appears in our simulator. Simulation validates software behavior and hypotheses. Biological claims require real observations and appropriate experimental evidence.
