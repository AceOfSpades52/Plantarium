# Architecture

## Product mental model

Each plant is simultaneously:
- a **patient** with an individual care history,
- a **research subject** with measured phenotype and environmental exposure,
- and optionally a **genetic individual** within a lineage.

Core care path:

`Perception/Sensors -> Raw Evidence -> Plant State -> Clinical Reasoning -> Prescription -> Deterministic Safety Controller -> Adapter -> Treatment -> Response`

Research path:

`Genetic Evidence + Lineage + Environment + Challenge + Experiment + Phenotype -> Analysis -> Candidate Association -> Validation`

A candidate association is not a causal claim.

## Observation provider boundary
The care/research core receives normalized `Reading` evidence through `SensorAdapter`. Simulation, recorded-data replay, mixed sources, and future live transports implement the same contract. Provider/channel identity and whether a reading is simulated are persisted with the observation.

`CompositeSensorAdapter` allows gradual replacement: one metric can become real while the rest remain simulated. `BufferedSensorAdapter` lets a future MQTT/BLE/serial/HTTP bridge push normalized measurements without changing `PlantCareEngine`.

Actuation is optional. With `controller=None`, the system remains a monitor/diagnostic advisor and never executes treatment.

`HumanMeasurementAdapter` implements the same provider contract. A handheld measurement is therefore normal evidence, with position/method/notes retained in `Reading.context`. Qualitative observations use a separate record instead of inventing numeric sensor values.

## Intelligence tiers

### Device intelligence
Future ESP32-class nodes: calibration, filtering, watchdogs, link health, bounded actuator failsafes. Until hardware exists, their output contracts are exercised through simulation/replay providers.

### Garden intelligence
Raspberry Pi-class hub: database, telemetry, local care loop, lightweight inference, cached policies, offline operation.

### Deep intelligence
Local workstation/cloud/on-prem model: multimodal vision, diagnosis, genomics interpretation, cross-grow analysis, breeding research, discovery.

Cloud loss must not stop bounded local care.

## Perception
`PerceptionAdapter` allows a multimodal model to inspect photos without coupling the domain to one AI vendor. Interpretations store model name, evidence source, payload, confidence, and time.

## Plant state
Raw readings are not the same as state. `PlantStateEstimate` represents inferred hydration/stress with confidence and evidence. Future learned time-series models should implement this role without deleting raw observations.

## Safe control
AI never directly toggles a pump, nutrient doser, heater, light, CO2 solenoid, or similar actuator. It asks for a target/change; deterministic controllers enforce hard physical limits and adapter calibration.

## Genetics
Raw genetic assets are durable evidence. The current VCF importer normalizes variants but deliberately does not assign biological meaning. Future QTL/GWAS/genomic-selection models operate above this evidence layer.

## Experiments
An experiment links subjects to an environment, optional challenge profile, and cohorts. Trait observations remain measurements with method and quality metadata. This supports later genotype-by-environment analysis.

## Knowledge
The Living Almanac preserves multiple evidence scopes: established, global learned, species, cultivar/line, grow method, garden/setup, and individual plant. More-specific knowledge supplements rather than deletes broader knowledge. Candidate learned patterns require replication/validation before they can be treated as conventional guidance.
