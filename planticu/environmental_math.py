from __future__ import annotations

import math


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Keep ``value`` inside an inclusive range.

    Keeping this tiny helper here makes the simulation equations easier for a
    beginner to read. It also prevents impossible values such as negative RH.
    """

    return max(minimum, min(maximum, value))


def saturation_vapor_pressure_kpa(air_temp_c: float) -> float:
    """Approximate saturation vapor pressure of air at a temperature.

    This is the common Tetens-style approximation. Plantarium currently uses
    it only to create a useful *simulation signal*; it is not a claim that our
    virtual plant is a validated crop-physiology model.
    """

    return 0.6108 * math.exp((17.27 * air_temp_c) / (air_temp_c + 237.3))


def vapor_pressure_deficit_kpa(air_temp_c: float, relative_humidity_pct: float) -> float:
    """Return air VPD from temperature and relative humidity.

    This is an air VPD estimate. A future leaf-temperature-aware model can
    calculate leaf VPD separately without changing this function's meaning.
    """

    rh_fraction = clamp(relative_humidity_pct, 0.0, 100.0) / 100.0
    saturated = saturation_vapor_pressure_kpa(air_temp_c)
    return max(0.0, saturated * (1.0 - rh_fraction))


def par_to_dli_increment(par_umol_m2_s: float, elapsed_hours: float) -> float:
    """Convert PAR over a time interval into a DLI increment.

    PAR is micromoles per square metre per second. Multiplying by seconds and
    dividing by one million converts micromoles to moles.
    """

    safe_par = max(0.0, par_umol_m2_s)
    safe_hours = max(0.0, elapsed_hours)
    return safe_par * safe_hours * 3600.0 / 1_000_000.0
