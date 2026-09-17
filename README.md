# Plantarium — v0.1.4 Repository Bootstrap + Guided Observation

Plantarium is a hardware-agnostic plant supervision and research core built around the idea that **each plant is a patient and a longitudinal research subject**.

No physical hardware is required. Simulation, recorded data, future live sensors, and **human-entered measurements** all cross the same normalized evidence boundary.


## One-command Android / Termux test

Run this from **any directory**:

```bash
curl -fsSL https://raw.githubusercontent.com/AceOfSpades52/Plantarium/main/termux-bootstrap.sh | bash
```

The bootstrap helper keeps a persistent checkout at `~/plantarium`, installs missing Termux prerequisites when possible, safely updates the Git checkout, applies any new `plantarium-patch-*.zip` or `plantarium-tests-*.zip` files found in `~/storage/downloads`, and runs the complete verification suite. It records patch hashes so the same archive is never applied twice.

Local edits are never intentionally deleted. Before an update they are stashed and a human-readable backup diff/status is written under `~/plantarium/.plantarium-local/backups/`. If Git cannot restore those edits cleanly, the script stops and leaves the conflict visible instead of overwriting the user's work.

## Run it

Requires Python 3.10+ and no third-party packages.

```bash
python -m planticu demo --steps 18
python -m planticu replay-demo
python -m planticu research-demo
python -m planticu guided-demo
```

Tests:

```bash
python -m unittest discover -s tests -v
```

On Termux:

```bash
sh termux-test.sh
```

## Current care path

`Provider -> Normalized Evidence -> Plant State -> Reasoning -> optional Deterministic Controller -> Treatment -> Response`

Providers currently include:
- simulation,
- recorded CSV replay,
- buffered future-live input,
- composites,
- human/manual measurements.

Manual measurements preserve position/method provenance. Qualitative observations are stored separately rather than converted into fake numbers.

## Living Almanac
Knowledge is layered rather than overwritten:

`Established -> Global learned -> Species -> Cultivar/line -> Grow method -> Garden -> Individual plant`

The current resolver selects relevant layers but deliberately does not pretend that network correlations are established science.

## Read the project
Begin with `docs/CODE_TOUR.md`, then see:
- `docs/TERMUX_WORKFLOW.md`
- `docs/GUIDED_OBSERVATIONS.md`
- `docs/LIVING_ALMANAC.md`
- `docs/PRODUCT_MAP.md`
- `docs/ARCHITECTURE.md`
- `docs/SENSOR_PROVIDERS.md`
- `docs/SIMULATION.md`
- `docs/GENOMICS.md`
- `docs/EXPERIMENTS.md`
- `STATUS.md`
