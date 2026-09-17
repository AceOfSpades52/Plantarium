# Plantarium — v0.2.0 Virtual Grow Lab: Environment + Biological Clock

Plantarium is a hardware-agnostic plant supervision and research platform built around the idea that **each plant is a patient and a longitudinal research subject**.

No physical hardware is required. Simulation, recorded data, future live sensors, and human-entered measurements all cross the same normalized evidence boundary.

## One-command Android / Termux test

Run this from **any directory**:

```bash
curl -fsSL https://raw.githubusercontent.com/AceOfSpades52/Plantarium/main/termux-bootstrap.sh | bash
```

The bootstrap keeps a persistent checkout at `~/plantarium`, safely updates it, applies new downloaded Plantarium patch/test bundles once, preserves local edits, and runs the complete verification suite.

## v0.2.0: first Virtual Grow Lab slice

The simulator now has a deliberately separated three-layer model:

`Hidden true world -> observable sensor evidence -> Plantarium belief/reasoning`

The new virtual world includes:
- a deterministic simulation clock,
- day/night photoperiod,
- air temperature and humidity,
- air VPD,
- CO2,
- PAR,
- accumulated daily light integral (DLI),
- growth-stage progression,
- environment-sensitive hidden plant water demand.

The care/research system **cannot read hidden growth stage or true demand through the sensor adapter**. Tests enforce that firewall. Soil/coco and DWC root-zone physics are intentionally deferred to later v0.2 slices.

Run the lab directly:

```bash
python -m planticu.virtual_grow_demo
```

The demo prints both observable sensor values and a clearly marked developer-only hidden truth line so we can verify the simulator while proving the hidden fields were never stored as observations.

## Other runnable slices

```bash
python -m planticu demo --steps 18
python -m planticu replay-demo
python -m planticu research-demo
python -m planticu guided-demo
python -m planticu.virtual_grow_demo
```

Tests:

```bash
python -m unittest discover -s tests -v
```

## Current care path

`Provider -> Normalized Evidence -> Plant State -> Reasoning -> optional Deterministic Controller -> Treatment -> Response`

Providers include simulation, recorded CSV replay, buffered future-live input, composites, and human/manual measurements.

## Living Almanac

Knowledge remains layered rather than overwritten:

`Established -> Global learned -> Species -> Cultivar/line -> Grow method -> Garden -> Individual plant`

## Read the project

Begin with `docs/CODE_TOUR.md`, then see:
- `docs/SIMULATION.md`
- `docs/ARCHITECTURE.md`
- `docs/SENSOR_PROVIDERS.md`
- `docs/GUIDED_OBSERVATIONS.md`
- `docs/LIVING_ALMANAC.md`
- `docs/PRODUCT_MAP.md`
- `docs/TERMUX_WORKFLOW.md`
- `docs/GENOMICS.md`
- `docs/EXPERIMENTS.md`
- `STATUS.md`
