# Beginner code tour

The codebase intentionally favors small modules and explicit data flow over clever abstractions.

## Start here

### `planticu/domain.py`
The nouns: Plant, Reading, Environment, GeneticProfile, KnowledgeEntry, Prescription, etc. If you want to know what information the system stores, start here.

### `planticu/adapters.py`
Where machine/simulated data enters. Simulation, CSV replay, and future live bridges all implement `SensorAdapter`.

### `planticu/guided_observation.py`
Where human-entered measurements enter. A person with a thermometer or meter is treated as a real evidence provider.

### `planticu/metrics.py`
Normalizes units. For example, Fahrenheit becomes Celsius and kilograms become grams before reasoning.

### `planticu/state.py`
Turns raw readings into a simple plant-state estimate. It is deliberately transparent today.

### `planticu/supervisor.py`
Makes care recommendations. It never talks directly to pumps or other hardware.

### `planticu/controller.py`
Safety boundary for physical treatment. Deterministic limits belong here, not in an AI prompt.

### `planticu/store.py`
SQLite persistence for the plant's longitudinal record and research evidence.

### `planticu/knowledge.py`
Selects relevant Living Almanac layers without overwriting broader knowledge.

### `planticu/engine.py`
The care pipeline that connects providers -> normalized evidence -> state -> reasoning -> optional control.

### `planticu/__main__.py`
Runnable demos. This is a useful place for a beginner to trace complete examples.

## Read one vertical slice
For the manual-care path, read in this order:

1. `guided_observation.py`
2. `metrics.py`
3. `engine.py`
4. `state.py`
5. `supervisor.py`
6. `store.py`
7. `tests/test_guided_knowledge.py`

The test file is intentionally readable as executable documentation.
