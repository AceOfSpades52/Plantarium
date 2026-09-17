# Sensor provider contract

## Goal
The plant-care and research layers must not know whether a measurement came from a simulator, a CSV export, a wireless node, a Raspberry Pi GPIO process, MQTT, BLE, serial, HTTP, or a commercial API.

Every source converts its native data into the same `Reading` object before the care engine sees it.

## Canonical reading shape

A reading records:

- `plant_id` — subject being observed
- `metric` — normalized meaning, for example `pot_mass_g`
- `value`
- `unit`
- `source` — human-readable source
- `quality` — 0..1 evidence quality
- `observed_at`
- `provider_id` — stable provider identity
- `channel_id` — stable channel/sensor identity within the provider
- `simulated` — explicit provenance flag

Synthetic data must always set `simulated=True`. Replayed real data remains `False`.

## Provider modes

### Simulation
`SimulatedSensorAdapter`

Produces deterministic virtual sensor values from the simulated plant environment.

### Replay
`RecordedSensorAdapter`

Reads normalized CSV frames. This is useful for:

1. testing with synthetic datasets,
2. replaying exported data from real sensors before a live integration exists,
3. regression-testing new AI/state models against historical grows.

Required CSV fields:

`sample, metric, value, unit`

Optional fields:

`plant_id, source, quality, channel_id, observed_at`

Rows with the same `sample` value are one observation frame.

### Live bridge
`BufferedSensorAdapter`

A future transport process can push normalized readings into this adapter. The transport can be MQTT, HTTP, BLE, serial, GPIO, WebSocket, or something else. The care engine remains unchanged.

### Composite
`CompositeSensorAdapter`

Combines providers. A garden can therefore use a real load cell, a simulated EC sensor, and replayed climate data in the same run while a feature is being developed.

## Provider description
Every provider publishes `SensorProviderInfo` with:

- provider ID
- display name
- mode
- transport
- simulated flag
- channel list

Every `SensorChannel` describes:

- channel ID
- metric
- canonical unit
- scope (`plant`, `environment`, etc.)
- description

The database stores provider/channel descriptions separately from observations.

## Canonical metrics currently used

| Metric | Unit | Meaning |
|---|---|---|
| `pot_mass_g` | g | total container/system mass |
| `substrate_moisture_pct` | % | root-zone/substrate moisture estimate |
| `air_temp_c` | C | air temperature |
| `relative_humidity_pct` | % | air relative humidity |
| `root_temp_c` | C | root-zone temperature |
| `root_ec_ms_cm` | mS/cm | root-zone electrical conductivity |
| `leaf_temp_c` | C | leaf/canopy temperature (contract demonstrated in tests) |

More metrics will be added as capabilities are modeled. The ingestion boundary validates known metrics and converts a small set of common device units into canonical units (for example Fahrenheit -> Celsius, kg/lb/oz -> g, and uS/cm -> mS/cm). Provider-specific code should still calibrate its raw device signal before constructing a reading.

## Monitor-only mode
`PlantCareEngine(..., controller=None)` is valid.

In this mode the system can:

- collect readings,
- estimate plant state,
- produce prescriptions/recommendations,
- create alerts,

but it cannot execute treatment.

This supports users who only have sensors or manually perform care.

## Multiple readings for one metric
More than one provider may measure the same thing. Current transparent behavior selects the reading with the highest `quality` for state/reasoning helpers while preserving **all** raw readings in the database.

A future sensor-fusion model can replace this selection rule without changing stored evidence.

## Adding real hardware later
A hardware integration should only need to:

1. read the native device/transport,
2. calibrate the raw device signal and provide a supported unit,
3. construct `Reading` objects or submit them to `BufferedSensorAdapter` (the ingestion layer normalizes common supported units),
4. declare `SensorProviderInfo` / channels.

It should **not** modify `Plant`, `PlantStore`, `PlantStateEstimator`, `PlantSupervisor`, genetics, experiments, or research records.

That is the acceptance test for the provider boundary.
