# Deferred Hardware Bridge

Physical hardware is **not currently required or assumed available**. Development should continue against simulation, replay, and transport-neutral provider contracts.

When hardware becomes available, the acceptance condition is simple: a real provider must replace one or more simulated channels without changing the plant domain, store, state estimator, supervisor, genetics, experiments, or research layers.

## Likely first physical station

### Minimum capabilities
- controller node capable of reading sensors and optionally switching a low-voltage irrigation device
- calibrated pot/load-cell mass measurement
- air temperature + relative humidity
- root-zone/substrate moisture measurement
- stable plant/station identifier

### Strongly recommended later
- root-zone temperature
- electrical conductivity (EC)
- local light/PAR measurement
- fixed camera position

## Physical safety
The intelligence layer never directly energizes a pump or dosing device. Firmware/device controllers must retain independent maximum run-time, maximum dose, sensor-validity, and fail-safe-off behavior.

## Communication contract
A future node should expose canonical observations rather than making the server understand individual sensor brands. MQTT, BLE, serial, HTTP, GPIO, or another transport can feed `BufferedSensorAdapter` or implement `SensorAdapter` directly.

Example telemetry:

```json
{
  "station_id": "station-001",
  "plant_id": "plant-001",
  "observations": [
    {"metric": "pot_mass_g", "value": 3212.4, "unit": "g", "quality": 0.99},
    {"metric": "air_temp_c", "value": 77.2, "unit": "F", "quality": 0.98},
    {"metric": "relative_humidity_pct", "value": 57.8, "unit": "%", "quality": 0.98}
  ]
}
```

The ingestion boundary can normalize common supported units before reasoning.

Example bounded command:

```json
{
  "command_id": "cmd-123",
  "capability": "water",
  "plant_id": "plant-001",
  "amount_ml": 120,
  "expires_in_s": 30
}
```

The node must independently reject an invalid, expired, or physically unsafe command.
