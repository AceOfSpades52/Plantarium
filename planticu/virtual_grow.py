from __future__ import annotations

import math
from dataclasses import dataclass

from .adapters import SensorAdapter
from .domain import Plant, Reading, SensorChannel, SensorProviderInfo
from .environmental_math import clamp, par_to_dli_increment, vapor_pressure_deficit_kpa


@dataclass
class SimulationClock:
    """A small deterministic clock for virtual grows.

    The clock begins at day 1, hour 0. ``elapsed_hours`` is deliberately kept
    as the single source of truth so advancing time cannot make day/hour fields
    disagree with one another.
    """

    elapsed_hours: float = 0.0

    @property
    def day_number(self) -> int:
        return int(self.elapsed_hours // 24.0) + 1

    @property
    def hour_of_day(self) -> float:
        return self.elapsed_hours % 24.0

    def advance(self, hours: float) -> None:
        if hours < 0.0:
            raise ValueError("simulation time cannot move backward")
        self.elapsed_hours += hours


@dataclass(frozen=True)
class VirtualEnvironmentProfile:
    """Configured day/night conditions for one virtual grow area."""

    lights_on_hour: float = 6.0
    lights_off_hour: float = 18.0
    peak_par_umol_m2_s: float = 650.0
    day_temp_c: float = 26.0
    night_temp_c: float = 20.0
    day_relative_humidity_pct: float = 55.0
    night_relative_humidity_pct: float = 70.0
    day_co2_ppm: float = 850.0
    night_co2_ppm: float = 600.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.lights_on_hour < 24.0:
            raise ValueError("lights_on_hour must be within 0..24")
        if not 0.0 < self.lights_off_hour <= 24.0:
            raise ValueError("lights_off_hour must be within 0..24")
        if self.lights_off_hour <= self.lights_on_hour:
            raise ValueError("v0.2.0 requires lights_off_hour after lights_on_hour on the same day")
        if self.peak_par_umol_m2_s < 0.0:
            raise ValueError("peak PAR cannot be negative")

    @property
    def photoperiod_hours(self) -> float:
        return self.lights_off_hour - self.lights_on_hour

    def light_fraction(self, hour_of_day: float) -> float:
        """Return a smooth 0..1 daylight fraction for the configured photoperiod."""

        hour = hour_of_day % 24.0
        if hour < self.lights_on_hour or hour >= self.lights_off_hour:
            return 0.0

        progress = (hour - self.lights_on_hour) / self.photoperiod_hours
        return math.sin(math.pi * progress)


@dataclass(frozen=True)
class GrowthStageRule:
    """One stage transition used by the hidden virtual plant model."""

    start_day: int
    stage: str
    water_demand_multiplier: float


@dataclass(frozen=True)
class VirtualPlantProfile:
    """Hidden plant parameters used to calculate synthetic biological demand."""

    base_daily_water_demand_ml: float = 360.0
    stage_rules: tuple[GrowthStageRule, ...] = (
        GrowthStageRule(1, "seedling", 0.45),
        GrowthStageRule(14, "vegetative", 1.00),
        GrowthStageRule(42, "flowering", 1.18),
        GrowthStageRule(70, "fruiting", 1.30),
    )

    def __post_init__(self) -> None:
        if self.base_daily_water_demand_ml < 0.0:
            raise ValueError("base water demand cannot be negative")
        if not self.stage_rules:
            raise ValueError("at least one growth-stage rule is required")
        previous_day = 0
        for rule in self.stage_rules:
            if rule.start_day < 1 or rule.start_day < previous_day:
                raise ValueError("growth-stage rules must be ordered by start_day")
            if rule.water_demand_multiplier < 0.0:
                raise ValueError("water-demand multiplier cannot be negative")
            previous_day = rule.start_day

    def stage_rule_for_day(self, day_number: int) -> GrowthStageRule:
        selected = self.stage_rules[0]
        for rule in self.stage_rules:
            if day_number >= rule.start_day:
                selected = rule
            else:
                break
        return selected


@dataclass(frozen=True)
class VirtualGrowSnapshot:
    """The simulator's hidden true state at one instant.

    Some fields are observable through virtual sensors. Other fields, such as
    ``true_water_demand_ml_day`` and ``growth_stage``, are intentionally hidden
    from ``VirtualGrowSensorAdapter``. This models the real-world distinction
    between what a plant *is doing* and what instruments can actually observe.
    """

    day_number: int
    hour_of_day: float
    lights_on: bool
    air_temp_c: float
    relative_humidity_pct: float
    vpd_kpa: float
    co2_ppm: float
    par_umol_m2_s: float
    dli_mol_m2_day: float
    previous_day_dli_mol_m2_day: float
    growth_stage: str
    true_water_demand_ml_day: float
    cumulative_true_water_demand_ml: float


class VirtualGrowLab:
    """Deterministic hidden-world simulation for environment + plant demand.

    v0.2.0 deliberately models only shared environment, biological time, growth
    stage, and synthetic water demand. Soil/coco and DWC root-zone physics come
    in later slices so each piece stays understandable and independently tested.
    """

    def __init__(
        self,
        environment: VirtualEnvironmentProfile | None = None,
        plant_profile: VirtualPlantProfile | None = None,
        clock: SimulationClock | None = None,
    ) -> None:
        self.environment = environment or VirtualEnvironmentProfile()
        self.plant_profile = plant_profile or VirtualPlantProfile()
        self.clock = clock or SimulationClock()
        self._current_day_dli = 0.0
        self._previous_day_dli = 0.0
        self._cumulative_true_water_demand_ml = 0.0

    def _environment_at_hour(self, hour_of_day: float) -> tuple[float, float, float, float]:
        light_fraction = self.environment.light_fraction(hour_of_day)

        # These simple interpolations are intentionally transparent. They are
        # test signals, not validated greenhouse climate dynamics.
        temp = self.environment.night_temp_c + (
            self.environment.day_temp_c - self.environment.night_temp_c
        ) * light_fraction
        humidity = self.environment.night_relative_humidity_pct + (
            self.environment.day_relative_humidity_pct - self.environment.night_relative_humidity_pct
        ) * light_fraction
        co2 = self.environment.night_co2_ppm + (
            self.environment.day_co2_ppm - self.environment.night_co2_ppm
        ) * light_fraction
        par = self.environment.peak_par_umol_m2_s * light_fraction
        return temp, humidity, co2, par

    def _true_water_demand_ml_day(self, day_number: int, hour_of_day: float) -> float:
        stage = self.plant_profile.stage_rule_for_day(day_number)
        temp, humidity, _, par = self._environment_at_hour(hour_of_day)
        vpd = vapor_pressure_deficit_kpa(temp, humidity)

        # The coefficients below create believable *software-test behavior*:
        # warmer/drier/brighter conditions raise demand, while night lowers it.
        # They are not crop-science recommendations.
        light_fraction = 0.0
        if self.environment.peak_par_umol_m2_s > 0.0:
            light_fraction = par / self.environment.peak_par_umol_m2_s
        light_factor = 0.30 + 0.70 * light_fraction
        vpd_factor = clamp(0.65 + (vpd / 1.2) * 0.35, 0.55, 1.45)
        temp_factor = clamp(1.0 + (temp - 24.0) * 0.025, 0.70, 1.35)

        return (
            self.plant_profile.base_daily_water_demand_ml
            * stage.water_demand_multiplier
            * light_factor
            * vpd_factor
            * temp_factor
        )

    def snapshot(self) -> VirtualGrowSnapshot:
        day = self.clock.day_number
        hour = self.clock.hour_of_day
        temp, humidity, co2, par = self._environment_at_hour(hour)
        vpd = vapor_pressure_deficit_kpa(temp, humidity)
        stage = self.plant_profile.stage_rule_for_day(day)
        water_demand = self._true_water_demand_ml_day(day, hour)

        return VirtualGrowSnapshot(
            day_number=day,
            hour_of_day=hour,
            lights_on=par > 0.0,
            air_temp_c=temp,
            relative_humidity_pct=humidity,
            vpd_kpa=vpd,
            co2_ppm=co2,
            par_umol_m2_s=par,
            dli_mol_m2_day=self._current_day_dli,
            previous_day_dli_mol_m2_day=self._previous_day_dli,
            growth_stage=stage.stage,
            true_water_demand_ml_day=water_demand,
            cumulative_true_water_demand_ml=self._cumulative_true_water_demand_ml,
        )

    def advance(self, hours: float) -> VirtualGrowSnapshot:
        """Advance the hidden world and return its new snapshot.

        We integrate in small chunks so DLI and demand remain stable even when a
        caller advances several hours at once. The 15-minute internal interval
        is a software-simulation choice, not a required real sensor frequency.
        """

        if hours < 0.0:
            raise ValueError("simulation time cannot move backward")

        remaining = hours
        while remaining > 1e-9:
            hours_to_midnight = 24.0 - self.clock.hour_of_day
            if hours_to_midnight <= 1e-9:
                hours_to_midnight = 24.0
            step = min(0.25, remaining, hours_to_midnight)

            start_day = self.clock.day_number
            midpoint_hour = (self.clock.hour_of_day + step / 2.0) % 24.0
            _, _, _, midpoint_par = self._environment_at_hour(midpoint_hour)
            midpoint_demand = self._true_water_demand_ml_day(start_day, midpoint_hour)

            self._current_day_dli += par_to_dli_increment(midpoint_par, step)
            self._cumulative_true_water_demand_ml += midpoint_demand * step / 24.0
            self.clock.advance(step)
            remaining -= step

            if self.clock.day_number != start_day:
                self._previous_day_dli = self._current_day_dli
                self._current_day_dli = 0.0

        return self.snapshot()


class VirtualGrowSensorAdapter(SensorAdapter):
    """Expose only observable environment signals from ``VirtualGrowLab``.

    The adapter is the firewall between simulated truth and the care/research
    system. Hidden growth stage and true plant demand are intentionally absent.
    """

    def __init__(self, lab: VirtualGrowLab, provider_id: str = "virtual_grow_environment") -> None:
        self.lab = lab
        self._info = SensorProviderInfo(
            provider_id=provider_id,
            display_name="Virtual Grow Lab environment sensors",
            mode="simulation",
            transport="in_process",
            simulated=True,
            channels=(
                SensorChannel("air_temp", "air_temp_c", "C", scope="environment"),
                SensorChannel("air_rh", "relative_humidity_pct", "%", scope="environment"),
                SensorChannel("air_vpd", "vpd_kpa", "kPa", scope="environment"),
                SensorChannel("co2", "co2_ppm", "ppm", scope="environment"),
                SensorChannel("par", "par_umol_m2_s", "umol/m2/s", scope="environment"),
                SensorChannel("dli", "dli_mol_m2_day", "mol/m2/day", scope="environment"),
            ),
        )

    @property
    def info(self) -> SensorProviderInfo:
        return self._info

    def _reading(self, plant: Plant, channel_id: str, metric: str, value: float, unit: str) -> Reading:
        snapshot = self.lab.snapshot()
        return Reading(
            plant_id=plant.plant_id,
            metric=metric,
            value=value,
            unit=unit,
            source=self.info.display_name,
            provider_id=self.info.provider_id,
            channel_id=channel_id,
            simulated=True,
            context={
                "simulation_day": snapshot.day_number,
                "simulation_hour": round(snapshot.hour_of_day, 4),
                "observation_class": "environment_sensor",
            },
        )

    def read(self, plant: Plant) -> list[Reading]:
        snapshot = self.lab.snapshot()
        return [
            self._reading(plant, "air_temp", "air_temp_c", snapshot.air_temp_c, "C"),
            self._reading(
                plant,
                "air_rh",
                "relative_humidity_pct",
                snapshot.relative_humidity_pct,
                "%",
            ),
            self._reading(plant, "air_vpd", "vpd_kpa", snapshot.vpd_kpa, "kPa"),
            self._reading(plant, "co2", "co2_ppm", snapshot.co2_ppm, "ppm"),
            self._reading(
                plant,
                "par",
                "par_umol_m2_s",
                snapshot.par_umol_m2_s,
                "umol/m2/s",
            ),
            self._reading(
                plant,
                "dli",
                "dli_mol_m2_day",
                snapshot.dli_mol_m2_day,
                "mol/m2/day",
            ),
        ]
