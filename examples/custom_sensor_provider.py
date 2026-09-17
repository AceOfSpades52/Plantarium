"""Minimal template for a future real sensor integration.

Replace `read_from_your_device()` with MQTT/serial/BLE/GPIO/API code. Nothing in
PlantCareEngine needs to change.
"""

from planticu.adapters import SensorAdapter
from planticu.domain import Plant, Reading, SensorChannel, SensorProviderInfo


class MyRealSensorProvider(SensorAdapter):
    @property
    def info(self) -> SensorProviderInfo:
        return SensorProviderInfo(
            provider_id="my_real_node_01",
            display_name="My real plant node",
            mode="live",
            transport="replace-with-mqtt-serial-ble-http-etc",
            simulated=False,
            channels=(
                SensorChannel("scale", "pot_mass_g", "g"),
                SensorChannel("root_probe", "substrate_moisture_pct", "%"),
            ),
        )

    def read_from_your_device(self) -> tuple[float, float]:
        raise NotImplementedError("Connect the actual transport here")

    def read(self, plant: Plant) -> list[Reading]:
        pot_mass_g, moisture_pct = self.read_from_your_device()
        return [
            Reading(
                plant.plant_id,
                "pot_mass_g",
                pot_mass_g,
                "g",
                self.info.display_name,
                provider_id=self.info.provider_id,
                channel_id="scale",
                simulated=False,
            ),
            Reading(
                plant.plant_id,
                "substrate_moisture_pct",
                moisture_pct,
                "%",
                self.info.display_name,
                provider_id=self.info.provider_id,
                channel_id="root_probe",
                simulated=False,
            ),
        ]
