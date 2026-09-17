from __future__ import annotations

import math
from dataclasses import dataclass, replace

from .domain import Reading


@dataclass(frozen=True)
class MetricDefinition:
    metric: str
    canonical_unit: str
    description: str


METRICS: dict[str, MetricDefinition] = {
    "pot_mass_g": MetricDefinition("pot_mass_g", "g", "Total container/system mass"),
    "substrate_moisture_pct": MetricDefinition("substrate_moisture_pct", "%", "Substrate/root-zone moisture estimate"),
    "air_temp_c": MetricDefinition("air_temp_c", "C", "Air temperature"),
    "relative_humidity_pct": MetricDefinition("relative_humidity_pct", "%", "Air relative humidity"),
    "root_temp_c": MetricDefinition("root_temp_c", "C", "Root-zone temperature"),
    "leaf_temp_c": MetricDefinition("leaf_temp_c", "C", "Leaf/canopy temperature"),
    "root_ec_ms_cm": MetricDefinition("root_ec_ms_cm", "mS/cm", "Root-zone electrical conductivity"),
    "ph": MetricDefinition("ph", "pH", "Acidity/alkalinity"),
    "co2_ppm": MetricDefinition("co2_ppm", "ppm", "Carbon dioxide concentration"),
    "par_umol_m2_s": MetricDefinition("par_umol_m2_s", "umol/m2/s", "Photosynthetically active radiation"),
    "dli_mol_m2_day": MetricDefinition("dli_mol_m2_day", "mol/m2/day", "Daily light integral"),
    "reservoir_level_pct": MetricDefinition("reservoir_level_pct", "%", "Reservoir level estimate"),
    "reservoir_temp_c": MetricDefinition("reservoir_temp_c", "C", "Nutrient-solution/reservoir temperature"),
    "dissolved_oxygen_mg_l": MetricDefinition("dissolved_oxygen_mg_l", "mg/L", "Dissolved oxygen"),
}


def _temperature_to_c(value: float, unit: str) -> float:
    normalized = unit.strip().lower().replace("°", "")
    if normalized in {"c", "celsius"}:
        return value
    if normalized in {"f", "fahrenheit"}:
        return (value - 32.0) * 5.0 / 9.0
    if normalized in {"k", "kelvin"}:
        return value - 273.15
    raise ValueError(f"unsupported temperature unit: {unit}")


def normalize_metric_value(metric: str, value: float, unit: str) -> tuple[float, str]:
    """Convert a small set of common device units into canonical platform units."""
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"non-finite value for {metric}: {value}")

    definition = METRICS.get(metric)
    if definition is None:
        if not unit.strip():
            raise ValueError(f"unknown metric {metric!r} requires an explicit unit")
        return value, unit.strip()

    canonical = definition.canonical_unit
    raw = unit.strip()
    low = raw.lower().replace("μ", "u")

    if canonical == "C":
        return _temperature_to_c(value, raw), canonical
    if canonical == "g":
        if low in {"g", "gram", "grams"}:
            return value, canonical
        if low in {"kg", "kilogram", "kilograms"}:
            return value * 1000.0, canonical
        if low in {"lb", "lbs", "pound", "pounds"}:
            return value * 453.59237, canonical
        if low in {"oz", "ounce", "ounces"}:
            return value * 28.349523125, canonical
        raise ValueError(f"unsupported mass unit for {metric}: {unit}")
    if canonical == "%":
        if low in {"%", "percent", "pct"}:
            return value, canonical
        if low in {"fraction", "ratio"}:
            return value * 100.0, canonical
        raise ValueError(f"unsupported percentage unit for {metric}: {unit}")
    if canonical == "mS/cm":
        if low in {"ms/cm", "ms/cm."}:
            return value, canonical
        if low in {"us/cm", "us/cm."}:
            return value / 1000.0, canonical
        raise ValueError(f"unsupported EC unit for {metric}: {unit}")

    # Units with no current conversion path must already be canonical.
    if raw != canonical:
        raise ValueError(f"{metric} expects {canonical}, got {unit}")
    return value, canonical


def normalize_reading(reading: Reading) -> Reading:
    if not reading.metric.strip():
        raise ValueError("reading metric cannot be empty")
    if not 0.0 <= reading.quality <= 1.0:
        raise ValueError(f"reading quality must be between 0 and 1: {reading.quality}")
    value, unit = normalize_metric_value(reading.metric, reading.value, reading.unit)
    return replace(reading, value=value, unit=unit)


def normalize_readings(readings: list[Reading]) -> list[Reading]:
    return [normalize_reading(reading) for reading in readings]
