from __future__ import annotations

"""Human-entered measurements and guided observation requests.

Why this module exists
----------------------
A grower should not need connected hardware to use Plant Medical AI. A person
holding a thermometer, pH pen, EC meter, measuring cup, or scale is still a
valid measurement provider. This module turns those manual measurements into
the same normalized ``Reading`` objects used by simulated and future live
sensors.

Qualitative observations stay separate because phrases such as "roots look
tan" or "leaves are slightly curled" should never be forced into made-up
numbers.
"""

from collections import deque
from dataclasses import dataclass

from .adapters import SensorAdapter
from .domain import Plant, QualitativeObservation, Reading, SensorChannel, SensorProviderInfo


@dataclass(frozen=True)
class GuidedObservationRequest:
    """A plain-language request for one useful manual observation."""

    request_id: str
    plant_id: str
    title: str
    question: str
    reason: str
    metric: str | None = None
    preferred_unit: str | None = None
    position: str | None = None
    instructions: tuple[str, ...] = ()


class HumanMeasurementAdapter(SensorAdapter):
    """Buffers manual numeric measurements until the care engine reads them.

    This intentionally looks like every other sensor provider. The care engine
    does not need a special 'manual mode'. The only special information is
    stored in ``Reading.context`` for provenance and later scientific review.
    """

    def __init__(self) -> None:
        self._buffer: deque[Reading] = deque()
        self._channels: dict[str, SensorChannel] = {}

    @property
    def info(self) -> SensorProviderInfo:
        return SensorProviderInfo(
            provider_id="human_manual",
            display_name="Human-entered measurements",
            mode="manual",
            transport="human_entry",
            simulated=False,
            channels=tuple(self._channels.values()),
        )

    def submit(
        self,
        plant_id: str,
        metric: str,
        value: float,
        unit: str,
        *,
        position: str | None = None,
        method: str = "manual_measurement",
        quality: float = 0.9,
        notes: str | None = None,
    ) -> Reading:
        """Add one manual measurement and return the created reading.

        ``quality`` is confidence in the measurement process, not in the plant
        diagnosis. A calibrated laboratory meter might use a higher value than
        an approximate household measurement.
        """

        channel_id = f"manual_{metric}"
        if channel_id not in self._channels:
            self._channels[channel_id] = SensorChannel(
                channel_id=channel_id,
                metric=metric,
                unit=unit,
                description="Measurement entered by a person",
            )

        context: dict[str, str | float | int | bool] = {
            "entered_by": "human",
            "method": method,
        }
        if position:
            context["position"] = position
        if notes:
            context["notes"] = notes

        reading = Reading(
            plant_id=plant_id,
            metric=metric,
            value=float(value),
            unit=unit,
            source="Human-entered measurement",
            quality=max(0.0, min(1.0, float(quality))),
            provider_id="human_manual",
            channel_id=channel_id,
            simulated=False,
            context=context,
        )
        self._buffer.append(reading)
        return reading

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


class GuidedObservationService:
    """Creates beginner-friendly requests for missing or useful evidence.

    This first slice uses deterministic requests. Later an AI reasoner can
    choose among these requests based on expected information gain.
    """

    def request_canopy_temperature(self, plant: Plant) -> GuidedObservationRequest:
        return GuidedObservationRequest(
            request_id=f"{plant.plant_id}:air-temp-above-canopy",
            plant_id=plant.plant_id,
            title="Check the air near the plant",
            question="What is the air temperature about 15 cm (6 in) above the top leaves?",
            reason="Temperature near the canopy can differ from the rest of the room.",
            metric="air_temp_c",
            preferred_unit="C",
            position="15_cm_above_canopy",
            instructions=(
                "Place the thermometer about 15 cm (6 in) above the top leaves.",
                "Keep the thermometer out of direct lamp or sunlight if possible.",
                "Wait for the reading to settle, then enter the value.",
            ),
        )

    def request_reservoir_temperature(self, plant: Plant) -> GuidedObservationRequest:
        return GuidedObservationRequest(
            request_id=f"{plant.plant_id}:reservoir-temp",
            plant_id=plant.plant_id,
            title="Check the nutrient solution temperature",
            question="What is the water temperature near the plant's roots?",
            reason="Water temperature affects root-zone conditions and dissolved oxygen.",
            metric="reservoir_temp_c",
            preferred_unit="C",
            position="reservoir_near_roots",
            instructions=(
                "Measure the solution near the roots rather than at the room edge of the reservoir.",
                "Let the thermometer stabilize before entering the value.",
            ),
        )

    def make_visual_note(
        self,
        plant: Plant,
        observation_type: str,
        description: str,
        *,
        position: str | None = None,
        confidence: float = 1.0,
    ) -> QualitativeObservation:
        return QualitativeObservation(
            plant_id=plant.plant_id,
            observation_type=observation_type,
            description=description,
            source="human",
            position=position,
            confidence=max(0.0, min(1.0, confidence)),
        )
