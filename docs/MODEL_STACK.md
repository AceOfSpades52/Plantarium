# Model stack

The product should use specialized models behind stable contracts rather than one giant model.

1. **Multimodal vision-language model** — beginner onboarding, setup understanding, visible symptoms, conversational explanation.
2. **Detection/segmentation model** — leaves, flowers, fruit, canopy, damaged regions, quantitative image measurements.
3. **Plant identification model** — species candidates with uncertainty; cultivar only when evidence supports it.
4. **Time-series/state model** — learns normal physiology for an individual plant and estimates latent state.
5. **Forecast model** — irrigation/refill/harvest/resource forecasts.
6. **Anomaly model** — detects combinations that deviate from a plant/setup baseline.
7. **Reasoning/diagnostic model** — combines observations, history, knowledge, and uncertainty.
8. **Prescription model** — proposes bounded target changes with evidence.
9. **Genomics models** — annotation, kinship, QTL/GWAS, genotype-by-environment, genomic selection.
10. **Discovery models** — search cross-grow data for candidate relationships, then request validation rather than declaring causation.

The deterministic controller is intentionally **not AI**.
