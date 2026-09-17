from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from planticu.adapters import (
    BufferedSensorAdapter,
    CompositeSensorAdapter,
    RecordedSensorAdapter,
    SimulatedPlantEnvironment,
    SimulatedSensorAdapter,
    SimulatedWaterAdapter,
)
from planticu.controller import DeterministicController
from planticu.domain import Plant, Reading, SensorChannel, readings_by_metric
from planticu.engine import PlantCareEngine
from planticu.metrics import normalize_reading
from planticu.store import PlantStore
from planticu.supervisor import PlantSupervisor


class SensorProviderTests(unittest.TestCase):
    def make_plant(self, plant_id: str = "provider-p1") -> Plant:
        return Plant(
            plant_id=plant_id,
            display_name="Provider Test Plant",
            species="Test species",
            cultivar=None,
            medium="coco",
            growth_stage="vegetative",
            container_volume_l=3.0,
        )

    def test_simulated_readings_carry_provenance(self):
        plant = self.make_plant()
        provider = SimulatedSensorAdapter(SimulatedPlantEnvironment())
        readings = provider.read(plant)
        self.assertTrue(readings)
        self.assertTrue(all(r.simulated for r in readings))
        self.assertTrue(all(r.provider_id == "simulated_station" for r in readings))
        self.assertTrue(all(r.channel_id for r in readings))

    def test_composite_provider_can_mix_simulated_and_live_inputs(self):
        plant = self.make_plant()
        simulated = SimulatedSensorAdapter(SimulatedPlantEnvironment())
        live = BufferedSensorAdapter(
            "future_mqtt_node",
            "Future MQTT node",
            "mqtt",
            (SensorChannel("leaf_temp", "leaf_temp_c", "C"),),
        )
        live.submit(plant.plant_id, "leaf_temp_c", 26.4, "C", channel_id="leaf_temp")
        combined = CompositeSensorAdapter((simulated, live))
        readings = combined.read(plant)
        by_metric = readings_by_metric(readings)
        self.assertIn("substrate_moisture_pct", by_metric)
        self.assertEqual(26.4, by_metric["leaf_temp_c"].value)
        self.assertFalse(by_metric["leaf_temp_c"].simulated)

    def test_csv_replay_consumes_frames_as_normalized_readings(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "readings.csv"
            path.write_text(
                "sample,plant_id,metric,value,unit,source,quality,channel_id\n"
                "1,replay-p1,pot_mass_g,3000,g,scale,0.99,scale_1\n"
                "1,replay-p1,substrate_moisture_pct,61,%,probe,0.9,moisture_1\n"
                "2,replay-p1,pot_mass_g,2950,g,scale,0.99,scale_1\n",
                encoding="utf-8",
            )
            provider = RecordedSensorAdapter(path)
            plant = self.make_plant("replay-p1")
            frame1 = provider.read(plant)
            frame2 = provider.read(plant)
            self.assertEqual(2, len(frame1))
            self.assertEqual(1, len(frame2))
            self.assertTrue(all(not r.simulated for r in frame1))
            self.assertEqual("recorded_csv", frame1[0].provider_id)

    def test_engine_registers_provider_and_preserves_reading_provenance(self):
        plant = self.make_plant()
        environment = SimulatedPlantEnvironment(water_mass_g=500.0, field_capacity_water_g=900.0)
        provider = SimulatedSensorAdapter(environment)
        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            store = PlantStore(handle.name)
            engine = PlantCareEngine(
                store,
                provider,
                PlantSupervisor(),
                DeterministicController(SimulatedWaterAdapter(environment)),
            )
            engine.run_cycle(plant)
            counts = store.counts()
            self.assertEqual(1, counts["sensor_providers"])
            self.assertEqual(len(provider.info.channels), counts["sensor_channels"])
            row = store.conn.execute(
                "SELECT provider_id, channel_id, simulated FROM observations LIMIT 1"
            ).fetchone()
            self.assertEqual(provider.info.provider_id, row["provider_id"])
            self.assertTrue(row["channel_id"])
            self.assertEqual(1, row["simulated"])
            store.close()



    def test_common_device_units_normalize_at_provider_boundary(self):
        temp = normalize_reading(Reading("p", "air_temp_c", 77.0, "F", "device"))
        mass = normalize_reading(Reading("p", "pot_mass_g", 3.2, "kg", "device"))
        ec = normalize_reading(Reading("p", "root_ec_ms_cm", 1500.0, "uS/cm", "device"))
        self.assertAlmostEqual(25.0, temp.value, places=5)
        self.assertEqual("C", temp.unit)
        self.assertAlmostEqual(3200.0, mass.value, places=5)
        self.assertEqual("g", mass.unit)
        self.assertAlmostEqual(1.5, ec.value, places=5)
        self.assertEqual("mS/cm", ec.unit)

    def test_monitor_only_engine_recommends_but_never_executes(self):
        plant = self.make_plant()
        environment = SimulatedPlantEnvironment(water_mass_g=500.0, field_capacity_water_g=900.0)
        provider = SimulatedSensorAdapter(environment)
        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            store = PlantStore(handle.name)
            engine = PlantCareEngine(store, provider, PlantSupervisor(), controller=None)
            result = engine.run_cycle(plant)
            self.assertTrue(result.prescriptions)
            self.assertEqual([], result.treatments)
            self.assertEqual(0, store.counts()["treatments"])
            store.close()

    def test_best_quality_reading_wins_when_two_providers_share_metric(self):
        low = Reading("p", "air_temp_c", 21.0, "C", "low", quality=0.4)
        high = Reading("p", "air_temp_c", 24.0, "C", "high", quality=0.95)
        self.assertEqual(24.0, readings_by_metric([high, low])["air_temp_c"].value)
        self.assertEqual(24.0, readings_by_metric([low, high])["air_temp_c"].value)


if __name__ == "__main__":
    unittest.main()
