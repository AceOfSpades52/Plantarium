from __future__ import annotations

from dataclasses import dataclass

from .adapters import SensorAdapter
from .controller import DeterministicController
from .domain import Alert, Plant, PlantStateEstimate, Prescription, Reading, Treatment
from .state import PlantStateEstimator
from .metrics import normalize_readings
from .store import PlantStore
from .supervisor import PlantSupervisor


@dataclass
class CycleResult:
    readings: list[Reading]
    state: PlantStateEstimate
    prescriptions: list[Prescription]
    treatments: list[Treatment]
    alerts: list[Alert]


class PlantCareEngine:
    def __init__(
        self,
        store: PlantStore,
        sensor_adapter: SensorAdapter,
        supervisor: PlantSupervisor,
        controller: DeterministicController | None,
        state_estimator: PlantStateEstimator | None = None,
    ) -> None:
        self.store = store
        self.sensor_adapter = sensor_adapter
        self.supervisor = supervisor
        self.controller = controller
        self.state_estimator = state_estimator or PlantStateEstimator()

    def run_cycle(self, plant: Plant) -> CycleResult:
        self.store.upsert_plant(plant)
        for provider in self.sensor_adapter.provider_infos():
            self.store.upsert_sensor_provider(provider)

        readings = normalize_readings(self.sensor_adapter.read(plant))
        self.store.record_readings(readings)

        state = self.state_estimator.estimate(plant, readings)
        self.store.record_state_estimate(state)

        prescriptions, alerts = self.supervisor.assess(plant, readings)
        for alert in alerts:
            self.store.record_alert(alert)

        treatments: list[Treatment] = []
        if self.controller is not None:
            for prescription in prescriptions:
                treatment = self.controller.execute(plant, prescription)
                if treatment is not None:
                    self.store.record_treatment(treatment)
                    treatments.append(treatment)

        return CycleResult(readings, state, prescriptions, treatments, alerts)
