import tempfile
import unittest
from pathlib import Path

from planticu.domain import (
    ChallengeProfile,
    Environment,
    Experiment,
    ExperimentMembership,
    GeneticProfile,
    Plant,
    TraitObservation,
)
from planticu.genomics import import_vcf
from planticu.perception import SimulatedVisionAdapter
from planticu.research import summarize_trait_by_cohort
from planticu.store import PlantStore


class ResearchFoundationTests(unittest.TestCase):
    def make_plant(self):
        return Plant(
            plant_id="research-p1",
            display_name="Research Plant",
            species="unknown",
            cultivar=None,
            medium="unknown",
            growth_stage="unknown",
            container_volume_l=0.0,
            genetic_line_id="line-r",
        )

    def test_simulated_perception_keeps_confidence_and_source(self):
        plant = self.make_plant()
        candidates, observation = SimulatedVisionAdapter().identify_plant(plant, "photo://1")
        self.assertGreater(candidates[0].confidence, candidates[1].confidence)
        self.assertEqual("photo://1", observation.source_asset)
        self.assertEqual("plant_identity", observation.observation_type)

    def test_vcf_import_preserves_variants_and_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.vcf"
            path.write_text(
                "##fileformat=VCFv4.2\n"
                "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
                "1\t10\trs1\tA\tG\t90\tPASS\t.\tGT\t0/1\n"
                "2\t20\t.\tC\tT,G\t.\tPASS\t.\tGT\t1/2\n",
                encoding="utf-8",
            )
            template = GeneticProfile(
                genetic_profile_id="gp1",
                plant_id="research-p1",
                source_format="VCF",
                source_name="pending",
                source_sha256="pending",
            )
            profile, variants = import_vcf(path, template)
            self.assertEqual(3, profile.variant_count)
            self.assertEqual(64, len(profile.source_sha256))
            self.assertEqual("0/1", variants[0].genotype)
            self.assertEqual({"T", "G"}, {variants[1].alternate, variants[2].alternate})

    def test_research_objects_persist_separately(self):
        plant = self.make_plant()
        environment = Environment("env1", "Chamber", "controlled_chamber")
        challenge = ChallengeProfile(
            "ch1", "Dry", "Reduced water", {"water_fraction": 0.5}, ("water_use_efficiency",)
        )
        experiment = Experiment("exp1", "Trial", "env1", "ch1", status="active")
        trait = TraitObservation(
            plant_id=plant.plant_id,
            trait="water_use_efficiency",
            value=12.5,
            unit="g/L",
            method="measured",
            environment_id=environment.environment_id,
            experiment_id=experiment.experiment_id,
        )

        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            store = PlantStore(handle.name)
            store.upsert_plant(plant)
            store.upsert_environment(environment)
            store.upsert_challenge(challenge)
            store.upsert_experiment(experiment)
            store.enroll(ExperimentMembership("exp1", plant.plant_id, "stress"))
            store.record_trait(trait)
            counts = store.counts()
            self.assertEqual(1, counts["environments"])
            self.assertEqual(1, counts["challenge_profiles"])
            self.assertEqual(1, counts["experiments"])
            self.assertEqual(1, counts["experiment_memberships"])
            self.assertEqual(1, counts["trait_observations"])
            store.close()

    def test_cohort_summary_is_descriptive_only_math(self):
        observations = [
            TraitObservation("a", "yield", 10.0, "g", "scale"),
            TraitObservation("b", "yield", 14.0, "g", "scale"),
        ]
        result = summarize_trait_by_cohort({"a": "control", "b": "control"}, observations, "yield")
        self.assertEqual(1, len(result))
        self.assertEqual(12.0, result[0].mean_value)
        self.assertEqual(2, result[0].count)


if __name__ == "__main__":
    unittest.main()
