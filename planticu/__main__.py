from __future__ import annotations

import argparse
from pathlib import Path

from .adapters import RecordedSensorAdapter, SimulatedPlantEnvironment, SimulatedSensorAdapter, SimulatedWaterAdapter
from .controller import DeterministicController
from .domain import (
    ChallengeProfile,
    Environment,
    Experiment,
    ExperimentMembership,
    GeneticProfile,
    KnowledgeEntry,
    Plant,
    TraitObservation,
)
from .engine import PlantCareEngine
from .genomics import import_vcf
from .guided_observation import GuidedObservationService, HumanMeasurementAdapter
from .knowledge import KnowledgeContext, KnowledgeResolver
from .perception import SimulatedVisionAdapter
from .research import summarize_trait_by_cohort
from .store import PlantStore
from .supervisor import PlantSupervisor


def make_demo_plant(plant_id: str = "plant-001") -> Plant:
    return Plant(
        plant_id=plant_id,
        display_name="Demo Plant 001",
        species="Fragaria × ananassa",
        cultivar="Albion",
        medium="coco/perlite",
        growth_stage="vegetative",
        container_volume_l=11.4,
        genetic_line_id="albion-demo-line",
        identity_confidence=0.94,
    )


def demo(steps: int, database: str) -> None:
    plant = make_demo_plant()
    env = SimulatedPlantEnvironment(
        water_mass_g=700.0,
        field_capacity_water_g=900.0,
        daily_water_use_ml=520.0,
    )
    sensors = SimulatedSensorAdapter(env)
    water = SimulatedWaterAdapter(env)
    store = PlantStore(database)
    engine = PlantCareEngine(store, sensors, PlantSupervisor(), DeterministicController(water))

    print("[PLANT_MEDICAL] demo start")
    print(f"[PLANT] id={plant.plant_id} species={plant.species} cultivar={plant.cultivar} medium={plant.medium}")

    try:
        for index in range(1, steps + 1):
            env.advance_hours(2.0)
            result = engine.run_cycle(plant)
            values = {reading.metric: reading.value for reading in result.readings}
            print(
                f"[CYCLE {index:02d}] moisture={values['substrate_moisture_pct']:.1f}% "
                f"pot_mass={values['pot_mass_g']:.1f}g "
                f"state={result.state.hydration}/{result.state.stress} "
                f"state_confidence={result.state.confidence:.2f}"
            )

            for prescription in result.prescriptions:
                print(
                    f"  [PRESCRIPTION] {prescription.capability}={prescription.amount:.1f}{prescription.unit} "
                    f"confidence={prescription.confidence:.2f} reason={prescription.reason}"
                )
                for evidence in prescription.evidence:
                    print(f"    evidence: {evidence}")

            for treatment in result.treatments:
                clamp = " CLAMPED_BY_SAFETY" if treatment.safety_clamped else ""
                print(
                    f"  [TREATMENT] requested={treatment.requested_amount:.1f}{treatment.unit} "
                    f"executed={treatment.executed_amount:.1f}{treatment.unit}{clamp}"
                )

            for alert in result.alerts:
                print(f"  [ALERT:{alert.severity.upper()}] {alert.message}")

        print(f"[DATABASE] {Path(database).resolve()}")
        print(f"[COUNTS] {store.counts()}")
    finally:
        store.close()


def research_demo(database: str, vcf_path: str) -> None:
    plant = make_demo_plant("plant-desert-001")
    store = PlantStore(database)

    environment = Environment(
        environment_id="env-arid-chamber-01",
        name="Arid Research Chamber 01",
        environment_type="controlled_chamber",
        description="Simulated hot, dry, resource-constrained research environment.",
    )
    challenge = ChallengeProfile(
        challenge_id="challenge-arid-01",
        name="Arid Water Efficiency",
        description="Measure performance under reduced water allocation without claiming genetic causation.",
        constraints={
            "day_temp_c": 42.0,
            "night_temp_c": 21.0,
            "relative_humidity_pct": 25.0,
            "water_allocation_fraction_of_control": 0.55,
        },
        selection_goals=("water_use_efficiency", "growth_retention", "recovery_after_stress"),
    )
    experiment = Experiment(
        experiment_id="exp-arid-001",
        name="Arid Line Evaluation",
        environment_id=environment.environment_id,
        challenge_id=challenge.challenge_id,
        hypothesis="Some lines may retain growth with less water; observations require replication.",
        status="active",
    )

    profile_template = GeneticProfile(
        genetic_profile_id="genome-plant-desert-001",
        plant_id=plant.plant_id,
        source_format="VCF",
        source_name="pending",
        source_sha256="pending",
        reference_genome="demo-reference-v1",
        ownership_scope="private",
    )
    profile, variants = import_vcf(vcf_path, profile_template)

    vision = SimulatedVisionAdapter()
    candidates, perception = vision.identify_plant(plant, "demo://phone-photo-001.jpg")

    try:
        store.upsert_plant(plant)
        store.upsert_environment(environment)
        store.upsert_challenge(challenge)
        store.upsert_experiment(experiment)
        store.enroll(ExperimentMembership(experiment.experiment_id, plant.plant_id, cohort="reduced-water"))
        store.record_genetic_profile(profile, variants)
        store.record_perception(perception)

        traits = [
            TraitObservation(
                plant_id=plant.plant_id,
                trait="water_use_efficiency",
                value=18.4,
                unit="g_fresh_mass_per_L",
                method="harvest_mass_divided_by_irrigation_volume",
                environment_id=environment.environment_id,
                experiment_id=experiment.experiment_id,
            ),
            TraitObservation(
                plant_id=plant.plant_id,
                trait="growth_retention",
                value=86.0,
                unit="percent_of_control",
                method="canopy_growth_rate_ratio",
                environment_id=environment.environment_id,
                experiment_id=experiment.experiment_id,
            ),
        ]
        for trait in traits:
            store.record_trait(trait)

        summaries = summarize_trait_by_cohort(
            {plant.plant_id: "reduced-water"},
            traits,
            "water_use_efficiency",
        )

        print("[RESEARCH_DEMO] evidence-first plant research record")
        print(f"[ENVIRONMENT] {environment.name} type={environment.environment_type}")
        print(f"[CHALLENGE] {challenge.name} constraints={challenge.constraints}")
        print(f"[EXPERIMENT] {experiment.name} status={experiment.status}")
        print(
            f"[VISION] top_candidate={candidates[0].species} "
            f"confidence={candidates[0].confidence:.2f} model={perception.model_name}"
        )
        print(
            f"[GENETICS] format={profile.source_format} variants={profile.variant_count} "
            f"scope={profile.ownership_scope} sha256={profile.source_sha256[:12]}..."
        )
        for trait in traits:
            print(f"[TRAIT] {trait.trait}={trait.value}{trait.unit} method={trait.method}")
        for summary in summaries:
            print(
                f"[DESCRIPTIVE_ONLY] cohort={summary.cohort} trait={summary.trait} "
                f"n={summary.count} mean={summary.mean_value:.2f}{summary.unit}"
            )
        print("[CAUSATION] no genetic or causal claim made from this single subject")
        print(f"[DATABASE] {Path(database).resolve()}")
        print(f"[COUNTS] {store.counts()}")
    finally:
        store.close()



def replay_demo(database: str, csv_path: str) -> None:
    plant = make_demo_plant("plant-replay-001")
    provider = RecordedSensorAdapter(csv_path, provider_id="replay_csv_demo")
    store = PlantStore(database)
    engine = PlantCareEngine(store, provider, PlantSupervisor(), controller=None)

    print("[REPLAY_DEMO] normalized recorded sensor data; monitor-only mode")
    print(f"[PROVIDER] id={provider.info.provider_id} mode={provider.info.mode} transport={provider.info.transport}")
    try:
        frame = 0
        while not provider.exhausted:
            frame += 1
            result = engine.run_cycle(plant)
            values = {reading.metric: reading.value for reading in result.readings}
            print(
                f"[FRAME {frame:02d}] metrics={len(result.readings)} "
                f"moisture={values.get('substrate_moisture_pct', float('nan')):.1f}% "
                f"state={result.state.hydration}/{result.state.stress}"
            )
            for prescription in result.prescriptions:
                print(
                    f"  [RECOMMENDATION_ONLY] {prescription.capability}={prescription.amount:.1f}{prescription.unit} "
                    f"confidence={prescription.confidence:.2f}"
                )
        print("[ACTUATION] disabled: no controller installed")
        print(f"[COUNTS] {store.counts()}")
    finally:
        store.close()


def guided_demo(database: str) -> None:
    """Show that a hands-on grower can provide evidence without hardware."""

    plant = make_demo_plant("plant-guided-001")
    manual = HumanMeasurementAdapter()
    guide = GuidedObservationService()
    store = PlantStore(database)

    # The UI would show this request before a human enters the value.
    request = guide.request_canopy_temperature(plant)
    print("[GUIDED_OBSERVATION] beginner/manual grower path")
    print(f"[REQUEST] {request.question}")
    print(f"[WHY] {request.reason}")
    print(f"[POSITION] {request.position}")

    # These values stand in for measurements a person entered in the app.
    # Fahrenheit is intentional: normal ingestion converts it to canonical C.
    manual.submit(
        plant.plant_id,
        "air_temp_c",
        78.8,
        "F",
        position="15_cm_above_canopy",
        method="handheld_thermometer",
        notes="Kept thermometer out of direct lamp light.",
    )
    manual.submit(
        plant.plant_id,
        "substrate_moisture_pct",
        58.0,
        "%",
        position="root_zone_center",
        method="handheld_moisture_meter",
        quality=0.80,
    )
    manual.submit(
        plant.plant_id,
        "pot_mass_g",
        3.18,
        "kg",
        position="whole_container",
        method="kitchen_scale",
        quality=0.95,
    )

    engine = PlantCareEngine(store, manual, PlantSupervisor(), controller=None)
    result = engine.run_cycle(plant)

    visual_note = guide.make_visual_note(
        plant,
        observation_type="leaf_posture",
        description="Leaves are slightly relaxed but not limp.",
        position="whole_canopy",
    )
    store.record_qualitative_observation(visual_note)

    print("[MANUAL_READINGS]")
    for reading in result.readings:
        position = reading.context.get("position", "unspecified")
        method = reading.context.get("method", "unspecified")
        print(
            f"  {reading.metric}={reading.value:.2f}{reading.unit} "
            f"position={position} method={method}"
        )
    for prescription in result.prescriptions:
        print(
            f"[RECOMMENDATION_ONLY] {prescription.capability}={prescription.amount:.1f}{prescription.unit} "
            f"confidence={prescription.confidence:.2f}"
        )
    print(f"[VISUAL_NOTE] {visual_note.description}")

    # Living Almanac example: broader knowledge is preserved beside specific knowledge.
    entries = [
        KnowledgeEntry(
            knowledge_id="knowledge-established-water",
            topic="watering",
            scope_type="established",
            scope_key=None,
            statement="Established horticultural guidance should be used as the starting baseline.",
            source_type="curated_horticulture",
            confidence=0.95,
            validation_status="established",
            evidence_count=1,
        ),
        KnowledgeEntry(
            knowledge_id="knowledge-species-strawberry-water",
            topic="watering",
            scope_type="species",
            scope_key=plant.species,
            statement="Species-level strawberry watering knowledge applies when more specific evidence is unavailable.",
            source_type="validated_aggregate",
            confidence=0.88,
            validation_status="validated",
            evidence_count=1200,
        ),
        KnowledgeEntry(
            knowledge_id="knowledge-plant-guided-water",
            topic="watering",
            scope_type="plant",
            scope_key=plant.plant_id,
            statement="This individual has recently used water slightly faster than its earlier baseline.",
            source_type="individual_history",
            confidence=0.82,
            validation_status="observed",
            evidence_count=7,
        ),
    ]
    for entry in entries:
        store.upsert_knowledge(entry)

    resolved = KnowledgeResolver().relevant_entries(
        store.list_knowledge(topic="watering"),
        KnowledgeContext(plant=plant, garden_id="demo-garden"),
        topic="watering",
    )
    print("[LIVING_ALMANAC] broad -> specific; nothing overwritten")
    for entry in resolved:
        print(
            f"  scope={entry.scope_type:<11} confidence={entry.confidence:.2f} "
            f"status={entry.validation_status} statement={entry.statement}"
        )

    print("[ACTUATION] disabled: hands-on grower keeps final control")
    print(f"[COUNTS] {store.counts()}")
    store.close()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plant Medical AI vertical slice")
    sub = parser.add_subparsers(dest="command", required=True)

    demo_parser = sub.add_parser("demo", help="run the simulated one-plant care slice")
    demo_parser.add_argument("--steps", type=int, default=18)
    demo_parser.add_argument("--database", default="plant_medical_demo.sqlite3")

    research_parser = sub.add_parser("research-demo", help="exercise vision/genetics/environment research contracts")
    research_parser.add_argument("--database", default="plant_research_demo.sqlite3")
    research_parser.add_argument(
        "--vcf",
        default=str(Path(__file__).resolve().parents[1] / "examples" / "demo_plant.vcf"),
    )

    replay_parser = sub.add_parser("replay-demo", help="run care inference over normalized recorded sensor data")
    replay_parser.add_argument("--database", default="plant_replay_demo.sqlite3")
    replay_parser.add_argument(
        "--csv",
        default=str(Path(__file__).resolve().parents[1] / "examples" / "sensor_replay.csv"),
    )

    guided_parser = sub.add_parser(
        "guided-demo",
        help="exercise human-entered measurements and layered Living Almanac knowledge",
    )
    guided_parser.add_argument("--database", default="plant_guided_demo.sqlite3")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "demo":
        demo(max(1, args.steps), args.database)
    elif args.command == "research-demo":
        research_demo(args.database, args.vcf)
    elif args.command == "replay-demo":
        replay_demo(args.database, args.csv)
    elif args.command == "guided-demo":
        guided_demo(args.database)


if __name__ == "__main__":
    main()
