import tempfile
import unittest

from planticu.adapters import SimulatedPlantEnvironment, SimulatedSensorAdapter, SimulatedWaterAdapter
from planticu.controller import DeterministicController, WaterSafetyLimits
from planticu.domain import Plant
from planticu.engine import PlantCareEngine
from planticu.store import PlantStore
from planticu.supervisor import PlantSupervisor


class VerticalSliceTests(unittest.TestCase):
    def make_plant(self):
        return Plant(
            plant_id="p1",
            display_name="P1",
            species="test species",
            cultivar="test cultivar",
            medium="coco",
            growth_stage="vegetative",
            container_volume_l=10.0,
            genetic_line_id="line-a",
        )

    def test_dry_plant_generates_prescription_and_safe_treatment(self):
        env = SimulatedPlantEnvironment(water_mass_g=450.0, field_capacity_water_g=900.0)
        sensor = SimulatedSensorAdapter(env)
        water = SimulatedWaterAdapter(env)
        supervisor = PlantSupervisor()
        controller = DeterministicController(water, WaterSafetyLimits(max_single_dose_ml=100.0))

        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            store = PlantStore(handle.name)
            engine = PlantCareEngine(store, sensor, supervisor, controller)
            result = engine.run_cycle(self.make_plant())

            self.assertEqual(1, len(result.prescriptions))
            self.assertEqual(1, len(result.treatments))
            self.assertLessEqual(result.treatments[0].executed_amount, 100.0)
            self.assertTrue(result.treatments[0].safety_clamped)
            counts = store.counts()
            self.assertEqual(1, counts["plants"])
            self.assertGreaterEqual(counts["observations"], 4)
            self.assertEqual(1, counts["treatments"])
            store.close()

    def test_wet_plant_does_not_irrigate(self):
        env = SimulatedPlantEnvironment(water_mass_g=800.0, field_capacity_water_g=900.0)
        sensor = SimulatedSensorAdapter(env)
        water = SimulatedWaterAdapter(env)
        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            store = PlantStore(handle.name)
            engine = PlantCareEngine(store, sensor, PlantSupervisor(), DeterministicController(water))
            result = engine.run_cycle(self.make_plant())
            self.assertEqual([], result.prescriptions)
            self.assertEqual([], result.treatments)
            store.close()

    def test_lineage_is_persisted(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            store = PlantStore(handle.name)
            plant = self.make_plant()
            store.upsert_plant(plant)
            row = store.conn.execute("SELECT genetic_line_id FROM plants WHERE plant_id='p1'").fetchone()
            self.assertEqual("line-a", row[0])
            store.close()


if __name__ == "__main__":
    unittest.main()
