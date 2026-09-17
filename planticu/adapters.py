from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .domain import Plant, Reading, SensorChannel, SensorProviderInfo, utc_now_iso


class SensorAdapter(ABC):
    """Normalized observation provider.

    Care logic depends only on this contract. A provider may be a simulator,
    replay file, wireless bridge, serial device, API, or real sensor package.
    """

    @property
    @abstractmethod
    def info(self) -> SensorProviderInfo:
        raise NotImplementedError

    @abstractmethod
    def read(self, plant: Plant) -> list[Reading]:
        raise NotImplementedError

    def provider_infos(self) -> tuple[SensorProviderInfo, ...]:
        return (self.info,)


class CompositeSensorAdapter(SensorAdapter):
    """Combines any number of providers without changing the care engine."""

    def __init__(self, providers: Iterable[SensorAdapter]) -> None:
        self.providers = tuple(providers)
        if not self.providers:
            raise ValueError("CompositeSensorAdapter requires at least one provider")

    @property
    def info(self) -> SensorProviderInfo:
        channels: list[SensorChannel] = []
        for provider in self.providers:
            channels.extend(provider.info.channels)
        return SensorProviderInfo(
            provider_id="composite",
            display_name="Composite sensor provider",
            mode="composite",
            transport="internal",
            simulated=all(provider.info.simulated for provider in self.providers),
            channels=tuple(channels),
        )

    def provider_infos(self) -> tuple[SensorProviderInfo, ...]:
        infos: list[SensorProviderInfo] = []
        for provider in self.providers:
            infos.extend(provider.provider_infos())
        return tuple(infos)

    def read(self, plant: Plant) -> list[Reading]:
        readings: list[Reading] = []
        for provider in self.providers:
            readings.extend(provider.read(plant))
        return readings


class WaterAdapter(ABC):
    name: str

    @abstractmethod
    def irrigate(self, plant: Plant, amount_ml: float) -> float:
        """Return the amount the hardware reports as actually delivered."""
        raise NotImplementedError


@dataclass
class SimulatedPlantEnvironment:
    """Simple physical state used by the current substrate simulation."""

    dry_system_mass_g: float = 2600.0
    water_mass_g: float = 700.0
    field_capacity_water_g: float = 900.0
    air_temp_c: float = 25.0
    relative_humidity_pct: float = 58.0
    daily_water_use_ml: float = 420.0
    root_ec_ms_cm: float = 1.45
    root_temp_c: float = 22.5

    def advance_hours(self, hours: float) -> None:
        loss = self.daily_water_use_ml * max(hours, 0.0) / 24.0
        self.water_mass_g = max(0.0, self.water_mass_g - loss)

    @property
    def pot_mass_g(self) -> float:
        return self.dry_system_mass_g + self.water_mass_g

    @property
    def substrate_moisture_pct(self) -> float:
        if self.field_capacity_water_g <= 0:
            return 0.0
        return max(0.0, min(100.0, 100.0 * self.water_mass_g / self.field_capacity_water_g))


class SimulatedSensorAdapter(SensorAdapter):
    def __init__(self, environment: SimulatedPlantEnvironment, provider_id: str = "simulated_station") -> None:
        self.environment = environment
        self._info = SensorProviderInfo(
            provider_id=provider_id,
            display_name="Simulated substrate station",
            mode="simulation",
            transport="in_process",
            simulated=True,
            channels=(
                SensorChannel("load_cell", "pot_mass_g", "g", description="Total pot/system mass"),
                SensorChannel("root_moisture", "substrate_moisture_pct", "%", description="Simulated substrate water content"),
                SensorChannel("air_temp", "air_temp_c", "C", scope="environment"),
                SensorChannel("air_rh", "relative_humidity_pct", "%", scope="environment"),
                SensorChannel("root_ec", "root_ec_ms_cm", "mS/cm"),
                SensorChannel("root_temp", "root_temp_c", "C"),
            ),
        )

    @property
    def info(self) -> SensorProviderInfo:
        return self._info

    def _reading(self, plant: Plant, channel_id: str, metric: str, value: float, unit: str) -> Reading:
        return Reading(
            plant.plant_id,
            metric,
            value,
            unit,
            self.info.display_name,
            provider_id=self.info.provider_id,
            channel_id=channel_id,
            simulated=True,
        )

    def read(self, plant: Plant) -> list[Reading]:
        env = self.environment
        return [
            self._reading(plant, "load_cell", "pot_mass_g", env.pot_mass_g, "g"),
            self._reading(plant, "root_moisture", "substrate_moisture_pct", env.substrate_moisture_pct, "%"),
            self._reading(plant, "air_temp", "air_temp_c", env.air_temp_c, "C"),
            self._reading(plant, "air_rh", "relative_humidity_pct", env.relative_humidity_pct, "%"),
            self._reading(plant, "root_ec", "root_ec_ms_cm", env.root_ec_ms_cm, "mS/cm"),
            self._reading(plant, "root_temp", "root_temp_c", env.root_temp_c, "C"),
        ]


class RecordedSensorAdapter(SensorAdapter):
    """Replays normalized sensor frames from CSV.

    This is intentionally useful for both simulation and *real* exported data.
    Required columns: sample, metric, value, unit. Optional: plant_id, source,
    quality, channel_id, observed_at. Rows sharing `sample` are returned together.
    """

    def __init__(
        self,
        path: str | Path,
        provider_id: str = "recorded_csv",
        loop: bool = False,
        simulated: bool = False,
    ) -> None:
        self.path = Path(path)
        self.loop = loop
        self._frames = self._load_frames(self.path)
        if not self._frames:
            raise ValueError(f"No sensor rows found in {self.path}")
        self._index = 0
        channels: dict[str, SensorChannel] = {}
        for frame in self._frames:
            for row in frame:
                channel_id = row.get("channel_id") or row["metric"]
                channels[channel_id] = SensorChannel(channel_id, row["metric"], row["unit"])
        self._info = SensorProviderInfo(
            provider_id=provider_id,
            display_name=f"Recorded sensor data: {self.path.name}",
            mode="replay",
            transport="csv",
            simulated=simulated,
            channels=tuple(channels.values()),
        )

    @property
    def info(self) -> SensorProviderInfo:
        return self._info

    @property
    def exhausted(self) -> bool:
        return not self.loop and self._index >= len(self._frames)

    @staticmethod
    def _load_frames(path: Path) -> list[list[dict[str, str]]]:
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        order: list[str] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"sample", "metric", "value", "unit"}
            if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
                raise ValueError(f"CSV must contain columns: {sorted(required)}")
            for row in reader:
                sample = row["sample"].strip()
                if sample not in grouped:
                    order.append(sample)
                grouped[sample].append(row)
        return [grouped[sample] for sample in order]

    def read(self, plant: Plant) -> list[Reading]:
        if self._index >= len(self._frames):
            if not self.loop:
                return []
            self._index = 0

        rows = self._frames[self._index]
        self._index += 1
        readings: list[Reading] = []
        for row in rows:
            row_plant = (row.get("plant_id") or "").strip()
            if row_plant and row_plant != plant.plant_id:
                continue
            readings.append(
                Reading(
                    plant_id=plant.plant_id,
                    metric=row["metric"].strip(),
                    value=float(row["value"]),
                    unit=row["unit"].strip(),
                    source=(row.get("source") or self.info.display_name).strip(),
                    quality=float((row.get("quality") or "1.0").strip()),
                    observed_at=(row.get("observed_at") or "").strip() or utc_now_iso(),
                    provider_id=self.info.provider_id,
                    channel_id=(row.get("channel_id") or row["metric"]).strip(),
                    simulated=self.info.simulated,
                )
            )
        return readings


class BufferedSensorAdapter(SensorAdapter):
    """Push-to-pull bridge for future live hardware transports.

    An MQTT/HTTP/serial/BLE bridge can submit normalized readings here while the
    unchanged PlantCareEngine continues to call `read()`. The transport itself is
    deliberately outside the plant domain.
    """

    def __init__(
        self,
        provider_id: str,
        display_name: str,
        transport: str,
        channels: Iterable[SensorChannel],
    ) -> None:
        self._info = SensorProviderInfo(
            provider_id=provider_id,
            display_name=display_name,
            mode="live",
            transport=transport,
            simulated=False,
            channels=tuple(channels),
        )
        self._buffer: deque[Reading] = deque()

    @property
    def info(self) -> SensorProviderInfo:
        return self._info

    def submit(
        self,
        plant_id: str,
        metric: str,
        value: float,
        unit: str,
        *,
        channel_id: str | None = None,
        quality: float = 1.0,
        observed_at: str | None = None,
    ) -> None:
        kwargs = {}
        if observed_at is not None:
            kwargs["observed_at"] = observed_at
        self._buffer.append(
            Reading(
                plant_id=plant_id,
                metric=metric,
                value=float(value),
                unit=unit,
                source=self.info.display_name,
                quality=max(0.0, min(1.0, float(quality))),
                provider_id=self.info.provider_id,
                channel_id=channel_id or metric,
                simulated=False,
                **kwargs,
            )
        )

    def read(self, plant: Plant) -> list[Reading]:
        matching: list[Reading] = []
        retained: deque[Reading] = deque()
        while self._buffer:
            reading = self._buffer.popleft()
            if reading.plant_id == plant.plant_id:
                matching.append(reading)
            else:
                retained.append(reading)
        self._buffer = retained
        return matching


class SimulatedWaterAdapter(WaterAdapter):
    name = "simulated_irrigation_pump"

    def __init__(self, environment: SimulatedPlantEnvironment) -> None:
        self.environment = environment

    def irrigate(self, plant: Plant, amount_ml: float) -> float:
        delivered = max(0.0, float(amount_ml))
        self.environment.water_mass_g = min(
            self.environment.field_capacity_water_g,
            self.environment.water_mass_g + delivered,
        )
        return delivered
